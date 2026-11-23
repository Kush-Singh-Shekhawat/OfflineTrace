"""Phase 4: Full Vertical Slice Workflow Orchestration (A + B + C).

Orchestrates the complete end-to-end provenance pipeline:
1. Recipient-local decrypt (ML-KEM-768 decapsulation + CEK unwrap + AES-256-GCM payload decrypt).
2. Unique session watermark generation & embedding (Member B).
3. Output hash computation (SHA3-256) over watermarked PDF.
4. Canonical event creation & recipient ML-DSA-65 signature (Member A).
5. 2-of-3 validator quorum proposal and commit (Member C).
6. Strict fail-closed release gate: No output is released if quorum fails!
7. Final release of the watermarked document and commit certificate.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, Optional
import uuid

from backend.api.contracts import (
    CommitCertificate,
    LedgerEvent,
    LedgerProposal,
    canonical_json_bytes,
    sha3_256_hex,
)
from backend.app.crypto.envelope import RecipientEnvelope, open_recipient_envelope
from backend.app.crypto.encryption import decrypt_document
from backend.app.crypto.key_manager import KeyManager
from backend.app.crypto.signatures import compute_fingerprint, sign_message
from backend.app.watermark.embed import embed_watermark
from backend.app.watermark.token_generator import generate_token
from backend.ledger.quorum import QuorumCoordinator, QuorumFailedError


class VerticalSliceError(Exception):
    """Raised when the vertical slice fails or quorum is not reached (fail-closed)."""
    pass


@dataclass(frozen=True)
class VerticalSliceResult:
    """Successful output of the vertical slice workflow.

    Only constructed and released AFTER 2-of-3 quorum commit is confirmed.
    """

    released_document: bytes
    commit_certificate: CommitCertificate
    session_watermark_token: str
    token_digest: str
    output_hash: str
    canonical_event: Dict[str, Any]
    recipient_signature_b64: str
    recipient_dsa_fingerprint: str


class RecipientWorkflowOrchestrator:
    """Orchestrates Phase 4 vertical slice integration across A, B, and C."""

    def __init__(
        self,
        key_manager: Optional[KeyManager] = None,
        quorum_coordinator: Optional[QuorumCoordinator] = None,
    ) -> None:
        self.key_manager = key_manager or KeyManager()
        self.quorum_coordinator = quorum_coordinator

    async def execute_recipient_decrypt_and_release(
        self,
        recipient_id: str,
        envelope: RecipientEnvelope,
        encrypted_document_bytes: bytes,
        document_id: str,
        version_id: str = "v1",
        passphrase: Optional[str] = "offline-trace-default-passphrase",
        forced_token: Optional[str] = None,
    ) -> VerticalSliceResult:
        """Execute the end-to-end vertical slice flow.

        Enforces:
        - Recipient must match envelope.
        - Plaintext CEK decrypted strictly locally.
        - Unique watermark token embedded into PDF.
        - Event canonicalized and signed with recipient ML-DSA-65 key.
        - Quorum commit of the proposal to 3 independent validator nodes.
        - FAIL-CLOSED: If quorum fails, no output document is returned!

        Returns:
            VerticalSliceResult containing released PDF and 2-of-3 commit certificate.

        Raises:
            VerticalSliceError: If decryption, watermark, or quorum consensus fails.
        """
        if envelope.recipient_id != recipient_id:
            raise VerticalSliceError(
                f"Recipient ID mismatch: expected '{recipient_id}', envelope has '{envelope.recipient_id}'."
            )

        # ------------------------------------------------------------------
        # Step 1: Member A - Recipient-local decryption (KEM + CEK + AES-GCM)
        # ------------------------------------------------------------------
        try:
            kem_dk, dsa_sk = self.key_manager.load_private_keys(recipient_id, passphrase)
            pub_record = self.key_manager.get_public_record(recipient_id)
        except Exception as exc:
            raise VerticalSliceError(f"Failed to load recipient private keys locally: {exc}") from exc

        try:
            cek = open_recipient_envelope(
                envelope=envelope,
                recipient_kem_private_key=kem_dk,
                document_id=document_id,
                version_id=version_id,
            )
            raw_pdf_bytes = decrypt_document(encrypted_document_bytes, cek)
        except Exception as exc:
            raise VerticalSliceError(f"Local decryption failed (tampered envelope or ciphertext): {exc}") from exc

        # ------------------------------------------------------------------
        # Step 2: Member B - Unique session watermark generation & embedding
        # ------------------------------------------------------------------
        session_token = forced_token or generate_token()
        token_digest = sha3_256_hex(session_token.encode("utf-8"))

        try:
            watermarked_pdf = embed_watermark(raw_pdf_bytes, session_token)
        except Exception as exc:
            raise VerticalSliceError(f"Watermark embedding failed: {exc}") from exc

        output_hash = sha3_256_hex(watermarked_pdf)

        # ------------------------------------------------------------------
        # Step 3: Member A - Canonical event creation & ML-DSA-65 signature
        # ------------------------------------------------------------------
        event_id = f"evt-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        canonical_event = {
            "action": "DOCUMENT_DECRYPTED",
            "document_id": document_id,
            "event_id": event_id,
            "output_hash": output_hash,
            "recipient_dsa_fingerprint": pub_record.dsa_fingerprint,
            "recipient_id": recipient_id,
            "timestamp": timestamp,
            "token_digest": token_digest,
            "version_id": version_id,
        }
        canonical_event_bytes = canonical_json_bytes(canonical_event)

        try:
            recipient_sig = sign_message(canonical_event_bytes, dsa_sk)
            recipient_sig_b64 = base64.b64encode(recipient_sig).decode("ascii")
        except Exception as exc:
            raise VerticalSliceError(f"Recipient event signing failed: {exc}") from exc

        # ------------------------------------------------------------------
        # Step 4: Member C - 2-of-3 Quorum consensus & commit
        # ------------------------------------------------------------------
        if not self.quorum_coordinator:
            raise VerticalSliceError("Quorum coordinator not configured (cannot commit to ledger).")

        proposal = LedgerProposal(
            proposal_id=f"prop-{event_id}",
            event=LedgerEvent(
                event_id=event_id,
                event_type="PROPOSAL",
                timestamp=timestamp,
                token_digest=token_digest,
                recipient_id=recipient_id,
                signature_b64=recipient_sig_b64,
                canonical_event=canonical_event,
            ),
            document_id=document_id,
            validator_signatures=[],
        )

        try:
            commit_cert = await self.quorum_coordinator.propose_and_commit(proposal)
        except QuorumFailedError as exc:
            # STRICT FAIL-CLOSED RELEASE BEHAVIOR:
            # If quorum fails, no output is ever released to the caller!
            raise VerticalSliceError(f"Consensus quorum failed: release blocked (fail-closed). Detail: {exc}") from exc
        except Exception as exc:
            raise VerticalSliceError(f"Unexpected ledger commit failure: {exc}") from exc

        # ------------------------------------------------------------------
        # Step 5: Quorum confirmed -> Release watermarked output!
        # ------------------------------------------------------------------
        return VerticalSliceResult(
            released_document=watermarked_pdf,
            commit_certificate=commit_cert,
            session_watermark_token=session_token,
            token_digest=token_digest,
            output_hash=output_hash,
            canonical_event=canonical_event,
            recipient_signature_b64=recipient_sig_b64,
            recipient_dsa_fingerprint=pub_record.dsa_fingerprint,
        )
