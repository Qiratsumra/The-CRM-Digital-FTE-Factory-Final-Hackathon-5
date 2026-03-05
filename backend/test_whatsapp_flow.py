"""
Test WhatsApp Message Flow

This script tests the complete WhatsApp message flow:
1. Check if Go bridge is running
2. Check if WhatsApp database exists
3. Send a test message
4. Verify response is sent

Usage:
    python test_whatsapp_flow.py
"""
import asyncio
import logging
from pathlib import Path

from src.config import get_settings
from src.channels.whatsapp_mcp_client import WhatsAppMCPClient
from src.channels.whatsapp_handler import WhatsAppHandler
from src.kafka.client import FTEKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


async def test_whatsapp_flow():
    """Test complete WhatsApp flow."""
    print("=" * 60)
    print("WhatsApp Integration Test")
    print("=" * 60)

    # Step 1: Check configuration
    print("\n1. Checking configuration...")
    print(f"   Bridge Path: {settings.whatsapp_mcp_bridge_path}")
    print(f"   MCP Enabled: {settings.whatsapp_mcp_enabled}")
    print(f"   Poll Interval: {settings.whatsapp_poll_interval}s")

    # Step 2: Check if bridge executable exists
    print("\n2. Checking Go bridge executable...")
    bridge_path = Path(settings.whatsapp_mcp_bridge_path)
    bridge_exe = bridge_path / "whatsapp-bridge.exe"
    if not bridge_exe.exists():
        bridge_exe = bridge_path / "whatsapp-bridge"

    if bridge_exe.exists():
        print(f"   [OK] Bridge executable found: {bridge_exe}")
    else:
        print(f"   [FAIL] Bridge executable NOT found at: {bridge_exe}")
        print(f"   -> Solution: Build the bridge with 'go build -o whatsapp-bridge.exe main.go'")
        return False

    # Step 3: Check if database exists
    print("\n3. Checking WhatsApp database...")
    messages_db = bridge_path / "store" / "messages.db"
    if messages_db.exists():
        print(f"   [OK] Database found: {messages_db}")
    else:
        print(f"   [FAIL] Database NOT found at: {messages_db}")
        print(f"   -> Solution: Run 'go run main.go' and scan QR code to authenticate")
        return False

    # Step 4: Initialize MCP client
    print("\n4. Initializing WhatsApp MCP client...")
    client = WhatsAppMCPClient(bridge_path=settings.whatsapp_mcp_bridge_path)
    initialized = await client.initialize()

    if initialized:
        print(f"   [OK] MCP client initialized successfully")
    else:
        print(f"   [FAIL] MCP client initialization failed")
        await client.close()
        return False

    # Step 5: Check Go bridge status
    print("\n5. Checking Go bridge status...")
    bridge_status = await client.check_go_bridge_status()
    if bridge_status:
        print(f"   [OK] Go bridge appears to be available")
    else:
        print(f"   [WARN] Go bridge may not be running")
        print(f"   -> Start it with: cd {bridge_path} && go run main.go")

    # Step 6: Test sending a message
    print("\n6. Testing message sending...")
    test_phone = "+923082931005"  # Replace with your test number
    test_message = "[TEST] WhatsApp Integration Test - Please ignore"

    print(f"   Sending to: {test_phone}")
    print(f"   Message: {test_message}")

    success = await client.send_message(test_phone, test_message)

    if success:
        print(f"   [OK] Message sent successfully!")
    else:
        print(f"   [FAIL] Message sending failed")
        print(f"   -> Make sure Go bridge is running and authenticated")

    # Step 7: Test handler initialization
    print("\n7. Testing WhatsApp handler...")
    producer = FTEKafkaProducer()
    await producer.start()

    handler = WhatsAppHandler(producer=producer, mcp_client=client)
    handler_initialized = await handler.initialize()

    if handler_initialized:
        print(f"   [OK] WhatsApp handler initialized")
    else:
        print(f"   [WARN] WhatsApp handler initialization failed")

    # Cleanup
    await handler.close()
    await producer.stop()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

    if success:
        print("\n[SUCCESS] WhatsApp integration is WORKING!")
        print("   You should receive a test message on WhatsApp shortly.")
    else:
        print("\n[FAIL] WhatsApp integration has ISSUES")
        print("\nNext Steps:")
        print("1. Make sure Go bridge is running:")
        print(f"   cd {bridge_path}")
        print("   go run main.go")
        print("\n2. Scan QR code with WhatsApp mobile app")
        print("\n3. Run this test again")

    return success


if __name__ == "__main__":
    result = asyncio.run(test_whatsapp_flow())
    exit(0 if result else 1)
