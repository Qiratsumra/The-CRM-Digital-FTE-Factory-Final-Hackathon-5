"""Run database migrations."""
import asyncio
import asyncpg
import os
from pathlib import Path

async def run_migration():
    """Run the whatsapp_only migration."""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Load from .env file
        from dotenv import load_dotenv
        load_dotenv()
        database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL not found")
        return
    
    print("Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        print("Running migration: add_whatsapp_only_to_tickets.sql")
        
        migration_sql = Path(__file__).parent / "add_whatsapp_only_to_tickets.sql"
        sql_content = migration_sql.read_text()
        
        # Execute migration
        await conn.execute(sql_content)
        
        print("Migration completed successfully!")
        print("  - Added whatsapp_only column to tickets table")
        print("  - Set whatsapp_only=TRUE for existing WhatsApp tickets")
        print("  - Created index on whatsapp_only")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    asyncio.run(run_migration())
