"""PDF validation/loading helpers placeholder."""

def validate_pdf(data: bytes) -> None:
    if not data.startswith(b"%PDF-"):
        raise ValueError("Input does not appear to be a PDF.")
