"""Test agent runner with Gemini SDK."""
import asyncio
from src.agent.runner import AgentRunner


async def main():
    """Test agent runner."""
    runner = AgentRunner()
    
    # Test with a sample message
    print("Testing agent runner...")
    response = await runner.process_message(
        ticket_id="test-123",
        customer_id="test-customer",
        message="How do I invite team members to my workspace?",
        channel="web_form",
    )
    print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
