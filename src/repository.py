from abc import ABC, abstractmethod
from typing import Generic, Optional, Type, TypeVar

from src.database import Base
from pydantic import BaseModel

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils import parse_pydantic_schema


class AbstractRepository(ABC):

    @abstractmethod
    async def create(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def update(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def get_single(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def get_multi(self, **kwargs):
        raise NotImplementedError


class FakeRepository(AbstractRepository):
    def __init__(self, objects):
        self._objects = set(objects)

    def add(self, objects):
        self._objects.add(objects)

    def get(self, reference):
        return next(b for b in self._objects if b.reference == reference)

    def list(self):
        return list(self._objects)


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class SQLAlchemyRepository(AbstractRepository, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):

    def __init__(self, model: Type[ModelType], db_session: AsyncSession) -> None:
        self._session_factory = db_session
        self.model = model

    async def create(self, data: CreateSchemaType) -> ModelType:
        async with self._session_factory as session:
            parsed_schema = parse_pydantic_schema(data)
            instance = self.model(**parsed_schema)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    async def update(self, data: UpdateSchemaType, **filters) -> ModelType:
        async with self._session_factory as session:
            stmt = update(self.model).values(
                **data).filter_by(**filters).returning(self.model)
            res = await session.execute(stmt)
            await session.commit()
            return res

    async def delete(self, **filters) -> None:
        async with self._session_factory as session:
            await session.execute(delete(self.model).filter_by(**filters))
            await session.commit()

    async def get_single(self, **filters) -> Optional[ModelType] | None:
        async with self._session_factory as session:
            row = await session.execute(select(self.model).filter_by(**filters))
            return row.scalar_one_or_none()

    async def get_multi(self, order: str = "id", limit: int = 100, offset: int = 0) -> list[ModelType]:
        async with self._session_factory as session:
            stmt = select(self.model).order_by(
                order).limit(limit).offset(offset)
            row = await session.execute(stmt)
            return row.scalars().all()
