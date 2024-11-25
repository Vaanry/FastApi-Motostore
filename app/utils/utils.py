from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models import Manufacturer


async def get_category_by_name(db: AsyncSession, name: str) -> Manufacturer:
    """Получить категорию по названию."""
    return await db.scalar(select(Manufacturer).where(Manufacturer.name == name))


async def check_admin_permissions(user: dict):
    """Проверка, что пользователь является администратором."""
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be admin user for this",
        )
