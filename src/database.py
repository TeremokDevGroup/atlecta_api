from typing import AsyncGenerator

import src.config as config

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base


SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{config.DB_USER}:{
    config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}"

Base = declarative_base()
metadata = Base.metadata

# engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, future=True,
                             pool_size=90,  # Maximum number of persistent connections
                             max_overflow=5,  # Maximum number of connections to create beyond pool_size
                             pool_recycle=3600,  # Recycle connections after this many seconds
                             pool_timeout=30,  # Seconds to wait for a connection before timing out
                             # pool_pre_ping=True,  # Test connection before using it
                             )


async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
