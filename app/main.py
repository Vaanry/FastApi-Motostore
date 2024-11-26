from app.routers import main_router
from fastapi import FastAPI

from .config import settings

app = FastAPI(title=settings.app_title)


@app.get("/")
async def welcome() -> dict:
    return {"message": "Motostore app"}


app.include_router(main_router)
