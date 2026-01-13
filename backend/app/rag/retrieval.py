from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from app import models
from app.rag.schemas import NoteSnippet
from app.rag.embeddings import get_embedding_model
from app.rag.vector_store import search_similar_notes


def retrieve_notes(
    query: str,
    db: Session,
    player_id: Optional[int] = None,
    team: Optional[str] = None,
    top_k: int = 5,
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6
) -> List[NoteSnippet]:
    """
    Retrieve relevant notes using hybrid search (keyword + semantic).

    Now uses Qdrant for semantic search instead of PostgreSQL arrays.

    Args:
        query: Search query
        db: Database session
        player_id: Optional player filter
        team: Optional team filter
        top_k: Number of results to return
        keyword_weight: Weight for keyword scoring (0-1)
        semantic_weight: Weight for semantic scoring (0-1)

    Returns:
        List of NoteSnippet objects ranked by relevance
    """
    # Generate query embedding
    model = get_embedding_model()
    query_embedding = model.encode(query, convert_to_tensor=False).tolist()

    # Perform keyword search (PostgreSQL full-text search)
    keyword_results = _keyword_search(query, db, player_id, team)

    # Perform semantic search (Qdrant vector database)
    semantic_results = _semantic_search_qdrant(query_embedding, player_id, team)

    # Combine scores
    combined = _combine_scores(
        keyword_results,
        semantic_results,
        keyword_weight,
        semantic_weight
    )

    # Rank and take top_k
    ranked = sorted(combined, key=lambda x: x['final_score'], reverse=True)[:top_k]

    # Format as NoteSnippet
    snippets = []
    for result in ranked:
        note_data = result['note_data']
        snippets.append(NoteSnippet(
            note_id=note_data['note_id'],
            player_id=note_data['player_id'],
            player_name=note_data['player_name'],
            title=note_data['title'],
            excerpt=_create_excerpt(note_data['content'], query),
            relevance_score=result['final_score'],
            keyword_score=result['keyword_score'],
            semantic_score=result['semantic_score'],
            game_date=note_data.get('game_date'),
            tags=note_data.get('tags')
        ))

    return snippets


def _keyword_search(
    query: str,
    db: Session,
    player_id: Optional[int],
    team: Optional[str]
) -> List[Tuple[dict, float]]:
    """
    PostgreSQL full-text search using ts_rank.
    Returns list of (note_data_dict, score) tuples.
    """
    ts_query = func.plainto_tsquery('english', query)

    query_obj = db.query(
        models.Note,
        func.ts_rank(models.Note.text_searchable, ts_query).label('rank')
    ).filter(
        models.Note.text_searchable.is_not(None),
        models.Note.text_searchable.bool_op('@@')(ts_query)
    ).join(models.Player)

    # Apply filters
    if player_id:
        query_obj = query_obj.filter(models.Note.player_id == player_id)
    if team:
        query_obj = query_obj.filter(models.Player.team.ilike(f"%{team}%"))

    results = query_obj.all()

    # Convert to dict format
    formatted_results = []
    for note, rank in results:
        note_data = {
            'note_id': note.id,
            'player_id': note.player_id,
            'player_name': note.player.name,
            'team': note.player.team or "",
            'title': note.title,
            'content': note.content,
            'tags': note.tags,
            'game_date': note.game_date
        }
        formatted_results.append((note_data, float(rank)))

    return formatted_results


def _semantic_search_qdrant(
    query_embedding: List[float],
    player_id: Optional[int],
    team: Optional[str],
    top_k: int = 20
) -> List[Tuple[dict, float]]:
    """
    Vector similarity search using Qdrant.
    Returns list of (note_data_dict, score) tuples.

    Args:
        query_embedding: Query vector
        player_id: Optional player filter
        team: Optional team filter
        top_k: Number of results to fetch

    Returns:
        List of (note_data_dict, cosine_similarity_score) tuples
    """
    # Search in Qdrant (handles filtering internally)
    results = search_similar_notes(
        query_embedding=query_embedding,
        player_id=player_id,
        team=team,
        top_k=top_k
    )

    # Convert to expected format
    formatted_results = []
    for result in results:
        note_data = {
            'note_id': result['note_id'],
            'player_id': result['player_id'],
            'player_name': result['player_name'],
            'team': result['team'],
            'title': result['title'],
            'content': result['content'],
            'tags': result['tags'],
            'game_date': result['game_date']
        }
        # Qdrant returns cosine similarity (0-1), higher is better
        formatted_results.append((note_data, result['score']))

    return formatted_results


def _combine_scores(
    keyword_results: List[Tuple[dict, float]],
    semantic_results: List[Tuple[dict, float]],
    keyword_weight: float,
    semantic_weight: float
) -> List[dict]:
    """
    Normalize and combine keyword and semantic scores.

    Args:
        keyword_results: List of (note_data_dict, score) from keyword search
        semantic_results: List of (note_data_dict, score) from semantic search
        keyword_weight: Weight for keyword scoring (0-1)
        semantic_weight: Weight for semantic scoring (0-1)

    Returns:
        List of dicts with combined scores
    """
    # Normalize keyword scores to [0, 1]
    if keyword_results:
        max_kw = max(score for _, score in keyword_results) if keyword_results else 1.0
        kw_dict = {note_data['note_id']: (note_data, score / max_kw if max_kw > 0 else 0.0)
                   for note_data, score in keyword_results}
    else:
        kw_dict = {}

    # Semantic scores from Qdrant are already in [0, 1] (cosine similarity)
    sem_dict = {note_data['note_id']: (note_data, score)
                for note_data, score in semantic_results}

    # Combine all note IDs
    all_note_ids = set(kw_dict.keys()) | set(sem_dict.keys())

    combined = []
    for note_id in all_note_ids:
        kw_note_data, kw_score = kw_dict.get(note_id, (None, 0.0))
        sem_note_data, sem_score = sem_dict.get(note_id, (None, 0.0))

        # Get note data (prefer from keyword results, then semantic)
        note_data = kw_note_data if kw_note_data else sem_note_data

        # Calculate final score
        final_score = (keyword_weight * kw_score) + (semantic_weight * sem_score)

        combined.append({
            'note_data': note_data,
            'final_score': final_score,
            'keyword_score': kw_score,
            'semantic_score': sem_score
        })

    return combined


def _create_excerpt(content: str, query: str, max_length: int = 200) -> str:
    """
    Create an excerpt from content, trying to center around query terms.
    """
    if len(content) <= max_length:
        return content

    # Try to find query in content (case-insensitive)
    query_lower = query.lower()
    content_lower = content.lower()

    # Try to find the query
    idx = content_lower.find(query_lower)

    if idx != -1:
        # Center excerpt around query
        start = max(0, idx - max_length // 2)
        end = min(len(content), idx + max_length // 2)

        excerpt = content[start:end]

        # Add ellipsis
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        return excerpt
    else:
        # Just truncate from start
        return content[:max_length] + "..."
