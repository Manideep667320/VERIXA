"""Test configuration and fixtures."""

import pytest
from app.core.config import settings


@pytest.fixture(autouse=True)
def use_mock_ticket_connector(monkeypatch):
    """Keep the default suite offline even if a developer selects Jira in their .env."""
    monkeypatch.setattr(settings, "connector_provider", "mock", raising=False)


@pytest.fixture
def base_url():
    return "http://localhost:8000"
