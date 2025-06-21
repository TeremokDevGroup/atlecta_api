import uuid
from typing import Callable, List

from fastapi import HTTPException, UploadFile
from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_users.exceptions import UserAlreadyExists

from src.auth.manager import (
    get_async_session_context,
    get_user_db_context,
    get_user_manager_context,
)
from src.auth.models import FriendStatus

# Assuming this exists for User model validation
from src.auth.schemas import (
    UserCreateSchema,
    UserProfileCreateSchema,
    UserProfileImageCreateSchema,
    UserProfileImageSchema,
    UserProfileSchema,
    UserProfileUpdateSchema,
)
from src.auth.schemas import (
    UserReadSchema as UserSchema,  # TODO: Remove this kind stuff
)
from src.s3_service import S3BucketService, s3_bucket_service_factory
from src.unitofwork import SQLAlchemyUnitOfWork


class UserProfileSQLAlchemyService:

    def __init__(self, uow_factory: Callable[[], SQLAlchemyUnitOfWork] = SQLAlchemyUnitOfWork) -> None:
        self._uow_factory = uow_factory

    async def add(self, user_profile: UserProfileCreateSchema) -> UserProfileSchema:
        async with self._uow_factory() as uow:
            user_profile = await uow.user_profiles.create(user_profile)
            created_profile = UserProfileSchema.model_validate(user_profile)
            return created_profile

    async def update(self, user_profile: UserProfileUpdateSchema) -> UserProfileSchema:
        async with self._uow_factory() as uow:
            user_profile = await uow.user_profiles.update_single(user_profile)
            updated_profile = UserProfileSchema.model_validate(user_profile)
            return updated_profile

    async def get_all(self) -> list[UserProfileSchema]:
        async with self._uow_factory() as uow:
            user_profiles = await uow.user_profiles.get_multi()
            user_profiles = [UserProfileSchema.model_validate(
                user_profile) for user_profile in user_profiles]
            return user_profiles

    async def get_multi(self, filter: Filter) -> list[UserProfileSchema]:
        async with self._uow_factory() as uow:
            user_profiles = await uow.user_profiles.get_multi(filter=filter)
            user_profiles = [UserProfileSchema.model_validate(
                user_profile) for user_profile in user_profiles]
            return user_profiles

    async def get_by_id(self, id: uuid.UUID) -> UserProfileSchema:
        async with self._uow_factory() as uow:
            user_profiles = await uow.user_profiles.get_single(user_id=id)
            user_profiles = UserProfileSchema.model_validate(user_profiles)
            return user_profiles


class UserProfileImageSQLAlchemyService():
    ALLOWED_IMAGE_TYPES = {"image/jpeg",
                           "image/png", "image/webp", "image/svg+xml"}

    def __init__(self, uow_factory: Callable[[], SQLAlchemyUnitOfWork] = SQLAlchemyUnitOfWork, s3_service: S3BucketService = s3_bucket_service_factory()) -> None:
        self._uow_factory = uow_factory
        self.s3_service = s3_service

    async def _validate_user_profile(self, user_id: uuid.UUID) -> UserProfileSchema:
        user_profile = await UserProfileSQLAlchemyService().get_by_id(id=user_id)

        if not user_profile:
            raise HTTPException(
                status_code=404, detail="User profile not found")

        return user_profile

    async def _validate_file_type(self, file: UploadFile):
        if file.content_type not in self.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. "
                f"Allowed types: {', '.join(self.ALLOWED_IMAGE_TYPES)}",
            )

    async def _upload_image_to_s3_bucket(self, user_id: uuid.UUID, file: UploadFile) -> str:
        await self._validate_file_type(file)

        file_uuid = str(uuid.uuid4())
        file_extention = file.filename.split(".")[-1]
        source_file_name = f"{file_uuid}.{file_extention}"

        prefix = f"profiles/{user_id}/images"

        content = await file.read()

        await self.s3_service.upload_file_object(
            prefix=prefix,
            source_file_name=source_file_name,
            content=content,
            content_type=file.content_type or "application/octet-stream"
        )

        file_url = f"{self.s3_service.bucket_name}/{prefix}/{source_file_name}"

        return file_url

    async def add(self, user_id: uuid.UUID, files: list[UploadFile]) -> list[UserProfileImageSchema]:
        async with self._uow_factory() as uow:

            await self._validate_user_profile(user_id)

            uploaded_images = []

            for file in files:
                try:
                    file_url = await self._upload_image_to_s3_bucket(user_id, file)

                    image_create_schema = UserProfileImageCreateSchema.model_construct(
                        url=file_url, is_profile_picture=True)

                    image_model = await uow.user_profile_images.create(user_id, image_create_schema)

                    image_schema = UserProfileImageSchema.model_validate(
                        image_model)

                    uploaded_images.append(image_schema)

                except Exception as e:
                    print(e)
                    raise HTTPException(
                        status_code=500, detail=f"Failed to upload {file.filename}: {str(e)}"
                    )

            return uploaded_images

    async def get_all(self, user_id: uuid.UUID) -> list[UserProfileImageSchema] | None:
        async with self._uow_factory() as uow:
            user_profile_images = await uow.user_profile_images.get_all_by_user_id(user_id=user_id)

            if user_profile_images:
                user_profile_images = [UserProfileImageSchema.model_validate(
                    sport_object_image) for sport_object_image in user_profile_images]
                return user_profile_images
            else:
                return None

    async def get_by_id(self, id: int) -> UserProfileImageSchema:
        async with self._uow_factory() as uow:
            sport_object = await uow.sport_objects.get_single(id=id)
            sport_object = UserProfileImageSchema.model_validate(sport_object)
            return sport_object


async def create_user(email: str, password: str, is_superuser: bool = False):
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreateSchema(
                            email=email, password=password, is_superuser=is_superuser
                        ))
                    print(f"User created {user}")
                    return user

    except UserAlreadyExists:
        print(f"User {email} already exists")
        raise


class UserFriendsSQLAlchemyService:
    def __init__(self, uow_factory: Callable[[], SQLAlchemyUnitOfWork] = SQLAlchemyUnitOfWork) -> None:
        self._uow_factory = uow_factory

    async def send_friend_request(self, user_id: uuid.UUID, friend_id: uuid.UUID) -> bool:
        """Send a friend request from user_id to friend_id."""
        async with self._uow_factory() as uow:
            if user_id == friend_id:
                raise HTTPException(
                    status_code=400, detail="Cannot send friend request to self")

            existing_status = await uow.user_friends.get_friendship(user_id, friend_id)
            if existing_status:
                raise HTTPException(
                    status_code=400, detail=f"Friendship status already exists: {existing_status.name}")
            # NOTE: Return something else?
            success = await uow.user_friends.create_friendship(user_id, friend_id, FriendStatus.PENDING)
            return success

    async def accept_friend_request(self, user_id: uuid.UUID, friend_id: uuid.UUID) -> bool:
        """Accept a friend request from friend_id to user_id."""
        async with self._uow_factory() as uow:
            existing_status = await uow.user_friends.get_friendship(friend_id, user_id)
            if existing_status != FriendStatus.PENDING:
                raise HTTPException(
                    status_code=400, detail="No pending friend request found")

            success = await uow.user_friends.update_friendship_status(friend_id, user_id, FriendStatus.ACCEPTED)
            if success:
                await uow.commit()
            return success

    async def decline_friend_request(self, user_id: uuid.UUID, friend_id: uuid.UUID) -> bool:
        """Decline a friend request from friend_id to user_id."""
        async with self._uow_factory() as uow:
            existing_status = await uow.user_friends.get_friendship(friend_id, user_id)
            if existing_status != FriendStatus.PENDING:
                raise HTTPException(
                    status_code=400, detail="No pending friend request found")

            success = await uow.user_friends.update_friendship_status(friend_id, user_id, FriendStatus.DECLINED)
            if success:
                await uow.commit()
            return success

    async def block_user(self, user_id: uuid.UUID, block_id: uuid.UUID) -> bool:
        """Block a user (block_id) by user_id."""
        async with self._uow_factory() as uow:
            if user_id == block_id:
                raise HTTPException(
                    status_code=400, detail="Cannot block self")

            existing_status = await uow.user_friends.get_friendship(user_id, block_id)
            if existing_status == FriendStatus.BLOCKED:
                raise HTTPException(
                    status_code=400, detail="User already blocked")

            success = await uow.user_friends.update_friendship_status(user_id, block_id, FriendStatus.BLOCKED)
            if success:
                await uow.commit()
            return success

    async def unblock_user(self, user_id: uuid.UUID, block_id: uuid.UUID) -> bool:
        """Unblock a user (block_id) by user_id."""
        async with self._uow_factory() as uow:
            existing_status = await uow.user_friends.get_friendship(user_id, block_id)
            if existing_status != FriendStatus.BLOCKED:
                raise HTTPException(
                    status_code=400, detail="User is not blocked")

            success = await uow.user_friends.update_friendship_status(user_id, block_id, FriendStatus.DECLINED)
            if success:
                await uow.commit()
            return success

    async def get_friends(self, user_id: uuid.UUID, filter: Filter | None = None) -> List[UserSchema]:
        """Get all accepted friends for a user."""
        async with self._uow_factory() as uow:
            friends = await uow.user_friends.get_friends(user_id, filter=filter)
            return [UserSchema.model_validate(friend) for friend in friends]

    async def get_friend_requests_sent(self, user_id: uuid.UUID, filter: Filter | None = None) -> List[UserSchema]:
        """Get all sent friend requests for a user."""
        async with self._uow_factory() as uow:
            requests = await uow.user_friends.get_friend_requests_sent(user_id, filter=filter)
            return [UserSchema.model_validate(request) for request in requests]

    async def get_friend_requests_received(self, user_id: uuid.UUID, filter: Filter | None = None) -> List[UserSchema]:
        """Get all received friend requests for a user."""
        async with self._uow_factory() as uow:
            requests = await uow.user_friends.get_friend_requests_received(user_id, filter=filter)
            return [UserSchema.model_validate(request) for request in requests]

    async def get_blocked_users(self, user_id: uuid.UUID, filter: Filter | None = None) -> List[UserSchema]:
        """Get all blocked users for a user."""
        async with self._uow_factory() as uow:
            blocked_users = await uow.user_friends.get_blocked_users(user_id, filter=filter)
            return [UserSchema.model_validate(user) for user in blocked_users]

    async def is_blocked(self, user_id: uuid.UUID, target_id: uuid.UUID) -> bool:
        """Check if target_id is blocked by user_id."""
        async with self._uow_factory() as uow:
            status = await uow.user_friends.get_friendship(user_id, target_id)
            return status == FriendStatus.BLOCKED
