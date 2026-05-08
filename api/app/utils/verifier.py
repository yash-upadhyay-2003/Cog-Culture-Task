import logging
import hashlib
from typing import Dict, Any
from api.app.services.groq_service import GroqService
from api.app.services.search_service import SearchService
from api.app.utils.prompts import VERIFICATION_PROMPT
from api.app.utils.helpers import safe_json_parse, format_evidence

logger = logging.getLogger(__name__)

VALID_VERDICTS = {"Verified", "Inaccurate", "Misleading", "False", "Unverifiable"}

# Source credibility bonus — higher tier = more confidence
_TIER1_DOMAINS = [
    "gov", "edu", "who.int", "nature.com", "ncbi.nlm.nih.gov",
    "reuters.com", "apnews.com", "bbc.com", "bloomberg.com",
    "statista.com", "gartner.com", "mckinsey.com"
]
_TIER2_DOMAINS = [
    "wikipedia.org", "techcrunch.com", "forbes.com",
    "cnbc.com", "theguardian.com", "wired.com"
]


def _source_bonus(sources: list) -> float:
    """Return a small confidence adjustment based on source quality."""
    bonus = 0.0
    for s in sources:
        url = s.get("url", "") or s.get("href", "")
        if any(d in url for d in _TIER1_DOMAINS):
            bonus += 2.5
        elif any(d in url for d in _TIER2_DOMAINS):
            bonus += 1.0
    return min(bonus, 6.0)  # cap bonus at +6


def _natural_variation(claim: str, base: float) -> float:
    """
    Add deterministic natural variation to confidence so identical
    scores don't repeat. Uses claim hash for reproducibility.
    """
    h = int(hashlib.md5(claim.encode()).hexdigest(), 16)
    # Variation in range [-3, +3]
    variation = (h % 7) - 3
    return max(0.0, min(97.0, base + variation))


async def verify_claim(
    claim: str,
    groq_service: GroqService,
    search_service: SearchService
) -> Dict[str, Any]:
    search_results = await search_service.search(claim)
    evidence_text = format_evidence(search_results)

    prompt = VERIFICATION_PROMPT.format(claim=claim, evidence=evidence_text)
    response = await groq_service.complete(prompt=prompt, max_tokens=400, temperature=0.1)

    parsed = safe_json_parse(response)

    if not isinstance(parsed, dict):
        logger.warning("Malformed verification response for: %s", claim[:80])
        return {
            "verdict": "Unverifiable",
            "confidence": 0,
            "correct_fact": "",
            "reasoning": "Insufficient evidence found to verify this claim.",
            "sources": _fmt(search_results)
        }

    verdict = parsed.get("verdict", "Unverifiable")
    if verdict not in VALID_VERDICTS:
        verdict = "Unverifiable"

    try:
        confidence = float(parsed.get("confidence", 0))
        confidence = max(0.0, min(97.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.0

    # Apply source quality bonus + natural variation
    confidence = _source_bonus(search_results) + confidence
    confidence = _natural_variation(claim, min(confidence, 97.0))

    reasoning = str(parsed.get("reasoning", "")).strip()
    sentences = reasoning.split(". ")
    if len(sentences) > 3:
        reasoning = ". ".join(sentences[:3]).rstrip(".") + "."

    # Clean correct_fact — never expose NaN/null/empty for Verified
    raw_fact = str(parsed.get("correct_fact", "") or "").strip()
    if verdict == "Verified":
        correct_fact = ""
    elif raw_fact.lower() in ("", "nan", "null", "none", "n/a", "na"):
        correct_fact = ""
    else:
        correct_fact = raw_fact

    return {
        "verdict": verdict,
        "confidence": round(confidence, 1),
        "correct_fact": correct_fact,
        "reasoning": reasoning,
        "sources": _fmt(search_results)
    }


def _fmt(results: list) -> list:
    return [
        {
            "title": r.get("title", ""),
            "snippet": r.get("body", r.get("snippet", "")),
            "url": r.get("href", r.get("url", ""))
        }
        for r in results
    ]
