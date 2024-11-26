from typing import Annotated

from app.backend.db_depends import get_db
from app.models import Orders, Payment, Users
from app.schemas import OrderDB, PaymentDB, User
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/profile", response_model=User)
async def user_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    id = get_user.get("id")
    user = await db.scalar(select(Users).where(Users.id == id))

    return user


@router.get("/my_orders", response_model=list[OrderDB])
async def my_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    id = get_user.get("id")
    user = await db.scalar(select(Users.tg_id).where(Users.id == id))
    orders = await db.scalars(select(Orders).where(Orders.tg_id == user))
    return orders.all()


@router.get("/my_payments", response_model=list[PaymentDB])
async def my_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    id = get_user.get("id")
    user = await db.scalar(select(Users.tg_id).where(Users.id == id))
    payments = await db.scalars(
        select(Payment).where(Payment.tg_id == user, Payment.confirmed == True)
    )
    return payments.all()
