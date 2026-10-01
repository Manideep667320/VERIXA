import asyncio
import gc

import pytest

from app.core.config import settings
from app.llm.provider import (
    RATE_LIMIT_MESSAGE,
    ProviderUnavailableError,
    GeminiProvider,
    OpenRouterProvider,
    ProviderRateLimitError,
)


async def test_missing_gemini_key_does_not_schedule_sdk_cleanup_error(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    loop = asyncio.get_running_loop()
    cleanup_errors = []
    previous_handler = loop.get_exception_handler()
    loop.set_exception_handler(lambda _loop, context: cleanup_errors.append(context.get("exception")))
    try:
        with pytest.raises(ValueError) as raised:
            GeminiProvider()
        gc.collect()
        await asyncio.sleep(0.05)
    finally:
        loop.set_exception_handler(previous_handler)

    assert "GEMINI_API_KEY" in str(raised.value)
    assert not any(
        isinstance(error, AttributeError) and "_async_httpx_client" in str(error)
        for error in cleanup_errors
    )


async def test_openrouter_retries_rate_limit_then_returns_sanitized_error(monkeypatch):
    class RateLimitedError(RuntimeError):
        status_code = 429

    class Completions:
        def __init__(self):
            self.calls = 0

        async def create(self, **_kwargs):
            self.calls += 1
            raise RateLimitedError("upstream shared pool details")

    completions = Completions()
    provider = object.__new__(OpenRouterProvider)
    provider._client = type("Client", (), {
        "chat": type("Chat", (), {"completions": completions})(),
    })()
    provider._model = "test-model"
    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("app.llm.provider.asyncio.sleep", no_sleep)

    with pytest.raises(ProviderRateLimitError, match="temporarily rate-limited") as raised:
        await provider.generate("prompt")

    assert completions.calls == 3
    assert str(raised.value) == RATE_LIMIT_MESSAGE
    assert "shared pool details" not in str(raised.value)


async def test_gemini_falls_back_after_transient_capacity_errors(monkeypatch):
    class UnavailableError(RuntimeError):
        code = 503

    class Models:
        def __init__(self):
            self.calls = []

        def generate_content(self, *, model, contents):
            self.calls.append(model)
            if model == "primary-model":
                raise UnavailableError("high demand")
            return type("Response", (), {"text": "OK"})()

    models = Models()
    provider = object.__new__(GeminiProvider)
    provider._client = type("Client", (), {"models": models})()
    provider._model = "primary-model"
    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("app.llm.provider.asyncio.sleep", no_sleep)
    assert await provider.generate("prompt") == "OK"
    assert models.calls == [
        "primary-model", "primary-model", "gemini-flash-lite-latest",
    ]


async def test_gemini_reports_sanitized_error_when_all_models_are_unavailable(monkeypatch):
    class UnavailableError(RuntimeError):
        code = 503

    class Models:
        def generate_content(self, **_kwargs):
            raise UnavailableError("upstream payload")

    provider = object.__new__(GeminiProvider)
    provider._client = type("Client", (), {"models": Models()})()
    provider._model = "primary-model"
    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("app.llm.provider.asyncio.sleep", no_sleep)
    with pytest.raises(ProviderUnavailableError, match="temporarily unavailable") as raised:
        await provider.generate("prompt")
    assert "upstream payload" not in str(raised.value)
