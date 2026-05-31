"""Database connection utilities."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from pathlib import Path
import os

# Use absolute path to avoid CWD issues
_project_root = Path(__file__).resolve().parents[2]
_default_db = f"sqlite+aiosqlite:///{_project_root}/data/traffic_cop.db"

DATABASE_URL = os.getenv("DATABASE_URL", _default_db)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
