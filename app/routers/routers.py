from fastapi import APIRouter

from .admins import router as admins_router
from .auth import router as auth_router
from .catalog import router as catalog_router
from .items import router as items_router
from .user import router as user_router

main_router = APIRouter()


main_router.include_router(catalog_router)
main_router.include_router(items_router)
main_router.include_router(user_router)
main_router.include_router(auth_router)
main_router.include_router(admins_router)
