import asyncio
from app.models import Catalog, Manufacturer
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_category_by_name(db: AsyncSession, name: str) -> Manufacturer:
    """Получить категорию по названию."""
    return await db.scalar(
        select(Manufacturer).where(Manufacturer.name == name)
    )


async def get_product_by_model(db: AsyncSession, model: str) -> Catalog:
    """Получить продукт по модели."""
    return await db.scalar(select(Catalog).where(Catalog.model == model))


async def check_admin_permissions(user: dict):
    """Проверка, что пользователь является администратором."""
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be admin user for this",
        )


async def ensure_exists(entity, entity_name="Entity"):
    """Убедиться, что объект существует."""
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} not found.",
        )


async def remove_code_after_timeout(warehouse, username, timeout=300):
    """
    Удаляет код верификации через заданный таймаут.
    """
    await asyncio.sleep(timeout)
    warehouse.pop(username, None)
