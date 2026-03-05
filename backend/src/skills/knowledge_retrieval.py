"""
Skill: Knowledge Retrieval
When to use: On customer product questions
Purpose: Search knowledge base using vector similarity
"""
from src.database.connection import get_pool
from src.config import get_settings
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)
settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)


async def get_embedding(text: str) -> list[float]:
    """Generate text embedding using Gemini."""
    try:
        result = genai.embed_content(model="models/embedding-001", content=text)
        return result["embedding"]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return []


async def search_knowledge_base(query: str, max_results: int = 5, category: str | None = None) -> str:
    """
    Search knowledge base for relevant information.
    
    Args:
        query: Search query
        max_results: Maximum results to return
        category: Optional category filter
        
    Returns:
        Formatted search results or error message
    """
    try:
        embedding = await get_embedding(query)
        if not embedding:
            return "Embedding generation failed."
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            if category:
                results = await conn.fetch(
                    """
                    SELECT title, content, category,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM knowledge_base
                    WHERE category = $2
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3
                    """,
                    embedding, category, max_results,
                )
            else:
                results = await conn.fetch(
                    """
                    SELECT title, content, category,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM knowledge_base
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                    """,
                    embedding, max_results,
                )
            
            if not results:
                return "No relevant documentation found. Consider escalating to human support."
            
            return "\n\n---\n\n".join(
                f"**{r['title']}** (relevance: {r['similarity']:.2f})\n{r['content'][:500]}"
                for r in results
            )
    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return "Knowledge base temporarily unavailable. Please try again or escalate."
