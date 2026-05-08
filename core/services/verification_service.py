import asyncio
import logging
import time
from typing import List
from core.models.schema import ClaimResult, SearchResult, Verdict, VerificationResponse
from core.services.groq_service import GroqService
from core.services.search_service import SearchService
from core.utils.verifier import verify_claim
from core.utils.prompts import SUMMARY_PROMPT

logger = logging.getLogger(__name__)


def _compute_trust_score(results: List[ClaimResult]) -> float:
    if not results:
        return 0.0
    weights = {"Verified": 1.0, "Inaccurate": 0.4, "Misleading": 0.2, "False": 0.0, "Unverifiable": 0.5}
    score = sum(weights.get(r.verdict.value, 0.5) * (r.confidence / 100) for r in results)
    return round((score / len(results)) * 100, 1)


class VerificationService:
    def __init__(self):
        self.groq = GroqService()
        self.search = SearchService()

    async def verify_all(self, claims: List[str], document_excerpt: str = "") -> VerificationResponse:
        start_time = time.time()
        semaphore = asyncio.Semaphore(3)

        async def bounded_verify(claim: str) -> ClaimResult:
            async with semaphore:
                try:
                    result = await verify_claim(claim, self.groq, self.search)
                    sources = [SearchResult(title=s.get("title", ""), snippet=s.get("snippet", ""),
                                            url=s.get("url", "")) for s in result.get("sources", [])]
                    return ClaimResult(claim=claim, verdict=Verdict(result.get("verdict", "Unverifiable")),
                                       confidence=result.get("confidence", 0),
                                       correct_fact=result.get("correct_fact", ""),
                                       reasoning=result.get("reasoning", ""), sources=sources)
                except Exception as e:
                    logger.error("Failed to verify '%s': %s", claim[:60], e)
                    return ClaimResult(claim=claim, verdict=Verdict.UNVERIFIABLE, confidence=0,
                                       correct_fact="", reasoning="Verification could not be completed.", sources=[])

        results = list(await asyncio.gather(*[bounded_verify(c) for c in claims]))
        elapsed = round(time.time() - start_time, 2)
        trust_score = _compute_trust_score(results)
        summary = await self._generate_summary(results)

        return VerificationResponse(claims=results, total_claims=len(results),
                                    processing_time_seconds=elapsed,
                                    document_excerpt=document_excerpt[:300] if document_excerpt else None,
                                    trust_score=trust_score, summary=summary)

    async def _generate_summary(self, results: List[ClaimResult]) -> str:
        counts = {"Verified": 0, "Inaccurate": 0, "Misleading": 0, "False": 0, "Unverifiable": 0}
        for r in results:
            counts[r.verdict.value] = counts.get(r.verdict.value, 0) + 1
        results_summary = (f"Total: {len(results)}. Verified: {counts['Verified']}, "
                           f"Inaccurate: {counts['Inaccurate']}, Misleading: {counts['Misleading']}, "
                           f"False: {counts['False']}, Unverifiable: {counts['Unverifiable']}.")
        try:
            return await self.groq.complete(SUMMARY_PROMPT.format(results_summary=results_summary),
                                            max_tokens=150, temperature=0.3)
        except Exception:
            v, i, f = counts["Verified"], counts["Inaccurate"], counts["False"]
            return (f"This document contains {len(results)} factual claims. "
                    f"{v} verified, {i} inaccurate, {f} false.")
