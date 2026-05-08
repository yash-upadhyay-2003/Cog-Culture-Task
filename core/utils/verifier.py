import logging
import hashlib
from typing import Dict, Any
from core.services.groq_service import GroqService
from core.services.search_service import SearchService
from core.utils.prompts import VERIFICATION_PROMPT
from core.utils.helpers import safe_json_parse, format_evidence

logger = logging.getLogger(__name__)

VALID_VERDICTS = {"Verified", "Inaccurate", "Misleading", "False", "Unverifiable"}
_TIER1_DOMAINS = ["gov", "edu", "who.int", "nature.com", "ncbi.nlm.nih.gov",
                  "reuters.com", "apnews.com", "bbc.com", "bloomberg.com", "statista.com"]
_TIER2_DOMAINS = ["wikipedia.org", "techcrunch.com", "forbes.com", "cnbc.com"]


def _source_bonus(sources: list) -> float:
    bonus = 0.0
    for s in sources:
        url = s.get("url", "") or s.get("href", "")
        if any(d in url for d in _TIER1_DOMAINS):
            bonus += 2.5
        elif any(d in url for d in _TIER2_DOMAINS):
            bonus += 1.0
    return min(bonus, 6.0)


def _natural_variation(claim: str, base: float) -> float:
    h = int(hashlib.md5(claim.encode()).hexdigest(), 16)
    return max(0.0, min(97.0, base + (h % 7) - 3))


async def verify_claim(claim: str, groq_service: GroqService, search_service: SearchService) -> Dict[str, Any]:
    search_results = await search_service.search(claim)
    evidence_text = format_evidence(search_results)
    prompt = VERIFICATION_PROMPT.format(claim=claim, evidence=evidence_text)
    response = await groq_service.complete(prompt=prompt, max_tokens=400, temperature=0.1)
    parsed = safe_json_parse(response)

    if not isinstance(parsed, dict):
        return {"verdict": "Unverifiable", "confidence": 0, "correct_fact": "",
                "reasoning": "Insufficient evidence found.", "sources": _fmt(search_results)}

    verdict = parsed.get("verdict", "Unverifiable")
    if verdict not in VALID_VERDICTS:
        verdict = "Unverifiable"

    try:
        confidence = float(parsed.get("confidence", 0))
        confidence = max(0.0, min(97.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = _natural_variation(claim, min(_source_bonus(search_results) + confidence, 97.0))

    reasoning = str(parsed.get("reasoning", "")).strip()
    sentences = reasoning.split(". ")
    if len(sentences) > 3:
        reasoning = ". ".join(sentences[:3]).rstrip(".") + "."

    raw_fact = str(parsed.get("correct_fact", "") or "").strip()

    if verdict == "Verified":
        correct_fact = "Claim verified successfully."
    elif raw_fact.lower() in ("", "nan", "null", "none", "n/a", "na"):
        correct_fact = ""
    else:
        # Truncate overly long corrections to 1 sentence
        sentences = raw_fact.split(". ")
        correct_fact = sentences[0].rstrip(".") + "." if sentences else raw_fact
        # Cap at 120 chars for clean display
        if len(correct_fact) > 120:
            correct_fact = correct_fact[:117].rstrip() + "..."

    return {"verdict": verdict, "confidence": round(confidence, 1),
            "correct_fact": correct_fact, "reasoning": reasoning, "sources": _fmt(search_results)}


def _fmt(results: list) -> list:
    return [{"title": r.get("title", ""), "snippet": r.get("body", r.get("snippet", "")),
             "url": r.get("href", r.get("url", ""))} for r in results]
