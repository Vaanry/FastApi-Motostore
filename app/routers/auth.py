from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPBasic
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select, insert

from jose import jwt, JWTError

from app.models import Users
from app.schemas import CreateUser
from app.backend.db_depends import get_db
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from passlib.context import CryptContext

from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm


@router.post("/")
async def create_user(
    db: Annotated[AsyncSession, Depends(get_db)], create_user: CreateUser
):
    await db.execute(
        insert(Users).values(
            username=create_user.username,
            hashed_password=bcrypt_context.hash(create_user.password),
        )
    )
    await db.commit()
    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "Successful",
    }


async def authanticate_user(
    db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str
):
    user = await db.scalar(select(Users).where(Users.username == username))
    if (
        not user
        or not bcrypt_context.verify(password, user.hashed_password)
        or user.active is False
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def create_access_token(
    username: str, tg_id: int, is_admin: bool, expires_delta: timedelta
):

    encode = {"sub": username, "id": tg_id, "is_admin": is_admin}
    expires = datetime.now() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        tg_id: int = payload.get("id")
        is_admin: str = payload.get("is_admin")
        expire = payload.get("exp")
        if username is None or tg_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
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

        return {"username": username, "id": tg_id, "is_admin": is_admin}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user",
        )


@router.get("/read_current_user")
async def read_current_user(user: Users = Depends(get_current_user)):
    return {"User": user}


@router.post("/token")
async def login(
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
        user.tg_id,
        user.is_admin,
        expires_delta=timedelta(minutes=20),
    )

    return {"access_token": token, "token_type": "bearer"}
