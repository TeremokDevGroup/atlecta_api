from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from src.sports.models import Sport as SportModel


class SportBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True, frozen=True)

    class Meta:
        orm_model = SportModel

    def __eq__(self, other):
        return self.name == other.name


class SportCreateShema(SportBaseSchema):
    pass


class SportSchema(SportBaseSchema):
    id: int


class SportObjectBaseSchema(BaseModel):
    name: str
    x_coord: float
    y_coord: float
    address: Optional[str] = None

    # NOTE: It's actually should be a set() but I get 'is not hashable' error when I call .model_dump()
    tags: list[SportBaseSchema]

    @field_validator("tags")
    def validate_tags(cls, value: list[SportBaseSchema]) -> list[SportBaseSchema]:
        return list(set(value))

    model_config = ConfigDict(from_attributes=True)


class SportObjectCreateSchema(SportObjectBaseSchema):
    pass


class SportObjectSchema(SportObjectBaseSchema):
    id: int


class SportObjectImageBaseSchema(BaseModel):
    url: str


class SportObjectImageCreateSchema(SportObjectImageBaseSchema):
    pass


class SportObjectImageSchema(SportObjectImageBaseSchema):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
