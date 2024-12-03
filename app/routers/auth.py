import asyncio
import random
from datetime import datetime, timedelta
from typing import Annotated

from aiogram import Bot, Dispatcher
from app.backend.db_depends import get_db
from app.models import Users
from app.schemas import CreateUser
from app.utils import remove_code_after_timeout
from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

bot = Bot(token=settings.token)
dp = Dispatcher()

templates = Jinja2Templates(directory="templates")
templates.env.globals["is_authenticated"] = (
    lambda request: hasattr(request.state, "user")
    and request.state.user is not None
)
router.mount("/static", StaticFiles(directory="static"), name="static")

# Глобальный словарь для хранения кодов подтверждения
verification_codes = {}
hash_passwords = {}


@router.get("/registration", response_class=HTMLResponse)
async def registration_form(request: Request):
    """
    Отображает HTML-форму для регистрации.
    """
    return templates.TemplateResponse(
        "login.html", {"request": request, "is_registration": True}
    )


@router.post("/registration")
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
    asyncio.create_task(
        remove_code_after_timeout(verification_codes, username)
    )

    hash_passwords[user.username] = bcrypt_context.hash(user.password)
    asyncio.create_task(remove_code_after_timeout(hash_passwords, username))

    await bot.send_message(
        tg_id, f"Ваш код подтверждения: {verification_code}"
    )

    return templates.TemplateResponse("verify.html", {"request": request})


# 2. Обработка формы и проверка кода
@router.post("/verify-registration/")
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
    db: Annotated[AsyncSession, Depends(get_db)], user_data: CreateUser
):
    user = await db.scalar(
        select(Users).where(Users.username == user_data.username)
    )
    if (
        not user
        or not bcrypt_context.verify(user_data.password, user.hashed_password)
        or user.active is False
        or user.hashed_password is None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/login/", response_class=HTMLResponse)
async def login_form(request: Request):
    """
    Отображает HTML-форму для входа.
    """
    return templates.TemplateResponse(
        "login.html", {"request": request, "is_registration": False}
    )


async def create_access_token(
    username: str, id: int, is_admin: bool, expires_delta: timedelta
):

    encode = {"sub": username, "id": id, "is_admin": is_admin}
    expires = datetime.now() + expires_delta
    encode.update({"exp": datetime.timestamp(expires)})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login/")
async def auth_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):

    try:
        user_data = CreateUser(username=username, password=password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")

    check = await authanticate_user(db, user_data)
    if check is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )
    access_token = await create_access_token(
        check.username,
        check.id,
        check.is_admin,
        timedelta(weeks=2),
    )
    response.set_cookie(
        key="users_access_token",
        value=access_token,
        httponly=True,
        secure=False,
        path="/",
    )

    return RedirectResponse(
        url="/user/profile/",
        status_code=status.HTTP_302_FOUND,
        headers=response.headers,
    )


def get_token(request: Request):
    token = request.cookies.get("users_access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found"
        )
    return token


async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истёк. Пожалуйста, войдите снова.",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не валидный!",
        )

    username: str = payload.get("sub")
    id: int = payload.get("id")
    is_admin: bool = payload.get("is_admin")
    if username is None or id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невозможно проверить пользователя.",
        )

    return {"username": username, "id": id, "is_admin": is_admin}


@router.get("/password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    get_user: Annotated[dict, Depends(get_current_user)],
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
    username = get_user.get("username")

    try:
        CreateUser(username=username, password=password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")

    tg_id = await db.scalar(
        select(Users.tg_id).where(Users.username == username)
    )
    # Генерируем код подтверждения
    verification_code = str(random.randint(100000, 999999))
    verification_codes[username] = verification_code
    asyncio.create_task(
        remove_code_after_timeout(verification_codes, username)
    )

    hash_passwords[username] = bcrypt_context.hash(password)
    asyncio.create_task(remove_code_after_timeout(hash_passwords, username))

    await bot.send_message(
        tg_id, f"Ваш код подтверждения: {verification_code}"
    )

    return templates.TemplateResponse(
        "verify_change.html", {"request": request}
    )


@router.post("/change_verify/")
async def change_verify_code(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    code: str = Form(...),
):

    username = get_user.get("username")
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


@router.get("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return RedirectResponse(
        url="/",
        status_code=status.HTTP_302_FOUND,
        headers=response.headers,
    )
