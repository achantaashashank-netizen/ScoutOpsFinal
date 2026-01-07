from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    environment: str = "development"

    # Week 2 RAG settings
    google_api_key: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    max_retrieval_results: int = 5
    keyword_weight: float = 0.4
    semantic_weight: float = 0.6
    generation_model: str = "models/gemini-2.5-flash"

    # Qdrant vector database settings
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "scout_notes"
    qdrant_vector_size: int = 384  # all-MiniLM-L6-v2 embedding size

    class Config:
        env_file = "../.env"  # Read from root directory


@lru_cache()
def get_settings():
    return Settings()
