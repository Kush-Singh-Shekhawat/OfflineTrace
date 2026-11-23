"""PDF watermark embedding using a custom PDF metadata field."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter

from .pdf_processor import validate_pdf


WATERMARK_METADATA_KEY = "/OfflineTraceWatermark"


def embed_watermark(pdf_bytes: bytes, token: str) -> bytes:
    """Embed a watermark token in PDF metadata and return the modified PDF."""

    validate_pdf(pdf_bytes)

    if not isinstance(token, str) or not token.strip():
        raise ValueError("Watermark token must not be empty.")

    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)

    metadata = dict(reader.metadata or {})
    metadata[WATERMARK_METADATA_KEY] = token
    writer.add_metadata(metadata)

    output = BytesIO()
    writer.write(output)

    return output.getvalue()