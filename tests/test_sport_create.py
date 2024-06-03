from src.sports.schemas import SportCreate, Sport
from src.sports.services import SportSQLAlchemyService
from src.unitofwork import SQLAlchemyUnitOfWork
from conftest import async_session_maker


async def test_sport_create():
    uow = SQLAlchemyUnitOfWork(async_session_maker)
    service = SportSQLAlchemyService(uow)

    sport = SportCreate(name="Some sport")
    await service.add_sport(sport)

    sport = await service.get_by_id(id=1)

    assert sport == Sport(id=2, name="Some sport")
