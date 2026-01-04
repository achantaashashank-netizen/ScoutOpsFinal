// Week 2 RAG Types

export interface NoteSnippet {
  note_id: number;
  player_id: number;
  player_name: string;
  title: string;
  excerpt: string;
  relevance_score: number;
  keyword_score: number;
  semantic_score: number;
  game_date: string | null;
  tags: string | null;
}

export interface RetrievalRequest {
  query: string;
  player_id?: number;
  team?: string;
  top_k?: number;
  keyword_weight?: number;
  semantic_weight?: number;
}

export interface RetrievalResponse {
  query: string;
  results: NoteSnippet[];
  total_results: number;
}

export interface Citation {
  note_id: number;
  player_name: string;
  title: string;
  excerpt: string;
  reference_number: number;
}

export interface GenerationRequest {
  query: string;
  player_id?: number;
  team?: string;
  top_k?: number;
  include_retrieval?: boolean;
}

export interface GenerationResponse {
  query: string;
  answer: string;
  citations: Citation[];
  has_sufficient_information: boolean;
  confidence: string; // "high" | "medium" | "low"
  retrieved_notes?: NoteSnippet[];
}
