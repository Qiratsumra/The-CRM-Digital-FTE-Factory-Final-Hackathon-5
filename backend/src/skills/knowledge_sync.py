#!/usr/bin/env python3
"""Knowledge base sync script - loads Markdown files and generates embeddings."""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "models/gemini-embedding-001"
DATABASE_URL = os.getenv("DATABASE_URL")

genai.configure(api_key=GEMINI_API_KEY)


def get_embedding(text: str) -> list[float]:
    """Generate embedding for text using Gemini."""
    try:
        result = genai.embed_content(model=GEMINI_MODEL, content=text)
        return result.get("embedding", [])
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return []


def load_markdown_file(filepath: Path) -> dict | None:
    """Load and parse a Markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8")
        
        # Extract title from first heading
        lines = content.split("\n")
        title = "Unknown"
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break
        
        # Determine category from filename
        category = filepath.stem.replace("-", " ").replace("_", " ")
        
        return {
            "title": title,
            "content": content,
            "category": category,
        }
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        return None


async def sync_knowledge_base(kb_dir: str) -> None:
    """Sync knowledge base from Markdown files to database."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        sys.exit(1)
    
    kb_path = Path(kb_dir)
    if not kb_path.exists():
        logger.error(f"Knowledge base directory not found: {kb_path}")
        sys.exit(1)
    
    # Connect to database
    logger.info(f"Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Clear existing knowledge base
        logger.info("Clearing existing knowledge base...")
        await conn.execute("TRUNCATE TABLE knowledge_base RESTART IDENTITY")
        
        # Find all Markdown files
        md_files = list(kb_path.glob("*.md"))
        if not md_files:
            logger.warning(f"No Markdown files found in {kb_path}")
            return
        
        logger.info(f"Found {len(md_files)} Markdown files to process")
        
        # Process each file
        for filepath in md_files:
            logger.info(f"Processing {filepath.name}...")
            
            data = load_markdown_file(filepath)
            if not data:
                continue
            
            # Generate embedding
            logger.info(f"Generating embedding for {data['title']}...")
            embedding = get_embedding(data["content"])
            
            if not embedding:
                logger.warning(f"Failed to generate embedding for {filepath.name}, skipping")
                continue
            
            # Insert into database
            embedding_json = "[" + ",".join(map(str, embedding)) + "]"
            
            await conn.execute(
                """
                INSERT INTO knowledge_base (title, content, category, embedding)
                VALUES ($1, $2, $3, $4::vector)
                """,
                data["title"],
                data["content"],
                data["category"],
                embedding_json,
            )
            
            logger.info(f"Inserted {data['title']} into knowledge base")
        
        logger.info("Knowledge base sync completed successfully!")
        
    finally:
        await conn.close()


def main():
    """Main entry point."""
    # Default to knowledge-base directory in project root
    kb_dir = os.getenv("KB_DIR", "knowledge-base")
    
    if len(sys.argv) > 1:
        kb_dir = sys.argv[1]
    
    logger.info(f"Syncing knowledge base from: {kb_dir}")
    
    asyncio.run(sync_knowledge_base(kb_dir))


if __name__ == "__main__":
    main()
