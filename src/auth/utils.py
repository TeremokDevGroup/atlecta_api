import contextlib

from fastapi_users.exceptions import UserAlreadyExists

from src.auth.manager import get_user_manager
from src.auth.models import get_user_db
from database import get_async_session
from auth.schemas import UserCreate

get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(email: str, password: str, is_superuser: bool = False):
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context as user_db:
                async with get_user_manager_context as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=email, password=password, is_superuser=is_superuser
                        ))
                    print(f"User created {user}")
                    return user

    except UserAlreadyExists:
        print(f"User {email} already exists")
        raise
