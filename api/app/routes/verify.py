import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
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


@router.post(
    "/verify",
    response_model=VerificationResponse,
    summary="Verify factual claims in a PDF",
    description="Upload a PDF, extract text, detect factual claims, and verify each against live web data."
)
async def verify_pdf(
    file: UploadFile = File(..., description="PDF file to fact-check"),
    settings: Settings = Depends(get_settings),
    service: VerificationService = Depends(get_verification_service)
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not configured. Please set it in the environment."
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f}MB). Maximum is {MAX_FILE_SIZE_MB}MB."
        )

    try:
        text, page_count = extract_text_from_pdf(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("PDF extraction error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF.")

    logger.info("Extracted text from %d pages (%d chars)", page_count, len(text))

    try:
        groq = GroqService()
        claims = await detect_claims(text, settings.max_claims, groq)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    logger.info("Detected %d claims, starting verification...", len(claims))

    try:
        result = await service.verify_all(claims, document_excerpt=text[:300])
    except Exception as e:
        logger.error("Verification pipeline error: %s", e)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

    return result
