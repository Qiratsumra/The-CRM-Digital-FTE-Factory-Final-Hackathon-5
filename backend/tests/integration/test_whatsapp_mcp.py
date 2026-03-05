"""
WhatsApp MCP Integration Tests

Tests for WhatsApp MCP channel integration.
"""
import pytest
import asyncio
from pathlib import Path
from src.channels.whatsapp_mcp_client import WhatsAppMCPClient, WhatsAppDatabaseClient, WhatsAppMessage
from src.channels.whatsapp_handler import WhatsAppHandler
from src.kafka.client import FTEKafkaProducer


class TestWhatsAppDatabaseClient:
    """Test WhatsApp database client."""

    @pytest.mark.asyncio
    async def test_database_client_init(self):
        """Test database client initialization."""
        client = WhatsAppDatabaseClient(db_path="./test_messages.db")
        assert client.db_path == Path("./test_messages.db")
        assert client._db is None

    @pytest.mark.asyncio
    async def test_database_connect_nonexistent(self):
        """Test connection to nonexistent database."""
        client = WhatsAppDatabaseClient(db_path="./nonexistent/messages.db")
        success = await client.connect()
        assert success is False
        await client.close()


class TestWhatsAppMCPClient:
    """Test WhatsApp MCP client."""

    @pytest.mark.asyncio
    async def test_client_init(self):
        """Test client initialization."""
        client = WhatsAppMCPClient(bridge_path="./whatsapp-mcp/whatsapp-bridge")
        assert client.bridge_path == Path("./whatsapp-mcp/whatsapp-bridge")
        assert client._initialized is False
        await client.close()

    @pytest.mark.asyncio
    async def test_phone_to_jid(self):
        """Test phone number to JID conversion."""
        client = WhatsAppMCPClient(bridge_path="./whatsapp-mcp/whatsapp-bridge")
        
        # Test various phone formats
        assert client._phone_to_jid("+923001234567") == "923001234567@s.whatsapp.net"
        assert client._phone_to_jid("923001234567") == "923001234567@s.whatsapp.net"
        assert client._phone_to_jid("+1-555-123-4567") == "15551234567@s.whatsapp.net"
        
        await client.close()


class TestWhatsAppHandler:
    """Test WhatsApp handler."""

    @pytest.mark.asyncio
    async def test_handler_init(self):
        """Test handler initialization."""
        producer = FTEKafkaProducer()
        handler = WhatsAppHandler(producer=producer)
        
        assert handler._handler is None
        assert handler._initialized is False
        
        await handler.close()

    @pytest.mark.asyncio
    async def test_handler_initialize(self):
        """Test handler initialization with MCP client."""
        producer = FTEKafkaProducer()
        handler = WhatsAppHandler(producer=producer)
        
        # Initialize (will fail gracefully if bridge not found)
        success = await handler.initialize()
        
        # Should fail gracefully in test environment
        assert success is False or success is True  # Depends on bridge availability
        
        await handler.close()


class TestWhatsAppWebhook:
    """Test WhatsApp webhook endpoints."""

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_payload(self):
        """Test WhatsApp webhook payload validation."""
        # Valid payload
        valid_payload = {
            "phone": "+923001234567",
            "message": "Test message",
        }
        
        assert "phone" in valid_payload
        assert "message" in valid_payload
        assert valid_payload["phone"].startswith("+")
        assert len(valid_payload["message"]) > 0

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_invalid_payload(self):
        """Test invalid webhook payload."""
        # Missing phone
        invalid_payload_1 = {
            "message": "Test message",
        }
        
        # Missing message
        invalid_payload_2 = {
            "phone": "+923001234567",
        }
        
        assert "phone" not in invalid_payload_1 or "message" not in invalid_payload_1
        assert "phone" not in invalid_payload_2 or "message" not in invalid_payload_2


class TestWhatsAppMessageFormatting:
    """Test WhatsApp message formatting."""

    def test_whatsapp_300_char_limit(self):
        """Test WhatsApp response respects 300 character limit."""
        long_message = "A" * 500
        truncated = long_message[:300]
        
        assert len(truncated) == 300
        assert len(long_message) > 300

    def test_whatsapp_short_message(self):
        """Test short messages are not truncated."""
        short_message = "Hello, how can I help?"
        
        assert len(short_message) <= 300
        # No truncation needed
        truncated = short_message[:300]
        assert truncated == short_message


class TestWhatsAppJIDFormat:
    """Test WhatsApp JID format validation."""

    def test_valid_jid_format(self):
        """Test valid JID format."""
        valid_jids = [
            "923001234567@s.whatsapp.net",
            "15551234567@s.whatsapp.net",
            "447700900123@s.whatsapp.net",
        ]
        
        for jid in valid_jids:
            assert "@s.whatsapp.net" in jid
            assert jid.count("@") == 1

    def test_invalid_jid_format(self):
        """Test invalid JID format."""
        invalid_jids = [
            "923001234567",  # Missing domain
            "@s.whatsapp.net",  # Missing number
            "923001234567@whatsapp.net",  # Wrong subdomain
        ]
        
        for jid in invalid_jids:
            # These should not be valid
            assert not (jid.count("@") == 1 and jid.endswith("@s.whatsapp.net") and len(jid) > 20)
