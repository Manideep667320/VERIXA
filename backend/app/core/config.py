"""Core configuration — single source of truth for all settings."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM
    llm_provider: Literal["gemini", "openrouter"] = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-exp:free"

    # Embedding
    embedding_model: str = "models/text-embedding-004"

    # Database
    database_url: str = "sqlite:///./data/evidence_to_action.db"

    # ChromaDB
    chroma_persist_dir: str = "./data/vectorstore"
    chroma_collection: str = "enterprise_knowledge"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Logging
    log_level: str = "INFO"

    # Paths
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
