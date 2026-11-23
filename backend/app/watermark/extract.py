
"""PDF watermark extraction with error correction."""
import base64
import binascii
from io import BytesIO

from pypdf import PdfReader

from .embed import WATERMARK_METADATA_KEY, WATERMARK_ENCODING_PREFIX
from .error_correction import decode_payload
from .pdf_processor import validate_pdf


def extract_watermark(pdf_bytes: bytes) -> str | None:
    """Extract and decode the OfflineTrace watermark token."""
    validate_pdf(pdf_bytes)

    reader = PdfReader(BytesIO(pdf_bytes))
    metadata = reader.metadata or {}
    token = metadata.get(WATERMARK_METADATA_KEY)

    if not isinstance(token, str) or not token.strip():
        return None

    # Support legacy PDFs containing plain-text tokens.
    if not token.startswith(WATERMARK_ENCODING_PREFIX):
        return token

    try:
        payload = base64.b64decode(
            token[len(WATERMARK_ENCODING_PREFIX):],
            validate=True,
        )
        decoded = decode_payload(payload).decode("utf-8")
    except (ValueError, UnicodeDecodeError, binascii.Error):
        return None

    return decoded if decoded.strip() else None
