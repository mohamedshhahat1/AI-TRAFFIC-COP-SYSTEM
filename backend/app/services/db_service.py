"""Database Service - handles all DB operations."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("db_service")
except ImportError:
    from loguru import logger

from pathlib import Path

# Use absolute path to avoid issues when server starts from different directories
_project_root = Path(__file__).resolve().parents[3]
_db_path = _project_root / "data" / "traffic_cop.db"

# Ensure data directory exists
_db_path.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{_db_path}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables."""
    try:
        from ..models.violation_model import Base
        from ..models.vehicle_model import VehicleBase
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(VehicleBase.metadata.create_all)
        logger.info("Database initialized successfully")
    except ImportError as e:
        logger.warning(f"Could not initialize DB models: {e}")
    except Exception as e:
        logger.error(f"Database init failed: {e}")


async def get_session():
    """Get async database session (FastAPI dependency)."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
