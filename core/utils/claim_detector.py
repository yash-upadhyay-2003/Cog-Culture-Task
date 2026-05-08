import logging
from typing import List
from core.services.groq_service import GroqService
from core.utils.prompts import CLAIM_EXTRACTION_PROMPT
from core.utils.helpers import safe_json_parse, truncate_text, clean_text, filter_claims, heuristic_claim_extraction

logger = logging.getLogger(__name__)


async def detect_claims(text: str, max_claims: int, groq_service: GroqService) -> List[str]:
    cleaned = clean_text(text)
    truncated = truncate_text(cleaned, max_chars=6000)
    logger.info("Input text: %d chars", len(cleaned))

    claims: List[str] = []
    try:
        prompt = CLAIM_EXTRACTION_PROMPT.format(text=truncated, max_claims=max_claims)
        response = await groq_service.complete(prompt=prompt, max_tokens=1024, temperature=0.1)
        parsed = safe_json_parse(response)
        if isinstance(parsed, list):
            raw = [str(c).strip() for c in parsed if str(c).strip()]
            claims = filter_claims(raw)
            logger.info("LLM extracted %d raw → %d valid claims", len(raw), len(claims))
        else:
            logger.warning("LLM did not return a list — falling back to heuristics")
    except Exception as e:
        logger.warning("LLM extraction failed: %s — falling back to heuristics", e)

    if not claims:
        raw_heuristic = heuristic_claim_extraction(cleaned, max_claims)
        claims = filter_claims(raw_heuristic)
        logger.info("Heuristic extracted %d valid claims", len(claims))

    if not claims:
        raise ValueError(
            "No verifiable factual claims were found. "
            "Please upload a PDF with statistics, dates, financial figures, or research findings."
        )
    return claims[:max_claims]
