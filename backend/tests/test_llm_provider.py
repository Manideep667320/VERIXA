import asyncio
import gc

import pytest

from app.core.config import settings
from app.llm.provider import GeminiProvider


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
