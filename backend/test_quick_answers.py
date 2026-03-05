"""
Test Quick Answers for WhatsApp

Tests the quick answer matching system to ensure fast, accurate responses.
"""
import asyncio
import logging
from src.skills.quick_answer import get_quick_answer, classify_intent, handle_greeting, handle_thanks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test cases: (input_message, expected_intent)
TEST_CASES = [
    # Greetings
    ("hi", "greeting"),
    ("hello", "greeting"),
    ("hey", "greeting"),
    ("good morning", "greeting"),
    
    # Thanks
    ("thanks", "thanks"),
    ("thank you", "thanks"),
    ("thx", "thanks"),
    
    # Password reset
    ("I forgot my password", "reset_password"),
    ("how do i reset password", "reset_password"),
    ("can't login to my account", "reset_password"),
    ("locked out of my account", "reset_password"),
    
    # Account setup
    ("how do i get started", "account_setup"),
    ("create new account", "account_setup"),
    ("sign up", "account_setup"),
    ("register", "account_setup"),
    
    # Pricing
    ("what are your prices", "pricing"),
    ("how much does it cost", "pricing"),
    ("upgrade plan", "pricing"),
    ("subscription cost", "pricing"),
    
    # Refund
    ("I want a refund", "refund"),
    ("cancel my subscription", "refund"),
    ("money back", "refund"),
    ("unsubscribe", "refund"),
    
    # API
    ("where is my api key", "api_key"),
    ("api token", "api_key"),
    ("api documentation", "api_key"),
    
    # Technical issues
    ("getting errors", "downtime"),
    ("can't access my account", "downtime"),
    ("bug in the system", "downtime"),
    ("service is down", "downtime"),
    
    # Contact support
    ("I want to talk to a human", "contact_support"),
    ("speak to agent", "contact_support"),
    ("real person please", "contact_support"),
    ("customer service", "contact_support"),
    
    # Integrations
    ("slack integration", "integration"),
    ("how to connect zapier", "integration"),
    ("webhook configuration", "integration"),
    
    # Team management
    ("invite team member", "team_invite"),
    ("add user to my account", "team_invite"),
    
    # Security
    ("enable two factor authentication", "two_factor"),
    ("2fa setup", "two_factor"),
    
    # Trial
    ("free trial", "trial"),
    ("can i try before buying", "trial"),
    
    # Data export
    ("export my data", "export_data"),
    ("download csv export", "export_data"),
    
    # Feature requests
    ("can you add this feature", "feature_request"),
    ("I have a suggestion", "feature_request"),
]


async def test_quick_answers():
    """Test all quick answer intents."""
    print("=" * 70)
    print("WhatsApp Quick Answers Test")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    
    for message, expected_intent in TEST_CASES:
        intent = await classify_intent(message)
        
        if intent == expected_intent:
            print(f"[PASS] '{message}' -> {intent}")
            passed += 1
        else:
            print(f"[FAIL] '{message}' -> {intent} (expected: {expected_intent})")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(TEST_CASES)} tests")
    print("=" * 70)
    print()
    
    # Test full quick answer retrieval
    print("Testing full quick answer retrieval:")
    print()
    
    test_messages = [
        "I forgot my password",
        "How much does it cost?",
        "I want to talk to a human",
        "How do I enable 2FA?",
    ]
    
    for message in test_messages:
        result = await get_quick_answer(message)
        if result:
            print(f"Message: {message}")
            print(f"Intent: {result['intent']}")
            print(f"Category: {result['category']}")
            print(f"Escalate: {result.get('escalate', False)}")
            response_preview = result['response'].replace('\u2192', '->')[:100]
            print(f"Response preview: {response_preview}...")
            print()
        else:
            print(f"[NO MATCH] {message}")
            print()

    # Test greetings
    print("Testing greetings:")
    for greeting_msg in ["hi", "hello", "hey"]:
        response = await handle_greeting(greeting_msg)  # FIXED: was asyncio.run()
        if response:
            resp_clean = response.replace('\u2192', '->').replace('\U0001f44b', '[wave]')
            print(f"[OK] '{greeting_msg}' -> {resp_clean[:50]}...")

    print()

    # Test thanks
    print("Testing thanks:")
    for thanks_msg in ["thanks", "thank you", "thx"]:
        response = await handle_thanks(thanks_msg)  # FIXED: was asyncio.run()
        if response:
            resp_clean = response.replace('\u2192', '->').replace('\U0001f60a', '[smile]')
            print(f"[OK] '{thanks_msg}' -> {resp_clean[:50]}...")

    print()
    print("=" * 70)
    print("Test Complete!")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    result = asyncio.run(test_quick_answers())
    exit(0 if result else 1)