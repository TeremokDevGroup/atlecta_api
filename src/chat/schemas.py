from pydantic import BaseModel, model_validator
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import ConfigDict

from src.auth.schemas import UserReadSchema


class ChatSchema(BaseModel):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class ChatCreateSchema(BaseModel):
    # For creating a 1:1 chat, typically provide user_ids to add members
    user_ids: list[UUID]


class GroupBaseSchema(BaseModel):
    name: str
    admin_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupCreateSchema(BaseModel):
    name: str


class GroupUpdateSchema(BaseModel):
    name: str


class GroupSchema(GroupBaseSchema):
    id: UUID
    admin: Optional[UserReadSchema] = None  # Include admin details


class GroupResponseSchema(GroupBaseSchema):
    id: UUID
    admin: Optional[UserReadSchema] = None  # Include admin details


class ChatMemberSchema(BaseModel):
    id: UUID
    chat_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    user_id: UUID
    is_moderator: bool

    model_config = ConfigDict(from_attributes=True)


class ChatMemberCreateSchema(BaseModel):
    user_id: UUID
    chat_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    is_moderator: bool = False

    @model_validator(mode='after')
    def check_chat_or_group_id(self):
        if self.chat_id is None and self.group_id is None:
            raise ValueError(
                "At least one of chat_id or group_id must be provided")
        if self.chat_id is not None and self.group_id is not None:
            raise ValueError("Only one of chat_id or group_id can be provided")
        return self


class ChatMemberResponseSchema(ChatMemberSchema):
    user: Optional[UserReadSchema] = None  # Include user details


class AttachmentSchema(BaseModel):
    id: UUID
    file_url: str
    file_type: str

    model_config = ConfigDict(from_attributes=True)


class AttachmentCreateSchema(BaseModel):
    file_url: str
    file_type: str = "image"


class MessageSchema(BaseModel):
    id: UUID
    chat_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    user_id: UUID
    content: Optional[str] = None
    timestamp: datetime
    attachment_id: Optional[UUID] = None
    sport_object_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class MessageCreateSchema(BaseModel):
    content: Optional[str] = None
    chat_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    attachment_id: Optional[UUID] = None
    sport_object_id: Optional[UUID] = None


class MessageResponseSchema(MessageSchema):
    user: Optional[UserReadSchema] = None
    attachment: Optional[AttachmentSchema] = None
