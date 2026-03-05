"""Customer Success FTE Agent definition."""
import os
from agents import Agent, ModelSettings, set_default_openai_key
from src.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from src.agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
)
from src.config import get_settings
from dotenv import load_dotenv
load_dotenv()
settings = get_settings()

# Configure the Agents SDK to use Gemini API key
# The SDK will use this key when calling the Gemini OpenAI-compatible endpoint
set_default_openai_key(settings.gemini_api_key)

customer_success_agent = Agent(
    name="Customer Success FTE",
    model=settings.gemini_model,
    model_settings=ModelSettings(
        base_url=settings.gemini_base_url,
        api_key=settings.gemini_api_key,
    ),
    instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
    tools=[
        search_knowledge_base,
        create_ticket,
        get_customer_history,
        escalate_to_human,
        send_response,
    ],
)
