import uuid
from typing import Any, List, Type

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.models import (
    FriendStatus,
    User,
    UserProfile,
    UserProfileImage,
    friendships,
)
from src.auth.schemas import (
    UserProfileCreateSchema,
    UserProfileImageCreateSchema,
    UserProfileUpdateSchema,
)
from src.repository import ModelType, SQLAlchemyRepository
from src.sports.models import Sport
from src.utils import parse_pydantic_schema


class UserRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = User) -> None:
        super().__init__(model, db_session)


class UserProfileRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = UserProfile) -> None:
        super().__init__(model, db_session)

    async def create(self, data: UserProfileCreateSchema) -> UserProfile:
        async with self.db_session as session:
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
            await session.refresh(instance)

            return instance

    async def update_single(self, data: UserProfileUpdateSchema, **filters: Any) -> UserProfile:
        async with self.db_session as session:
            parsed_schema = parse_pydantic_schema(data)
            sports = parsed_schema.pop("sports", None)

            update_data = data.model_dump(
                exclude_none=True, exclude_unset=True)
            update_data.pop("sports", None)

            stmt = select(UserProfile).where(
                UserProfile.user_id == data.user_id)
            row = await session.execute(stmt)
            profile = row.scalars().one()

            for key, value in update_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
                else:
                    # Log a warning if a field from the schema doesn't exist on the model.
                    # This might indicate a mismatch between schema and model definitions.
                    print(
                        f"Warning: Attribute '{key}' from update data not found on UserProfile model.")

            if sports is not None:
                profile.sports = []
                for sport in sports:
                    query = select(Sport).where(Sport.name == sport.name)
                    db_sport = (await session.execute(query)).scalar_one_or_none()

                    if db_sport is not None:
                        profile.sports.append(db_sport)

            session.add(profile)
            await session.flush()
            await session.commit()

            return profile

    async def get_multi(self, order: str = "id", limit: int = 100, offset: int = 0, filter: Filter | None = None, **filters) -> list[ModelType]:
        async with self.db_session as session:
            # stmt = (select(self.model)
            #         .join(User, self.model.user_id == User.id)
            #         .filter(User.is_active == True)
            #         .order_by(order)
            #         .limit(limit)
            #         .offset(offset)
            # )

            stmt = (
                select(self.model)
                .join(User, self.model.user_id == User.id)
                .filter(User.is_active == True)
                .outerjoin(UserProfile.sports)
                .outerjoin(UserProfile.images)
                .limit(limit)
                .offset(offset)
            )

            if filter:
                stmt = filter.filter(stmt)
                stmt = filter.sort(stmt)

            try:
                result = await session.execute(stmt)
                return result.unique().scalars().all()
            except Exception as e:
                # Log the error if needed (e.g., using logging module)
                raise Exception(f"Database query failed: {str(e)}")


class UserProfileImageRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = UserProfileImage) -> None:
        super().__init__(model, db_session)

    async def create(self, user_id: uuid.UUID, data: UserProfileImageCreateSchema) -> ModelType:
        async with self.db_session as session:
            stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            res = await session.execute(stmt)
            user_profile = res.scalar_one()

            parsed_schema = parse_pydantic_schema(data)
            instance = self.model(**parsed_schema)

            user_profile.images.append(instance)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)

        return instance

    async def get_all_by_user_id(self, order: str = "user_id", limit: int = 100, offset: int = 0, **filters) -> list[ModelType] | None:
        async with self.db_session as session:
            stmt = select(UserProfile).filter_by(**filters)

            result = await session.execute(stmt)
            user_profile = result.scalars().first()

            if user_profile:
                return user_profile.images
            else:
                return None


class UserFriendsRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = User) -> None:
        super().__init__(model, db_session)

    async def create_friendship(self, user_id: uuid.UUID, friend_id: uuid.UUID, status: FriendStatus = FriendStatus.PENDING) -> bool:
        """Create a friendship record with the given status."""
        async with self.db_session as session:
            # Load user with friend_requests_sent eagerly
            stmt = select(self.model).where(self.model.id == user_id).options(
                selectinload(self.model.friend_requests_sent))
            result = await session.execute(stmt)
            user = result.unique().scalar_one_or_none()

            # Load friend
            friend = await session.get(self.model, friend_id)

            if user and friend:
                user.friend_requests_sent.append(friend)
                await session.commit()
                return True
            return False

    async def update_friendship_status(self, user_id: uuid.UUID, friend_id: uuid.UUID, status: FriendStatus) -> bool:
        """Update the status of a friendship."""
        async with self.db_session as session:
            stmt = update(friendships).where(
                friendships.c.user_id == user_id,
                friendships.c.friend_id == friend_id
            ).values(status=status)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def get_friendship(self, user_id: uuid.UUID, friend_id: uuid.UUID) -> FriendStatus | None:
        """Get the status of a friendship."""
        async with self.db_session as session:
            stmt = select(friendships.c.status).where(
                friendships.c.user_id == user_id,
                friendships.c.friend_id == friend_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_friends(self, user_id: uuid.UUID, filter=None, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all accepted friends for a user."""
        async with self.db_session as session:
            stmt = (
                select(self.model)
                .where(self.model.id == user_id)
                .options(selectinload(self.model.friends))
                .limit(limit)
                .offset(offset)
            )
            if filter:
                stmt = filter.filter(stmt)
                stmt = filter.sort(stmt)
            result = await session.execute(stmt)
            user = result.unique().scalar_one_or_none()
            return user.friends if user else []

    async def get_friend_requests_sent(self, user_id: uuid.UUID, filter=None, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all sent friend requests for a user."""
        async with self.db_session as session:
            stmt = (
                select(self.model)
                .where(self.model.id == user_id)
                .options(selectinload(self.model.friend_requests_sent))
                .limit(limit)
                .offset(offset)
            )
            if filter:
                stmt = filter.filter(stmt)
                stmt = filter.sort(stmt)
            result = await session.execute(stmt)
            user = result.unique().scalar_one_or_none()
            return user.friend_requests_sent if user else []

    async def get_friend_requests_received(self, user_id: uuid.UUID, filter=None, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all received friend requests for a user."""
        async with self.db_session as session:
            stmt = (
                select(self.model)
                .where(self.model.id == user_id)
                .options(selectinload(self.model.friend_requests_received))
                .limit(limit)
                .offset(offset)
            )
            if filter:
                stmt = filter.filter(stmt)
                stmt = filter.sort(stmt)
            result = await session.execute(stmt)
            user = result.unique().scalar_one_or_none()
            return user.friend_requests_received if user else []

    async def get_blocked_users(self, user_id: uuid.UUID, filter=None, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all blocked users for a user."""
        async with self.db_session as session:
            stmt = (
                select(self.model)
                .where(self.model.id == user_id)
                .options(selectinload(self.model.blocked_users))
                .limit(limit)
                .offset(offset)
            )
            if filter:
                stmt = filter.filter(stmt)
                stmt = filter.sort(stmt)
            result = await session.execute(stmt)
            user = result.unique().scalar_one_or_none()
            return user.blocked_users if user else []
