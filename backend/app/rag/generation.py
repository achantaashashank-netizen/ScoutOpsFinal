import google.generativeai as genai
from sqlalchemy.orm import Session
from typing import List, Optional
import re
from app.config import get_settings
from app.rag.schemas import Citation, GenerationResponse, NoteSnippet
from app.rag.retrieval import retrieve_notes


settings = get_settings()

# Configure Gemini API
if settings.google_api_key:
    genai.configure(api_key=settings.google_api_key)


GROUNDING_PROMPT_TEMPLATE = """You are an expert NBA scout assistant. Your job is to answer questions about players based ONLY on the provided scouting notes.

STRICT RULES:
1. Only use information from the notes below
2. Cite every claim using [1], [2], etc. notation
3. If the notes don't contain enough information to answer, say: "I don't have enough information in the scouting notes to answer this question."
4. Do not make up or infer information not explicitly in the notes
5. If asked about a player not in the notes, say you don't have notes on them

SCOUTING NOTES:
{context}

QUESTION: {query}

ANSWER (with citations):"""


def generate_answer(
    query: str,
    db: Session,
    player_id: Optional[int] = None,
    team: Optional[str] = None,
    top_k: int = 5,
    include_retrieval: bool = True
) -> GenerationResponse:
    """
    Generate a grounded answer with citations using Google Gemini.

    Args:
        query: Question to answer
        db: Database session
        player_id: Optional player filter
        team: Optional team filter
        top_k: Number of notes to retrieve
        include_retrieval: Include retrieval results in response

    Returns:
        GenerationResponse with answer, citations, and metadata
    """
    # Step 1: Retrieve relevant notes
    retrieved_notes = retrieve_notes(
        query=query,
        db=db,
        player_id=player_id,
        team=team,
        top_k=top_k
    )

    # Step 2: Check if we have notes
    if not retrieved_notes:
        return GenerationResponse(
            query=query,
            answer="I don't have any scouting notes to answer this question.",
            citations=[],
            has_sufficient_information=False,
            confidence="low",
            retrieved_notes=[] if include_retrieval else None
        )

    # Step 3: Build context from retrieved notes
    context = _build_context(retrieved_notes)

    # Step 4: Build prompt
    prompt = GROUNDING_PROMPT_TEMPLATE.format(
        context=context,
        query=query
    )

    # Step 5: Call Gemini API
    try:
        model = genai.GenerativeModel(settings.generation_model)
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,  # Low temperature for factual responses
                'max_output_tokens': 500
            }
        )

        answer = response.text.strip()

    except Exception as e:
        # Fallback on API error
        return GenerationResponse(
            query=query,
            answer=f"Error generating answer: {str(e)}. Please check your Google API key.",
            citations=[],
            has_sufficient_information=False,
            confidence="low",
            retrieved_notes=retrieved_notes if include_retrieval else None
        )

    # Step 6: Extract citations
    citations = _extract_citations(answer, retrieved_notes)

    # Step 7: Assess confidence
    has_sufficient_info = "don't have enough information" not in answer.lower()
    confidence = _assess_confidence(answer, citations, retrieved_notes)

    return GenerationResponse(
        query=query,
        answer=answer,
        citations=citations,
        has_sufficient_information=has_sufficient_info,
        confidence=confidence,
        retrieved_notes=retrieved_notes if include_retrieval else None
    )


def _build_context(notes: List[NoteSnippet]) -> str:
    """
    Format notes as numbered context for the prompt.
    """
    context_parts = []
    for i, note in enumerate(notes, 1):
        context_parts.append(
            f"[{i}] Player: {note.player_name}\n"
            f"    Title: {note.title}\n"
            f"    Content: {note.excerpt}\n"
            f"    Game Date: {note.game_date or 'N/A'}\n"
            f"    Tags: {note.tags or 'N/A'}"
        )
    return "\n\n".join(context_parts)


def _extract_citations(answer: str, notes: List[NoteSnippet]) -> List[Citation]:
    """
    Parse [1], [2] citation references from the answer.
    """
    # Find all [N] patterns
    citation_refs = re.findall(r'\[(\d+)\]', answer)
    citation_refs = sorted(set(int(ref) for ref in citation_refs))

    citations = []
    for ref_num in citation_refs:
        # Check if reference is valid (within bounds of notes list)
        if 1 <= ref_num <= len(notes):
            note = notes[ref_num - 1]
            citations.append(Citation(
                note_id=note.note_id,
                player_name=note.player_name,
                title=note.title,
                excerpt=note.excerpt,
                reference_number=ref_num
            ))

    return citations


def _assess_confidence(
    answer: str,
    citations: List[Citation],
    notes: List[NoteSnippet]
) -> str:
    """
    Heuristic confidence assessment based on citations and answer content.

    Returns:
        "high", "medium", or "low"
    """
    # Low confidence indicators
    if "don't have enough information" in answer.lower():
        return "low"

    if "i don't have" in answer.lower() or "no information" in answer.lower():
        return "low"

    # High confidence: multiple citations from multiple notes
    if len(citations) >= 3 and len(notes) >= 3:
        return "high"

    # Medium confidence: some citations
    if len(citations) >= 1:
        return "medium"

    # Low confidence: no citations
    return "low"
