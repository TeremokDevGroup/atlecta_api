import time

from fastapi import FastAPI, Request
from src.auth.auth import auth_backend
from src.auth.schemas import UserCreate, UserRead

from src.sports import router as sports_router
from src.auth import router as users_router
from src.auth.auth import fastapi_users

app = FastAPI(
    title="Atlecta API",
)


@app.get("/about")
async def about():
    return {"message": "Hello, World!"}

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


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    print("Time took to process the request and return response is {} sec".format(
        time.time() - start_time))
    return response
