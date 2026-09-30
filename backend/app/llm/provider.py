"""LLM provider abstraction — supports Gemini and OpenRouter (OpenAI-compatible)."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract LLM interface — all agent LLM calls go through this."""

    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate a text completion."""

    @abstractmethod
    async def structured_output(self, prompt: str, schema: dict, system: str = "") -> dict:
        """Generate a response constrained to a JSON schema."""

    async def extract_json(self, text: str) -> dict:
        """Best-effort JSON extraction from LLM text output."""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        return json.loads(text)


class GeminiProvider(LLMProvider):
    """Google Gemini via the google-genai SDK."""

    def __init__(self) -> None:
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def generate(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = self._client.models.generate_content(model=self._model, contents=full_prompt)
        return response.text or ""

    async def structured_output(self, prompt: str, schema: dict, system: str = "") -> dict:
        full_prompt = (
            f"{system}\n\n{prompt}\n\n"
            f"Respond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        )
        text = await self.generate(full_prompt)
        return await self.extract_json(text)


class OpenRouterProvider(LLMProvider):
    """OpenRouter via OpenAI-compatible API."""

    def __init__(self) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self._model = settings.openrouter_model

    async def generate(self, prompt: str, system: str = "") -> str:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = await self._client.chat.completions.create(model=self._model, messages=messages)
        return response.choices[0].message.content or ""

    async def structured_output(self, prompt: str, schema: dict, system: str = "") -> dict:
        augmented = (
            f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        )
        text = await self.generate(augmented, system=system)
        return await self.extract_json(text)


# ── Factory ─────────────────────────────────────────────────────────────

_provider: LLMProvider | None = None


def get_llm() -> LLMProvider:
    """Return the singleton LLM provider instance."""
    global _provider
    if _provider is None:
        if settings.llm_provider == "gemini":
            _provider = GeminiProvider()
            logger.info("LLM provider initialized: Gemini (%s)", settings.gemini_model)
        else:
            _provider = OpenRouterProvider()
            logger.info("LLM provider initialized: OpenRouter (%s)", settings.openrouter_model)
    return _provider
