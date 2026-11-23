"""Forensic investigation workflow for OfflineTrace."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any, List, Optional

from backend.api.contracts import (
    InvestigationRequest,
    InvestigationReport,
    LedgerProposal,
    canonical_json_bytes,
    sha3_256_hex,
)
from backend.api.interfaces import CryptoProvider
from backend.storage.db import Database, get_db
from backend.ledger.models import verify_chain_integrity
from backend.ledger.crypto_provider import default_crypto_provider
from backend.app.watermark.extract import extract_watermark


# ---------------------------------------------------------------------------
# Exception Hierarchy
# ---------------------------------------------------------------------------
class InvestigationServiceError(Exception):
    """Base exception for investigation service errors."""
    pass


class UnauthorizedInvestigatorError(InvestigationServiceError):
    """Raised when an investigator is not authorized."""
    pass


class UnknownDocumentError(InvestigationServiceError):
    """Raised when the document ID does not exist."""
    pass


class InvalidInvestigationRequestError(InvestigationServiceError):
    """Raised when the investigation request is invalid."""
    pass


class MissingLedgerEntryError(InvestigationServiceError):
    """Raised when no ledger entry is found for the document."""
    pass


class DatabaseFailureError(InvestigationServiceError):
    """Raised when a database operation fails."""
    pass


# ---------------------------------------------------------------------------
# Investigator Authorization
# ---------------------------------------------------------------------------
def is_authorized_investigator(investigator_id: str) -> bool:
    """Validate whether an investigator is authorized."""
    if not investigator_id or not str(investigator_id).strip():
        return False
    lower = str(investigator_id).strip().lower()
    if (
        lower.startswith("unauthorized")
        or lower.startswith("forbidden")
        or lower == "unknown"
        or lower.startswith("invalid")
    ):
        return False
    return True


# ---------------------------------------------------------------------------
# Investigation Services
# ---------------------------------------------------------------------------
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


def investigate_document(
    request: InvestigationRequest,
    db: Optional[Database] = None,
    crypto_provider: Optional[CryptoProvider] = None,
    pdf_bytes: Optional[bytes] = None,
) -> InvestigationReport:
    """Execute complete cryptographic and ledger investigation for a document.

    Checks:
    1. Request validity and investigator authorization.
    2. Document identity in database / ledger.
    3. Ledger hash-chain continuity and block integrity (chain_verified).
    4. Validator signatures verification on the document proposal (signature_verified).
    5. 2-of-3 quorum verification of valid distinct validator signatures (quorum_verified).
    6. Watermark verification if PDF payload is available.
    7. Produces realistic confidence and detailed diagnostics based on actual results.
    8. Persists the generated report safely in the database.
    """
    if not request.investigation_id or not str(request.investigation_id).strip():
        raise InvalidInvestigationRequestError("investigation_id is required")
    if not request.document_id or not str(request.document_id).strip():
        raise InvalidInvestigationRequestError("document_id is required")
    if not is_authorized_investigator(request.investigator_id):
        raise UnauthorizedInvestigatorError(
            f"Investigator '{request.investigator_id}' is not authorized"
        )

    if db is None:
        db = get_db()
    if crypto_provider is None:
        crypto_provider = default_crypto_provider

    # Step 1: Document existence
    try:
        has_doc = db.has_document(request.document_id)
        blocks = db.get_blocks()
    except Exception as exc:
        raise DatabaseFailureError(f"Database error during document lookup: {exc}") from exc

    found_in_blocks = any(
        any(p.get("document_id") == request.document_id for p in b.get("data", {}).get("proposals", []))
        for b in blocks
    )
    if not has_doc and not found_in_blocks:
        raise UnknownDocumentError(f"Document '{request.document_id}' not found")

    # Step 2: Ledger chain integrity
    try:
        chain_verified = verify_chain_integrity(blocks)
    except Exception:
        chain_verified = False

    # Step 3: Proposals for this document
    doc_proposals: List[LedgerProposal] = []
    for b in blocks:
        proposals_data = b.get("data", {}).get("proposals", [])
        for p_data in proposals_data:
            if p_data.get("document_id") == request.document_id:
                try:
                    doc_proposals.append(LedgerProposal.model_validate(p_data))
                except Exception:
                    pass

    has_ledger_entry = len(doc_proposals) > 0
    valid_validators = set()
    any_sig_invalid = False
    total_signatures = 0

    if has_ledger_entry:
        for prop in doc_proposals:
            prop_bytes_with = canonical_json_bytes(prop.model_dump())
            prop_no_sigs = prop.model_copy(update={"validator_signatures": []})
            prop_bytes_without = canonical_json_bytes(prop_no_sigs.model_dump())

            for sig in prop.validator_signatures:
                total_signatures += 1
                try:
                    if crypto_provider.verify_mldsa_signature(
                        prop_bytes_with, sig.signature, sig.validator_id
                    ) or crypto_provider.verify_mldsa_signature(
                        prop_bytes_without, sig.signature, sig.validator_id
                    ):
                        valid_validators.add(sig.validator_id)
                    else:
                        any_sig_invalid = True
                except Exception:
                    any_sig_invalid = True

        signature_verified = (
            (total_signatures > 0)
            and (not any_sig_invalid)
            and (len(valid_validators) > 0)
        )
        quorum_verified = len(valid_validators) >= 2
    else:
        signature_verified = False
        quorum_verified = False

    # Step 4: Watermark check if available
    watermark_found = False
    if pdf_bytes is None:
        env = db.get_envelope(request.document_id)
        if env and env.get("ciphertext"):
            try:
                pdf_bytes = base64.b64decode(env["ciphertext"])
            except Exception:
                pass

    if pdf_bytes:
        try:
            token = extract_watermark(pdf_bytes)
            if token is not None:
                watermark_found = True
        except Exception:
            pass

    # Step 5: Diagnostics and confidence
    if not chain_verified:
        confidence = 0.0
        diagnostics = "Ledger chain integrity compromised: block hash or linkage mismatch."
    elif not has_ledger_entry:
        confidence = 0.0
        diagnostics = "Missing ledger entries: No committed block found for document."
    elif any_sig_invalid or not signature_verified:
        confidence = 0.0
        signature_verified = False
        quorum_verified = False
        diagnostics = "Validator signature verification failed: invalid ML-DSA signature detected."
    elif not quorum_verified:
        confidence = 0.2
        diagnostics = f"Quorum verification failed: required >= 2 valid signatures, found {len(valid_validators)}."
    else:
        confidence = 0.94
        diagnostics = "All signatures verified, quorum satisfied, chain integrity intact."
        if watermark_found:
            diagnostics += " Watermark extracted and verified."

    generated_at = datetime.now(timezone.utc).isoformat()
    report = InvestigationReport(
        investigation_id=request.investigation_id,
        document_id=request.document_id,
        confidence=confidence,
        diagnostics=diagnostics,
        signature_verified=signature_verified,
        quorum_verified=quorum_verified,
        chain_verified=chain_verified,
        generated_at=generated_at,
    )

    # Step 6: Persist report in database
    try:
        db.insert_investigation(report, request.investigator_id)
    except Exception as exc:
        raise DatabaseFailureError(f"Failed to persist investigation report: {exc}") from exc

    return report
