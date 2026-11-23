
"""Unit tests for OfflineTrace PDF watermarking."""

import base64
from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from app.watermark.embed import (
    embed_watermark,
    WATERMARK_METADATA_KEY,
    WATERMARK_ENCODING_PREFIX,
)
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


def test_watermark_recovers_from_corrupted_metadata_byte():
    pdf = create_test_pdf()
    token = "OFFLINETRACE-RECOVERY-123"

    protected_pdf = embed_watermark(pdf, token)

    reader = PdfReader(BytesIO(protected_pdf))
    metadata = dict(reader.metadata or {})

    stored = metadata[WATERMARK_METADATA_KEY]
    encoded = bytearray(
        base64.b64decode(stored[len(WATERMARK_ENCODING_PREFIX):])
    )

    # Corrupt one byte in the first repeated group.
    encoded[0] ^= 0xFF

    metadata[WATERMARK_METADATA_KEY] = (
        WATERMARK_ENCODING_PREFIX
        + base64.b64encode(encoded).decode("ascii")
    )

    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.add_metadata(metadata)

    output = BytesIO()
    writer.write(output)

    assert extract_watermark(output.getvalue()) == token


def test_extract_legacy_plain_text_watermark():
    token = "OFFLINETRACE-LEGACY-123"

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_metadata({WATERMARK_METADATA_KEY: token})

    output = BytesIO()
    writer.write(output)

    assert extract_watermark(output.getvalue()) == token
