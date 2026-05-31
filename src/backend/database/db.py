"""
Database Module
SQLAlchemy async database connection and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger
import os

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite+aiosqlite:///./data/traffic_cop.db"
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Session factory
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_database():
    """Initialize database tables."""
    from .models import Base as ModelBase
    
    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)
    
    logger.info(f"Database initialized: {DATABASE_URL}")


async def get_db():
    """Get database session dependency."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
