import json
import re
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

_FACTUAL_SIGNAL = re.compile(
    r'\b(\d{4}|\d+[\.,]\d+|\d+\s*%|\$\s*[\d,]+|million|billion|trillion|'
    r'founded|launched|released|acquired|declared|announced|increased|decreased|'
    r'grew|fell|rose|dropped|reached|exceeded|ranked|reported|published|discovered)\b',
    re.IGNORECASE
)
_FRAGMENT = re.compile(
    r'^[\d\s\.\,\%\$\-\:]+$|^\d{4}$|^\d+\s*%$|^\$[\d\s,\.]+$|'
    r'^(figure|table|ref|see|note|source|page|chapter|section)\b',
    re.IGNORECASE
)
_HAS_VERB = re.compile(
    r'\b(is|are|was|were|has|have|had|will|would|founded|launched|released|sold|'
    r'reached|grew|fell|increased|decreased|declared|announced|reported|published|'
    r'became|holds|owns|operates|replaced|acquired|exceeded|ranked|named|discovered)\b',
    re.IGNORECASE
)
_SENTENCE_SIGNAL = re.compile(
    r'(\d+\s*%|\$\s*[\d,]+|\d+\s*(million|billion|trillion)|founded\s+in|'
    r'launched\s+in|released\s+in|increased\s+by|decreased\s+by|grew\s+by|'
    r'fell\s+by|sold\s+\d+|reached\s+\d+|declared\s+\w+)',
    re.IGNORECASE
)
MIN_WORDS, MIN_CHARS = 6, 30


def is_valid_claim(text: str) -> bool:
    t = text.strip()
    if len(t) < MIN_CHARS or len(t.split()) < MIN_WORDS:
        return False
    if _FRAGMENT.match(t):
        return False
    if not _FACTUAL_SIGNAL.search(t):
        return False
    if not _HAS_VERB.search(t):
        return False
    return True


def filter_claims(claims: List[str]) -> List[str]:
    seen, valid = set(), []
    for c in claims:
        c = re.sub(r'^\d+[\.\)]\s*', '', c.strip().strip('"').strip("'")).strip()
        if not c or c.lower() in seen or not is_valid_claim(c):
            continue
        seen.add(c.lower())
        valid.append(c)
    return valid


def heuristic_claim_extraction(text: str, max_claims: int = 10) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    candidates = []
    for s in sentences:
        s = s.strip()
        if _SENTENCE_SIGNAL.search(s) and is_valid_claim(s):
            candidates.append(s)
        if len(candidates) >= max_claims:
            break
    return candidates


def safe_json_parse(text: str) -> Optional[Any]:
    text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for pattern in [r'\[[\s\S]*\]', r'\{[\s\S]*\}']:
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return None


def truncate_text(text: str, max_chars: int = 6000) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    if last_period > max_chars * 0.8:
        return truncated[:last_period + 1]
    return truncated + "..."


def clean_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\t+', ' ', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


def format_evidence(search_results: list) -> str:
    if not search_results:
        return "No search results found."
    parts = []
    for i, r in enumerate(search_results, 1):
        title = r.get('title', 'No title')
        snippet = r.get('body', r.get('snippet', 'No snippet'))
        url = r.get('href', r.get('url', ''))
        parts.append(f"[{i}] {title}\n{snippet}\nSource: {url}")
    return "\n\n".join(parts)
