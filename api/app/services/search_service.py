import logging
import asyncio
from typing import List, Dict, Any
from duckduckgo_search import DDGS
from api.app.config.settings import get_settings

logger = logging.getLogger(__name__)

TRUSTED_DOMAINS = [
    "gov", "edu", "who.int", "un.org", "worldbank.org",
    "reuters.com", "apnews.com", "bbc.com", "nature.com",
    "science.org", "ncbi.nlm.nih.gov", "statista.com"
]


class SearchService:
    """DuckDuckGo search service for claim evidence retrieval."""

    def __init__(self):
        self.max_results = get_settings().search_results_per_claim

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search DuckDuckGo for evidence related to a claim.
        Runs in a thread pool to avoid blocking the event loop.

        Returns:
            List of result dicts with title, body/snippet, href/url
        """
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._sync_search,
                query
            )
            return results
        except Exception as e:
            logger.warning("Search failed for query '%s': %s", query[:60], e)
            return []

    def _sync_search(self, query: str) -> List[Dict[str, Any]]:
        """Synchronous search call for executor."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    max_results=self.max_results + 2,
                    safesearch="moderate"
                ))
            prioritized = self._prioritize_trusted(results)
            return prioritized[:self.max_results]
        except Exception as e:
            logger.warning("DDGS search error: %s", e)
            return []

    def _prioritize_trusted(self, results: List[Dict]) -> List[Dict]:
        """Sort results to put trusted sources first."""
        trusted = []
        others = []
        for r in results:
            url = r.get("href", r.get("url", ""))
            if any(domain in url for domain in TRUSTED_DOMAINS):
                trusted.append(r)
            else:
                others.append(r)
        return trusted + others
