"""Per-recipient CEK envelope implementation for OfflineTrace (Member A).

Enforces:
- 1 shared AES-256-GCM ciphertext per document payload.
- N recipient-specific envelopes.
- Each envelope encapsulates the 32-byte CEK using ML-KEM-768 and HKDF-SHA-256,
  binding document ID, version ID, and recipient fingerprint.
- Recipient-local unwrapping fails closed if the envelope or context has been tampered with.
"""

from dataclasses import asdict, dataclass
import base64
from typing import Any, Dict
from .encryption import (
    DecryptionError,
    EncryptedPayload,
    decrypt_payload,
    encrypt_payload,
)
from .kem import (
    decapsulate_key,
    encapsulate_key,
)
from .key_derivation import derive_envelope_key
from .signatures import compute_fingerprint


@dataclass(frozen=True)
class RecipientEnvelope:
    """Structure of an individual recipient's CEK envelope."""

    recipient_id: str
    recipient_fingerprint: str
    kem_ciphertext: bytes
    wrapping_nonce: bytes
    wrapped_cek: bytes  # Encrypted CEK + 16B GCM tag

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary with base64 encoded bytes."""
        return {
            "recipient_id": self.recipient_id,
            "recipient_fingerprint": self.recipient_fingerprint,
            "kem_ciphertext": base64.b64encode(self.kem_ciphertext).decode("ascii"),
            "wrapping_nonce": base64.b64encode(self.wrapping_nonce).decode("ascii"),
            "wrapped_cek": base64.b64encode(self.wrapped_cek).decode("ascii"),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecipientEnvelope":
        """Deserialize from dictionary with base64 encoded bytes."""
        return cls(
            recipient_id=data["recipient_id"],
            recipient_fingerprint=data["recipient_fingerprint"],
            kem_ciphertext=base64.b64decode(data["kem_ciphertext"]),
            wrapping_nonce=base64.b64decode(data["wrapping_nonce"]),
            wrapped_cek=base64.b64decode(data["wrapped_cek"]),
        )


def create_recipient_envelope(
    cek: bytes,
    recipient_id: str,
    recipient_kem_public_key: bytes,
    document_id: str,
    version_id: str,
) -> RecipientEnvelope:
    """Create a context-bound CEK envelope for a single recipient.

    1. Encapsulate random shared secret against recipient's ML-KEM-768 public key.
    2. Derive envelope wrapping key using HKDF-SHA-256 bound to doc_id, ver_id, and recipient fingerprint.
    3. Encrypt the 32-byte CEK using AES-256-GCM.

    Args:
        cek: 32-byte Content Encryption Key.
        recipient_id: Opaque identifier of the recipient.
        recipient_kem_public_key: Recipient's 1,184-byte ML-KEM-768 public key.
        document_id: Document ID.
        version_id: Document version ID.

    Returns:
        RecipientEnvelope containing KEM ciphertext, wrapping nonce, and wrapped CEK.
    """
    if len(cek) != 32:
        raise ValueError(f"CEK must be 32 bytes, got {len(cek)}.")

    fingerprint = compute_fingerprint(recipient_kem_public_key)

    # 1. KEM Encapsulation
    shared_secret, kem_ciphertext = encapsulate_key(recipient_kem_public_key)

    # 2. Context-bound key derivation
    wrapping_key = derive_envelope_key(
        shared_secret=shared_secret,
        document_id=document_id,
        version_id=version_id,
        recipient_fingerprint=fingerprint,
    )

    # 3. AEAD encryption of the CEK
    context_aad = f"{document_id}|{version_id}|{fingerprint}".encode("utf-8")
    encrypted_cek_payload = encrypt_payload(
        plaintext=cek,
        key=wrapping_key,
        associated_data=context_aad,
    )

    # wrapped_cek stores ciphertext + tag
    wrapped_cek = encrypted_cek_payload.ciphertext + encrypted_cek_payload.tag

    return RecipientEnvelope(
        recipient_id=recipient_id,
        recipient_fingerprint=fingerprint,
        kem_ciphertext=kem_ciphertext,
        wrapping_nonce=encrypted_cek_payload.nonce,
        wrapped_cek=wrapped_cek,
    )


def open_recipient_envelope(
    envelope: RecipientEnvelope,
    recipient_kem_private_key: bytes,
    document_id: str,
    version_id: str,
) -> bytes:
    """Open an envelope and recover the CEK on the recipient's local device.

    1. Decapsulate shared secret using recipient's ML-KEM-768 private key.
    2. Derive wrapping key with identical context binding.
    3. Authenticate and decrypt wrapped CEK with AES-256-GCM.

    Fails closed if the envelope, key, or context do not match.

    Returns:
        32-byte recovered CEK.

    Raises:
        DecryptionError: If decapsulation, unwrap, or authentication fails.
    """
    try:
        shared_secret = decapsulate_key(
            private_key=recipient_kem_private_key,
            ciphertext=envelope.kem_ciphertext,
        )
    except Exception as exc:
        raise DecryptionError("KEM decapsulation failed.") from exc

    wrapping_key = derive_envelope_key(
        shared_secret=shared_secret,
        document_id=document_id,
        version_id=version_id,
        recipient_fingerprint=envelope.recipient_fingerprint,
    )

    context_aad = f"{document_id}|{version_id}|{envelope.recipient_fingerprint}".encode("utf-8")
    
    # Split wrapped_cek into ciphertext and 16-byte tag
    if len(envelope.wrapped_cek) < 16:
        raise DecryptionError("Wrapped CEK payload is corrupted or truncated.")

    ciphertext = envelope.wrapped_cek[:-16]
    tag = envelope.wrapped_cek[-16:]

    payload = EncryptedPayload(
        ciphertext=ciphertext,
        nonce=envelope.wrapping_nonce,
        tag=tag,
        associated_data=context_aad,
    )

    return decrypt_payload(payload, wrapping_key)
