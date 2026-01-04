from pydantic import BaseModel, Field
from typing import List, Optional


# Retrieval request/response schemas
class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    player_id: Optional[int] = Field(None, description="Filter by player ID")
    team: Optional[str] = Field(None, description="Filter by team name")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")
    keyword_weight: Optional[float] = Field(0.4, ge=0, le=1, description="Weight for keyword search")
    semantic_weight: Optional[float] = Field(0.6, ge=0, le=1, description="Weight for semantic search")


class NoteSnippet(BaseModel):
    note_id: int
    player_id: int
    player_name: str
    title: str
    excerpt: str
    relevance_score: float
    keyword_score: float
    semantic_score: float
    game_date: Optional[str]
    tags: Optional[str]

    class Config:
        from_attributes = True


class RetrievalResponse(BaseModel):
    query: str
    results: List[NoteSnippet]
    total_results: int


# Generation request/response schemas
class GenerationRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question to answer")
    player_id: Optional[int] = Field(None, description="Filter by player ID")
    team: Optional[str] = Field(None, description="Filter by team name")
    top_k: int = Field(5, ge=1, le=20, description="Number of notes to retrieve")
    include_retrieval: bool = Field(True, description="Include retrieval results in response")


class Citation(BaseModel):
    note_id: int
    player_name: str
    title: str
    excerpt: str
    reference_number: int


class GenerationResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    has_sufficient_information: bool
    confidence: str  # "high" | "medium" | "low"
    retrieved_notes: Optional[List[NoteSnippet]] = None
