import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.app.models.claim_schema import VerificationResponse, ErrorResponse
from api.app.services.verification_service import VerificationService
from api.app.utils.pdf_extractor import extract_text_from_pdf
from api.app.utils.claim_detector import detect_claims
from api.app.services.groq_service import GroqService
from api.app.config.settings import get_settings, Settings

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE_MB = 20


def get_verification_service() -> VerificationService:
    return VerificationService()


def _error(status: int, error: str, details: str = ""):
    return JSONResponse(
        status_code=status,
        content={"success": False, "error": error, "details": details}
    )


@router.post(
    "/verify",
    response_model=VerificationResponse,
    summary="Verify factual claims in a PDF",
)
async def verify_pdf(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    service: VerificationService = Depends(get_verification_service)
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return _error(400, "Only PDF files are accepted.", "Please upload a .pdf file.")

    if not settings.groq_api_key:
        return _error(503, "GROQ_API_KEY is not configured.", "Add your Groq API key to the .env file.")

    file_bytes = await file.read()

    if not file_bytes:
        return _error(400, "Uploaded file is empty.", "The file has no content.")

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return _error(413, f"File too large ({size_mb:.1f}MB).", f"Maximum allowed size is {MAX_FILE_SIZE_MB}MB.")

    # ── PDF text extraction ──────────────────────────────────────────────────
    try:
        text, page_count = extract_text_from_pdf(file_bytes)
    except ValueError as e:
        msg = str(e)
        if "scanned" in msg.lower() or "no extractable" in msg.lower() or "image" in msg.lower():
            return _error(422, "Scanned or image-based PDF detected.",
                          "This PDF has no extractable text. Please upload a text-based PDF.")
        return _error(422, "PDF extraction failed.", msg)
    except Exception as e:
        logger.error("PDF extraction error: %s", e)
        return _error(500, "Failed to read PDF.", "An unexpected error occurred during text extraction.")

    logger.info("Extracted %d chars from %d pages. Preview: %.200s", len(text), page_count, text)

    # ── Claim detection ────────────────────────────────────────────────────────
    try:
        groq = GroqService()
        claims = await detect_claims(text, settings.max_claims, groq)
    except ValueError as e:
        return _error(422, "No verifiable claims found.", str(e))
    except RuntimeError as e:
        return _error(503, "AI service unavailable.", str(e))
    except Exception as e:
        logger.error("Claim detection error: %s", e)
        return _error(500, "Claim detection failed.", str(e))

    logger.info("Detected %d claims, starting verification...", len(claims))

    # ── Verification ────────────────────────────────────────────────────────────
    try:
        result = await service.verify_all(claims, document_excerpt=text[:300])
    except Exception as e:
        logger.error("Verification pipeline error: %s", e)
        return _error(500, "Verification failed.", str(e))

    return result
