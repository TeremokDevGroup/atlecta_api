from __future__ import annotations

from sqlalchemy import Column, Numeric, String, ForeignKey, Table, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base, metadata, get_async_session

# Base = declarative_base()
# metadata = Base.metadata


sport_objects_tags = Table(
    'sport_objects_tags',
    Base.metadata,
    Column('sport_id', ForeignKey('sport.id'), primary_key=True),
    Column('sport_object_id', ForeignKey('sport_object.id'), primary_key=True),
)


class Sport(Base):
    __tablename__ = "sport"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    def __str__(self) -> str:
        return f"{self.id} {self.name}"


class SportObject(Base):
    __tablename__ = "sport_object"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    x_coord: Mapped[float] = mapped_column(Numeric(17, 15), nullable=False)
    y_coord: Mapped[float] = mapped_column(Numeric(18, 15), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=True)

    tags: Mapped[set[Sport]] = relationship(
        secondary=sport_objects_tags, lazy="selectin")

    def __str__(self) -> str:
        return f"{self.x_coord}, {self.y_coord}, {self.address}, {[str(tag) for tag in self.tags]}"
