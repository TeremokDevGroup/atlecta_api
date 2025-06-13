import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Chat(Base):
    __tablename__ = "chat"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    # For 1:1 chats, members are stored in chat_members


class Group(Base):
    __tablename__ = "group"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    admin_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_account.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ChatMember(Base):
    __tablename__ = "chat_member"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat.id"),
                                               nullable=True)  # Null for group members
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("group.id"),
                                                nullable=True)  # Null for 1:1 chat members
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_account.id"), nullable=False)

    is_moderator: Mapped[bool] = mapped_column(
        default=False)  # For group moderators


class Message(Base):
    __tablename__ = "message"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat.id"),
                                               nullable=True)  # Null for group messages
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("group.id"),
                                                nullable=True)  # Null for 1:1 chat messages
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_account.id"), nullable=False)

    # Nullable for messages with only attachments/sport objects
    content: Mapped[str] = mapped_column(nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    attachment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(
        "attachment.id"), nullable=True)
    # TODO: change this to UUID in the future
    sport_object_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(
        "sport_object.id"), nullable=True)


class Attachment(Base):
    __tablename__ = "attachment"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    file_url: Mapped[str] = mapped_column(
        nullable=False)
    file_type: Mapped[str] = mapped_column(
        default="image")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
