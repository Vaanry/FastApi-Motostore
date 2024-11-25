from fastapi import APIRouter

from .catalog import router as catalog_router
from .auth import router as auth_router
from .admins import router as admins_router


main_router = APIRouter()


main_router.include_router(catalog_router)
main_router.include_router(auth_router)
main_router.include_router(admins_router)
