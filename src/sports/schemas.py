from pydantic import BaseModel


class SportBase(BaseModel):
    name: str


class SportCreate(SportBase):
    pass


class Sport(SportBase):
    id: int

    class Config:
        from_attributes = True
