import uuid
from datetime import datetime

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


# NOTE: Not inherited from UserProfileBaseShcema to make fiels optional
class UserProfileUpdateSchema(BaseModel):
    user_id: uuid.UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    age: int | None = None
    height: int | None = None
    weight: int | None = None
    gender: int | None = None
    bio: str | None = None

    sports: list[SportBaseSchema] | None = None

    @field_validator("sports")
    def unique_sport_list(cls, value: list[SportBaseSchema] | None) -> list[SportBaseSchema] | None:
        if value is None:
            return value

        return list(set(value))

    model_config = ConfigDict(from_attributes=True)


class UserProfileSchema(UserProfileBaseSchema):
    user_id: uuid.UUID
    bio: str


class UserImageBaseSchema(BaseModel):
    url: str


class UserImageCreateSchema(UserImageBaseSchema):
    pass


class UserImageSchema(UserImageBaseSchema):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
