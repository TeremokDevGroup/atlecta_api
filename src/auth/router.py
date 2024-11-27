import uuid
from fastapi import APIRouter, Depends

from src.auth.schemas import UserProfileCreate, UserProfile, UserProfileUpdate
from src.auth.services import UserProfileSQLAlchemyService
from .models import User
from .auth import current_active_user

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

users_router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@auth_router.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return user


@users_router.get("/profiles/")
async def get_all_users_profiles() -> list[UserProfile]:
    user_profiles = await UserProfileSQLAlchemyService().get_all()
    return user_profiles


@users_router.get("/profiles/{user_profile_id}")
async def get_user_profile_by_id(user_profile_id: uuid.UUID) -> UserProfile:
    user_profile = await UserProfileSQLAlchemyService().get_by_id(user_profile_id)
    return user_profile


@users_router.post("/profiles")
async def create_user_profile(user_profile: UserProfileCreate, user: User = Depends(current_active_user)) -> UserProfile:
    user_profile.user_id = user.id
    created_profile = await UserProfileSQLAlchemyService().add(user_profile)
    return created_profile


@users_router.put("/profiles")
async def update_user_profile(user_profile: UserProfileUpdate, user: User = Depends(current_active_user)) -> UserProfile:
    user_profile.user_id = user.id
    updated_profile = await UserProfileSQLAlchemyService().update(user_profile)
    return updated_profile
