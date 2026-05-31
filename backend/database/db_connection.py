"""Database connection utilities."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from pathlib import Path
import os

# Use absolute path to avoid CWD issues
_project_root = Path(__file__).resolve().parents[2]
_default_db = f"sqlite+aiosqlite:///{_project_root}/data/traffic_cop.db"

DATABASE_URL = os.getenv("DATABASE_URL", _default_db)

# pool_pre_ping not supported by aiosqlite; conditional on DB type
_pool_args = {"pool_pre_ping": True} if "postgresql" in DATABASE_URL else {}
engine = create_async_engine(DATABASE_URL, echo=False, **_pool_args)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
