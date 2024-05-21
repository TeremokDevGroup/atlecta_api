from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession
from src.repository import ModelType, SQLAlchemyRepository
from src.sports.models import Sport


class SportRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = Sport) -> None:
        super().__init__(model, db_session)
