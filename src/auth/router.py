import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi_filter.base.filter import FilterDepends

from src.auth.filters import UserProfileFilter
from src.auth.schemas import (
    UserProfileCreateSchema,
    UserProfileImageSchema,
    UserProfileSchema,
    UserProfileUpdateSchema,
    UserReadSchema as UserSchema,  # Assuming this exists for User model
)
from src.auth.services import (
    UserFriendsSQLAlchemyService,
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

friends_router = APIRouter(
    prefix="/friends",
    tags=["friends"],
    responses={404: {"description": "Not found"}},
)


# Dependency for UserFriendsSQLAlchemyService
async def get_friends_service():
    return UserFriendsSQLAlchemyService()


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


@users_router.get("/profiles/all")
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


@friends_router.post("/request/{friend_id}")
async def send_friend_request(
    friend_id: uuid.UUID,
    user: User = Depends(current_active_user),
    service: UserFriendsSQLAlchemyService = Depends(get_friends_service)
) -> dict:
    success = await service.send_friend_request(user.id, friend_id)
    if not success:
        raise HTTPException(
            status_code=400, detail="Failed to send friend request")
    return {"message": "Friend request sent"}


@friends_router.post("/accept/{friend_id}")
async def accept_friend_request(
    friend_id: uuid.UUID,
    user: User = Depends(current_active_user),
    service: UserFriendsSQLAlchemyService = Depends(get_friends_service)
) -> dict:
    success = await service.accept_friend_request(user.id, friend_id)
    if not success:
        raise HTTPException(
            status_code=400, detail="Failed to accept friend request")
    return {"message": "Friend request accepted"}


@friends_router.post("/decline/{friend_id}")
async def decline_friend_request(
    friend_id: uuid.UUID,
    user: User = Depends(current_active_user),
    service: UserFriendsSQLAlchemyService = Depends(get_friends_service)
) -> dict:
    success = await service.decline_friend_request(user.id, friend_id)
    if not success:
        raise HTTPException(
            status_code=400, detail="Failed to decline friend request")
    return {"message": "Friend request declined"}


@friends_router.post("/block/{block_id}")
async def block_user(
    block_id: uuid.UUID,
    user: User = Depends(current_active_user),
    service: UserFriendsSQLAlchemyService = Depends(get_friends_service)
) -> dict:
    success = await service.block_user(user.id, block_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to block user")
    return {"message": "User blocked"}


@friends_router.post("/unblock/{block_id}")
async def unblock_user(
    block_id: uuid.UUID,
    user: User = Depends(current_active_user),
    service: UserFriendsSQLAlchemyService = Depends(get_friends_service)
) -> dict:
    success = await service.unblock_user(user.id, block_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to unblock user")
    return {"message": "User unblocked"}


@friends_router.get("/list")
async def get_friends(
    user: User = Depends(current_active_user),
    service: UserFriendsSQLAlchemyService = Depends(get_friends_service)
) -> list[UserSchema]:
    friends = await service.get_friends(user.id)
    return friends


@friends_router.get("/requests/sent")
async def get_friend_requests_sent(
    user: User = Depends(current_active_user),
    service: UserFriendsSQLAlchemyService = Depends(get_friends_service)
) -> list[UserSchema]:
    requests = await service.get_friend_requests_sent(user.id)
    return requests


@friends_router.get("/requests/received")
async def get_friend_requests_received(
    user: User = Depends(current_active_user),
    service: UserFriendsSQLAlchemyService = Depends(get_friends_service)
) -> list[UserSchema]:
    requests = await service.get_friend_requests_received(user.id)
    return requests


@friends_router.get("/blocked")
async def get_blocked_users(
    user: User = Depends(current_active_user),
    service: UserFriendsSQLAlchemyService = Depends(get_friends_service)
) -> list[UserSchema]:
    blocked_users = await service.get_blocked_users(user.id)
    return blocked_users
