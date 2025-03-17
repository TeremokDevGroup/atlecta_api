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
    sports = await SportSQLAlchemyService().get_all()
    return sports


@sports_router.get("/{sport_id}")
async def get_sport_by_id(sport_id: int) -> SportSchema:
    sport = await SportSQLAlchemyService().get_by_id(id=sport_id)
    return sport


@sports_router.post("/")
async def add_sport(sport: Annotated[SportCreateSchema, Depends(SportCreateSchema)]) -> SportSchema:
    sport_created = await SportSQLAlchemyService().add(sport)
    return sport_created


@sports_router.get("/objects/")
async def get_all_sport_objects() -> list[SportObjectSchema]:
    sport_objects = await SportObjectSQLAlchemyService().get_all()
    return sport_objects


@sports_router.get("/objects/{sport_object_id}/")
async def get_sport_object_by_id(sport_object_id: int) -> SportObjectSchema:
    sport_object = await SportObjectSQLAlchemyService().get_by_id(id=sport_object_id)
    return sport_object


@sports_router.post("/objects")
async def add_sport_object(sport_object: Annotated[SportObjectCreateSchema, Depends(SportObjectCreateSchema)]) -> SportObjectSchema:
    sport_object_created = await SportObjectSQLAlchemyService().add(sport_object)
    return sport_object_created


@sports_router.get("/objects/{sport_object_id}/images/")
async def get_sport_object_images(sport_object_id: int) -> list[SportObjectImageSchema] | None:
    sport_object_images = await SportObjectImageSQLAlchemyService().get_all(sport_object_id=sport_object_id)
    return sport_object_images


@sports_router.post("/sports/objects/{sport_object_id}/images")
async def add_sport_object_images(sport_object_id: int, files: list[UploadFile] = File(...)) -> list[SportObjectImageSchema]:
    uploaded_images = await SportObjectImageSQLAlchemyService().add(sport_object_id, files)
    return uploaded_images
