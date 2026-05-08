import logging
from typing import List
from api.app.services.groq_service import GroqService
from api.app.utils.prompts import CLAIM_EXTRACTION_PROMPT
from api.app.utils.helpers import safe_json_parse, truncate_text, clean_text

logger = logging.getLogger(__name__)


async def detect_claims(text: str, max_claims: int, groq_service: GroqService) -> List[str]:
    """
    Use Groq LLM to extract verifiable factual claims from text.

    Returns:
        List of claim strings

    Raises:
        ValueError: If extraction fails or response is malformed
    """
    cleaned = clean_text(text)
    truncated = truncate_text(cleaned, max_chars=6000)

    prompt = CLAIM_EXTRACTION_PROMPT.format(
        text=truncated,
        max_claims=max_claims
    )

    response = await groq_service.complete(
        prompt=prompt,
        max_tokens=1024,
        temperature=0.1
    )

    parsed = safe_json_parse(response)
    if parsed is None:
        logger.error("Failed to parse claim extraction response")
        raise ValueError("LLM returned malformed claim extraction response.")

    if not isinstance(parsed, list):
        raise ValueError("Claim extraction response is not a list.")

    claims = [str(c).strip() for c in parsed if str(c).strip()]
    claims = claims[:max_claims]

    if not claims:
        raise ValueError("No verifiable factual claims were found in this document.")

    logger.info("Detected %d claims", len(claims))
    return claims
