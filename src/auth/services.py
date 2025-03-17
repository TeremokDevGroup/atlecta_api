import uuid
from src.auth.schemas import UserProfileSchema, UserProfileCreateSchema, UserProfileUpdateSchema
from src.unitofwork import SQLAlchemyUnitOfWork


class UserProfileSQLAlchemyService():

    def __init__(self, uow: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork()) -> None:
        self.uow = uow

    async def add(self, user_profile: UserProfileCreateSchema) -> UserProfileSchema:
        async with self.uow:
            user_profile = await self.uow.user_profiles.create(user_profile)
            created_profile = UserProfileSchema.model_validate(user_profile)
            return created_profile

    async def update(self, user_profile: UserProfileUpdateSchema) -> UserProfileSchema:
        async with self.uow:
            user_profile = await self.uow.user_profiles.update(user_profile)
            updated_profile = UserProfileSchema.model_validate(user_profile)
            return updated_profile

    async def get_all(self) -> list[UserProfileSchema]:
        async with self.uow:
            user_profiles = await self.uow.user_profiles.get_multi()
            user_profiles = [UserProfileSchema.model_validate(
                user_profile) for user_profile in user_profiles]
            return user_profiles

    async def get_by_id(self, id: uuid.UUID) -> UserProfileSchema:
        async with self.uow:
            user_profiles = await self.uow.user_profiles.get_single(user_id=id)
            user_profiles = UserProfileSchema.model_validate(user_profiles)
            return user_profiles
