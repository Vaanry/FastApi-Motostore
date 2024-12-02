from typing import Annotated

from app.backend.db_depends import get_db
from app.models import Orders, Payment, Users
from app.schemas import OrderDB, PaymentDB, User
from app.utils import sqlalchemy_to_dict
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


templates = Jinja2Templates(directory="templates")
router.mount("/static", StaticFiles(directory="static"), name="static")


@router.get("/profile", response_model=User)
async def user_profile(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    id = get_user.get("id")
    user = await db.scalar(select(Users).where(Users.id == id))

    validated_user = User.model_validate(sqlalchemy_to_dict(user))
    user_data = validated_user.model_dump()
    user_data["reg_date"] = validated_user.reg_date.strftime("%Y-%m-%d")

    return templates.TemplateResponse(
        "profile.html", {"request": request, "user": user_data}
    )


@router.get("/my_orders", response_model=list[OrderDB])
async def my_orders(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    id = get_user.get("id")
    user = await db.scalar(select(Users.tg_id).where(Users.id == id))
    orders = await db.scalars(
        select(Orders).where(Orders.tg_id == user, Orders.is_paid == True)
    )

    return templates.TemplateResponse(
        "orders.html", {"request": request, "orders": orders}
    )


@router.get("/my_payments", response_model=list[PaymentDB])
async def my_payments(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    id = get_user.get("id")
    user = await db.scalar(select(Users.tg_id).where(Users.id == id))
    payments = await db.scalars(
        select(Payment).where(Payment.tg_id == user, Payment.confirmed == True)
    )
    return templates.TemplateResponse(
        "payments.html", {"request": request, "payments": payments}
    )
