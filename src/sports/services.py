from typing import Callable
import uuid

from fastapi import HTTPException, UploadFile
from fastapi_filter.contrib.sqlalchemy import Filter

from src.s3_service import S3BucketService, s3_bucket_service_factory
from src.sports.filters import SportObjectFilter
from src.unitofwork import SQLAlchemyUnitOfWork
from src.sports.schemas import (
    InventoryBaseSchema, InventoryCreateSchema, InventorySchema, SportObjectUpdateSchema, SportSchema, SportCreateSchema,
    SportObjectSchema, SportObjectCreateSchema,
    SportObjectImageSchema, SportObjectImageCreateSchema
)


class InventorySQLAlchemyService():
    def __init__(self, uow_factory: Callable[[], SQLAlchemyUnitOfWork] = SQLAlchemyUnitOfWork) -> None:
        self._uow_factory = uow_factory

    async def add(self, inventory: InventoryCreateSchema) -> InventorySchema:
        async with self._uow_factory() as uow:
            inventory_data = inventory.model_dump()
            inventory_created = await uow.inventory.create(inventory_data)
            inventory_created = InventorySchema.model_validate(
                inventory_created)
            return inventory_created

    async def get_all(self) -> list[InventorySchema]:
        async with self._uow_factory() as uow:
            inventories = await uow.inventory.get_multi()
            inventories = [InventorySchema.model_validate(
                inventory) for inventory in inventories]
            return inventories

    async def get_by_id(self, id: int) -> InventorySchema:
        async with self._uow_factory() as uow:
            inventory = await uow.inventory.get_single(id=id)
            inventory = InventorySchema.model_validate(inventory)
            return inventory


class SportSQLAlchemyService():
    def __init__(self, uow_factory: Callable[[], SQLAlchemyUnitOfWork] = SQLAlchemyUnitOfWork) -> None:
        self._uow_factory = uow_factory

    async def add(self, sport_model: SportCreateSchema) -> SportSchema:
        async with self._uow_factory() as uow:
            sport_dict = sport_model.model_dump()
            sport_model = await uow.sports.create(sport_dict)
            sport = SportSchema.model_validate(sport_model)
            return sport

    async def get_all(self) -> list[SportSchema]:
        async with self._uow_factory() as uow:
            sports = await uow.sports.get_multi()
            sports = [SportSchema.model_validate(
                sport_object) for sport_object in sports]
            return sports

    async def get_by_id(self, id: int) -> SportSchema:
        async with self._uow_factory() as uow:
            sport = await uow.sports.get_single(id=id)
            sport = SportSchema.model_validate(sport)
            return sport


class SportObjectSQLAlchemyService():
    def __init__(self, uow_factory: Callable[[], SQLAlchemyUnitOfWork] = SQLAlchemyUnitOfWork) -> None:
        self._uow_factory = uow_factory

    async def add(self, sport_object: SportObjectCreateSchema) -> SportObjectSchema:
        async with self._uow_factory() as uow:
            sport_object_model = await uow.sport_objects.create(sport_object)
            sport_object_created = SportObjectSchema.model_validate(
                sport_object_model)
            return sport_object_created

    async def get_all(self) -> list[SportObjectSchema]:
        async with self._uow_factory() as uow:
            sport_objects = await uow.sport_objects.get_multi()
            sport_objects = [SportObjectSchema.model_validate(
                sport_object) for sport_object in sport_objects]
            return sport_objects

    async def get_multi(self, filter: Filter) -> list[SportObjectSchema]:
        async with self._uow_factory() as uow:
            sport_objects = await uow.sport_objects.get_multi(filter=filter)
            sport_objects = [SportObjectSchema.model_validate(
                sport_object) for sport_object in sport_objects]
            return sport_objects

    async def get_by_id(self, id: int) -> SportObjectSchema:
        async with self._uow_factory() as uow:
            sport_object = await uow.sport_objects.get_single(id=id)
            sport_object = SportObjectSchema.model_validate(sport_object)
            return sport_object

    async def find_nearest(self, x_coord: float, y_coord: float, limit: int = 10, max_distance_meters: float = 1000, filter: Filter = SportObjectFilter(), **filters) -> list[SportObjectSchema]:
        async with self._uow_factory() as uow:
            nearest_sport_objects = await uow.sport_objects.find_nearest(x_coord, y_coord, limit, max_distance_meters, **filters)
            nearest_sport_objects = [SportObjectSchema.model_validate(
                sport_object) for sport_object in nearest_sport_objects]
            return nearest_sport_objects

    async def update_sport_object(self, sport_object: SportObjectUpdateSchema) -> SportObjectSchema:
        async with self._uow_factory() as uow:
            updated_sport_object = await uow.sport_objects.update_single(data=sport_object)
            updated_sport_object = SportObjectSchema.model_validate(
                updated_sport_object)

            return updated_sport_object


class SportObjectImageSQLAlchemyService():
    ALLOWED_IMAGE_TYPES = {"image/jpeg",
                           "image/png", "image/webp", "image/svg+xml"}

    def __init__(self, uow_factory: Callable[[], SQLAlchemyUnitOfWork] = SQLAlchemyUnitOfWork, s3_service: S3BucketService = s3_bucket_service_factory()) -> None:
        self._uow_factory = uow_factory
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
        async with self._uow_factory() as uow:

            await self._validate_sport_object(sport_object_id)

            uploaded_images = []

            for file in files:
                try:
                    file_url = await self._upload_image_to_s3_bucket(sport_object_id, file)

                    image_create_schema = SportObjectImageCreateSchema.model_construct(
                        url=file_url)

                    image_model = await uow.sport_object_images.create(sport_object_id, image_create_schema)

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
        async with self._uow_factory() as uow:
            sport_object_images = await uow.sport_object_images.get_all_by_object_id(id=sport_object_id)

            if sport_object_images:
                sport_object_images = [SportObjectImageSchema.model_validate(
                    sport_object_image) for sport_object_image in sport_object_images]
                return sport_object_images
            else:
                return None

    async def get_by_id(self, id: int) -> SportObjectImageSchema:
        async with self._uow_factory() as uow:
            sport_object = await uow.sport_objects.get_single(id=id)
            sport_object = SportObjectImageSchema.model_validate(sport_object)
            return sport_object
