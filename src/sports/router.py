from typing import Annotated
from fastapi import APIRouter, Depends

from src.sports.dependencies import sport_service
from .repository import SportRepository
from .services import SportService
from src.sports.schemas import SportCreate

router = APIRouter(
    prefix="/sports",
    tags=["sports"],
    responses={404: {"description": "Not found"}},
)


@router.get("/greeting")
async def greeting():
    return {"message": "Hello World"}


@router.get("/sports/sports-list")
async def get_sports(sport_service: Annotated[SportService, Depends(sport_service)]):
    sports = await sport_service.get_all()
    return {"sports": sports}


@router.post("/sports/add")
async def add_sport(sport: Annotated[SportCreate, Depends(SportCreate)],
                    sport_service: Annotated[SportService, Depends(sport_service)]):
    sport_id = await sport_service.add_sport(sport)
    return {"sport_id": sport_id}
