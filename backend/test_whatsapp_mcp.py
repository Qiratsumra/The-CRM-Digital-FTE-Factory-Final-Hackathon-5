import asyncio
from src.channels.whatsapp_mcp_client import WhatsAppMCPClient

async def test():
    print("Testing WhatsApp MCP Client...")
    client = WhatsAppMCPClient(bridge_path='./whatsapp-mcp/whatsapp-bridge')
    initialized = await client.initialize()
    print(f"Initialized: {initialized}")
    
    if initialized:
        # Test sending a message
        success = await client.send_message("+923001234567", "Test message from WhatsApp MCP!")
        print(f"Message sent: {success}")
    
    await client.close()
    print("Test complete")

if __name__ == "__main__":
    asyncio.run(test())
