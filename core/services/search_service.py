import logging
import asyncio
from typing import List, Dict, Any
from urllib.parse import urlparse
from ddgs import DDGS
from core.config import get_search_results

logger = logging.getLogger(__name__)

_TIER1 = ["gov", "edu", "who.int", "un.org", "nature.com", "ncbi.nlm.nih.gov",
          "reuters.com", "apnews.com", "bbc.com", "bloomberg.com", "statista.com",
          "gartner.com", "mckinsey.com", "worldbank.org"]
_TIER2 = ["wikipedia.org", "techcrunch.com", "forbes.com", "cnbc.com",
          "theguardian.com", "wired.com", "nytimes.com"]


def _tier(url: str) -> int:
    for d in _TIER1:
        if d in url: return 0
    for d in _TIER2:
        if d in url: return 1
    return 2


class SearchService:
    def __init__(self):
        self.max_results = get_search_results()

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
                raw = list(ddgs.text(query, max_results=self.max_results + 4, safesearch="moderate"))
            deduped = self._deduplicate(raw)
            return sorted(deduped, key=lambda r: _tier(r.get("href", r.get("url", ""))))[:self.max_results]
        except Exception as e:
            logger.warning("DDGS error: %s", e)
            return []

    def _deduplicate(self, results: List[Dict]) -> List[Dict]:
        seen_domains, seen_urls, out = set(), set(), []
        for r in results:
            url = r.get("href", r.get("url", ""))
            try:
                domain = urlparse(url).netloc
            except Exception:
                domain = url
            if url in seen_urls or domain in seen_domains:
                continue
            seen_urls.add(url)
            seen_domains.add(domain)
            out.append(r)
        return out
