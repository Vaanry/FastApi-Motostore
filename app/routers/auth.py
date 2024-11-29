import asyncio
import random
from datetime import datetime, timedelta
from typing import Annotated

from aiogram import Bot, Dispatcher
from app.backend.db_depends import get_db
from app.models import Users
from app.schemas import CreateUser
from app.utils import remove_code_after_timeout
from fastapi import APIRouter, Depends, Form, HTTPException, status, Response
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.security import (
    HTTPBasic,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

bot = Bot(token=settings.token)
dp = Dispatcher()

templates = Jinja2Templates(directory="templates")
router.mount("/static", StaticFiles(directory="static"), name="static")

# Глобальный словарь для хранения кодов подтверждения
verification_codes = {}
hash_passwords = {}


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """
    Отображает HTML-форму для входа.
    """
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def send_code_to_telegram(
    request: Request,
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    username: str = Form(...),
    password: str = Form(...),
):

    try:
        user = CreateUser(username=username, password=password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")

    tg_id = await db.scalar(
        select(Users.tg_id).where(Users.username == user.username)
    )
    if tg_id is None:
        raise HTTPException(
            status_code=400,
            detail="Вас нет в базе. Пожалуйста, зарегистрируйтесь через наш бот.",
        )

    # Генерируем код подтверждения
    verification_code = str(random.randint(100000, 999999))
    verification_codes[user.username] = verification_code
    asyncio.create_task(remove_code_after_timeout(verification_codes, username))

    hash_passwords[user.username] = bcrypt_context.hash(user.password)
    asyncio.create_task(remove_code_after_timeout(hash_passwords, username))

    await bot.send_message(
        tg_id, f"Ваш код подтверждения: {verification_code}"
    )

    return templates.TemplateResponse("verify.html", {"request": request})


# 2. Обработка формы и проверка кода
@router.post("/verify-code/")
async def verify_code(
    db: Annotated[AsyncSession, Depends(get_db)],
    username: str = Form(...),
    code: str = Form(...),
):
    # Проверяем, есть ли пользователь
    if username not in verification_codes:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем код подтверждения
    if verification_codes.get(username) == code:
        del verification_codes[username]  # Удаляем код после подтверждения

        password = hash_passwords.get(username)
        del hash_passwords[username]

        await db.execute(
            update(Users)
            .where(Users.username == username)
            .values(
                hashed_password=password,
            )
        )
        await db.commit()
        return {"status": "Успешно подтверждено!"}
    else:
        raise HTTPException(
            status_code=400, detail="Неверный код подтверждения"
        )


async def authanticate_user(
    db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str
):
    user = await db.scalar(select(Users).where(Users.username == username))
    if (
        not user
        or not bcrypt_context.verify(password, user.hashed_password)
        or user.active is False
        or user.hashed_password is None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def create_access_token(
    username: str, id: int, is_admin: bool, expires_delta: timedelta
):

    encode = {"sub": username, "id": id, "is_admin": is_admin}
    expires = datetime.now() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        id: int = payload.get("id")
        is_admin: str = payload.get("is_admin")
        expire = payload.get("exp")
        if username is None or id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate use1r",
            )
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied",
            )
        if datetime.now() > datetime.fromtimestamp(expire):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Token expired!"
            )

        return {"username": username, "id": id, "is_admin": is_admin}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user",
        )


@router.post("/token")
async def login(response: Response, 
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user = await authanticate_user(db, form_data.username, form_data.password)

    if not user or user.active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user",
        )
    token = await create_access_token(
        user.username,
        user.id,
        user.is_admin,
        expires_delta=timedelta(minutes=20),
    )
    response.set_cookie(key="users_access_token", value=token, httponly=True)
    
    return {"access_token": token, "token_type": "bearer"}


def get_token(request: Request):
    token = request.cookies.get('users_access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not found')
    return token


async def get_current_user1(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен не валидный!')

    expire = payload.get('exp')
    if expire is None:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied",
        )
    if datetime.now() > datetime.fromtimestamp(expire):
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Token expired!"
        )

    username: str = payload.get("sub")
    id: int = payload.get("id")
    is_admin: str = payload.get("is_admin")
    if username is None or id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate use1r",
        )

    return {"username": username, "id": id, "is_admin": is_admin}


@router.get("/read_current_user")
async def read_current_user(user: Users = Depends(get_current_user1)):
    return {"User": user}


@router.get("/password", response_class=HTMLResponse)
async def change_password(request: Request,
    get_user: Annotated[dict, Depends(get_current_user1)],
    ):
    """
    Отображает HTML-форму для смены пароля.
    """
    return templates.TemplateResponse("password.html", {"request": request})


@router.post("/password")
async def send_change_code_to_telegram(
    request: Request,
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    get_user: Annotated[dict, Depends(get_current_user)],
    password: str = Form(...),
):

    try:
        password = CreateUser(password=password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")

    id = get_user.get("id")
    tg_id = await db.scalar(
        select(Users.tg_id).where(Users.id == id)
    )
    # Генерируем код подтверждения
    verification_code = str(random.randint(100000, 999999))
    verification_codes[id] = verification_code
    asyncio.create_task(remove_code_after_timeout(verification_codes, id))

    hash_passwords[id] = bcrypt_context.hash(password)
    asyncio.create_task(remove_code_after_timeout(hash_passwords, id))

    await bot.send_message(
        tg_id, f"Ваш код подтверждения: {verification_code}"
    )

    return templates.TemplateResponse("verify_change.html", {"request": request})


@router.post("/change_verify/")
async def change_verify_code(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    code: str = Form(...),
):

    id = get_user.get("id")
    # Проверяем, есть ли пользователь
    if id not in verification_codes:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем код подтверждения
    if verification_codes.get(id) == code:
        del verification_codes[id]  # Удаляем код после подтверждения

        password = hash_passwords.get(id)
        del hash_passwords[id]

        await db.execute(
            update(Users)
            .where(Users.id == id)
            .values(
                hashed_password=password,
            )
        )
        await db.commit()
        return {"status": "Успешно подтверждено!"}
    else:
        raise HTTPException(
            status_code=400, detail="Неверный код подтверждения"
        )
