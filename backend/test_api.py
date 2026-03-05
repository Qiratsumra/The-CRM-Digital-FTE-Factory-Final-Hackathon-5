"""
API Testing Script for Customer Success FTE

Run this script to test all API endpoints.

Usage:
    python test_api.py

Make sure the API server is running:
    uvicorn src.api.main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("\n=== Testing GET /health ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")


def test_submit_ticket():
    """Test web form submission."""
    print("\n=== Testing POST /support/submit ===")
    
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Support Ticket",
        "category": "technical",
        "priority": "normal",
        "message": "This is a test message to verify the API works correctly."
    }
    
    response = requests.post(
        f"{BASE_URL}/support/submit",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Ticket created: {data['ticket_id']}")
        return data['ticket_id']
    else:
        print(f"❌ Failed: {response.text}")
        return None


def test_get_ticket(ticket_id):
    """Test get ticket status."""
    print(f"\n=== Testing GET /support/ticket/{ticket_id} ===")
    
    response = requests.get(f"{BASE_URL}/support/ticket/{ticket_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print("ℹ️  Ticket not found (expected - not implemented yet)")
    elif response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Ticket status retrieved")


def test_customer_lookup():
    """Test customer lookup."""
    print("\n=== Testing GET /customers/lookup ===")
    
    # Test with email
    response = requests.get(
        f"{BASE_URL}/customers/lookup",
        params={"email": "test@example.com"}
    )
    print(f"Lookup by email - Status: {response.status_code}")
    
    # Test with phone
    response = requests.get(
        f"{BASE_URL}/customers/lookup",
        params={"phone": "+14155551234"}
    )
    print(f"Lookup by phone - Status: {response.status_code}")
    
    # Test without parameters (should fail)
    response = requests.get(f"{BASE_URL}/customers/lookup")
    print(f"No params - Status: {response.status_code} (expected 400)")


def test_metrics():
    """Test channel metrics."""
    print("\n=== Testing GET /metrics/channels ===")
    
    response = requests.get(f"{BASE_URL}/metrics/channels")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Metrics retrieved")


def test_webhooks():
    """Test webhook endpoints."""
    print("\n=== Testing Webhooks ===")
    
    # Gmail webhook
    print("\nPOST /webhooks/gmail")
    response = requests.post(
        f"{BASE_URL}/webhooks/gmail",
        headers={"X-Goog-Signature": "test-signature"}
    )
    print(f"Gmail - Status: {response.status_code}")
    
    # WhatsApp webhook
    print("\nPOST /webhooks/whatsapp")
    response = requests.post(
        f"{BASE_URL}/webhooks/whatsapp",
        data={
            "From": "+14155551234",
            "Body": "Test message",
            "MessageSid": "SM123"
        }
    )
    print(f"WhatsApp - Status: {response.status_code}")
    
    # WhatsApp status webhook
    print("\nPOST /webhooks/whatsapp/status")
    response = requests.post(
        f"{BASE_URL}/webhooks/whatsapp/status",
        data={
            "MessageSid": "SM123",
            "MessageStatus": "delivered"
        }
    )
    print(f"WhatsApp Status - Status: {response.status_code}")


def main():
    """Run all API tests."""
    print("=" * 60)
    print("Customer Success FTE API Tests")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    
    try:
        # Test health
        test_health()
        
        # Test ticket submission
        ticket_id = test_submit_ticket()
        
        # Test ticket status (if ticket was created)
        if ticket_id:
            test_get_ticket(ticket_id)
        
        # Test customer lookup
        test_customer_lookup()
        
        # Test metrics
        test_metrics()
        
        # Test webhooks
        test_webhooks()
        
        print("\n" + "=" * 60)
        print("✅ All API tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Make sure the server is running:")
        print("  uvicorn src.api.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
