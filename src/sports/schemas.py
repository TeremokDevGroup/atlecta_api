from pydantic import BaseModel


class SportBase(BaseModel):
    name: str


class SportCreate(SportBase):
    pass


class Sport(SportBase):
    id: int

    class Config:
        from_attributes = True

    def __eq__(self, other):
        return self.name == other.name


class SportObjectBase(BaseModel):
    x_coord: float
    y_coord: float
    address: str

    tags: set[Sport]


class SportObjectCreate(SportObjectBase):
    pass


class SportObject(SportObjectBase):
    id: int

    class Config:
        from_attributes = True
