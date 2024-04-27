from __future__ import annotations

from typing import Set
from sqlalchemy import Column, Numeric, String, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.sports import schemas

Base = declarative_base()
metadata = Base.metadata


sports_objects_tags = Table(
    'sports_objects_tags',
    Base.metadata,
    Column('sport_id', ForeignKey('sport.id'), primary_key=True),
    Column('sport_object_id', ForeignKey('sport_object.id'), primary_key=True),
)


class Sport(Base):
    __tablename__ = "sport"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    def to_read_model(self) -> schemas.Sport:
        return schemas.Sport(
            id=self.id,
            name=self.name
        )


class SportObject(Base):
    __tablename__ = "sport_object"

    id: Mapped[int] = mapped_column(primary_key=True)
    x_coord: Mapped[float] = mapped_column(Numeric(17, 15), nullable=False)
    y_coord: Mapped[float] = mapped_column(Numeric(18, 15), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=True)

    tags: Mapped[Set[Sport]] = relationship(
        secondary=sports_objects_tags)

    def __str__(self) -> str:
        return f"{self.name} || {self.x_coord}, {self.y_coord}"
