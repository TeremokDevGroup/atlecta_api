from src.repository import AbstractRepository
from src.sports.schemas import SportCreate


class SportService():

    def __init__(self, sports_repo: AbstractRepository) -> None:
        self.sports_repo: AbstractRepository = sports_repo()

    async def add_sport(self, sport: SportCreate):
        sport_dict = sport.model_dump()
        sport_id = await self.sports_repo.add_one(sport_dict)
        return sport_id

    async def get_all(self):
        sports = await self.sports_repo.get_all()
        return sports
