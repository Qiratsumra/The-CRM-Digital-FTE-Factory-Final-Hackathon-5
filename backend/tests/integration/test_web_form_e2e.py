"""Integration tests for web form submission flow."""
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app
from src.database.connection import get_pool, close_pool
import asyncio


@pytest.fixture
async def db_pool():
    """Create database pool for tests."""
    pool = await get_pool()
    yield pool
    await close_pool()


@pytest.mark.anyio
async def test_full_submission_flow(db_pool):
    """Integration test: Complete web form submission flow."""
    # Submit ticket
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/support/submit",
            json={
                "name": "Integration Test User",
                "email": "integration-test@example.com",
                "subject": "Integration test for web form submission",
                "category": "technical",
                "priority": "medium",
                "message": "This is an integration test to verify the complete web form submission flow works correctly.",
            },
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate ticket created
    assert "ticket_id" in data
    ticket_id = data["ticket_id"]
    
    # Verify ticket exists in database
    async with db_pool.acquire() as conn:
        ticket = await conn.fetchrow(
            "SELECT * FROM tickets WHERE id = $1",
            ticket_id,
        )
        
        assert ticket is not None
        assert ticket["source_channel"] == "web_form"
        assert ticket["status"] == "open"
        
        # Verify customer was created
        customer = await conn.fetchrow(
            "SELECT * FROM customers WHERE id = $1",
            ticket["customer_id"],
        )
        
        assert customer is not None
        assert customer["email"] == "integration-test@example.com"
        
        # Verify conversation was created
        conversation = await conn.fetchrow(
            "SELECT * FROM conversations WHERE id = $1",
            ticket["conversation_id"],
        )
        
        assert conversation is not None
        assert conversation["initial_channel"] == "web_form"
        
        # Verify message was stored
        message = await conn.fetchrow(
            "SELECT * FROM messages WHERE conversation_id = $1",
            ticket["conversation_id"],
        )
        
        assert message is not None
        assert message["direction"] == "incoming"
        assert "Integration test" in message["content"]


@pytest.mark.anyio
async def test_duplicate_customer_by_email(db_pool):
    """Integration test: Same email returns existing customer."""
    email = "duplicate-test@example.com"
    
    # First submission
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response1 = await ac.post(
            "/support/submit",
            json={
                "name": "First Test",
                "email": email,
                "subject": "First test subject",
                "category": "general",
                "priority": "low",
                "message": "This is the first test message.",
            },
        )
    
    assert response1.status_code == 200
    
    # Second submission with same email
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response2 = await ac.post(
            "/support/submit",
            json={
                "name": "Second Test",
                "email": email,
                "subject": "Second test subject",
                "category": "general",
                "priority": "low",
                "message": "This is the second test message.",
            },
        )
    
    assert response2.status_code == 200
    
    # Verify only one customer exists
    async with db_pool.acquire() as conn:
        customers = await conn.fetch(
            "SELECT * FROM customers WHERE email = $1",
            email,
        )
        
        assert len(customers) == 1
        
        # But two tickets exist
        tickets = await conn.fetch(
            "SELECT * FROM tickets WHERE customer_id = $1",
            customers[0]["id"],
        )
        
        assert len(tickets) == 2


@pytest.mark.anyio
async def test_ticket_status_endpoint(db_pool):
    """Integration test: Get ticket status after submission."""
    # Submit ticket
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/support/submit",
            json={
                "name": "Status Test User",
                "email": "status-test@example.com",
                "subject": "Status test subject",
                "category": "billing",
                "priority": "high",
                "message": "This is a test message for status verification.",
            },
        )
    
    assert response.status_code == 200
    ticket_id = response.json()["ticket_id"]
    
    # Get ticket status
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        status_response = await ac.get(f"/support/ticket/{ticket_id}")
    
    assert status_response.status_code == 200
    data = status_response.json()
    
    # Validate status data
    assert data["ticket_id"] == ticket_id
    assert data["channel"] == "web_form"
    assert data["category"] == "billing"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert "created_at" in data


@pytest.mark.anyio
async def test_customer_lookup_by_email(db_pool):
    """Integration test: Lookup customer by email."""
    email = "lookup-test@example.com"
    
    # Create customer via ticket submission
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/support/submit",
            json={
                "name": "Lookup Test User",
                "email": email,
                "subject": "Lookup test subject",
                "category": "general",
                "priority": "low",
                "message": "This is a test message.",
            },
        )
    
    # Lookup customer
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/customers/lookup?email={email}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate customer data
    assert data["email"] == email
    assert data["name"] == "Lookup Test User"
    assert "customer_id" in data
    assert "conversations" in data
    assert len(data["conversations"]) >= 1


@pytest.mark.anyio
async def test_channel_metrics_endpoint(db_pool):
    """Integration test: Get channel metrics."""
    from datetime import datetime, timedelta
    
    # Submit multiple tickets
    test_data = [
        {"category": "technical", "priority": "high"},
        {"category": "billing", "priority": "medium"},
        {"category": "general", "priority": "low"},
    ]
    
    for data in test_data:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            await ac.post(
                "/support/submit",
                json={
                    "name": "Metrics Test User",
                    "email": f"metrics-{data['category']}@example.com",
                    "subject": f"Metrics test {data['category']}",
                    "category": data["category"],
                    "priority": data["priority"],
                    "message": "This is a test message for metrics.",
                },
            )
    
    # Get metrics for today
    today = datetime.utcnow().date().isoformat()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/metrics/channels?date={today}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate metrics structure
    assert "web_form" in data
    assert "total" in data["web_form"]
    assert "avg_sentiment" in data["web_form"]
    assert "escalations" in data["web_form"]
    assert "avg_response_time_sec" in data["web_form"]
    
    # Should have at least 3 tickets from this test
    assert data["web_form"]["total"] >= 3
