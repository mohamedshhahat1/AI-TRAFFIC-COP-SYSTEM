"""Database Service - handles all DB operations."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from loguru import logger

from pathlib import Path

# Use absolute path to avoid issues when server starts from different directories
_project_root = Path(__file__).resolve().parents[3]
DATABASE_URL = f"sqlite+aiosqlite:///{_project_root}/data/traffic_cop.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables."""
    try:
        from ..models.violation_model import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")
    except ImportError as e:
        logger.warning(f"Could not initialize DB models: {e}")
    except Exception as e:
        logger.error(f"Database init failed: {e}")


async def get_session():
    """Get async database session."""
    async with async_session() as session:
        yield session
