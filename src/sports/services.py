from pydantic import parse_obj_as

from src.sports.schemas import Sport, SportCreate, SportObject, SportObjectCreate, SportBase
from src.unitofwork import SQLAlchemyUnitOfWork


class SportSQLAlchemyService():
    def __init__(self, uow: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork()) -> None:
        self.uow = uow

    async def add(self, sport: SportCreate):
        async with self.uow:
            sport_dict = sport.model_dump()
            sport_id = await self.uow.sports.create(sport_dict)
            return sport_id

    async def get_all(self) -> list[Sport]:
        async with self.uow:
            sports = await self.uow.sports.get_multi()
            return sports

    async def get_by_id(self, id: int) -> Sport:
        async with self.uow:
            sport = await self.uow.sports.get_single(id=id)
            sport = Sport.model_validate(sport)
            return sport


class SportObjectSQLAlchemyService():
    # TODO: Here (and in class above) I need to put uow factory
    def __init__(self, uow: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork()) -> None:
        self.uow = uow

    async def add(self, sport_object: SportObjectCreate) -> SportObjectCreate:
        async with self.uow:
            sports_list = await self.uow.sports.get_multi()
            sports_list = parse_obj_as(list[SportBase], sports_list)

            for sport in sport_object.tags:
                if sport not in sports_list:
                    # TODO: Proper error handling
                    print("THERE IS NO SUCH SPORT IN DATABASE")

            sport_object = await self.uow.sport_objects.create(sport_object)
            return sport_object

    async def get_all(self) -> list[SportObject]:
        async with self.uow:
            sport_objects = await self.uow.sport_objects.get_multi()
            return sport_objects

    async def get_by_id(self, id: int) -> SportObject:
        async with self.uow:
            sport_object = await self.uow.sport_objects.get_single(id=id)
            sport_object = SportObject.model_validate(sport_object)
            return sport_object
