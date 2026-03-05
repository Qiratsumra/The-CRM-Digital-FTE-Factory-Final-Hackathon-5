"""Test agent runner with Gemini."""
import asyncio
from agents import Agent, Runner, ModelSettings, set_default_openai_key
from src.config import get_settings

settings = get_settings()

# Set the API key for the Agents SDK
set_default_openai_key(settings.gemini_api_key)

agent = Agent(
    name="Test",
    model=settings.gemini_model,
    model_settings=ModelSettings(
        base_url=settings.gemini_base_url,
        api_key=settings.gemini_api_key,
    ),
    instructions="You are a helpful customer support assistant.",
)


async def main():
    """Test agent run."""
    print("Running agent test...")
    result = await Runner.run(agent, "Hello, how do I invite team members?")
    print(f"Result: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
