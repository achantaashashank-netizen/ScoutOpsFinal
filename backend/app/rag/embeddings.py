from sentence_transformers import SentenceTransformer
from typing import List
from functools import lru_cache
from sqlalchemy.orm import Session
from app import models
from app.rag.vector_store import upsert_note_embedding


# Global model cache
_embedding_model: SentenceTransformer = None


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load and cache the sentence-transformers embedding model.
    Uses all-MiniLM-L6-v2: lightweight (80MB), fast (~50ms), 384-dim vectors.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def generate_embedding(text: str) -> List[float]:
    """
    Generate a 384-dimensional embedding vector for the given text.

    Args:
        text: Input text to embed

    Returns:
        List of 384 float values representing the embedding
    """
    if not text or text.strip() == "":
        # Return zero vector for empty text
        return [0.0] * 384

    model = get_embedding_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()


def store_note_embedding(note: models.Note, db: Session) -> bool:
    """
    Generate and store a note's embedding in Qdrant vector database.

    Args:
        note: Note object to process
        db: Database session (to access player relationship)

    Returns:
        bool: True if successful
    """
    # Generate embedding from title + content
    combined_text = f"{note.title} {note.content}"
    embedding = generate_embedding(combined_text)

    # Get player info (refresh if needed)
    if not note.player:
        db.refresh(note)

    # Store in Qdrant
    return upsert_note_embedding(
        note_id=note.id,
        embedding=embedding,
        player_id=note.player_id,
        player_name=note.player.name,
        team=note.player.team or "",
        title=note.title,
        content=note.content,
        tags=note.tags,
        game_date=note.game_date
    )


def generate_text_searchable(title: str, content: str, tags: str = "") -> str:
    """
    Generate a combined text string for PostgreSQL full-text search (tsvector).

    Args:
        title: Note title
        content: Note content
        tags: Optional comma-separated tags

    Returns:
        Combined text string with weighted components
    """
    # Weight title more heavily (appear multiple times)
    # This makes title matches rank higher in keyword search
    components = []

    if title:
        # Title appears 3 times for higher weight
        components.extend([title] * 3)

    if content:
        components.append(content)

    if tags:
        # Tags appear 2 times for medium weight
        components.extend([tags] * 2)

    return " ".join(components)
