import uuid

from pydantic import BaseModel, ConfigDict, field_validator
from fastapi_users import schemas

from src.sports.schemas import SportBase


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class UserProfileBase(BaseModel):
    first_name: str
    last_name: str
    age: int
    height: int
    weight: int
    gender: int

    sports: list[SportBase]

    @field_validator("sports")
    def validate_tags(cls, value: list[SportBase]) -> list[SportBase]:
        return list(set(value))

    model_config = ConfigDict(from_attributes=True)


class UserProfileCreate(UserProfileBase):
    user_id: uuid.UUID
    bio: str


class UserProfileUpdate(UserProfileBase):
    user_id: uuid.UUID
    bio: str


class UserProfile(UserProfileBase):
    user_id: uuid.UUID
    bio: str
