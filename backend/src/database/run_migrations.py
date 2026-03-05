"""Database migration runner."""
import asyncpg
import asyncio
from pathlib import Path
from src.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration(migration_file: str) -> None:
    """Run a single migration file."""
    settings = get_settings()
    
    logger.info(f"Connecting to database...")
    conn = await asyncpg.connect(settings.database_url)
    
    try:
        migration_path = Path(__file__).parent / "migrations" / migration_file
        sql = migration_path.read_text()
        
        logger.info(f"Running migration: {migration_file}")
        await conn.execute(sql)
        logger.info(f"Migration {migration_file} completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()


async def main():
    """Run all pending migrations."""
    migrations = ["001_initial.sql", "002_add_verification_token.sql"]

    for migration in migrations:
        await run_migration(migration)

    logger.info("All migrations completed")


if __name__ == "__main__":
    asyncio.run(main())
