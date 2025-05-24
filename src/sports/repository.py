from typing import Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from geoalchemy2.functions import ST_Distance, ST_SetSRID, ST_MakePoint
from src.repository import ModelType, SQLAlchemyRepository
from src.sports.models import Sport, SportObject, SportObjectImage
from src.sports.schemas import SportObjectCreateSchema, SportObjectImageCreateSchema
from src.utils import parse_pydantic_schema


class SportRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = Sport) -> None:
        super().__init__(model, db_session)


class SportObjectImageRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = SportObjectImage) -> None:
        super().__init__(model, db_session)

    async def create(self, sport_object_id: int, data: SportObjectImageCreateSchema) -> SportObject:
        async with self.db_session as session:
            stmt = select(SportObject).where(SportObject.id == sport_object_id)
            res = await session.execute(stmt)
            sport_object = res.scalar_one()

            parsed_schema = parse_pydantic_schema(data)
            instance = self.model(**parsed_schema)

            sport_object.images.append(instance)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)

        return instance

    async def get_all_by_object_id(self, order: str = "id", limit: int = 100, offset: int = 0, **filters) -> list[ModelType] | None:
        async with self.db_session as session:
            stmt = select(SportObject).filter_by(**filters)

            result = await session.execute(stmt)
            sport_object = result.scalars().first()

            if sport_object:
                return sport_object.images
            else:
                return None


class SportObjectRepository(SQLAlchemyRepository):

    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = SportObject) -> None:
        super().__init__(model, db_session)

    async def create(self, data: SportObjectCreateSchema) -> ModelType:
        async with self.db_session as session:
            parsed_schema = parse_pydantic_schema(data)
            tags = parsed_schema.pop("tags")
            instance = self.model(**parsed_schema)

            # WARNING: Just a feeling I get, that this is so bad...
            for tag in tags:
                query = select(Sport).where(Sport.name == tag.name)
                db_tag = (await session.execute(query)).scalar_one_or_none()

                # TODO: Do not create a tag if there is no such tag in database
                if db_tag is None:
                    # db_tag = tag
                    # session.add(db_tag)
                    continue

                instance.tags.append(db_tag)

            session.add(instance)
            # await session.flush()
            await session.commit()

            return instance

    async def get_multi(self, order: str = "id", limit: int = 100, offset: int = 0) -> list[ModelType]:
        # WARNING: order: str is unsafe. Need to order by order_column or something like that
        stmt = select(self.model).order_by(
            order).limit(limit).offset(offset)
        row = await self.db_session.execute(stmt)

        return row.scalars().all()

    async def find_nearest(
        self,
        y_coord: float,
        x_coord: float,
        limit: int = 10,
        max_distance_meters: float | None = None,
        **filters
    ) -> list[SportObject]:
        user_point = ST_SetSRID(ST_MakePoint(x_coord, y_coord), 4326)
        distance = ST_Distance(self.model.location,
                               user_point).label("distance")
        query = select(self.model, distance)

        if filters:
            query = query.filter_by(**filters)
        if max_distance_meters is not None:
            query = query.where(distance <= max_distance_meters)

        query = query.order_by(distance).limit(limit)
        result = await self.db_session.execute(query)

        nearest_objects = [row[0] for row in result.all()]
        return nearest_objects
