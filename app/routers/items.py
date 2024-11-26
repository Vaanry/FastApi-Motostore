from typing import Annotated

from app.backend.db_depends import get_db
from app.models import Items
from app.schemas import CreateItem, ItemDB
from app.utils import (
    check_admin_permissions,
    ensure_exists,
    get_product_by_model,
)
from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/all_items", response_model=list[ItemDB])
async def get_all_items(db: Annotated[AsyncSession, Depends(get_db)]):
    items = await db.scalars(select(Items))
    return items.all()


@router.get("/{model}", response_model=list[ItemDB])
async def get_model_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    model: str,
):
    model_ = await get_product_by_model(db, model)
    await ensure_exists(model_, "Model")

    items = await db.scalars(select(Items).where(Items.model == model))
    return items.all()


@router.get("/detail/{id}", response_model=ItemDB)
async def get_item_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: int,
):
    item = await db.scalar(select(Items).where(Items.id == id))
    await ensure_exists(item, "Motorbike")

    return item


@router.post("/create_item")
async def create_item(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_item: CreateItem,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)
    model_ = await get_product_by_model(db, create_item.model)
    await ensure_exists(model_, "Model")

    await db.execute(insert(Items).values(**create_item.model_dump()))
    await db.commit()
    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "Successful",
    }


@router.patch("/update_item/{id}")
async def update_item(
    db: Annotated[AsyncSession, Depends(get_db)],
    update_item: CreateItem,
    get_user: Annotated[dict, Depends(get_current_user)],
    id: int,
):
    await check_admin_permissions(get_user)
    item = await db.scalar(select(Items).where(Items.id == id))
    await ensure_exists(item, "Motorbike")

    await db.execute(
        update(Items).where(Items.id == id).values(**update_item.model_dump())
    )
    await db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Item update is successful",
    }


@router.delete("/delete_item/{id}")
async def delete_item(
    db: Annotated[AsyncSession, Depends(get_db)],
    update_item: CreateItem,
    get_user: Annotated[dict, Depends(get_current_user)],
    id: int,
):
    await check_admin_permissions(get_user)
    item = await db.scalar(select(Items).where(Items.id == id))
    await ensure_exists(item, "Motorbike")

    await db.execute(
        delete(Items).where(Items.id == id).values(**update_item.model_dump())
    )
    await db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Item delete is successful",
    }
