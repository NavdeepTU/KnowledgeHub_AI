from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise RAG Platform"
    upload_directory: Path = Path("uploads")
    max_upload_size_mb: int = 10
    chunk_size_chars: int = Field(default=1000, gt=0)
    chunk_overlap_chars: int = Field(default=200, ge=0)
    embedding_model_name: str = "all-MiniLM-L6-v2"
    chroma_persist_directory: Path = Path("chroma_db")
    answer_model_name: str = "llama-3.1-8b-instant"
    groq_api_key: str | None = None
    conversation_directory: Path = Path("conversations")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
settings.upload_directory.mkdir(parents=True, exist_ok=True)
