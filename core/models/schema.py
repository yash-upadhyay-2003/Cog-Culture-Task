from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Verdict(str, Enum):
    VERIFIED = "Verified"
    INACCURATE = "Inaccurate"
    MISLEADING = "Misleading"
    FALSE = "False"
    UNVERIFIABLE = "Unverifiable"


class SearchResult(BaseModel):
    title: str = ""
    snippet: str = ""
    url: str = ""


class ClaimResult(BaseModel):
    claim: str
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=100.0)
    correct_fact: str = ""
    reasoning: str = ""
    sources: List[SearchResult] = []


class VerificationResponse(BaseModel):
    claims: List[ClaimResult]
    total_claims: int
    processing_time_seconds: float
    document_excerpt: Optional[str] = None
    trust_score: Optional[float] = None
    summary: Optional[str] = None
