from typing import Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from uuid import uuid4, UUID
from src.chat.schemas import ChatSchema, GroupBaseSchema, GroupCreateSchema
from src.repository import SQLAlchemyRepository, ModelType
from src.utils import parse_pydantic_schema
from .models import Chat, Group, ChatMember, Message, Attachment


class ChatRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = Chat):
        super().__init__(model, db_session)

    async def create(self, data: ChatSchema) -> Chat:
        async with self.db_session as session:
            chat = Chat(**data.model_dump())
            session.add(chat)
            try:
                await session.commit()
                await session.refresh(chat)
                return chat
            except IntegrityError:
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail="Chat creation failed")


class GroupRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = Group):
        super().__init__(model, db_session)

    async def create(self, data: GroupCreateSchema) -> Group:
        async with self.db_session as session:
            group = Group(**data)
            session.add(group)
            try:
                await session.commit()
                await session.refresh(group)
                return group
            except IntegrityError:
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail="Group creation failed")

    async def get_single(self, id: UUID) -> Group | None:
        async with self.db_session as session:
            result = await session.execute(select(self.model).filter_by(id=id))
            return result.scalar()


class ChatMemberRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = ChatMember):
        super().__init__(model, db_session)

    async def create(self, chat_id: UUID | None, group_id: UUID | None, user_id: UUID, is_moderator: bool = False) -> ChatMember:
        async with self.db_session as session:
            member = ChatMember(id=uuid4(), chat_id=chat_id, group_id=group_id,
                                user_id=user_id, is_moderator=is_moderator)
            session.add(member)
            try:
                await session.commit()
                await session.refresh(member)
                return member
            except IntegrityError:
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail="Chat member creation failed")

    async def get_by_chat_or_group(self, chat_id: UUID | None, group_id: UUID | None, user_id: UUID) -> ChatMember | None:
        async with self.db_session as session:
            result = await session.execute(
                select(self.model).filter_by(chat_id=chat_id,
                                             group_id=group_id, user_id=user_id)
            )
            return result.scalar()


class MessageRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = Message):
        super().__init__(model, db_session)

    async def create(
        self,
        chat_id: UUID | None,
        group_id: UUID | None,
        user_id: UUID,
        content: str | None,
        attachment_id: UUID | None,
        sport_object_id: UUID | None
    ) -> Message:
        async with self.db_session as session:
            message = Message(
                id=uuid4(),
                chat_id=chat_id,
                group_id=group_id,
                user_id=user_id,
                content=content,
                attachment_id=attachment_id,
                sport_object_id=sport_object_id
            )
            session.add(message)
            try:
                await session.commit()
                await session.refresh(message)
                result = await session.execute(
                    select(self.model)
                    .filter_by(id=message.id)
                    .options(selectinload(self.model.user), selectinload(self.model.attachment))
                )
                return result.scalar()
            except IntegrityError:
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail="Message creation failed")

    async def get_multi_by_group(self, group_id: UUID, limit: int = 50) -> list[Message]:
        async with self.db_session as session:
            result = await session.execute(
                select(self.model)
                .filter_by(group_id=group_id)
                .options(selectinload(self.model.user), selectinload(self.model.attachment))
                .order_by(self.model.timestamp.desc())
                .limit(limit)
            )
            return result.scalars().all()


class AttachmentRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = Attachment):
        super().__init__(model, db_session)

    async def create(self, file_url: str, file_type: str) -> Attachment:
        async with self.db_session as session:
            attachment = Attachment(
                id=uuid4(), file_url=file_url, file_type=file_type)
            session.add(attachment)
            try:
                await session.commit()
                await session.refresh(attachment)
                return attachment
            except IntegrityError:
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail="Attachment creation failed")
