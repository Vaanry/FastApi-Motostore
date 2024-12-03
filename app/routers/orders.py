import os
from typing import Annotated

from app.backend.db_depends import get_db
from app.models import Orders, Users
from app.schemas import OrderDB
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


templates = Jinja2Templates(directory="templates")
templates.env.globals["is_authenticated"] = (
    lambda request: hasattr(request.state, "user")
    and request.state.user is not None
)

router.mount("/static", StaticFiles(directory="static"), name="static")


@router.get("/{id}", response_model=OrderDB)
async def order_detail(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    id: int,
):
    user_id = get_user.get("id")
    user = await db.scalar(select(Users.tg_id).where(Users.id == user_id))
    order = await db.scalar(select(Orders).where(Orders.id == id))
    if user != order.tg_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not your order!",
        )
    photos = []
    for file in os.listdir(order.order_archive):
        photo = os.path.join(
            "/static/orders/", os.path.basename(order.order_archive), file
        )
        photos.append(photo)

    return templates.TemplateResponse(
        "order_card.html",
        {"request": request, "order": order, "photos": photos},
    )
