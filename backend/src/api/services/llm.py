"""LLM provider boundary. Providers receive prompts, never database sessions."""

from typing import Protocol

from litellm import acompletion

from src.api.config import settings


class LLMProviderError(RuntimeError):
    """Raised when a model provider cannot produce a usable completion."""


class LLMClient(Protocol):
    async def complete(self, prompt: str) -> str: ...


class GeminiLiteLLMClient:
    """Gemini adapter using LiteLLM's provider-neutral completion interface."""

    async def complete(self, prompt: str) -> str:
        if settings.gemini_api_key is None:
            raise LLMProviderError("Gemini is not configured")

        try:
            response = await acompletion(
                model=settings.gemini_model,
                api_key=settings.gemini_api_key.get_secret_value(),
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content
        except Exception as exc:
            raise LLMProviderError("Gemini completion failed") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("Gemini returned an empty completion")
        return content.strip()
