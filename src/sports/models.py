from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geography
from geoalchemy2.types import Geometry
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base

# Base = declarative_base()
# metadata = Base.metadata


sport_objects_tags = Table(
    'sport_objects_tags',
    Base.metadata,
    Column('sport_id', ForeignKey('sport.id'), primary_key=True),
    Column('sport_object_id', ForeignKey('sport_object.id'), primary_key=True),
)

sport_objects_images = Table(
    'sport_objects_images',
    Base.metadata,
    Column('sport_object_image_id', ForeignKey(
        'sport_object_image.id'), primary_key=True),
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
    y_coord: Mapped[float] = mapped_column(
        Numeric(17, 15), nullable=False)  # Latitude
    x_coord: Mapped[float] = mapped_column(
        Numeric(18, 15), nullable=False)  # Longitude

    # Use PostGIS geometry column (SRID 4326 for WGS84 latitude/longitude)
    location: Mapped[str] = mapped_column(
        Geography('POINT', srid=4326), nullable=True)

    address: Mapped[str] = mapped_column(String(255), nullable=True)
    # TODO: created_at: Mapped[datetime]

    images: Mapped[list[SportObjectImage]] = relationship(
        secondary=sport_objects_images, lazy="selectin")

    tags: Mapped[list[Sport]] = relationship(
        secondary=sport_objects_tags, lazy="selectin")

    def __str__(self) -> str:
        return f"{self.x_coord}, {self.y_coord}, {self.name}, {self.address}, {[str(tag) for tag in self.tags]}"


class SportObjectImage(Base):
    __tablename__ = "sport_object_image"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
