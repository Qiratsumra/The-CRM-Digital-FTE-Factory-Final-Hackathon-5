"""Contract tests for web form endpoint."""
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app


@pytest.mark.anyio
async def test_submit_returns_ticket_id():
    """Contract test: POST /support/submit returns valid ticket ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/support/submit",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Test support request",
                "category": "technical",
                "priority": "medium",
                "message": "I need help with testing the support form.",
            },
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "ticket_id" in data
    assert "message" in data
    assert "estimated_response_time" in data
    
    # Validate ticket_id format (UUID)
    import uuid
    try:
        uuid.UUID(data["ticket_id"])
    except ValueError:
        pytest.fail(f"ticket_id is not a valid UUID: {data['ticket_id']}")
    
    # Validate message content
    assert data["message"] == "Ticket created successfully"
    
    # Validate estimated response time
    assert "seconds" in data["estimated_response_time"].lower() or "minute" in data["estimated_response_time"].lower()


@pytest.mark.anyio
async def test_submit_validates_required_fields():
    """Contract test: POST /support/submit validates required fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/support/submit",
            json={
                "name": "T",  # Too short
                "email": "invalid-email",
                "subject": "Hi",  # Too short
                "message": "Short",  # Too short
            },
        )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_submit_validates_email_format():
    """Contract test: POST /support/submit validates email format."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/support/submit",
            json={
                "name": "Test User",
                "email": "not-an-email",
                "subject": "Test support request",
                "category": "general",
                "priority": "medium",
                "message": "This is a test message with valid length.",
            },
        )
    
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_ticket_status_returns_correct_structure():
    """Contract test: GET /support/ticket/{id} returns correct structure."""
    # First create a ticket
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_response = await ac.post(
            "/support/submit",
            json={
                "name": "Test User",
                "email": "teststatus@example.com",
                "subject": "Test support request",
                "category": "general",
                "priority": "low",
                "message": "This is a test message to verify ticket status endpoint.",
            },
        )
    
    assert create_response.status_code == 200
    ticket_id = create_response.json()["ticket_id"]
    
    # Get ticket status
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/support/ticket/{ticket_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "ticket_id" in data
    assert "status" in data
    assert "channel" in data
    assert "created_at" in data
    assert "last_updated" in data
    
    # Validate values
    assert data["ticket_id"] == ticket_id
    assert data["channel"] == "web_form"
    assert data["status"] in ["open", "pending", "resolved", "escalated"]


@pytest.mark.anyio
async def test_get_ticket_not_found():
    """Contract test: GET /support/ticket/{id} returns 404 for non-existent ticket."""
    import uuid
    fake_id = str(uuid.uuid4())
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/support/ticket/{fake_id}")
    
    assert response.status_code == 404
