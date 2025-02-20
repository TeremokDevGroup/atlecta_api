from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, File

from .services import SportObjectImageSQLAlchemyService, SportObjectSQLAlchemyService, SportSQLAlchemyService
from src.sports.schemas import SportCreate, SportObjectCreate, SportObjectImage

sports_router = APIRouter(
    prefix="/sports",
    tags=["sports"],
    responses={404: {"description": "Not found"}},
)


@sports_router.get("/")
async def get_all_sports():
    sports = await SportSQLAlchemyService().get_all()
    return {"sports": sports}


@sports_router.get("/{sport_id}")
async def get_sport_by_id(sport_id: int):
    sport = await SportSQLAlchemyService().get_by_id(id=sport_id)
    return {sport_id: sport}


@sports_router.post("/")
async def add_sport(sport: Annotated[SportCreate, Depends(SportCreate)]):
    sport_id = await SportSQLAlchemyService().add(sport)
    return {"sport_id": sport_id}


@sports_router.get("/objects/")
async def get_all_sport_objects():
    sport_objects = await SportObjectSQLAlchemyService().get_all()
    return sport_objects


@sports_router.get("/objects/{sport_object_id}/")
async def get_sport_object_by_id(sport_object_id: int):
    sport_object = await SportObjectSQLAlchemyService().get_by_id(id=sport_object_id)
    return {"sport_object": sport_object}


@sports_router.post("/objects")
async def add_sport_object(sport_object: Annotated[SportObjectCreate, Depends(SportObjectCreate)]):
    sport_object = await SportObjectSQLAlchemyService().add(sport_object)
    return sport_object


@sports_router.get("/objects/{sport_object_id}/images/")
async def get_sport_object_images(sport_object_id: int) -> list[SportObjectImage] | None:
    sport_object_images = await SportObjectImageSQLAlchemyService().get_all(sport_object_id=sport_object_id)
    return sport_object_images


@sports_router.post("/sports/objects/{sport_object_id}/images")
async def add_sport_object_images(
    sport_object_id: int,
    files: list[UploadFile] = File(...)
):

    uploaded_images = await SportObjectImageSQLAlchemyService().add(sport_object_id, files)
    return {"uploaded_images": uploaded_images}
