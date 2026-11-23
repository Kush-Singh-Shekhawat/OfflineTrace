"""PDF watermark extraction."""

from io import BytesIO

from pypdf import PdfReader

from .embed import WATERMARK_METADATA_KEY
from .pdf_processor import validate_pdf


def extract_watermark(pdf_bytes: bytes) -> str | None:
    """Extract the OfflineTrace watermark token from PDF metadata."""

    validate_pdf(pdf_bytes)

    reader = PdfReader(BytesIO(pdf_bytes))
    metadata = reader.metadata or {}

    token = metadata.get(WATERMARK_METADATA_KEY)

    if not isinstance(token, str) or not token.strip():
        return None

    return token