import logging
import asyncio
from groq import AsyncGroq, APIError, APITimeoutError
from api.app.config.settings import get_settings

logger = logging.getLogger(__name__)


class GroqService:
    """Async Groq LLM client with automatic model fallback."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.primary_model = settings.groq_model_primary
        self.fallback_model = settings.groq_model_fallback

    async def complete(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.2
    ) -> str:
        """
        Send a completion request. Tries primary model first, falls back on error.

        Returns:
            Response text string

        Raises:
            RuntimeError: If both models fail
        """
        for model in [self.primary_model, self.fallback_model]:
            try:
                logger.debug("Calling Groq model: %s", model)
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
                raise ValueError("Empty response from model.")
            except APITimeoutError:
                logger.warning("Timeout on model %s, trying fallback...", model)
                continue
            except APIError as e:
                if "model" in str(e).lower() or "429" in str(e):
                    logger.warning("Model %s unavailable (%s), trying fallback...", model, e)
                    continue
                raise RuntimeError(f"Groq API error: {e}") from e
            except Exception as e:
                if model == self.fallback_model:
                    raise RuntimeError(f"Both Groq models failed. Last error: {e}") from e
                logger.warning("Error on model %s: %s, trying fallback...", model, e)
                continue

        raise RuntimeError("All Groq models exhausted without a successful response.")
