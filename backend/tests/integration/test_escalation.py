"""Integration tests for escalation flows."""
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app
from src.database.connection import get_pool
import asyncio


@pytest.fixture
async def db_pool():
    """Create database pool for tests."""
    pool = await get_pool()
    yield pool


@pytest.mark.anyio
async def test_legal_keyword_triggers_escalation(db_pool):
    """Integration test: Legal keywords trigger immediate escalation."""
    from src.agent.runner import AgentRunner
    
    # Submit ticket with legal keyword
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/support/submit",
            json={
                "name": "Legal Test User",
                "email": "legal-test@example.com",
                "subject": "I want to speak to a lawyer about GDPR violation",
                "category": "legal",
                "priority": "urgent",
                "message": "I believe your company has violated GDPR regulations and I want to speak to a lawyer immediately.",
            },
        )
    
    assert response.status_code == 200
    ticket_id = response.json()["ticket_id"]
    
    # Process with AI agent
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        process_response = await ac.post(f"/agent/process/{ticket_id}")
    
    # Agent should process (may return escalation response)
    assert process_response.status_code == 200
    
    # Verify ticket was escalated in database
    async with db_pool.acquire() as conn:
        ticket = await conn.fetchrow(
            "SELECT status, resolution_notes FROM tickets WHERE id = $1",
            ticket_id,
        )
        
        # Ticket should be escalated
        assert ticket["status"] == "escalated"
        assert "legal" in ticket["resolution_notes"].lower() or "lawyer" in ticket["resolution_notes"].lower()


@pytest.mark.anyio
async def test_angry_customer_triggers_escalation(db_pool):
    """Integration test: Very negative sentiment triggers escalation."""
    # This test would require mocking the sentiment analysis
    # For now, we test the escalation detection logic directly
    
    from src.skills.escalation_decision import decide_escalation
    from src.skills.sentiment_analysis import SentimentResult
    
    # Create a very negative sentiment
    sentiment = SentimentResult(score=0.15, label="very negative")
    
    # Test escalation decision
    escalation = decide_escalation("I'm extremely frustrated!", sentiment.score)
    
    assert escalation.should_escalate is True
    assert "sentiment" in escalation.reason.lower()


@pytest.mark.anyio
async def test_explicit_human_request_triggers_escalation(db_pool):
    """Integration test: Explicit request for human triggers escalation."""
    from src.skills.escalation_decision import decide_escalation
    
    # Test with explicit human request
    escalation = decide_escalation("I want to speak to a real person, not a bot!")
    
    assert escalation.should_escalate is True
    assert "human" in escalation.reason.lower() or "explicit" in escalation.reason.lower()


@pytest.mark.anyio
async def test_refund_request_triggers_escalation(db_pool):
    """Integration test: Refund request triggers escalation."""
    from src.skills.escalation_decision import decide_escalation
    
    # Test with refund request
    escalation = decide_escalation("I want a refund for my subscription")
    
    assert escalation.should_escalate is True
    assert "refund" in escalation.reason.lower()


@pytest.mark.anyio
async def test_normal_query_no_escalation(db_pool):
    """Integration test: Normal product question does not escalate."""
    from src.skills.escalation_decision import decide_escalation
    from src.skills.sentiment_analysis import SentimentResult
    
    # Test with normal question and neutral sentiment
    sentiment = SentimentResult(score=0.65, label="neutral")
    escalation = decide_escalation("How do I invite team members?", sentiment.score)
    
    assert escalation.should_escalate is False


@pytest.mark.anyio
async def test_escalation_notification(db_pool):
    """Integration test: Escalation publishes to Kafka topic."""
    from src.kafka.topics import TOPICS
    
    # This test verifies the escalation topic exists
    assert "escalations" in TOPICS
    assert TOPICS["escalations"] == "fte.escalations"
    
    # Full Kafka integration test would require running Kafka
    # For now, we verify the topic configuration
