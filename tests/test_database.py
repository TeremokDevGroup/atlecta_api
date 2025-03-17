from src.sports.schemas import SportCreateSchema, SportSchema
from src.sports.services import SportSQLAlchemyService
from src.unitofwork import SQLAlchemyUnitOfWork
from conftest import async_session_maker


async def test_sport_create():
    uow = SQLAlchemyUnitOfWork(async_session_maker)
    service = SportSQLAlchemyService(uow)

    sport = SportCreateSchema(name="Some sport")
    await service.add(sport)

    sport = await service.get_by_id(id=1)

    assert sport == SportSchema(id=2, name="Some sport")
