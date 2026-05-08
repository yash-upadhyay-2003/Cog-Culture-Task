import json
import re
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# ── Claim validation ──────────────────────────────────────────────────────────

# A claim must contain at least one of these to be considered factual
_FACTUAL_SIGNAL = re.compile(
    r'\b(\d{4}|\d+[\.,]\d+|\d+\s*%|\$\s*[\d,]+|'
    r'million|billion|trillion|thousand|'
    r'founded|launched|released|acquired|merged|declared|announced|'
    r'increased|decreased|grew|fell|rose|dropped|reached|exceeded|'
    r'ranked|named|awarded|reported|published|discovered|invented)\b',
    re.IGNORECASE
)

# Patterns that indicate a fragment, not a sentence
_FRAGMENT_PATTERNS = re.compile(
    r'^[\d\s\.\,\%\$\-\:]+$|'          # pure numbers/symbols
    r'^\d{4}$|'                          # standalone year
    r'^\d+\s*%$|'                        # standalone percentage
    r'^\$[\d\s,\.]+$|'                   # standalone currency
    r'^(figure|table|ref|see|note|source|page|chapter|section)\b',
    re.IGNORECASE
)

# Must have a verb to be a real sentence
_HAS_VERB = re.compile(
    r'\b(is|are|was|were|has|have|had|will|would|can|could|should|'
    r'founded|launched|released|sold|reached|grew|fell|increased|decreased|'
    r'declared|announced|reported|published|became|holds|owns|operates|'
    r'replaced|acquired|merged|exceeded|ranked|named|awarded|discovered)\b',
    re.IGNORECASE
)

MIN_WORDS = 6
MIN_CHARS = 30


def is_valid_claim(text: str) -> bool:
    """
    Returns True only if the text is a meaningful, complete factual claim.
    Rejects fragments, isolated numbers, headings, and table artifacts.
    """
    t = text.strip()

    # Length gates
    if len(t) < MIN_CHARS:
        return False
    if len(t.split()) < MIN_WORDS:
        return False

    # Reject pure fragments
    if _FRAGMENT_PATTERNS.match(t):
        return False

    # Must contain a factual signal
    if not _FACTUAL_SIGNAL.search(t):
        return False

    # Must contain a verb
    if not _HAS_VERB.search(t):
        return False

    return True


def filter_claims(claims: List[str]) -> List[str]:
    """Filter and deduplicate a list of raw extracted claims."""
    seen, valid = set(), []
    for c in claims:
        c = c.strip().strip('"').strip("'")
        # Remove leading numbering like "1." or "1)"
        c = re.sub(r'^\d+[\.\)]\s*', '', c).strip()
        if not c or c.lower() in seen:
            continue
        if not is_valid_claim(c):
            logger.debug("Rejected claim fragment: %s", c[:80])
            continue
        seen.add(c.lower())
        valid.append(c)
    return valid


# ── Heuristic fallback extraction ─────────────────────────────────────────────

# Patterns that signal a sentence worth extracting
_SENTENCE_SIGNAL = re.compile(
    r'(\d+\s*%|\$\s*[\d,]+|\d+\s*(million|billion|trillion)|'
    r'founded\s+in|launched\s+in|released\s+in|'
    r'increased\s+by|decreased\s+by|grew\s+by|fell\s+by|'
    r'ranked\s+#?\d+|sold\s+\d+|reached\s+\d+|'
    r'declared\s+\w+|announced\s+\w+)',
    re.IGNORECASE
)


def heuristic_claim_extraction(text: str, max_claims: int = 10) -> List[str]:
    """
    Fallback: extract complete sentences containing strong factual signals.
    Never extracts isolated numbers or fragments.
    """
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    candidates = []
    for s in sentences:
        s = s.strip()
        if _SENTENCE_SIGNAL.search(s) and is_valid_claim(s):
            candidates.append(s)
        if len(candidates) >= max_claims:
            break
    return candidates


# ── JSON parsing ──────────────────────────────────────────────────────────────

def safe_json_parse(text: str) -> Optional[Any]:
    """Parse JSON from LLM response, handling markdown and embedded text."""
    text = text.strip()
    # Strip markdown code fences
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON array or object
    for pattern in [r'\[[\s\S]*\]', r'\{[\s\S]*\}']:
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass

    logger.warning("Failed to parse JSON from: %s", text[:200])
    return None


# ── Text utilities ────────────────────────────────────────────────────────────

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
    # Remove page numbers and isolated numbers on their own line
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
