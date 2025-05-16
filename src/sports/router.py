from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from src.sports.schemas import (
    SportCreateSchema,
    SportObjectCreateSchema,
    SportObjectImageSchema,
    SportObjectSchema,
    SportSchema,
)

from .services import (
    SportObjectImageSQLAlchemyService,
    SportObjectSQLAlchemyService,
    SportSQLAlchemyService,
)

sports_router = APIRouter(
    prefix="/sports",
    tags=["sports"],
    responses={404: {"description": "Not found"}},
)


@sports_router.get("/")
async def get_all_sports() -> list[SportSchema]:
    """Retrieve a list of all sports.

    Returns:
        list[SportSchema]: A list of all sports in the database.
    """
    sports = await SportSQLAlchemyService().get_all()
    return sports


@sports_router.get("/{sport_id}")
async def get_sport_by_id(sport_id: int) -> SportSchema:
    """Retrieve a specific sport by its ID.

    Args:
        sport_id (int): The ID of the sport to retrieve.

    Returns:
        SportSchema: The sport with the specified ID.
    """
    sport = await SportSQLAlchemyService().get_by_id(id=sport_id)
    return sport


@sports_router.post("/")
async def add_sport(sport: Annotated[SportCreateSchema, Depends(SportCreateSchema)]) -> SportSchema:
    """Add a new sport to the database.

    Args:
        sport (SportCreateSchema): The sport data to be added.

    Returns:
        SportSchema: The created sport.
    """
    sport_created = await SportSQLAlchemyService().add(sport)
    return sport_created


@sports_router.get("/objects/")
async def get_all_sport_objects() -> list[SportObjectSchema]:
    """Retrieve a list of all sport objects.

    Returns:
        list[SportObjectSchema]: A list of all sport objects in the database.
    """
    sport_objects = await SportObjectSQLAlchemyService().get_all()
    return sport_objects


@sports_router.get("/objects/{sport_object_id}/")
async def get_sport_object_by_id(sport_object_id: int) -> SportObjectSchema:
    """Retrieve a specific sport object by its ID.

    Args:
        sport_object_id (int): The ID of the sport object to retrieve.

    Returns:
        SportObjectSchema: The sport object with the specified ID.
    """
    sport_object = await SportObjectSQLAlchemyService().get_by_id(id=sport_object_id)
    return sport_object


@sports_router.post("/objects")
async def add_sport_object(sport_object: Annotated[SportObjectCreateSchema, Depends(SportObjectCreateSchema)]) -> SportObjectSchema:
    """Add a new sport object to the database.

    Args:
        sport_object (SportObjectCreateSchema): The sport object data to be added.

    Returns:
        SportObjectSchema: The created sport object.
    """
    sport_object_created = await SportObjectSQLAlchemyService().add(sport_object)
    return sport_object_created


@sports_router.get("/objects/{sport_object_id}/images/")
async def get_sport_object_images(sport_object_id: int) -> list[SportObjectImageSchema] | None:
    """Retrieve all images associated with a specific sport object.

    Args:
        sport_object_id (int): The ID of the sport object whose images are to be retrieved.

    Returns:
        list[SportObjectImageSchema] | None: A list of images for the specified sport object, or None if none exist.
    """
    sport_object_images = await SportObjectImageSQLAlchemyService().get_all(sport_object_id=sport_object_id)
    return sport_object_images


@sports_router.post("/sports/objects/{sport_object_id}/images")
async def add_sport_object_images(sport_object_id: int, files: list[UploadFile] = File(...)) -> list[SportObjectImageSchema]:
    """Add images to a specific sport object.

    Args:
        sport_object_id (int): The ID of the sport object to associate the images with.
        files (list[UploadFile]): The list of image files to upload.

    Returns:
        list[SportObjectImageSchema]: A list of the uploaded images.
    """
    uploaded_images = await SportObjectImageSQLAlchemyService().add(sport_object_id, files)
    return uploaded_images


@sports_router.post("/sports/test-router")
async def find_nearest_sport_objects(y_coord: float, x_coord: float, distance: float = 1000) -> list[SportObjectSchema]:
    nearest_sport_objects = await SportObjectSQLAlchemyService().find_nearest(y_coord, x_coord, max_distance_meters=distance)
    return nearest_sport_objects
