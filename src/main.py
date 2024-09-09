from fastapi import FastAPI
from src.auth.auth import auth_backend
from src.auth.schemas import UserCreate, UserRead

from src.sports import router as sports_router
from src.auth import router as users_router
from src.auth.auth import fastapi_users

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
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth/verification",
    tags=["auth"],
)
app.include_router(
    users_router.router
)
app.include_router(
    sports_router.router
)
