"""Test agent runner with real ticket."""
import asyncio
from src.database.connection import get_pool
from src.agent.runner import AgentRunner


async def main():
    """Test agent runner with real data."""
    pool = await get_pool()
    
    # Get a real ticket and customer from DB
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT t.id as ticket_id, t.customer_id, m.content as message, t.source_channel as channel
            FROM tickets t
            JOIN conversations c ON c.id = t.conversation_id
            JOIN messages m ON m.conversation_id = c.id
            WHERE m.direction = 'incoming'
            ORDER BY t.created_at DESC
            LIMIT 1
        """)
        
        if not row:
            print("No tickets found in database")
            return
        
        ticket_id = str(row["ticket_id"])
        customer_id = str(row["customer_id"])
        message = row["message"]
        channel = row["channel"]
        
        print(f"Testing with ticket: {ticket_id}")
        print(f"Customer: {customer_id}")
        print(f"Message: {message[:100]}...")
        print(f"Channel: {channel}")
        print()
    
    # Run agent
    runner = AgentRunner()
    response = await runner.process_message(
        ticket_id=ticket_id,
        customer_id=customer_id,
        message=message,
        channel=channel,
    )
    print(f"\nAgent Response:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
