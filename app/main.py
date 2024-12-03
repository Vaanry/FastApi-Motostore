from app.routers import main_router
from app.routers.auth import get_current_user
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

app = FastAPI(title=settings.app_title)

templates = Jinja2Templates(directory="templates")
templates.env.globals["is_authenticated"] = (
    lambda request: hasattr(request.state, "user")
    and request.state.user is not None
)

app.mount("/static", StaticFiles(directory="static"), name="static")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Попытка получить текущего пользователя
        try:
            user = await get_current_user(
                token=request.cookies.get("users_access_token")
            )
            request.state.user = user
        except:
            request.state.user = (
                None  # Если токен недействителен или отсутствует
            )

        response = await call_next(request)
        return response


app.add_middleware(AuthMiddleware)


@app.get("/")
async def welcome(request: Request) -> dict:

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "message": "Добро пожаловать!"},
    )


app.include_router(main_router)
