import uuid

from fastapi import FastAPI
from fastapi_users import FastAPIUsers

from src.auth.models import User
from src.auth.manager import get_user_manager
from src.auth.auth import auth_backend
from src.auth.schemas import UserCreate, UserRead

from src.sports import router as sports_router

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

app = FastAPI(
    title="Atlecta API",
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    sports_router.router
)
