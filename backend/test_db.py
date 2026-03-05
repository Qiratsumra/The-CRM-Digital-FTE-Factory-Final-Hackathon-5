"""Test database connection and queries."""
import asyncio
from src.database.connection import get_pool, close_pool
from src.database import queries


async def test_db():
    """Test database operations."""
    try:
        print("Getting database pool...")
        pool = await get_pool()
        print("Database pool initialized successfully")
        
        # Test creating a customer
        print("\nTesting create_customer...")
        customer_id = await queries.create_customer(
            pool, email="test@example.com", name="Test User"
        )
        print(f"Customer created: {customer_id}")
        
        # Test creating a ticket
        print("\nTesting create_ticket...")
        ticket_id = await queries.create_ticket(
            pool,
            customer_id=customer_id,
            source_channel="web_form",
            subject="Test Ticket",
            category="general",
            priority="normal",
        )
        print(f"Ticket created: {ticket_id}")
        
        # Test getting ticket
        print("\nTesting get_ticket_by_id...")
        ticket_data = await queries.get_ticket_by_id(pool, ticket_id)
        print(f"Ticket data: {ticket_data}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(test_db())
