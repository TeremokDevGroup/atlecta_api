from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from src.sports.models import Inventory, Sport as SportModel, SportObject, SportObjectInventory


class InventoryBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True, frozen=True)

    class Meta:
        orm_model = Inventory

    def __eq__(self, other):
        return self.name == other.name


class InventoryCreateSchema(InventoryBaseSchema):
    pass


class InventorySchema(InventoryBaseSchema):
    id: int


class SportObjectInventoryBaseSchema(BaseModel):
    amount: int = Field(default=0, ge=0)  # Ensure amount is non-negative
    inventory: InventoryBaseSchema

    model_config = ConfigDict(from_attributes=True, frozen=True)

    class Meta:
        orm_model = SportObjectInventory


class SportObjectInventorySchema(SportObjectInventoryBaseSchema):
    id: int


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
    inventory: list[SportObjectInventoryBaseSchema]

    @field_validator("tags")
    def validate_tags(cls, value: list[SportBaseSchema]) -> list[SportBaseSchema]:
        return list(set(value))

    model_config = ConfigDict(from_attributes=True)

    class Meta:
        orm_model = SportObject


class SportObjectCreateSchema(SportObjectBaseSchema):
    # TODO: Remove this from OpenAPI schema
    location: str = Field(default="", exclude=False)

    @model_validator(mode="after")
    def populate_location(self) -> "SportObjectCreateSchema":
        self.location = f"POINT({self.x_coord} {self.y_coord})"
        return self


class SportObjectUpdateSchema(BaseModel):
    id: int
    name: str | None = None
    y_coord: float | None = None
    x_coord: float | None = None
    address: str | None = None

    tags: list[SportBaseSchema] | None = None
    inventory: list[SportObjectInventoryBaseSchema] | None = None

    @field_validator("tags")
    def validate_tags(cls, value: list[SportBaseSchema] | None) -> list[SportBaseSchema] | None:
        if value is None:
            return value

        return list(set(value))

    # TODO: Remove this from OpenAPI schema
    location: str | None = None

    @model_validator(mode="after")
    def populate_location(self) -> "SportObjectUpdateSchema":
        if self.location is None:
            return self

        self.location = f"POINT({self.x_coord} {self.y_coord})"
        return self

    model_config = ConfigDict(from_attributes=True)


class SportObjectSchema(SportObjectBaseSchema):
    id: int


class SportObjectImageBaseSchema(BaseModel):
    url: str


class SportObjectImageCreateSchema(SportObjectImageBaseSchema):
    sport_object_id: int


class SportObjectImageSchema(SportObjectImageBaseSchema):
    id: uuid.UUID
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)
