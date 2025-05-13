import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastapi_users import schemas

from src.sports.schemas import SportBaseSchema


class UserReadSchema(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreateSchema(schemas.BaseUserCreate):
    pass


class UserUpdateSchema(schemas.BaseUserUpdate):
    pass


class UserProfileImageBaseSchema(BaseModel):
    url: str


class UserProfileImageCreateSchema(UserProfileImageBaseSchema):
    # TODO: Rename this to is_profile_image (and do the same thing for UserProfileImage model)
    is_profile_picture: bool = False


class UserProfileImageSchema(UserProfileImageBaseSchema):
    id: uuid.UUID
    is_profile_picture: bool
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileBaseSchema(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    age: int = Field(..., ge=16, le=100)
    height: int | None
    weight: int | None
    gender: int | None

    sports: list[SportBaseSchema]

    @field_validator("sports")
    def validate_tags(cls, value: list[SportBaseSchema]) -> list[SportBaseSchema]:
        return list(set(value))

    model_config = ConfigDict(from_attributes=True)


class UserProfileCreateSchema(UserProfileBaseSchema):
    _user_id: uuid.UUID
    bio: str | None

    @property
    def user_id(self) -> uuid.UUID:
        return self._user_id

    @user_id.setter
    def user_id(self, user_id: uuid.UUID):
        self._user_id = user_id


# NOTE: Not inherited from UserProfileBaseShcema to make fiels optional
class UserProfileUpdateSchema(BaseModel):
    _user_id: uuid.UUID
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

    # NOTE: This is to hide user_id from swagger schema
    @property
    def user_id(self) -> uuid.UUID:
        return self._user_id

    @user_id.setter
    def user_id(self, user_id: uuid.UUID):
        self._user_id = user_id

    model_config = ConfigDict(from_attributes=True)


class UserProfileSchema(UserProfileBaseSchema):
    user_id: uuid.UUID
    bio: str
    images: list[UserProfileImageSchema]
