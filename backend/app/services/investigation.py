
"""Forensic investigation workflow for OfflineTrace."""

from datetime import datetime, timezone

from api.contracts import InvestigationRequest, InvestigationReport
from app.watermark.extract import extract_watermark


def investigate_pdf(
    request: InvestigationRequest,
    pdf_bytes: bytes,
) -> InvestigationReport:
    """Inspect a PDF for an OfflineTrace watermark and produce a report."""

    generated_at = datetime.now(timezone.utc).isoformat()

    try:
        token = extract_watermark(pdf_bytes)

        if token is None:
            return InvestigationReport(
                investigation_id=request.investigation_id,
                document_id=request.document_id,
                confidence=0.0,
                diagnostics=(
                    "No OfflineTrace watermark metadata was found. "
                    "Document attribution is inconclusive."
                ),
                signature_verified=False,
                quorum_verified=False,
                chain_verified=False,
                generated_at=generated_at,
            )

        return InvestigationReport(
            investigation_id=request.investigation_id,
            document_id=request.document_id,
            confidence=0.25,
            diagnostics=(
                "OfflineTrace watermark metadata was recovered. "
                "This is preliminary evidence only: PDF metadata can be "
                "modified or removed. Signature, quorum, and ledger "
                "verification have not been performed."
            ),
            signature_verified=False,
            quorum_verified=False,
            chain_verified=False,
            generated_at=generated_at,
        )

    except (ValueError, TypeError) as exc:
        return InvestigationReport(
            investigation_id=request.investigation_id,
            document_id=request.document_id,
            confidence=0.0,
            diagnostics=f"PDF investigation failed: {exc}",
            signature_verified=False,
            quorum_verified=False,
            chain_verified=False,
            generated_at=generated_at,
        )
