import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

NUMBER_PATTERN = re.compile(r'[\d,]+\.?\d*%?')


def apply_rule_based_checks(claim: str, evidence_text: str) -> Dict[str, Any]:
    """
    Apply lightweight rule-based checks before LLM verification.
    Returns hints that can adjust confidence.
    """
    hints = {
        "numbers_match": None,
        "date_conflict": None,
        "confidence_adjustment": 0.0
    }

    claim_numbers = set(NUMBER_PATTERN.findall(claim))
    evidence_numbers = set(NUMBER_PATTERN.findall(evidence_text))

    if claim_numbers and evidence_numbers:
        overlap = claim_numbers & evidence_numbers
        if overlap:
            hints["numbers_match"] = True
            hints["confidence_adjustment"] = 5.0
        elif claim_numbers and not (claim_numbers & evidence_numbers):
            hints["numbers_match"] = False
            hints["confidence_adjustment"] = -5.0

    return hints


def adjust_confidence(base_confidence: float, hints: Dict[str, Any]) -> float:
    """Apply rule-based adjustments to LLM confidence score."""
    adjusted = base_confidence + hints.get("confidence_adjustment", 0.0)
    return max(0.0, min(100.0, adjusted))
