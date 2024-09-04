from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.sports.models import Sport


async def get_or_create_sport(session: AsyncSession, name: str) -> Sport:
    sport = await session.scalar(select(Sport).filter_by(name=name))
    if sport is None:
        sport = Sport(name=name)
        session.add(sport)
    return sport
