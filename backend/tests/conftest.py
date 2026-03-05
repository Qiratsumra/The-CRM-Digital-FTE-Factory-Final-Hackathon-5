"""Pytest configuration and fixtures."""
import pytest
import asyncio
import os
from pathlib import Path


# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://test:test@localhost:5432/test_db"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "api_key": "test-api-key",
        "gemini_api_key": "test-gemini-key",
        "database_url": os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/test_db"),
    }
