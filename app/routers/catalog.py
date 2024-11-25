from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models import Catalog, Manufacturer
from app.schemas import CreateManufacturer, ManufacturerDB, CreateModel, ModelDB
from app.utils import get_category_by_name, check_admin_permissions
from .auth import get_current_user


router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/all_marks",
            response_model=list[ManufacturerDB],)
async def get_all_marks(db: Annotated[AsyncSession, Depends(get_db)]):
    categories = await db.scalars(select(Manufacturer))
    return categories.all()


@router.get("/{mark}",
            response_model=ManufacturerDB,)
async def get_mark(db: Annotated[AsyncSession, Depends(get_db)], mark: str):

    category = await get_category_by_name(db, mark)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no category found",
        )
    return category


@router.post("/create_mark")
async def create_mark(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_category: CreateManufacturer,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)

    category = await get_category_by_name(db, create_category.name)
    if category is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category already exists.",
        )

    await db.execute(
        insert(Manufacturer).values(
            name=create_category.name, country=create_category.country
        )
    )
    await db.commit()
    return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}


@router.put("/update_mark")
async def update_mark(
    db: Annotated[AsyncSession, Depends(get_db)],
    mark: str,
    update_category: CreateManufacturer,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)

    category = await get_category_by_name(db, mark)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no category found",
        )

    await db.execute(
        update(Manufacturer)
        .where(Manufacturer.name == mark)
        .values(name=update_category.name, country=update_category.country)
    )
    await db.commit()
    return {"status_code": status.HTTP_200_OK, "transaction": "Category update is successful"}


@router.delete("/delete_mark")
async def delete_mark(
    db: Annotated[AsyncSession, Depends(get_db)],
    mark: str,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)

    category = await get_category_by_name(db, mark)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no category found",
        )

    await db.execute(delete(Manufacturer).where(Manufacturer.name == mark))
    await db.commit()
    return {"status_code": status.HTTP_200_OK, "transaction": "Category delete is successful"}


@router.get("/models/all_models",
            response_model=list[ModelDB],)
async def get_all_models(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Catalog))

    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no products",
        )

    return products.all()


@router.get("/models/in_stock",
            response_model=list[ModelDB],)
async def get_stock_models(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Catalog).where(Catalog.quantity > 0))

    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no products",
        )

    return products.all()


@router.get("/{mark}/models",
            response_model=list[ModelDB],)
async def product_by_mark(
    db: Annotated[AsyncSession, Depends(get_db)], mark: str
):
    category = await get_category_by_name(db, mark)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no category found",
        )

    products = await db.scalars(
        select(Catalog).where(Catalog.manufacturer == mark)
    )

    return products.all()


@router.get("/{mark}/in_stock",
            response_model=list[ModelDB],)
async def product_by_mark_in_stock(
    db: Annotated[AsyncSession, Depends(get_db)], mark: str
):
    category = await get_category_by_name(db, mark)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no category found",
        )

    products = await db.scalars(
        select(Catalog).where(
            Catalog.manufacturer == mark, Catalog.quantity > 0
        )
    )

    return products.all()


@router.get("/models/detail/{model}",
            response_model=ModelDB)
async def product_detail(
    db: Annotated[AsyncSession, Depends(get_db)], model: str
):
    product = await db.scalar(select(Catalog).where(Catalog.model == model))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product",
        )
    return product


@router.post("/models/create")
async def create_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_product: CreateModel,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)
    category = await get_category_by_name(db, create_product.manufacturer)

    if category.scalar() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no category found",
        )

    await db.execute(
        insert(Catalog).values(
            manufacturer=create_product.manufacturer,
            type=create_product.type,
            model=create_product.model,
        )
    )

    await db.commit()
    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "Successful",
    }


@router.patch("/models/update/{model}")
async def update_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    update_product: CreateModel,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)

    product = await db.scalar(
        select(Catalog).where(Catalog.model == update_product.model)
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product",
        )
    category = await get_category_by_name(db, update_product.manufacturer)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no category found",
        )

    await db.execute(
        update(Catalog)
        .where(Catalog.model == update_product.model)
        .values(
            manufacturer=update_product.manufacturer,
            type=update_product.type,
            model=update_product.model,
        )
    )

    await db.commit()
    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "Successful",
    }


@router.delete("/models/delete")
async def delete_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    model: str,
    get_user: Annotated[dict, Depends(get_current_user)],
):

    product = await db.scalar(
        select(Catalog).where(Catalog.model == update_product.model)
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product",
        )

    await db.execute(delete(Catalog).where(Catalog.model == model))
    await db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Product delete is successful",
    }
