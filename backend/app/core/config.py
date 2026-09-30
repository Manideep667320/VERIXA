"""Core configuration — single source of truth for all settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


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

    # Ticket-system connector
    connector_provider: Literal["mock", "jira"] = "mock"
    connector_timeout_seconds: float = 5.0
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""
    jira_issue_type: str = "Task"

    # Approval routing and notifier integrations
    approval_notifier: Literal["mock", "slack", "email"] = "mock"
    approval_timeout_seconds: int | None = Field(default=None, ge=1)
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_approval_channel: str = ""
    approval_role_slack_users: dict[str, list[str]] = Field(default_factory=dict)
    approval_link_secret: str = ""
    approval_public_base_url: str = "http://localhost:8000"
    approval_role_email_recipients: dict[str, list[str]] = Field(default_factory=dict)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # Analytics estimates (used only for presentation; no policy side effects)
    analytics_minutes_per_case: float = Field(default=15.0, ge=0)
    analytics_cost_per_hour: float = Field(default=50.0, ge=0)

    # Paths
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    model_config = {
        "env_file": _PROJECT_ROOT / ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
