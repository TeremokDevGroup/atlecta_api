from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional
from src.sports.models import Sport as SportModel


class SportBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True, frozen=True)

    class Meta:
        orm_model = SportModel

    def __eq__(self, other):
        return self.name == other.name


class SportCreateSchema(SportBaseSchema):
    pass


class SportSchema(SportBaseSchema):
    id: int


class SportObjectBaseSchema(BaseModel):
    name: str
    y_coord: float
    x_coord: float
    address: str | None = None

    # NOTE: It's actually should be a set() but I get 'is not hashable' error when I call .model_dump()
    tags: list[SportBaseSchema]

    @field_validator("tags")
    def validate_tags(cls, value: list[SportBaseSchema]) -> list[SportBaseSchema]:
        return list(set(value))

    model_config = ConfigDict(from_attributes=True)


class SportObjectCreateSchema(SportObjectBaseSchema):
    # TODO: Remove this from OpenAPI schema
    location: str = Field(default="", exclude=False)

    @model_validator(mode="after")
    def populate_location(self) -> "SportObjectCreateSchema":
        self.location = f"POINT({self.x_coord} {self.y_coord})"
        return self


class SportObjectSchema(SportObjectBaseSchema):
    id: int


class SportObjectImageBaseSchema(BaseModel):
    url: str


class SportObjectImageCreateSchema(SportObjectImageBaseSchema):
    pass


class SportObjectImageSchema(SportObjectImageBaseSchema):
    id: uuid.UUID
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
