from typing import Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository import ModelType, SQLAlchemyRepository
from src.sports.models import Sport, SportObject
from src.sports.schemas import SportObjectCreate
from src.utils import parse_pydantic_schema


class SportRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = Sport) -> None:
        super().__init__(model, db_session)


class SportObjectRepository(SQLAlchemyRepository):

    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = SportObject) -> None:
        super().__init__(model, db_session)

    async def create(self, data: SportObjectCreate) -> ModelType:
        async with self._session_factory as session:
            parsed_schema = parse_pydantic_schema(data)
            tags = parsed_schema.pop("tags")
            instance = self.model(**parsed_schema)

            # await session.commit()
            # await session.refresh(instance, ["tags"])

            for tag in tags:
                query = select(Sport).where(Sport.name == tag.name)
                db_tag = (await session.execute(query)).scalar_one_or_none()

                # TODO: Do not create a tag if there is no such tag in database
                if db_tag is None:
                    db_tag = Sport(name=tag)
                    session.add(db_tag)

                instance.tags.append(db_tag)

            session.add(instance)
            await session.flush()
            await session.commit()

            return instance

    async def get_multi(self, order: str = "id", limit: int = 100, offset: int = 0) -> list[ModelType]:
        async with self._session_factory as session:
            stmt = select(self.model).order_by(
                order).limit(limit).offset(offset)
            row = await session.execute(stmt)
            return row.scalars().all()
