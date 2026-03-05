import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    try:
        print("Testing Neon database connection...")
        database_url = os.getenv("DATABASE_URL")
        print(f"Connecting to: {database_url[:50]}...")
        
        conn = await asyncpg.connect(database_url)
        print("Connected to Neon database!")
        
        # Test query
        result = await conn.fetchval("SELECT 1")
        print(f"Test query result: {result}")
        
        await conn.close()
        print("Connection closed")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test())
