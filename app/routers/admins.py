from typing import Annotated

from app.backend.db_depends import get_db
from app.models import Orders, Users
from app.schemas import OrderDB, User
from app.utils import check_admin_permissions, ensure_exists
from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from .auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.patch("/update_user_balance")
async def update_user_balance(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    username: str,
    amout: float,
):
    await check_admin_permissions(get_user)
    balance = await db.scalar(
        select(Users.balance).where(Users.username == username)
    )
    await ensure_exists(balance, "User")

    new_balance = balance + amout

    await db.execute(
        update(Users)
        .where(Users.username == username)
        .values(balance=new_balance)
    )
    await db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "detail": "User's balance has been updated",
    }


@router.patch("/update_user_status")
async def update_user_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    username: str,
):
    await check_admin_permissions(get_user)
    status = await db.scalar(
        select(Users.active).where(Users.username == username)
    )
    await ensure_exists(status, "User")

    new_status = not status

    await db.execute(
        update(Users)
        .where(Users.username == username)
        .values(active=new_status)
    )
    await db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "detail": "User's balance has been updated",
    }


@router.get("/get_user", response_model=User)
async def get_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    username: str
):
    await check_admin_permissions(get_user)
    user = await db.scalar(select(Users).where(Users.username == username))
    await ensure_exists(user, "User")

    return user


@router.get("/user_orders", response_model=list[OrderDB])
async def get_user_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    username: str,
):
    await check_admin_permissions(get_user)
    user = await db.scalar(
        select(Users.tg_id).where(Users.username == username)
    )
    orders = await db.scalars(
        select(Orders).where(Orders.tg_id == user, Orders.is_paid == True)
    )
    return orders.all()
