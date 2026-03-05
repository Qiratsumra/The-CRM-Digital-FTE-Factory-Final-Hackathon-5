"""Database connection pool management with asyncpg."""
import asyncpg
from asyncpg import Pool
from src.config import get_settings
import logging

logger = logging.getLogger(__name__)
_pool: Pool | None = None


async def get_pool() -> Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        logger.info("Database pool initialized")
    return _pool


async def close_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
