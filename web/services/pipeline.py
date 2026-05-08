import asyncio
import logging
import sys

# ── Show logs in Streamlit terminal ──────────────────────────────────────────
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True
)

from core.config import get_groq_api_key, get_max_claims
from core.utils.pdf_extractor import extract_text_from_pdf
from core.utils.claim_detector import detect_claims
from core.services.groq_service import GroqService
from core.services.verification_service import VerificationService

logger = logging.getLogger(__name__)
MAX_FILE_SIZE_MB = 20


def run_verification(file_bytes: bytes, filename: str) -> dict:
    """Run full pipeline synchronously. Called directly by Streamlit."""

    if not filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are accepted.")
    if not get_groq_api_key():
        raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large ({size_mb:.1f}MB). Maximum is {MAX_FILE_SIZE_MB}MB.")

    # ── Step 1: Extract text ──────────────────────────────────────────────────
    logger.info("Starting PDF extraction...")
    text, page_count = extract_text_from_pdf(file_bytes)
    logger.info("Extracted %d chars from %d pages", len(text), page_count)

    # ── Step 2 + 3: Detect claims + Verify ───────────────────────────────────
    async def _pipeline():
        logger.info("Detecting claims...")
        groq = GroqService()
        claims = await detect_claims(text, get_max_claims(), groq)
        logger.info("Found %d claims. Starting verification...", len(claims))
        service = VerificationService()
        result = await service.verify_all(claims, document_excerpt=text[:300])
        logger.info("Verification complete in %.2fs", result.processing_time_seconds)
        return result

    # Use a fresh event loop — safe to call from a background thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_pipeline())
    finally:
        loop.close()

    return result.model_dump()
