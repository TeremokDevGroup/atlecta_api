from typing import Annotated
from fastapi import APIRouter, Depends

from .services import SportObjectSQLAlchemyService, SportSQLAlchemyService
from src.sports.schemas import SportCreate, SportObjectCreate

router = APIRouter(
    prefix="/sports",
    tags=["sports"],
    responses={404: {"description": "Not found"}},
)


@router.get("/greeting")
async def greeting():
    return {"message": "Hello World"}


@router.get("/")
async def get_all_sports():
    sports = await SportSQLAlchemyService().get_all()
    return {"sports": sports}


@router.get("/{sport_id}")
async def get_sport_by_id(sport_id: int):
    sport = await SportSQLAlchemyService().get_by_id(id=sport_id)
    return {sport_id: sport}


@router.post("/")
async def add_sport(sport: Annotated[SportCreate, Depends(SportCreate)]):
    sport_id = await SportSQLAlchemyService().add(sport)
    return {"sport_id": sport_id}


@router.get("/objects")
async def get_all_sport_objects():
    sports = await SportObjectSQLAlchemyService().get_all()
    return {"sport_objects": sports}


@router.get("/objects/{sport_object_id}")
async def get_sport_object_by_id(sport_object_id: int):
    sport_object = await SportObjectSQLAlchemyService().get_by_id(id=sport_object_id)
    return {"sport_object": sport_object}


@router.post("/objects")
async def add_sport_object(sport_object: Annotated[SportObjectCreate, Depends(SportObjectCreate)]):
    sport_object = await SportObjectSQLAlchemyService().add(sport_object)
    return {"sport_object": sport_object}
