"""Database Service - handles all DB operations."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from loguru import logger

DATABASE_URL = "sqlite+aiosqlite:///./data/traffic_cop.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables."""
    from ..models.violation_model import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def get_session():
    """Get async database session."""
    async with async_session() as session:
        yield session
