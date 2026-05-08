import json
import re
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def safe_json_parse(text: str) -> Optional[Any]:
    """Attempt to parse JSON, trying to extract it if embedded in other text."""
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to parse JSON from: %s", text[:200])
    return None


def truncate_text(text: str, max_chars: int = 4000) -> str:
    """Truncate text to max_chars, trying to break at sentence boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    if last_period > max_chars * 0.8:
        return truncated[:last_period + 1]
    return truncated + "..."


def clean_text(text: str) -> str:
    """Clean extracted text by removing excessive whitespace."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\t+', ' ', text)
    return text.strip()


def format_evidence(search_results: list) -> str:
    """Format search results into a readable evidence block."""
    if not search_results:
        return "No search results found."
    parts = []
    for i, result in enumerate(search_results, 1):
        title = result.get('title', 'No title')
        snippet = result.get('body', result.get('snippet', 'No snippet'))
        url = result.get('href', result.get('url', ''))
        parts.append(f"[{i}] {title}\n{snippet}\nSource: {url}")
    return "\n\n".join(parts)
