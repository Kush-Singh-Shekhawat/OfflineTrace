"""Recipient-local crypto service boundary for OfflineTrace (Member A).

Enforces:
- Browser and backend server NEVER receive or custody recipient private keys or plaintext CEKs.
- All KEM decapsulation, CEK unwrap, AES-GCM payload decryption, and ML-DSA-65
  canonical event signing occur strictly within this recipient-local component.
- Raw watermark tokens are never recorded on the ledger; only their SHA3-256 digest is stored.
- Any AEAD authentication or envelope tampering fails closed.
"""

import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Optional
import uuid

from ..crypto.encryption import decrypt_document
from ..crypto.envelope import RecipientEnvelope, open_recipient_envelope
from ..crypto.key_manager import KeyManager
from ..crypto.signatures import (
    compute_fingerprint,
    sign_message,
    verify_signature,
)


class RecipientServiceError(Exception):
    """Raised when recipient local decryption or event signing fails."""
    pass


@dataclass(frozen=True)
class DecryptionSessionResult:
    """Safe session result returned to recipient application.

    Contains NO private key material and NO plaintext CEK.
    """

    decrypted_document: bytes
    canonical_event: Dict[str, Any]
    canonical_event_bytes: bytes
    signature: bytes
    recipient_dsa_public_key: bytes
    recipient_dsa_fingerprint: str
    token_digest: Optional[str]

    def to_provenance_payload(self) -> Dict[str, Any]:
        """Format the cryptographic provenance data for validator submission."""
        return {
            "canonical_event": self.canonical_event,
            "signature_b64": base64.b64encode(self.signature).decode("ascii"),
            "recipient_dsa_public_key_b64": base64.b64encode(self.recipient_dsa_public_key).decode("ascii"),
            "recipient_dsa_fingerprint": self.recipient_dsa_fingerprint,
        }


class RecipientCryptoService:
    """Recipient-local service providing secure decryption and event provenance."""

    def __init__(self, key_manager: Optional[KeyManager] = None):
        self.key_manager = key_manager or KeyManager()

    def decrypt_and_sign_provenance(
        self,
        recipient_id: str,
        envelope: RecipientEnvelope,
        packed_encrypted_document: bytes,
        document_id: str,
        version_id: str,
        watermark_token: Optional[str] = None,
        passphrase: Optional[str] = "offline-trace-default-passphrase",
    ) -> DecryptionSessionResult:
        """Execute the recipient-local decryption and provenance signing workflow.

        1. Verifies envelope recipient matches the requesting recipient.
        2. Loads recipient's private keys (ML-KEM-768 dk, ML-DSA-65 sk) locally.
        3. Decapsulates and unwraps the 32-byte CEK locally in memory.
        4. Decrypts the common PDF payload using AES-256-GCM.
        5. Computes SHA3-256 token digest (never storing raw token in event).
        6. Constructs canonical decryption event and signs canonical bytes with ML-DSA-65.
        7. Returns the decrypted document and the signed provenance event.

        Raises:
            RecipientServiceError: If envelope, decryption, or signing fails.
        """
        if envelope.recipient_id != recipient_id:
            raise RecipientServiceError(
                f"Envelope recipient mismatch: expected '{recipient_id}', got '{envelope.recipient_id}'."
            )

        # 1. Load recipient local private keys
        try:
            kem_dk, dsa_sk = self.key_manager.load_private_keys(recipient_id, passphrase)
            pub_record = self.key_manager.get_public_record(recipient_id)
            dsa_pk = base64.b64decode(pub_record.dsa_public_key_b64)
        except Exception as exc:
            raise RecipientServiceError(f"Failed to load recipient keys: {exc}") from exc

        # 2. Local unwrap of CEK
        try:
            cek = open_recipient_envelope(
                envelope=envelope,
                recipient_kem_private_key=kem_dk,
                document_id=document_id,
                version_id=version_id,
            )
        except Exception as exc:
            raise RecipientServiceError(f"Envelope unwrap failed: {exc}") from exc

        # 3. Local decryption of common document
        try:
            decrypted_pdf = decrypt_document(packed_encrypted_document, cek)
        except Exception as exc:
            raise RecipientServiceError(f"Document decryption failed: {exc}") from exc

        # 4. Compute token digest if token provided (SHA3-256)
        token_digest: Optional[str] = None
        if watermark_token:
            token_digest = hashlib.sha3_256(watermark_token.encode("utf-8")).hexdigest()

        # 5. Canonical event representation (sorted keys, no extraneous whitespace)
        canonical_event = {
            "action": "DOCUMENT_DECRYPTED",
            "document_id": document_id,
            "event_id": f"evt-{uuid.uuid4().hex[:12]}",
            "recipient_dsa_fingerprint": pub_record.dsa_fingerprint,
            "recipient_id": recipient_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "token_digest": token_digest,
            "version_id": version_id,
        }
        canonical_event_bytes = json.dumps(
            canonical_event,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        # 6. Sign canonical event bytes using ML-DSA-65
        try:
            signature = sign_message(canonical_event_bytes, dsa_sk)
        except Exception as exc:
            raise RecipientServiceError(f"Provenance event signing failed: {exc}") from exc

        # Verify our own signature locally before returning
        if not verify_signature(dsa_pk, canonical_event_bytes, signature):
            raise RecipientServiceError("Local signature self-verification failed.")

        return DecryptionSessionResult(
            decrypted_document=decrypted_pdf,
            canonical_event=canonical_event,
            canonical_event_bytes=canonical_event_bytes,
            signature=signature,
            recipient_dsa_public_key=dsa_pk,
            recipient_dsa_fingerprint=pub_record.dsa_fingerprint,
            token_digest=token_digest,
        )
