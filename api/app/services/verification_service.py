import asyncio
import logging
import time
from typing import List
from api.app.models.claim_schema import ClaimResult, SearchResult, Verdict, VerificationResponse
from api.app.services.groq_service import GroqService
from api.app.services.search_service import SearchService
from api.app.utils.verifier import verify_claim

logger = logging.getLogger(__name__)


class VerificationService:
    """Orchestrates the full claim verification pipeline."""

    def __init__(self):
        self.groq = GroqService()
        self.search = SearchService()

    async def verify_all(
        self,
        claims: List[str],
        document_excerpt: str = ""
    ) -> VerificationResponse:
        """
        Verify a list of claims concurrently.
        Processes all claims in parallel, bounded by semaphore for rate limiting.
        """
        start_time = time.time()
        semaphore = asyncio.Semaphore(3)

        async def bounded_verify(claim: str) -> ClaimResult:
            async with semaphore:
                try:
                    result = await verify_claim(claim, self.groq, self.search)
                    sources = [
                        SearchResult(
                            title=s.get("title", ""),
                            snippet=s.get("snippet", ""),
                            url=s.get("url", "")
                        )
                        for s in result.get("sources", [])
                    ]
                    return ClaimResult(
                        claim=claim,
                        verdict=Verdict(result.get("verdict", "Unverifiable")),
                        confidence=result.get("confidence", 0),
                        correct_fact=result.get("correct_fact", ""),
                        reasoning=result.get("reasoning", ""),
                        sources=sources
                    )
                except Exception as e:
                    logger.error("Failed to verify claim '%s': %s", claim[:60], e)
                    return ClaimResult(
                        claim=claim,
                        verdict=Verdict.UNVERIFIABLE,
                        confidence=0,
                        correct_fact="",
                        reasoning=f"Verification failed: {str(e)}",
                        sources=[]
                    )

        tasks = [bounded_verify(claim) for claim in claims]
        results = await asyncio.gather(*tasks)
        elapsed = round(time.time() - start_time, 2)

        return VerificationResponse(
            claims=list(results),
            total_claims=len(results),
            processing_time_seconds=elapsed,
            document_excerpt=document_excerpt[:300] if document_excerpt else None
        )
