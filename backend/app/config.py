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

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
