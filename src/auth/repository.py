from typing import Type

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserProfile
from src.auth.schemas import UserProfileCreate, UserProfileUpdate
from src.repository import ModelType, SQLAlchemyRepository
from src.sports.models import Sport
from src.utils import parse_pydantic_schema


class UserRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = User) -> None:
        super().__init__(model, db_session)


class UserProfileRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = UserProfile) -> None:
        super().__init__(model, db_session)

    async def create(self, data: UserProfileCreate) -> UserProfile:
        async with self._session_factory as session:
            parsed_schema = parse_pydantic_schema(data)
            sports = parsed_schema.pop("sports")
            instance = self.model(**parsed_schema)

            # NOTE: Copypaste from sports.repository
            # WARNING: Just a feeling I get, that this is so bad...
            for sport in sports:
                query = select(Sport).where(Sport.name == sport.name)
                db_sport = (await session.execute(query)).scalar_one_or_none()

                # TODO: Do not create a tag if there is no such tag in database
                if db_sport is None:
                    db_sport = sport
                    session.add(db_sport)

                instance.sports.append(db_sport)

            session.add(instance)
            await session.flush()
            await session.commit()

            return instance

    async def update_single(self, data: UserProfileUpdate, **filters) -> ModelType:
        async with self._session_factory as session:
            stmt = update(self.model).values(
                **data).filter_by(**filters).returning(self.model)
            res = await session.execute(stmt)
            await session.commit()
            return res

    async def get_multi(self, order: str = "id", limit: int = 100, offset: int = 0, **filters) -> list[ModelType]:
        async with self._session_factory as session:
            stmt = (select(self.model)
                    .join(User, self.model.user_id == User.id)
                    .filter(User.is_active == True)
                    .filter_by(**filters)
                    .order_by(order)
                    .limit(limit)
                    .offset(offset)
                    )
            row = await session.execute(stmt)
            return row.scalars().all()
