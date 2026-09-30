"""LLM provider abstraction — supports Gemini and OpenRouter."""
from __future__ import annotations
import json
import logging
from abc import ABC, abstractmethod
from typing import TypeVar
from pydantic import BaseModel, ValidationError
from app.core.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

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
        from google import genai
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def generate(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = self._client.models.generate_content(model=self._model, contents=full_prompt)
        return response.text or ""

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
        response = await self._client.chat.completions.create(model=self._model, messages=messages)
        return response.choices[0].message.content or ""

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
