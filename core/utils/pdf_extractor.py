import fitz
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, int]:
    if not file_bytes:
        raise ValueError("Empty file provided.")
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Could not open PDF: {str(e)}")
    if doc.page_count == 0:
        raise ValueError("PDF has no pages.")
    pages_text = []
    total_pages = doc.page_count
    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text.strip():
            pages_text.append(text)
    doc.close()
    full_text = "\n\n".join(pages_text)
    if not full_text.strip():
        raise ValueError("PDF contains no extractable text. It may be scanned or image-based.")
    logger.info("Extracted %d characters from %d pages", len(full_text), total_pages)
    return full_text, len(pages_text)
