from fastapi import HTTPException
from uuid import UUID, uuid4
from typing import Callable, Set, Dict
import json

from src.unitofwork import SQLAlchemyUnitOfWork
from .repository import ChatRepository
from .schemas import ChatSchema, ChatMemberResponseSchema, MessageResponseSchema, AttachmentSchema, GroupResponseSchema

chat_connections: Dict[UUID, Set] = {}
group_connections: Dict[UUID, Set] = {}


class ChatService:
    def __init__(self, uow_factory: Callable[[], SQLAlchemyUnitOfWork] = SQLAlchemyUnitOfWork) -> None:
        self._uow_factory = uow_factory

    async def create_chat(self, user_ids: list[UUID], current_user_id: UUID) -> ChatSchema:
        async with self._uow_factory() as uow:
            chat = await uow.chats.create(ChatSchema(id=uuid4()))
            for user_id in set(user_ids + [current_user_id]):
                await uow.chat_members.create(chat_id=chat.id, group_id=None, user_id=user_id)
            return ChatSchema.model_validate(chat)

    async def create_group(self, name: str, current_user_id: UUID) -> GroupResponseSchema:
        group = await self.repo.create_group(name, current_user_id)
        await self.repo.create_chat_member(chat_id=None, group_id=group.id, user_id=current_user_id, is_moderator=True)
        return GroupResponseSchema.from_orm(group)

    async def join_group(self, group_id: UUID, user_id: UUID) -> ChatMemberResponseSchema:
        if not await self.repo.get_group(group_id):
            raise HTTPException(status_code=404, detail="Group not found")
        if await self.repo.get_chat_member(chat_id=None, group_id=group_id, user_id=user_id):
            raise HTTPException(
                status_code=400, detail="User already in group")
        member = await self.repo.create_chat_member(chat_id=None, group_id=group_id, user_id=user_id)
        return ChatMemberResponseSchema.from_orm(member)

    async def create_attachment(self, file: bytes, file_type: str) -> AttachmentSchema:
        import os
        file_name = f"uploads/{UUID().hex}.jpg"
        os.makedirs("uploads", exist_ok=True)
        with open(file_name, "wb") as f:
            f.write(file)
        return await self.repo.create_attachment(file_url=file_name, file_type=file_type)

    async def send_message(
        self,
        chat_id: UUID | None,
        group_id: UUID | None,
        user_id: UUID,
        username: str,
        content: str | None,
        attachment_id: UUID | None,
        sport_object_id: UUID | None
    ) -> MessageResponseSchema:
        if chat_id is None and group_id is None:
            raise HTTPException(
                status_code=422, detail="At least one of chat_id or group_id must be provided")
        if chat_id is not None and group_id is not None:
            raise HTTPException(
                status_code=422, detail="Only one of chat_id or group_id can be provided")

        # Verify user membership
        if not await self.repo.get_chat_member(chat_id=chat_id, group_id=group_id, user_id=user_id):
            raise HTTPException(
                status_code=403, detail="User not in chat or group")

        message = await self.repo.create_message(
            chat_id=chat_id,
            group_id=group_id,
            user_id=user_id,
            content=content,
            attachment_id=attachment_id,
            sport_object_id=sport_object_id
        )
        message_data = {
            "id": str(message.id),
            "content": message.content,
            "username": username,
            "timestamp": message.timestamp.isoformat(),
            "attachment_id": str(message.attachment_id) if message.attachment_id else None,
            "sport_object_id": str(message.sport_object_id) if message.sport_object_id else None,
            "attachment": AttachmentSchema.from_orm(message.attachment).__dict__ if message.attachment else None
        }
        # Broadcast to WebSocket connections
        connections = chat_connections.get(
            chat_id, set()) if chat_id else group_connections.get(group_id, set())
        for ws in connections:
            await ws.send_json(message_data)
        return MessageResponseSchema.from_orm(message)

    async def get_group_messages(self, group_id: UUID, user_id: UUID) -> list[MessageResponseSchema]:
        if not await self.repo.get_chat_member(chat_id=None, group_id=group_id, user_id=user_id):
            raise HTTPException(status_code=403, detail="User not in group")
        messages = await self.repo.get_group_messages(group_id)
        return [MessageResponseSchema.from_orm(m) for m in messages]


class GroupService:
    pass


class MessageService:
    pass


class AttachmentService:
    pass
