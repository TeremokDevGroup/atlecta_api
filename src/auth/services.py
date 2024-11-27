import uuid
from src.auth.schemas import UserProfile, UserProfileCreate, UserProfileUpdate
from src.unitofwork import SQLAlchemyUnitOfWork


class UserProfileSQLAlchemyService():

    def __init__(self, uow: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork()) -> None:
        self.uow = uow

    async def add(self, user_profile: UserProfileCreate) -> UserProfile:
        async with self.uow:
            user_profile = await self.uow.user_profiles.create(user_profile)
            created_profile = UserProfile.model_validate(user_profile)
            return created_profile

    async def update(self, user_profile: UserProfileUpdate) -> UserProfile:
        async with self.uow:
            user_profile = await self.uow.user_profiles.update(user_profile)

    async def get_all(self) -> list[UserProfile]:
        async with self.uow:
            user_profiles = await self.uow.user_profiles.get_multi()
            user_profiles = [UserProfile.model_validate(
                user_profile) for user_profile in user_profiles]
            return user_profiles

    async def get_by_id(self, id: uuid.UUID) -> UserProfile:
        async with self.uow:
            user_profiles = await self.uow.user_profiles.get_single(user_id=id)
            user_profiles = UserProfile.model_validate(user_profiles)
            return user_profiles
