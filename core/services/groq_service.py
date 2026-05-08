import logging
from groq import AsyncGroq, APIError, APITimeoutError
from core.config import get_groq_api_key, get_model_primary, get_model_fallback

logger = logging.getLogger(__name__)


class GroqService:
    def __init__(self):
        self.client = AsyncGroq(api_key=get_groq_api_key())
        self.primary_model = get_model_primary()
        self.fallback_model = get_model_fallback()

    async def complete(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        for model in [self.primary_model, self.fallback_model]:
            try:
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
                logger.warning("Timeout on %s, trying fallback...", model)
                continue
            except APIError as e:
                if "model" in str(e).lower() or "429" in str(e) or "decommissioned" in str(e).lower():
                    logger.warning("Model %s unavailable, trying fallback...", model)
                    continue
                raise RuntimeError(f"Groq API error: {e}") from e
            except Exception as e:
                if model == self.fallback_model:
                    raise RuntimeError(f"Both models failed: {e}") from e
                logger.warning("Error on %s: %s, trying fallback...", model, e)
                continue
        raise RuntimeError("All Groq models exhausted.")
