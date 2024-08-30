from pydantic import BaseModel, field_validator
from typing import Optional
from src.sports.models import Sport as SportModel


class SportBase(BaseModel):
    name: str

    class Config:
        from_attributes = True
        frozen = True

    class Meta:
        orm_model = SportModel


class SportCreate(SportBase):
    pass


class Sport(SportBase):
    id: int

    def __eq__(self, other):
        return self.name == other.name


class SportObjectBase(BaseModel):
    name: str
    x_coord: float
    y_coord: float
    address: Optional[str] = None

    # NOTE: It's actually should be a set() but I get 'is not hashable' error when I call .model_dump()
    tags: list[SportBase]

    @field_validator("tags")
    def validate_tags(cls, value: list[SportBase]) -> list[SportBase]:
        return list(set(value))

    class Config:
        from_attributes = True


class SportObjectCreate(SportObjectBase):
    pass


class SportObject(SportObjectBase):
    id: int
