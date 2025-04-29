import uuid

from fastapi import Depends
from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
)
from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import (
    Column,
    ForeignKey,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from src.database import Base, get_async_session
from src.sports.models import Sport

# Base = declarative_base()
# metadata = Base.metadata


user_profiles_sports = Table(
    'user_profiles_sports',
    Base.metadata,
    Column('user_profile_id', ForeignKey('user_profile.id'), primary_key=True),
    Column('sport_id', ForeignKey(Sport.id), primary_key=True),
)


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("user_account.id", ondelete="cascade"), nullable=False
    )


class User(SQLAlchemyBaseUserTableUUID, Base):
    # NOTE: since 'user' is a reserved name in PostgreSQL.
    # Also this way we decompose 'user' to 'user_account' and 'user_profile'
    __tablename__ = "user_account"

    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined")

    profile: Mapped["UserProfile"] = relationship(
        back_populates="user_account")
    # created_at: datetime = Field(default=datetime.utcnow(), nullable=False)
    # last_edited: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profile"
    __table_args__ = (UniqueConstraint(
        "user_id", name="one_user_to_one_profile"),)
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"))
    user_account: Mapped[User] = relationship(back_populates="profile")

    first_name: Mapped[str] = mapped_column(String(150))
    last_name: Mapped[str] = mapped_column(String(150))
    age: Mapped[int] = mapped_column()
    gender: Mapped[int] = mapped_column(SmallInteger())
    height: Mapped[int] = mapped_column()
    weight: Mapped[int] = mapped_column()
    bio: Mapped[str] = mapped_column(Text)  # NOTE: deferred=True

    sports: Mapped[list[Sport]] = relationship(
        secondary=user_profiles_sports, lazy="selectin")


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)
