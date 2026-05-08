import logging
from typing import Dict, Any
from api.app.services.groq_service import GroqService
from api.app.services.search_service import SearchService
from api.app.utils.prompts import VERIFICATION_PROMPT
from api.app.utils.helpers import safe_json_parse, format_evidence

logger = logging.getLogger(__name__)


async def verify_claim(
    claim: str,
    groq_service: GroqService,
    search_service: SearchService
) -> Dict[str, Any]:
    """
    Verify a single claim using web search + LLM reasoning.

    Returns dict with: verdict, confidence, correct_fact, reasoning, sources
    """
    search_results = await search_service.search(claim)
    evidence_text = format_evidence(search_results)

    prompt = VERIFICATION_PROMPT.format(
        claim=claim,
        evidence=evidence_text
    )

    response = await groq_service.complete(
        prompt=prompt,
        max_tokens=512,
        temperature=0.2
    )

    parsed = safe_json_parse(response)

    if parsed is None or not isinstance(parsed, dict):
        logger.warning("Malformed verification response for claim: %s", claim[:80])
        return {
            "verdict": "Unverifiable",
            "confidence": 0,
            "correct_fact": "",
            "reasoning": "Could not process verification response.",
            "sources": _format_sources(search_results)
        }

    valid_verdicts = {"Verified", "Inaccurate", "False", "Unverifiable"}
    verdict = parsed.get("verdict", "Unverifiable")
    if verdict not in valid_verdicts:
        verdict = "Unverifiable"

    try:
        confidence = float(parsed.get("confidence", 0))
        confidence = max(0.0, min(100.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.0

    return {
        "verdict": verdict,
        "confidence": confidence,
        "correct_fact": str(parsed.get("correct_fact", "")),
        "reasoning": str(parsed.get("reasoning", "")),
        "sources": _format_sources(search_results)
    }


def _format_sources(search_results: list) -> list:
    """Convert raw search results to source dicts."""
    sources = []
    for r in search_results:
        sources.append({
            "title": r.get("title", ""),
            "snippet": r.get("body", r.get("snippet", "")),
            "url": r.get("href", r.get("url", ""))
        })
    return sources
