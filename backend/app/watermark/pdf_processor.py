"""PDF validation and loading helpers."""

from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


def validate_pdf(data: bytes) -> None:
    """Validate PDF structure and reject empty or encrypted documents."""

    if not data:
        raise ValueError("PDF file is empty.")

    if not data.startswith(b"%PDF-"):
        raise ValueError("Input does not appear to be a PDF.")

    try:
        reader = PdfReader(BytesIO(data), strict=False)

        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported.")

        if len(reader.pages) == 0:
            raise ValueError("PDF contains no pages.")

    except PdfReadError as exc:
        raise ValueError("PDF is corrupted or invalid.") from exc