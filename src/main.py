import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.auth.auth import auth_backend
from src.auth.schemas import UserCreate, UserRead

from src.sports.router import sports_router
from src.auth.router import auth_router, users_router
from src.auth.auth import fastapi_users

app = FastAPI(
    title="Atlecta API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/about")
async def about():
    return {"message": "Hello, world!"}

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
    auth_router
)
app.include_router(
    users_router
)
app.include_router(
    sports_router
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    print("Time took to process the request and return response is {} sec".format(
        time.time() - start_time))
    return response
