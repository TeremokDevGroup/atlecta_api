from abc import ABC, abstractmethod

from src.auth.models import UserProfile, UserProfileImage
from src.auth.repository import UserProfileImageRepository, UserProfileRepository
from src.chat.models import Attachment, Chat, ChatMember, Group, Message
from src.chat.repository import (
    AttachmentRepository,
    ChatMemberRepository,
    ChatRepository,
    GroupRepository,
    MessageRepository,
)
from src.database import async_session_factory
from src.sports.models import Inventory, Sport, SportObject, SportObjectImage
from src.sports.repository import (
    InventoryRepository,
    SportObjectImageRepository,
    SportObjectRepository,
    SportRepository,
)


class AbstractUnitOfWork(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

    @abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abstractmethod
    async def rollback(self):
        raise NotImplementedError


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):

    def __init__(self, session_factory=async_session_factory) -> None:
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()

        self.inventory = InventoryRepository(
            db_session=self.session, model=Inventory)
        self.sports = SportRepository(
            db_session=self.session, model=Sport)
        self.sport_objects = SportObjectRepository(
            db_session=self.session, model=SportObject)
        self.sport_object_images = SportObjectImageRepository(
            db_session=self.session, model=SportObjectImage)

        self.user_profiles = UserProfileRepository(
            db_session=self.session, model=UserProfile)
        self.user_profile_images = UserProfileImageRepository(
            db_session=self.session, model=UserProfileImage)

        self.chats = ChatRepository(
            db_session=self.session, model=Chat)
        self.groups = GroupRepository(
            db_session=self.session, model=Group)
        self.chat_members = ChatMemberRepository(
            db_session=self.session, model=ChatMember)
        self.messages = MessageRepository(
            db_session=self.session, model=Message)
        self.attachmets = AttachmentRepository(
            db_session=self.session, model=Attachment)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # TODO: log the exception here
            await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()


def unit_of_work_factory(session_factory=async_session_factory):
    return SQLAlchemyUnitOfWork(session_factory=session_factory)
