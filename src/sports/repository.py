from src.repository import SQLAlchemyRepository
from src.sports.models import Sport


class SportRepository(SQLAlchemyRepository):
    model = Sport
