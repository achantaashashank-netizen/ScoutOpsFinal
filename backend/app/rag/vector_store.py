from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Optional, Dict, Any
from functools import lru_cache
from app.config import get_settings


# Global Qdrant client cache
_qdrant_client: Optional[QdrantClient] = None


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """
    Get or create a singleton Qdrant client instance.

    Returns:
        QdrantClient: Connected Qdrant client
    """
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = QdrantClient(url=settings.qdrant_url)
    return _qdrant_client


def ensure_collection_exists():
    """
    Ensure the Qdrant collection exists with proper configuration.
    Creates the collection if it doesn't exist.
    """
    settings = get_settings()
    client = get_qdrant_client()

    collections = client.get_collections().collections
    collection_names = [col.name for col in collections]

    if settings.qdrant_collection_name not in collection_names:
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(
                size=settings.qdrant_vector_size,
                distance=Distance.COSINE
            )
        )
        print(f"✓ Created Qdrant collection: {settings.qdrant_collection_name}")
    else:
        print(f"✓ Qdrant collection already exists: {settings.qdrant_collection_name}")


def upsert_note_embedding(
    note_id: int,
    embedding: List[float],
    player_id: int,
    player_name: str,
    team: str,
    title: str,
    content: str,
    tags: Optional[str] = None,
    game_date: Optional[str] = None
) -> bool:
    """
    Insert or update a note's embedding in Qdrant.

    Args:
        note_id: Note ID (used as point ID)
        embedding: 384-dimensional embedding vector
        player_id: Player ID for filtering
        player_name: Player name for metadata
        team: Team name for filtering
        title: Note title
        content: Note content
        tags: Optional comma-separated tags
        game_date: Optional game date

    Returns:
        bool: True if successful
    """
    settings = get_settings()
    client = get_qdrant_client()

    point = PointStruct(
        id=note_id,
        vector=embedding,
        payload={
            "note_id": note_id,
            "player_id": player_id,
            "player_name": player_name,
            "team": team,
            "title": title,
            "content": content,
            "tags": tags or "",
            "game_date": game_date or ""
        }
    )

    client.upsert(
        collection_name=settings.qdrant_collection_name,
        points=[point]
    )

    return True


def delete_note_embedding(note_id: int) -> bool:
    """
    Delete a note's embedding from Qdrant.

    Args:
        note_id: Note ID to delete

    Returns:
        bool: True if successful
    """
    settings = get_settings()
    client = get_qdrant_client()

    client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=[note_id]
    )

    return True


def search_similar_notes(
    query_embedding: List[float],
    player_id: Optional[int] = None,
    team: Optional[str] = None,
    top_k: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for similar notes using vector similarity.

    Args:
        query_embedding: Query embedding vector
        player_id: Optional player filter
        team: Optional team filter
        top_k: Number of results to return

    Returns:
        List of dicts with note metadata and similarity scores
    """
    settings = get_settings()
    client = get_qdrant_client()

    # Build filter conditions
    filter_conditions = []

    if player_id is not None:
        filter_conditions.append(
            FieldCondition(
                key="player_id",
                match=MatchValue(value=player_id)
            )
        )

    if team is not None:
        filter_conditions.append(
            FieldCondition(
                key="team",
                match=MatchValue(value=team)
            )
        )

    # Prepare filter (None if no conditions)
    search_filter = Filter(must=filter_conditions) if filter_conditions else None

    # Perform search
    search_results = client.search(
        collection_name=settings.qdrant_collection_name,
        query_vector=query_embedding,
        query_filter=search_filter,
        limit=top_k
    )

    # Format results
    results = []
    for hit in search_results:
        results.append({
            "note_id": hit.payload["note_id"],
            "player_id": hit.payload["player_id"],
            "player_name": hit.payload["player_name"],
            "team": hit.payload["team"],
            "title": hit.payload["title"],
            "content": hit.payload["content"],
            "tags": hit.payload["tags"],
            "game_date": hit.payload["game_date"],
            "score": hit.score  # Cosine similarity score (0-1)
        })

    return results


def get_collection_info() -> Dict[str, Any]:
    """
    Get information about the Qdrant collection.

    Returns:
        Dict with collection statistics
    """
    settings = get_settings()
    client = get_qdrant_client()

    try:
        collection_info = client.get_collection(settings.qdrant_collection_name)
        return {
            "name": collection_info.config.params.vectors.size,
            "vector_size": collection_info.config.params.vectors.size,
            "points_count": collection_info.points_count,
            "status": collection_info.status
        }
    except Exception as e:
        return {
            "error": str(e),
            "exists": False
        }
