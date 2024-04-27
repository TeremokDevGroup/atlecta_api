from fastapi_users.authentication import BearerTransport, JWTStrategy, AuthenticationBackend
from src.config import AUTH_SECRET

SECRET = AUTH_SECRET

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


# TODO: rewrite this using key pairs
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
