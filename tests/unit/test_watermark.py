
"""Unit tests for OfflineTrace PDF watermarking."""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.watermark.embed import embed_watermark
from app.watermark.extract import extract_watermark
from app.watermark.pdf_processor import validate_pdf


def create_test_pdf() -> bytes:
    """Create a minimal PDF for testing."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_watermark_round_trip():
    pdf = create_test_pdf()
    token = "OFFLINETRACE-TEST-123"

    protected_pdf = embed_watermark(pdf, token)

    assert extract_watermark(protected_pdf) == token


def test_extract_missing_watermark():
    pdf = create_test_pdf()

    assert extract_watermark(pdf) is None


def test_reject_invalid_pdf():
    with pytest.raises(ValueError):
        validate_pdf(b"This is not a PDF")


def test_reject_empty_pdf():
    with pytest.raises(ValueError):
        validate_pdf(b"")


def test_reject_empty_watermark_token():
    pdf = create_test_pdf()

    with pytest.raises(ValueError):
        embed_watermark(pdf, "")
