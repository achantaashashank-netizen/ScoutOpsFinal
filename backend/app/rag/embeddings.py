from sentence_transformers import SentenceTransformer
from typing import List
from functools import lru_cache


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
