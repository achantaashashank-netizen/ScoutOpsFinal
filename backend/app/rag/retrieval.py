from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from app import models
from app.rag.schemas import NoteSnippet
from app.rag.embeddings import get_embedding_model


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

    # Perform keyword search
    keyword_results = _keyword_search(query, db, player_id, team)

    # Perform semantic search
    semantic_results = _semantic_search(query_embedding, db, player_id, team)

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
        note = result['note']
        snippets.append(NoteSnippet(
            note_id=note.id,
            player_id=note.player_id,
            player_name=note.player.name,
            title=note.title,
            excerpt=_create_excerpt(note.content, query),
            relevance_score=result['final_score'],
            keyword_score=result['keyword_score'],
            semantic_score=result['semantic_score'],
            game_date=note.game_date,
            tags=note.tags
        ))

    return snippets


def _keyword_search(
    query: str,
    db: Session,
    player_id: Optional[int],
    team: Optional[str]
) -> List[Tuple[models.Note, float]]:
    """
    PostgreSQL full-text search using ts_rank.
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
    return [(note, float(rank)) for note, rank in results]


def _semantic_search(
    query_embedding: List[float],
    db: Session,
    player_id: Optional[int],
    team: Optional[str]
) -> List[Tuple[models.Note, float]]:
    """
    Vector similarity search using PostgreSQL array operations (no pgvector needed).
    Computes cosine similarity manually using SQL.
    """
    import numpy as np

    # Fetch all notes with embeddings
    query_obj = db.query(models.Note).filter(
        models.Note.embedding.is_not(None)
    ).join(models.Player)

    # Apply filters
    if player_id:
        query_obj = query_obj.filter(models.Note.player_id == player_id)
    if team:
        query_obj = query_obj.filter(models.Player.team.ilike(f"%{team}%"))

    notes = query_obj.all()

    # Calculate cosine similarity in Python
    results = []
    query_emb = np.array(query_embedding)
    query_norm = np.linalg.norm(query_emb)

    for note in notes:
        if note.embedding and len(note.embedding) == len(query_embedding):
            note_emb = np.array(note.embedding)
            note_norm = np.linalg.norm(note_emb)

            if note_norm > 0 and query_norm > 0:
                # Cosine similarity = dot product / (norm1 * norm2)
                similarity = np.dot(query_emb, note_emb) / (query_norm * note_norm)
                results.append((note, float(similarity)))

    # Sort by similarity (descending) and limit to top 20
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:20]


def _combine_scores(
    keyword_results: List[Tuple[models.Note, float]],
    semantic_results: List[Tuple[models.Note, float]],
    keyword_weight: float,
    semantic_weight: float
) -> List[dict]:
    """
    Normalize and combine keyword and semantic scores.
    """
    # Normalize keyword scores to [0, 1]
    if keyword_results:
        max_kw = max(score for _, score in keyword_results) if keyword_results else 1.0
        kw_dict = {note.id: (note, score / max_kw if max_kw > 0 else 0.0)
                   for note, score in keyword_results}
    else:
        kw_dict = {}

    # Semantic scores are already in [0, 1] (cosine similarity)
    sem_dict = {note.id: (note, score) for note, score in semantic_results}

    # Combine all note IDs
    all_note_ids = set(kw_dict.keys()) | set(sem_dict.keys())

    combined = []
    for note_id in all_note_ids:
        kw_note, kw_score = kw_dict.get(note_id, (None, 0.0))
        sem_note, sem_score = sem_dict.get(note_id, (None, 0.0))

        # Get note object (prefer from keyword results, then semantic)
        note = kw_note if kw_note else sem_note

        # Calculate final score
        final_score = (keyword_weight * kw_score) + (semantic_weight * sem_score)

        combined.append({
            'note': note,
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
