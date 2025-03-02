import uuid

from pydantic import BaseModel, ConfigDict, field_validator
from fastapi_users import schemas

from src.sports.schemas import SportBaseSchema


class UserReadSchema(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreateSchema(schemas.BaseUserCreate):
    pass


class UserUpdateSchema(schemas.BaseUserUpdate):
    pass


class UserProfileBaseSchema(BaseModel):
    first_name: str
    last_name: str
    age: int
    height: int
    weight: int
    gender: int

    sports: list[SportBaseSchema]

    @field_validator("sports")
    def validate_tags(cls, value: list[SportBaseSchema]) -> list[SportBaseSchema]:
        return list(set(value))

    model_config = ConfigDict(from_attributes=True)


class UserProfileCreateSchema(UserProfileBaseSchema):
    user_id: uuid.UUID
    bio: str


class UserProfileUpdateSchema(UserProfileBaseSchema):
    user_id: uuid.UUID
    bio: str


class UserProfileSchema(UserProfileBaseSchema):
    user_id: uuid.UUID
    bio: str
