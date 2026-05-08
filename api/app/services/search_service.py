import logging
import asyncio
from typing import List, Dict, Any
from ddgs import DDGS
from api.app.config.settings import get_settings

logger = logging.getLogger(__name__)

# Tier 1 — highest credibility
_TIER1 = [
    "gov", "edu", "who.int", "un.org", "worldbank.org", "imf.org",
    "nasa.gov", "nih.gov", "ncbi.nlm.nih.gov", "nature.com", "science.org",
    "reuters.com", "apnews.com", "bbc.com", "bloomberg.com", "ft.com",
    "statista.com", "gartner.com", "mckinsey.com", "oxfordeconomics.com",
]
# Tier 2 — moderate credibility
_TIER2 = [
    "wikipedia.org", "techcrunch.com", "wired.com", "theguardian.com",
    "nytimes.com", "wsj.com", "forbes.com", "cnbc.com", "economist.com",
]


def _source_tier(url: str) -> int:
    for d in _TIER1:
        if d in url:
            return 0
    for d in _TIER2:
        if d in url:
            return 1
    return 2


class SearchService:
    def __init__(self):
        self.max_results = get_settings().search_results_per_claim

    async def search(self, query: str) -> List[Dict[str, Any]]:
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_search, query)
        except Exception as e:
            logger.warning("Search failed for '%s': %s", query[:60], e)
            return []

    def _sync_search(self, query: str) -> List[Dict[str, Any]]:
        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(
                    query,
                    max_results=self.max_results + 4,
                    safesearch="moderate"
                ))
            deduped = self._deduplicate(raw)
            ranked = sorted(deduped, key=lambda r: _source_tier(r.get("href", r.get("url", ""))))
            return ranked[:self.max_results]
        except Exception as e:
            logger.warning("DDGS search error: %s", e)
            return []

    def _deduplicate(self, results: List[Dict]) -> List[Dict]:
        seen_domains, seen_urls, out = set(), set(), []
        for r in results:
            url = r.get("href", r.get("url", ""))
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
            except Exception:
                domain = url
            if url in seen_urls or domain in seen_domains:
                continue
            seen_urls.add(url)
            seen_domains.add(domain)
            out.append(r)
        return out
