from src.repository import AbstractRepository
from src.sports.schemas import SportCreate, Sport
from src.unitofwork import AbstractUnitOfWork, SQLAlchemyUnitOfWork


class SportSQLAlchemyService():

    def __init__(self, uow: AbstractUnitOfWork = SQLAlchemyUnitOfWork()) -> None:
        self.uow = uow

    async def add_sport(self, sport: SportCreate):
        async with self.uow:
            sport_dict = sport.model_dump()
            sport_id = await self.uow.sports.create(sport_dict)
            return sport_id

    async def get_all(self):
        async with self.uow:
            sports = await self.uow.sports.get_multi()
            return sports

    async def get_by_id(self, id: int) -> Sport:
        async with self.uow:
            sport = await self.uow.sports.get_single(id=id)
            return sport
