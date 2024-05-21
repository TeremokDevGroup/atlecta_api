from typing import Annotated
from fastapi import APIRouter, Depends

from .services import SportSQLAlchemyService
from src.sports.schemas import SportCreate

router = APIRouter(
    prefix="/sports",
    tags=["sports"],
    responses={404: {"description": "Not found"}},
)


@router.get("/greeting")
async def greeting():
    return {"message": "Hello World"}


@router.get("/all")
async def get_all_sports():
    sports = await SportSQLAlchemyService().get_all()
    return {"sports": sports}


@router.get("/{sport_id}")
async def get_sport_by_id(sport_id: int):
    sport = await SportSQLAlchemyService().get_by_id(id=sport_id)
    return {sport_id: sport}


@router.post("/sports/add")
async def add_sport(sport: Annotated[SportCreate, Depends(SportCreate)]):
    sport_id = await SportSQLAlchemyService().add_sport(sport)
    return {"sport_id": sport_id}
