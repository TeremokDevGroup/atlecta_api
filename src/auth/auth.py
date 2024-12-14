import uuid
import redis.asyncio

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
    RedisStrategy,
)

from src.auth.manager import get_user_manager
from src.auth.models import User
from src.config import AUTH_SECRET, REDIS_HOST, REDIS_PORT

SECRET = AUTH_SECRET


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

redis = redis.asyncio.from_url(
    f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)


# NOTE: We are using this one, because it supports token invalidation
def get_redis_stretegy() -> RedisStrategy:
    return RedisStrategy(redis, lifetime_seconds=3600)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_redis_stretegy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(
    active=True, superuser=True)
