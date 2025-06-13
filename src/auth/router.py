import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi_filter.base.filter import FilterDepends

from src.auth.filters import UserProfileFilter
from src.auth.schemas import (
    UserProfileCreateSchema,
    UserProfileImageSchema,
    UserProfileSchema,
    UserProfileUpdateSchema,
)
from src.auth.services import (
    UserProfileImageSQLAlchemyService,
    UserProfileSQLAlchemyService,
)

from .auth import current_active_user
from .models import User

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


@users_router.get("/profiles/me")
async def get_current_active_user_profile(user: User = Depends(current_active_user)) -> UserProfileSchema:
    user_profile = await UserProfileSQLAlchemyService().get_by_id(user.id)
    return user_profile


@users_router.patch("/profiles/me")
async def update_user_profile(user_profile: Annotated[UserProfileUpdateSchema, Depends(UserProfileUpdateSchema)], user: User = Depends(current_active_user)) -> UserProfileSchema:
    user_profile.user_id = user.id
    updated_profile = await UserProfileSQLAlchemyService().update(user_profile)
    return updated_profile


@users_router.post("/profiles/me/profile_image")
async def add_user_profile_image(
        file: UploadFile = File(...),
        user: User = Depends(current_active_user)) -> list[UserProfileImageSchema]:

    uploaded_image = await UserProfileImageSQLAlchemyService().add(user.id, [file])
    return uploaded_image


@users_router.get("/profiles")
async def get_users_profiles(user_profile_filter: UserProfileFilter = FilterDepends(UserProfileFilter)) -> list[UserProfileSchema]:
    user_profiles = await UserProfileSQLAlchemyService().get_multi(filter=user_profile_filter)
    return user_profiles


@users_router.get("/profiles/all")  # NOTE:Get all active user profiles
async def get_all_users_profiles() -> list[UserProfileSchema]:
    user_profiles = await UserProfileSQLAlchemyService().get_all()
    return user_profiles


@users_router.get("/profiles/{user_profile_id}")
async def get_user_profile_by_id(user_profile_id: uuid.UUID) -> UserProfileSchema:
    user_profile = await UserProfileSQLAlchemyService().get_by_id(user_profile_id)
    return user_profile


@users_router.post("/profiles")
async def create_user_profile(user_profile: Annotated[UserProfileCreateSchema, Depends(UserProfileCreateSchema)], user: User = Depends(current_active_user)) -> UserProfileSchema:
    user_profile.user_id = user.id
    created_profile = await UserProfileSQLAlchemyService().add(user_profile)
    return created_profile


@users_router.get("/profiles/{user_id}/images")
async def get_user_profile_images(user_id: uuid.UUID) -> list[UserProfileImageSchema] | None:
    user_profile_images = await UserProfileImageSQLAlchemyService().get_all(user_id=user_id)
    return user_profile_images
