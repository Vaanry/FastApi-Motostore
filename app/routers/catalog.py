from typing import Annotated

from app.backend.db_depends import get_db
from app.models import Catalog, Manufacturer
from app.schemas import (
    CreateManufacturer,
    CreateModel,
    ManufacturerDB,
    ModelDB,
)
from app.utils import (
    check_admin_permissions,
    ensure_exists,
    get_category_by_name,
    get_product_by_model,
)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user

router = APIRouter(prefix="/catalog", tags=["catalog"])

templates = Jinja2Templates(directory="templates")
templates.env.globals["is_authenticated"] = (
    lambda request: hasattr(request.state, "user")
    and request.state.user is not None
)

router.mount("/static", StaticFiles(directory="static"), name="static")


# Обработчики категорий
@router.get("/", response_model=list[ManufacturerDB])
async def get_all_marks(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
):
    categories = await db.scalars(select(Manufacturer))
    return templates.TemplateResponse(
        "marks.html", {"request": request, "categories": categories}
    )


@router.get("/{mark}", response_model=ManufacturerDB)
async def get_mark(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)], mark: str
):
    category = await get_category_by_name(db, mark)
    await ensure_exists(category, "Category")
    return templates.TemplateResponse(
        "cart.html", {"request": request, "moto": category, "type": "mark"}
    )


@router.post("/create_mark")
async def create_mark(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_category: CreateManufacturer,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)
    category = await get_category_by_name(db, create_category.name)
    if category:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category already exists.",
        )
    await db.execute(
        insert(Manufacturer).values(**create_category.model_dump())
    )
    await db.commit()
    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "Successful",
    }


@router.patch("/update_mark")
async def update_mark(
    db: Annotated[AsyncSession, Depends(get_db)],
    mark: str,
    update_category: CreateManufacturer,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)
    category = await get_category_by_name(db, mark)
    await ensure_exists(category, "Category")
    await db.execute(
        update(Manufacturer)
        .where(Manufacturer.name == mark)
        .values(**update_category.model_dump())
    )
    await db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Category update is successful",
    }


@router.delete("/delete_mark")
async def delete_mark(
    db: Annotated[AsyncSession, Depends(get_db)],
    mark: str,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)
    category = await get_category_by_name(db, mark)
    await ensure_exists(category, "Category")
    await db.execute(delete(Manufacturer).where(Manufacturer.name == mark))
    await db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Category delete is successful",
    }


# Обработчики продуктов
@router.get("/models/all_models", response_model=list[ModelDB])
async def get_all_models(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
):
    products = await db.scalars(select(Catalog))
    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "products": products,
            "all": True,
            "in_stock": False,
        },
    )


@router.get("/models/in_stock", response_model=list[ModelDB])
async def get_stock_models(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
):
    products = await db.scalars(select(Catalog).where(Catalog.quantity > 0))
    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "products": products,
            "all": True,
            "in_stock": True,
        },
    )


@router.get("/{mark}/models", response_model=list[ModelDB])
async def product_by_mark(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)], mark: str
):
    category = await get_category_by_name(db, mark)
    await ensure_exists(category, "Category")
    products = await db.scalars(
        select(Catalog).where(Catalog.manufacturer == mark)
    )
    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "products": products,
            "all": False,
            "in_stock": False,
            "mark": mark,
        },
    )


@router.get("/{mark}/in_stock", response_model=list[ModelDB])
async def product_by_mark_in_stock(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)], mark: str
):
    category = await get_category_by_name(db, mark)
    await ensure_exists(category, "Category")
    products = await db.scalars(
        select(Catalog).where(
            Catalog.manufacturer == mark, Catalog.quantity > 0
        )
    )
    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "products": products,
            "all": False,
            "in_stock": True,
            "mark": mark,
        },
    )


@router.get("/models/detail/{model}", response_model=ModelDB)
async def product_detail(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)], model: str
):
    product = await get_product_by_model(db, model)
    await ensure_exists(product, "Model")
    return templates.TemplateResponse(
        "cart.html", {"request": request, "moto": product, "type": "model"}
    )


@router.post("/models/create")
async def create_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_product: CreateModel,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)
    category = await get_category_by_name(db, create_product.manufacturer)
    await ensure_exists(category, "Category")
    await db.execute(insert(Catalog).values(**create_product.model_dump()))
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
    product = await get_product_by_model(db, update_product.model)
    await ensure_exists(product, "Product")
    category = await get_category_by_name(db, update_product.manufacturer)
    await ensure_exists(category, "Category")
    await db.execute(
        update(Catalog)
        .where(Catalog.model == update_product.model)
        .values(**update_product.dict())
    )
    await db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Product update is successful",
    }


@router.delete("/models/delete")
async def delete_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    model: str,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    await check_admin_permissions(get_user)
    product = await get_product_by_model(db, model)
    await ensure_exists(product, "Product")
    await db.execute(delete(Catalog).where(Catalog.model == model))
    await db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Product delete is successful",
    }
