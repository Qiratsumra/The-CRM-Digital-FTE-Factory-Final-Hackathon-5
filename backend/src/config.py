"""Backend configuration with pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # Neon PostgreSQL
    database_url: str

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"

    # Gmail (SMTP for sending + API)
    gmail_sender_email: str = "sheikhqirat100@gmail.com"
    gmail_sender_password: str = ""  # App password, not regular password
    gmail_credentials_path: str = "credentials.json"
    gmail_pubsub_topic: str = ""
    gmail_api_enabled: bool = True  # Enable Gmail API for receiving/sending
    
    # IMAP Polling (alternative to Gmail API for receiving)
    imap_poll_interval: int = 60  # Seconds between polling

    # WhatsApp MCP
    whatsapp_mcp_bridge_path: str = "./whatsapp-mcp/whatsapp-bridge"
    whatsapp_mcp_enabled: bool = True  # Enable WhatsApp MCP for receiving/sending
    whatsapp_poll_interval: int = 30  # Seconds between message polls

    # Support team
    support_team_email: str = "sheikhqirat100@gmail.com"

    # App
    environment: str = "development"
    api_key: str = "dev-api-key"
    max_email_length_words: int = 500
    max_webform_length_words: int = 300
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_webform_per_minute: int = 10
    
    # Sentry (error monitoring)
    sentry_dsn: str = ""  # Optional: Set to your Sentry DSN for error tracking

    # SendGrid (email sending via API - works on Render)
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "sheikhqirat100@gmail.com"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
