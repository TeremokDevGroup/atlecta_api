from abc import ABC, abstractmethod

from src.database import async_session_maker
from src.repository import SQLAlchemyRepository
from src.sports.models import Sport, SportObject
from src.sports.repository import SportObjectRepository, SportRepository


class AbstractUnitOfWork(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self):
        raise NotImplementedError

    @abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abstractmethod
    async def rollback(self):
        raise NotImplementedError


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):

    def __init__(self, session_factory=async_session_maker) -> None:
        self.session_factory = session_factory

    async def __aenter__(self, *args, **kwargs):
        self.session = self.session_factory()
        self.sports = SportRepository(
            db_session=self.session, model=Sport)
        self.sport_objects = SportObjectRepository(
            db_session=self.session, model=SportObject)

    async def __aexit__(self, *args, **kwargs):
        await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
