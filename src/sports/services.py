import uuid

from fastapi import HTTPException, UploadFile

from src.s3_service import S3BucketService, s3_bucket_service_factory
from src.unitofwork import SQLAlchemyUnitOfWork
from src.sports.schemas import (
    SportSchema, SportCreateShema,
    SportObjectSchema, SportObjectCreateSchema,
    SportObjectImageSchema, SportObjectImageCreateSchema
)


class SportSQLAlchemyService():
    def __init__(self, uow: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork()) -> None:
        self.uow = uow

    async def add(self, sport: SportCreateShema):
        async with self.uow:
            sport_dict = sport.model_dump()
            sport_id = await self.uow.sports.create(sport_dict)
            return sport_id

    async def get_all(self) -> list[SportSchema]:
        async with self.uow:
            sports = await self.uow.sports.get_multi()
            return sports

    async def get_by_id(self, id: int) -> SportSchema:
        async with self.uow:
            sport = await self.uow.sports.get_single(id=id)
            sport = SportSchema.model_validate(sport)
            return sport


class SportObjectSQLAlchemyService():
    # TODO: Here (and in class above) I need to put uow factory
    def __init__(self, uow: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork()) -> None:
        self.uow = uow

    async def add(self, sport_object: SportObjectCreateSchema) -> SportObjectCreateSchema:
        async with self.uow:
            sport_object = await self.uow.sport_objects.create(sport_object)
            return sport_object

    async def get_all(self) -> list[SportObjectSchema]:
        async with self.uow:
            sport_objects = await self.uow.sport_objects.get_multi()
            sport_objects = [SportObjectSchema.model_validate(
                sport_object) for sport_object in sport_objects]
            return sport_objects

    async def get_by_id(self, id: int) -> SportObjectSchema:
        async with self.uow:
            sport_object = await self.uow.sport_objects.get_single(id=id)
            sport_object = SportObjectSchema.model_validate(sport_object)
            return sport_object


class SportObjectImageSQLAlchemyService():
    ALLOWED_IMAGE_TYPES = {"image/jpeg",
                           "image/png", "image/webp", "image/svg+xml"}

    def __init__(self, uow: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork(), s3_service: S3BucketService = s3_bucket_service_factory()) -> None:
        self.uow = uow
        self.s3_service = s3_service

    async def _validate_sport_object(self, sport_object_id: int) -> SportObjectSchema:
        sport_object = await SportObjectSQLAlchemyService().get_by_id(id=sport_object_id)

        if not sport_object:
            raise HTTPException(
                status_code=404, detail="SportObject not found")

        return sport_object

    async def _validate_file_type(self, file: UploadFile):
        if file.content_type not in self.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. "
                f"Allowed types: {', '.join(self.ALLOWED_IMAGE_TYPES)}",
            )

    async def _upload_image_to_s3_bucket(self, sport_object_id: int, file: UploadFile) -> str:
        await self._validate_file_type(file)

        file_uuid = str(uuid.uuid4())
        file_extention = file.filename.split(".")[-1]
        source_file_name = f"{file_uuid}.{file_extention}"

        prefix = f"sports/objects/{sport_object_id}/images"

        content = await file.read()

        await self.s3_service.upload_file_object(
            prefix=prefix,
            source_file_name=source_file_name,
            content=content,
            content_type=file.content_type or "application/octet-stream"
        )

        file_url = f"{self.s3_service.bucket_name}/{prefix}/{source_file_name}"

        return file_url

    async def add(self, sport_object_id: int, files: list[UploadFile]) -> list[SportObjectImageSchema]:
        async with self.uow:

            await self._validate_sport_object(sport_object_id)

            uploaded_images = []

            for file in files:
                try:
                    file_url = await self._upload_image_to_s3_bucket(sport_object_id, file)

                    image_create_schema = SportObjectImageCreateSchema.model_construct(
                        url=file_url)

                    image_model = await self.uow.sport_object_images.create(sport_object_id, image_create_schema)

                    image_schema = SportObjectImageSchema.model_validate(
                        image_model)

                    uploaded_images.append(image_schema)

                except Exception as e:
                    print(e)
                    raise HTTPException(
                        status_code=500, detail=f"Failed to upload {file.filename}: {str(e)}"
                    )

            return uploaded_images

            # sport_object_image_model = await self.uow.sport_object_images.create(sport_object_image)
            # sport_object_image_schema = SportObjectImage.model_validate(
            #     sport_object_image_model)
            # return sport_object_image_schema

    async def get_all(self, sport_object_id: int) -> list[SportObjectImageSchema] | None:
        async with self.uow:
            sport_object_images = await self.uow.sport_object_images.get_all_by_object_id(id=sport_object_id)

            if sport_object_images:
                sport_object_images = [SportObjectImageSchema.model_validate(
                    sport_object_image) for sport_object_image in sport_object_images]
                return sport_object_images
            else:
                return None

    async def get_by_id(self, id: int) -> SportObjectImageSchema:
        async with self.uow:
            sport_object = await self.uow.sport_objects.get_single(id=id)
            sport_object = SportObjectImageSchema.model_validate(sport_object)
            return sport_object
