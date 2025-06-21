from enum import IntEnum
import uuid
from datetime import datetime

from fastapi import Depends
from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
)
from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
    and_,
)
from sqlalchemy.sql.sqltypes import Enum  # Explicitly import SQLAlchemy Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base, get_async_session
from src.sports.models import Sport

# Base = declarative_base()
# metadata = Base.metadata


class FriendStatus(IntEnum):
    PENDING = 1
    ACCEPTED = 2
    DECLINED = 3
    BLOCKED = 4


user_profiles_sports = Table(
    'user_profiles_sports',
    Base.metadata,
    Column('user_profile_id', ForeignKey('user_profile.id'), primary_key=True),
    Column('sport_id', ForeignKey(Sport.id), primary_key=True),
)


# Friendship table for managing friend relationships and blocks
friendships = Table(
    'friendships',
    Base.metadata,
    Column('user_id', ForeignKey('user_account.id'), primary_key=True),
    Column('friend_id', ForeignKey('user_account.id'), primary_key=True),
    Column('status', Enum(FriendStatus),
           nullable=False, default=FriendStatus.PENDING),
    Column('created_at', DateTime(timezone=True),
           server_default=func.now(), nullable=False),
    Column('updated_at', DateTime(timezone=True),
           server_default=func.now(), onupdate=func.now(), nullable=False),
    UniqueConstraint('user_id', 'friend_id', name='unique_friendship')
)


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("user_account.id", ondelete="cascade"), nullable=False
    )


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user_account"

    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined")

    profile: Mapped["UserProfile"] = relationship(
        back_populates="user_account")

    # Add relationships for friends and blocked users
    # Add relationships for friends and blocked users
    friends: Mapped[list["User"]] = relationship(
        secondary=friendships,
        primaryjoin=lambda: and_(
            User.id == friendships.c.user_id,
            friendships.c.status == FriendStatus.ACCEPTED
        ),
        secondaryjoin=lambda: User.id == friendships.c.friend_id,
        lazy="selectin"
    )

    friend_requests_sent: Mapped[list["User"]] = relationship(
        secondary=friendships,
        primaryjoin=lambda: and_(
            User.id == friendships.c.user_id,
            friendships.c.status == FriendStatus.PENDING
        ),
        secondaryjoin=lambda: User.id == friendships.c.friend_id,
        lazy="selectin",
        overlaps="friends"  # Declare overlap with friends
    )

    friend_requests_received: Mapped[list["User"]] = relationship(
        secondary=friendships,
        primaryjoin=lambda: and_(
            User.id == friendships.c.friend_id,
            friendships.c.status == FriendStatus.PENDING
        ),
        secondaryjoin=lambda: User.id == friendships.c.user_id,
        lazy="selectin",
        overlaps="friend_requests_sent,friends"  # Declare overlaps
    )

    blocked_users: Mapped[list["User"]] = relationship(
        secondary=friendships,
        primaryjoin=lambda: and_(
            User.id == friendships.c.user_id,
            friendships.c.status == FriendStatus.BLOCKED
        ),
        secondaryjoin=lambda: User.id == friendships.c.friend_id,
        lazy="selectin",
        overlaps="friend_requests_received,friend_requests_sent,friends"  # Declare overlaps
    )


class UserProfile(Base):
    __tablename__ = "user_profile"
    __table_args__ = (UniqueConstraint(
        "user_id", name="one_user_to_one_profile"),)
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"))
    user_account: Mapped[User] = relationship(back_populates="profile")

    first_name: Mapped[str] = mapped_column(String(150))
    last_name: Mapped[str] = mapped_column(String(150))
    # birthday: Mapped[date] = mapped_column(Date) # correct way to store age
    age: Mapped[int] = mapped_column()
    gender: Mapped[int] = mapped_column(SmallInteger())
    height: Mapped[int] = mapped_column()
    weight: Mapped[int] = mapped_column()
    bio: Mapped[str] = mapped_column(Text)  # NOTE: deferred=True

    sports: Mapped[list[Sport]] = relationship(
        secondary=user_profiles_sports, lazy="selectin")

    images: Mapped[list["UserProfileImage"]] = relationship(
        back_populates="user_profile",
        cascade="all, delete-orphan",  # Delete images if profile is deleted
        lazy="selectin"  # Eagerly load images with profile
    )


class UserProfileImage(Base):
    """Represents an image associated with a user profile."""
    __tablename__ = "user_profile_image"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,  default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profile.user_id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="URL or path to the stored image file"
    )
    # description: Mapped[str | None] = mapped_column(
    #     Text, nullable=True, comment="Optional description or caption for the image"
    # )
    # TODO: Rename this to is_profile_image (and do the same thing for UserProfileImageSchema)
    is_profile_picture: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Is this the main profile picture?"
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user_profile: Mapped["UserProfile"] = relationship(
        back_populates="images"
    )

# This probably should be in dependencies.py


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)
