import uuid

from fastapi import HTTPException, UploadFile
from src.s3_service import S3BucketService, s3_bucket_service_factory
from src.auth.schemas import UserProfileImageCreateSchema, UserProfileSchema, UserProfileCreateSchema, UserProfileUpdateSchema, UserProfileImageSchema
from src.unitofwork import SQLAlchemyUnitOfWork


class UserProfileSQLAlchemyService():

    def __init__(self, uow: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork()) -> None:
        self.uow = uow

    async def add(self, user_profile: UserProfileCreateSchema) -> UserProfileSchema:
        async with self.uow:
            user_profile = await self.uow.user_profiles.create(user_profile)
            created_profile = UserProfileSchema.model_validate(user_profile)
            return created_profile

    async def update(self, user_profile: UserProfileUpdateSchema) -> UserProfileSchema:
        async with self.uow:
            user_profile = await self.uow.user_profiles.update_single(user_profile)
            updated_profile = UserProfileSchema.model_validate(user_profile)
            return updated_profile

    async def get_all(self) -> list[UserProfileSchema]:
        async with self.uow:
            user_profiles = await self.uow.user_profiles.get_multi()
            user_profiles = [UserProfileSchema.model_validate(
                user_profile) for user_profile in user_profiles]
            return user_profiles

    async def get_by_id(self, id: uuid.UUID) -> UserProfileSchema:
        async with self.uow:
            user_profiles = await self.uow.user_profiles.get_single(user_id=id)
            user_profiles = UserProfileSchema.model_validate(user_profiles)
            return user_profiles


class UserProfileImageSQLAlchemyService():
    ALLOWED_IMAGE_TYPES = {"image/jpeg",
                           "image/png", "image/webp", "image/svg+xml"}

    def __init__(self, uow: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork(), s3_service: S3BucketService = s3_bucket_service_factory()) -> None:
        self.uow = uow
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
        async with self.uow:

            await self._validate_user_profile(user_id)

            uploaded_images = []

            for file in files:
                try:
                    file_url = await self._upload_image_to_s3_bucket(user_id, file)

                    image_create_schema = UserProfileImageCreateSchema.model_construct(
                        url=file_url, is_profile_picture=True)

                    image_model = await self.uow.user_profile_images.create(user_id, image_create_schema)

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
        async with self.uow:
            user_profile_images = await self.uow.user_profile_images.get_all_by_user_id(user_id=user_id)

            if user_profile_images:
                user_profile_images = [UserProfileImageSchema.model_validate(
                    sport_object_image) for sport_object_image in user_profile_images]
                return user_profile_images
            else:
                return None

    async def get_by_id(self, id: int) -> UserProfileImageSchema:
        async with self.uow:
            sport_object = await self.uow.sport_objects.get_single(id=id)
            sport_object = UserProfileImageSchema.model_validate(sport_object)
            return sport_object
