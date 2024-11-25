from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.backend.db_depends import get_db
from app.models import Users

from .auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.patch("/update_user_balance")
async def update_user_balance(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    username: str,
    amout: float,
):
    if get_user.get("is_admin"):
        user = await db.scalar(select(Users).where(Users.username == username))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        balance = await db.execute(
            select(Users.balance).where(Users.username == username)
        )
        new_balance = balance.scalar() + amout

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

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin permission",
        )
