"""LLM provider abstraction — supports Gemini and OpenRouter."""
from __future__ import annotations
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import TypeVar
from pydantic import BaseModel, ValidationError
from app.core.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

RATE_LIMIT_MESSAGE = (
    "The AI provider is temporarily rate-limited. "
    "Please retry shortly or configure a dedicated provider API key."
)
UNAVAILABLE_MESSAGE = (
    "The AI provider is temporarily unavailable. "
    "Please retry shortly or configure another provider."
)


class ProviderRateLimitError(RuntimeError):
    """Raised when an upstream model provider rejects a request with HTTP 429."""


class ProviderUnavailableError(RuntimeError):
    """Raised when all configured model attempts return a transient 503."""


def is_rate_limit_error(error: BaseException) -> bool:
    """Identify provider rate limits without depending on an SDK exception class."""
    if isinstance(error, ProviderRateLimitError):
        return True
    if getattr(error, "status_code", None) == 429:
        return True
    response = getattr(error, "response", None)
    if getattr(response, "status_code", None) == 429:
        return True
    return "429" in str(error) and any(
        marker in str(error).lower() for marker in ("rate limit", "rate-limit", "rate_limited", "rate limited")
    )


def is_unavailable_error(error: BaseException) -> bool:
    """Identify transient provider capacity failures without SDK coupling."""
    if isinstance(error, ProviderUnavailableError):
        return True
    if getattr(error, "status_code", None) == 503 or getattr(error, "code", None) == 503:
        return True
    response = getattr(error, "response", None)
    return getattr(response, "status_code", None) == 503 or (
        "503" in str(error) and "unavailable" in str(error).lower()
    )


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str: ...

    @abstractmethod
    async def structured_output(self, prompt: str, schema: dict, system: str = "") -> dict: ...

    async def extract_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        return json.loads(text)

    async def structured_model(self, prompt: str, output_model: type[T], system: str = "") -> T:
        """Return schema-valid structured output, retrying once after parse/validation failure."""
        schema = output_model.model_json_schema()
        retry_prompt = prompt
        for attempt in range(2):
            try:
                raw = await self.structured_output(retry_prompt, schema=schema, system=system)
                if isinstance(raw, output_model):
                    return raw
                if isinstance(raw, str):
                    raw = await self.extract_json(raw)
                return output_model.model_validate(raw)
            except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
                if attempt:
                    raise
                retry_prompt = (f"{prompt}\n\nYour previous response was invalid ({exc}). "
                                "Retry once. Return only JSON that satisfies the supplied schema.")
        raise RuntimeError("unreachable")

class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        api_key = settings.gemini_api_key.strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini.")
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = settings.gemini_model

    async def generate(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        models = tuple(dict.fromkeys((
            self._model,
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
        )))
        last_error: BaseException | None = None
        for model in models:
            for attempt in range(2):
                try:
                    response = self._client.models.generate_content(model=model, contents=full_prompt)
                    return response.text or ""
                except Exception as exc:
                    last_error = exc
                    if not (is_unavailable_error(exc) or is_rate_limit_error(exc)):
                        raise
                    if attempt == 0:
                        await asyncio.sleep(0.5)
        if is_rate_limit_error(last_error):
            raise ProviderRateLimitError(RATE_LIMIT_MESSAGE) from last_error
        raise ProviderUnavailableError(UNAVAILABLE_MESSAGE) from last_error

    async def structured_output(self, prompt: str, schema: dict, system: str = "") -> dict:
        full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        return await self.extract_json(await self.generate(full_prompt, system=system))

class OpenRouterProvider(LLMProvider):
    def __init__(self) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.openrouter_api_key, base_url="https://openrouter.ai/api/v1")
        self._model = settings.openrouter_model

    async def generate(self, prompt: str, system: str = "") -> str:
        messages = ([{"role": "system", "content": system}] if system else [])
        messages.append({"role": "user", "content": prompt})
        for attempt in range(3):
            try:
                response = await self._client.chat.completions.create(model=self._model, messages=messages)
                return response.choices[0].message.content or ""
            except Exception as exc:
                if not is_rate_limit_error(exc):
                    raise
                if attempt == 2:
                    raise ProviderRateLimitError(RATE_LIMIT_MESSAGE) from exc
                await asyncio.sleep(0.5 * (2 ** attempt))
        raise RuntimeError("unreachable")

    async def structured_output(self, prompt: str, schema: dict, system: str = "") -> dict:
        augmented = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        return await self.extract_json(await self.generate(augmented, system=system))

_provider: LLMProvider | None = None

def get_llm() -> LLMProvider:
    global _provider
    if _provider is None:
        if settings.llm_provider == "gemini":
            _provider = GeminiProvider()
            logger.info("LLM provider initialized: Gemini (%s)", settings.gemini_model)
        else:
            _provider = OpenRouterProvider()
            logger.info("LLM provider initialized: OpenRouter (%s)", settings.openrouter_model)
    return _provider
