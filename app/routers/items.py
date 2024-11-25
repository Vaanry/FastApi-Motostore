from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models import Catalog, Items
from app.schemas import CreateManufacturer, CreateModel

from .auth import get_current_user


router = APIRouter(prefix="/items", tags=["items"])


@router.get("/all_items")
async def get_all_items(db: Annotated[AsyncSession, Depends(get_db)]):
    items = await db.scalars(select(Items))
    return items.all()


@router.get("/{model}")
async def get_model_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    model: str,
):
    model_ = await db.scalar(select(Catalog).where(Catalog.model == model))
    if model_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product",
        )

    items = await db.scalars(select(Items).where(Items.model == model))
    return items.all()


@router.get("/detail/{id}")
async def get_item_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: int,
):
    item = await db.scalar(select(Items).where(Items.id == id))
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product",
        )

    return item
