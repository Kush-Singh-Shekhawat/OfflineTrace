
"""PDF watermark embedding with error-corrected metadata."""
import base64
from io import BytesIO

from pypdf import PdfReader, PdfWriter

from .error_correction import encode_payload
from .pdf_processor import validate_pdf

WATERMARK_METADATA_KEY = "/OfflineTraceWatermark"
WATERMARK_ENCODING_PREFIX = "OTFEC1:"


def embed_watermark(pdf_bytes: bytes, token: str) -> bytes:
    """Embed an error-corrected watermark token in PDF metadata."""
    validate_pdf(pdf_bytes)

    if not isinstance(token, str) or not token.strip():
        raise ValueError("Watermark token must not be empty.")

    encoded = encode_payload(token.encode("utf-8"))
    stored_token = WATERMARK_ENCODING_PREFIX + base64.b64encode(
        encoded
    ).decode("ascii")

    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)

    metadata = dict(reader.metadata or {})
    metadata[WATERMARK_METADATA_KEY] = stored_token
    writer.add_metadata(metadata)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()
