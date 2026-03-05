"""
Skill: Quick Answer for WhatsApp

Optimized for fast, accurate responses to common WhatsApp queries.
Uses caching, intent classification, and pre-approved response templates.
"""
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)


# Common intents with keywords and pre-approved responses
QUICK_ANSWERS = {
    "reset_password": {
        "keywords": ["reset password", "forgot password", "can't login", "cannot login", "locked out", "password reset", "forgot my password", "forget password"],
        "response": """Hi! To reset your password:

1. Go to the login page
2. Click "Forgot Password"
3. Enter your email
4. Check your inbox for reset link
5. Click the link and create a new password

The reset link expires in 24 hours. Need more help?""",
        "category": "account",
    },
    "account_setup": {
        "keywords": ["get started", "setup account", "create account", "new user", "how to start", "sign up", "register", "new account"],
        "response": """Welcome! Here's how to get started:

1. Visit our signup page
2. Create account with work email
3. Set up your workspace
4. Invite team members
5. Create your first project

Need a walkthrough of features?""",
        "category": "onboarding",
    },
    "pricing": {
        "keywords": ["price", "cost", "pricing", "how much", "upgrade", "plan", "subscription", "billing", "prices", "costs", "pricing plan"],
        "response": """We offer 3 plans:

- Free: Up to 5 team members
- Pro: Up to 50 members, advanced features
- Enterprise: Unlimited members, priority support

14-day free trial. No credit card needed.

Want me to connect you with sales for custom pricing?""",
        "category": "sales",
        "escalate": True,
    },
    "refund": {
        "keywords": ["refund", "money back", "cancel subscription", "billing issue", "chargeback", "unsubscrib", "cancel", "subscription cancel", "unsubscribe", "cancel my subscription"],
        "response": """I understand you have a billing concern.

Let me connect you with our billing specialist who can review your account and assist with refunds.

A billing agent will contact you within 2 hours. Is there a specific issue I should note?""",
        "category": "billing",
        "escalate": True,
    },
    "api_key": {
        "keywords": ["api key", "api token", "api access", "integration", "webhook", "api docs", "rest api", "api documentation", "developer api"],
        "response": """To find your API key:

1. Log in to dashboard
2. Go to Settings → API
3. Click "Generate New Key"
4. Store it securely (can't view again!)

API docs available at our developer portal.

Need help with specific integration?""",
        "category": "technical",
    },
    "downtime": {
        "keywords": ["down", "not working", "error", "server down", "can't access", "outage", "broken", "bug", "service down", "service is down", "errors", "getting errors", "bug in"],
        "response": """Sorry you're experiencing issues!

Current system status: All systems operational

Try these:
1. Clear browser cache
2. Try incognito mode
3. Check internet connection
4. Try different browser

Still not working? I'll escalate to tech support.""",
        "category": "technical",
    },
    "feature_request": {
        "keywords": ["feature", "suggestion", "would be nice", "can you add", "request", "idea", "improve"],
        "response": """Great idea! I'd love to pass this to our product team.

Can you share:
- What problem this solves?
- How you'd use it?
- Any examples?

Your feedback helps us improve!""",
        "category": "feedback",
    },
    "contact_support": {
        "keywords": ["talk to human", "speak to agent", "real person", "customer service", "support team", "help", "human support", "talk to a human", "human agent"],
        "response": """I'll connect you with a human specialist right away.

They'll review your conversation and contact you shortly.

Is there a specific issue I should note for them?""",
        "category": "support",
        "escalate": True,
    },
    "shipping": {
        "keywords": ["shipping", "delivery", "when will", "track order", "shipment", "where is my order"],
        "response": """To check your order status:

1. Log in to your account
2. Go to Orders
3. Click on order number
4. View tracking info

Standard: 3-5 business days
Express: 1-2 business days

Need help tracking?""",
        "category": "orders",
    },
    "integration": {
        "keywords": ["integrate", "integration", "connect", "slack", "zapier", "webhook", "teams", "github", "webhook configuration", "slack integration"],
        "response": """We support these integrations:

- Slack/Teams: Notifications
- Zapier: 1000+ apps
- GitHub/GitLab: Dev workflows
- API: Custom integrations

Which integration? I can guide you.""",
        "category": "technical",
    },
    "export_data": {
        "keywords": ["export", "download data", "backup", "csv", "json", "data export", "download csv", "csv export"],
        "response": """To export your data:

1. Go to Settings
2. Click "Data & Privacy"
3. Select "Export Data"
4. Choose format (CSV/JSON)
5. Download will start

Large exports may take a few minutes.

Need help with specific data?""",
        "category": "account",
    },
    "team_invite": {
        "keywords": ["invite", "add member", "add user", "team member", "collaborator", "invite team"],
        "response": """To invite team members:

1. Go to Settings → Team
2. Click "Invite Members"
3. Enter email addresses
4. Assign roles (Admin/Member/Viewer)
5. Send invitations

They'll receive an email with signup link.

Need help with permissions?""",
        "category": "account",
    },
    "two_factor": {
        "keywords": ["2fa", "two factor", "authentication", "security", "enable 2fa"],
        "response": """To enable 2FA:

1. Go to Settings → Security
2. Click "Enable Two-Factor Auth"
3. Scan QR code with authenticator app
4. Enter the 6-digit code
5. Save backup codes

Supported apps: Google Authenticator, Authy, Microsoft Authenticator.

Need help setting up?""",
        "category": "security",
    },
    "trial": {
        "keywords": ["trial", "free trial", "trial period", "test", "try before"],
        "response": """We offer a 14-day free trial of our Pro plan:

- No credit card required
- All Pro features included
- Up to 50 team members
- Cancel anytime

Want me to help you start a trial?""",
        "category": "sales",
    },
    "demo": {
        "keywords": ["demo", "demo request", "show me", "walkthrough", "tutorial"],
        "response": """We offer live demos:

- Group onboarding (Pro plans)
- Dedicated training (Enterprise)
- Self-service docs (all plans)

What would you like to see? I can guide you to the right resources.""",
        "category": "sales",
    },
}

# Intent patterns for faster matching (regex)
INTENT_PATTERNS = {
    "greeting": re.compile(r"^(hi|hello|hey|good morning|good afternoon|good evening|yo|sup)", re.IGNORECASE),
    "thanks": re.compile(r"(thank|thanks|thx|appreciate)", re.IGNORECASE),
    "yes": re.compile(r"^(yes|yeah|yep|sure|ok|okay|yup)$", re.IGNORECASE),
    "no": re.compile(r"^(no|nope|nah|don't|doesn't|not)$", re.IGNORECASE),
}


async def classify_intent(message: str) -> Optional[str]:
    """
    Classify user intent using keyword matching.
    
    Fast alternative to LLM-based classification.
    
    Args:
        message: User message text
        
    Returns:
        Intent name or None if not matched
    """
    message_lower = message.lower()
    
    # Check greeting patterns first (very common)
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(message_lower):
            return intent
    
    # Priority order for keyword matching (more specific first)
    # Integration must come before api_key to catch "slack integration" etc.
    priority_order = [
        "reset_password", "account_setup", "refund", "pricing",
        "integration", "api_key",  # integration before api_key
        "downtime", "feature_request", "contact_support", "shipping",
        "export_data", "team_invite", "two_factor", "trial", "demo"
    ]
    
    # Check quick answer keywords in priority order
    for intent_name in priority_order:
        if intent_name not in QUICK_ANSWERS:
            continue
            
        intent_data = QUICK_ANSWERS[intent_name]
        for keyword in intent_data["keywords"]:
            # Use word boundary matching for better accuracy
            keyword_lower = keyword.lower()
            if keyword_lower in message_lower:
                # Skip if keyword is part of a larger word (unless it's a root word)
                if len(keyword) > 3 or keyword in ["down", "csv", "2fa"]:
                    # Check it's not part of another word
                    idx = message_lower.find(keyword_lower)
                    if idx >= 0:
                        before_ok = (idx == 0) or (not message_lower[idx-1].isalnum())
                        after_ok = (idx + len(keyword) >= len(message_lower)) or (not message_lower[idx + len(keyword)].isalnum())
                        if before_ok and after_ok:
                            logger.info(f"Intent matched: {intent_name} (keyword: {keyword})")
                            return intent_name
    
    return None


async def get_quick_answer(message: str) -> Optional[dict]:
    """
    Get instant answer for common questions.
    
    Args:
        message: User message
        
    Returns:
        Dict with response, category, and escalate flag, or None
    """
    intent = await classify_intent(message)
    
    if not intent or intent not in QUICK_ANSWERS:
        return None
    
    intent_data = QUICK_ANSWERS[intent]
    
    # Skip greeting/thanks - not actionable
    if intent in ["greeting", "thanks", "yes", "no"]:
        return None
    
    return {
        "intent": intent,
        "response": intent_data["response"],
        "category": intent_data["category"],
        "escalate": intent_data.get("escalate", False),
        "source": "quick_answer",
    }


async def handle_greeting(message: str) -> Optional[str]:
    """Handle simple greetings."""
    if INTENT_PATTERNS["greeting"].search(message):
        return """Hello! 👋 I'm your AI support assistant.

What can I help you with today?"""
    return None


async def handle_thanks(message: str) -> Optional[str]:
    """Handle thank you messages."""
    if INTENT_PATTERNS["thanks"].search(message):
        return """You're welcome! 😊

Is there anything else I can help you with?"""
    return None
