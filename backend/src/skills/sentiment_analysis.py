"""
Skill: Sentiment Analysis
When to use: On EVERY incoming customer message
Purpose: Score sentiment 0.0 (very negative) to 1.0 (very positive)
Escalation trigger: score < 0.3
"""
import google.generativeai as genai
from src.config import get_settings
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)
settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    score: float        # 0.0 to 1.0
    label: str          # "positive", "neutral", "negative", "hostile"
    confidence: float   # 0.0 to 1.0
    should_escalate: bool


async def analyze_sentiment(message: str) -> SentimentResult:
    """
    Analyze customer message sentiment using Gemini.

    Args:
        message: Customer message text

    Returns:
        SentimentResult with score, label, confidence, and escalation flag
    """
    model = genai.GenerativeModel(settings.gemini_model)
    prompt = f"""
Analyze the sentiment of this customer support message and respond with JSON only:
{{
  "score": <float 0.0-1.0>,
  "label": <"positive"|"neutral"|"negative"|"hostile">,
  "confidence": <float 0.0-1.0>
}}

Message: "{message}"
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().strip("```json").strip("```")
        data = json.loads(text)
        score = float(data["score"])
        return SentimentResult(
            score=score,
            label=data["label"],
            confidence=float(data["confidence"]),
            should_escalate=score < 0.3,
        )
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return SentimentResult(score=0.5, label="neutral", confidence=0.0, should_escalate=False)
