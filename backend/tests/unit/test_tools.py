"""Unit tests for agent tools."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import ValidationError


class TestKnowledgeSearchInput:
    """Tests for KnowledgeSearchInput validation."""
    
    def test_valid_input(self):
        """Test valid knowledge search input."""
        from src.agent.tools import KnowledgeSearchInput
        
        input_data = KnowledgeSearchInput(query="How do I reset password?")
        assert input_data.query == "How do I reset password?"
        assert input_data.max_results == 5
        assert input_data.category is None
    
    def test_custom_max_results(self):
        """Test custom max_results value."""
        from src.agent.tools import KnowledgeSearchInput
        
        input_data = KnowledgeSearchInput(query="test", max_results=10)
        assert input_data.max_results == 10
    
    def test_with_category(self):
        """Test with category filter."""
        from src.agent.tools import KnowledgeSearchInput
        
        input_data = KnowledgeSearchInput(query="test", category="api")
        assert input_data.category == "api"


class TestTicketInput:
    """Tests for TicketInput validation."""
    
    def test_valid_input(self):
        """Test valid ticket input."""
        from src.agent.tools import TicketInput, Channel
        
        input_data = TicketInput(
            customer_id="cust-123",
            issue="Cannot login",
            priority="high",
            channel=Channel.EMAIL,
        )
        assert input_data.customer_id == "cust-123"
        assert input_data.issue == "Cannot login"
        assert input_data.priority == "high"
        assert input_data.channel == Channel.EMAIL
    
    def test_default_priority(self):
        """Test default priority value."""
        from src.agent.tools import TicketInput, Channel
        
        input_data = TicketInput(
            customer_id="cust-123",
            issue="Test issue",
            channel=Channel.WEB_FORM,
        )
        assert input_data.priority == "medium"
    
    def test_invalid_channel(self):
        """Test invalid channel raises error."""
        from src.agent.tools import TicketInput
        
        with pytest.raises(ValidationError):
            TicketInput(
                customer_id="cust-123",
                issue="Test",
                channel="invalid_channel",
            )


class TestEscalationInput:
    """Tests for EscalationInput validation."""
    
    def test_valid_input(self):
        """Test valid escalation input."""
        from src.agent.tools import EscalationInput
        
        input_data = EscalationInput(
            ticket_id="ticket-123",
            reason="Customer requested lawyer",
        )
        assert input_data.ticket_id == "ticket-123"
        assert input_data.reason == "Customer requested lawyer"
        assert input_data.urgency == "normal"
    
    def test_custom_urgency(self):
        """Test custom urgency value."""
        from src.agent.tools import EscalationInput
        
        input_data = EscalationInput(
            ticket_id="ticket-123",
            reason="Angry customer",
            urgency="high",
        )
        assert input_data.urgency == "high"


class TestResponseInput:
    """Tests for ResponseInput validation."""
    
    def test_valid_input(self):
        """Test valid response input."""
        from src.agent.tools import ResponseInput, Channel
        
        input_data = ResponseInput(
            ticket_id="ticket-123",
            message="Hello, I can help you with that.",
            channel=Channel.EMAIL,
        )
        assert input_data.ticket_id == "ticket-123"
        assert input_data.message == "Hello, I can help you with that."
        assert input_data.channel == Channel.EMAIL


class TestChannelEnum:
    """Tests for Channel enum."""
    
    def test_channel_values(self):
        """Test channel enum values."""
        from src.agent.tools import Channel
        
        assert Channel.EMAIL.value == "email"
        assert Channel.WHATSAPP.value == "whatsapp"
        assert Channel.WEB_FORM.value == "web_form"
    
    def test_channel_from_string(self):
        """Test creating channel from string."""
        from src.agent.tools import Channel
        
        assert Channel("email") == Channel.EMAIL
        assert Channel("whatsapp") == Channel.WHATSAPP
        assert Channel("web_form") == Channel.WEB_FORM


@pytest.mark.anyio
async def test_search_knowledge_base_success():
    """Test successful knowledge base search."""
    from src.agent.tools import search_knowledge_base, KnowledgeSearchInput
    
    # Mock database connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    # Mock search results
    mock_results = [
        {
            "title": "How to Reset Password",
            "content": "To reset your password, go to settings...",
            "category": "account",
            "similarity": 0.95,
        }
    ]
    mock_conn.fetch.return_value = mock_results
    
    with patch("src.agent.tools.get_pool", return_value=mock_pool):
        with patch("src.agent.tools._get_embedding", return_value=[0.1] * 768):
            input_data = KnowledgeSearchInput(query="reset password")
            result = await search_knowledge_base(input_data)
    
    assert "How to Reset Password" in result
    assert "relevance: 0.95" in result


@pytest.mark.anyio
async def test_search_knowledge_base_no_results():
    """Test knowledge base search with no results."""
    from src.agent.tools import search_knowledge_base, KnowledgeSearchInput
    
    # Mock database connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetch.return_value = []
    
    with patch("src.agent.tools.get_pool", return_value=mock_pool):
        with patch("src.agent.tools._get_embedding", return_value=[0.1] * 768):
            input_data = KnowledgeSearchInput(query="nonexistent topic")
            result = await search_knowledge_base(input_data)
    
    assert "No relevant documentation found" in result


@pytest.mark.anyio
async def test_create_ticket_success():
    """Test successful ticket creation."""
    from src.agent.tools import create_ticket, TicketInput, Channel
    
    # Mock database connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetchval.return_value = "ticket-uuid-123"
    
    with patch("src.agent.tools.get_pool", return_value=mock_pool):
        input_data = TicketInput(
            customer_id="cust-123",
            issue="Test issue",
            channel=Channel.EMAIL,
        )
        result = await create_ticket(input_data)
    
    assert "Ticket created: ticket-uuid-123" == result


@pytest.mark.anyio
async def test_get_customer_history_success():
    """Test getting customer history."""
    from src.agent.tools import get_customer_history
    
    # Mock database connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    mock_results = [
        {
            "initial_channel": "email",
            "content": "Hello, I need help",
            "role": "customer",
            "channel": "email",
            "created_at": "2026-02-18T10:00:00Z",
        }
    ]
    mock_conn.fetch.return_value = mock_results
    
    with patch("src.agent.tools.get_pool", return_value=mock_pool):
        result = await get_customer_history("cust-123")
    
    assert "[EMAIL] customer: Hello, I need help" in result


@pytest.mark.anyio
async def test_get_customer_history_empty():
    """Test getting customer history with no history."""
    from src.agent.tools import get_customer_history
    
    # Mock database connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetch.return_value = []
    
    with patch("src.agent.tools.get_pool", return_value=mock_pool):
        result = await get_customer_history("cust-123")
    
    assert "No previous interactions found" in result


@pytest.mark.anyio
async def test_escalate_to_human_success():
    """Test successful ticket escalation."""
    from src.agent.tools import escalate_to_human, EscalationInput
    
    # Mock database connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.execute.return_value = None
    
    with patch("src.agent.tools.get_pool", return_value=mock_pool):
        input_data = EscalationInput(
            ticket_id="ticket-123",
            reason="Legal inquiry",
            urgency="high",
        )
        result = await escalate_to_human(input_data)
    
    assert "Escalated to human support" in result
    assert "ticket-123" in result
    assert "Legal inquiry" in result


@pytest.mark.anyio
async def test_send_response_success():
    """Test successful response sending."""
    from src.agent.tools import send_response, ResponseInput, Channel
    
    # Mock database connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    mock_conn.fetchrow.return_value = {"conversation_id": "conv-123", "channel_message_id": "msg-123"}
    mock_conn.execute.return_value = None
    
    with patch("src.agent.tools.get_pool", return_value=mock_pool):
        input_data = ResponseInput(
            ticket_id="ticket-123",
            message="Hello, I can help you.",
            channel=Channel.EMAIL,
        )
        result = await send_response(input_data)
    
    assert "Response sent via email" in result
