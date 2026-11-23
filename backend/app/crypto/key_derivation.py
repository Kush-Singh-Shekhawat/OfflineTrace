"""Key derivation interfaces and implementation for OfflineTrace (Member A).

Uses HKDF-SHA-256 from cryptography.hazmat.primitives.kdf.hkdf.
Provides context-bound derivation to bind document ID, document version,
and recipient public-key fingerprint with domain separation.
"""

from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


DOMAIN_ENVELOPE = b"OfflineTrace|v1|recipient_cek_envelope"


def derive_key(
    secret: bytes,
    salt: Optional[bytes] = None,
    info: Optional[bytes] = None,
    length: int = 32,
) -> bytes:
    """Derive key material using HKDF-SHA-256.

    Args:
        secret: Input key material / shared secret.
        salt: Optional salt. If None, HKDF uses a zero-filled byte string per RFC 5869.
        info: Optional domain/context binding string.
        length: Number of bytes to derive (default 32 for AES-256).

    Returns:
        Derived key bytes of specified length.

    Raises:
        ValueError: If secret is empty or length <= 0.
    """
    if not secret:
        raise ValueError("Input secret must not be empty.")
    if length <= 0:
        raise ValueError("Derivation length must be positive.")

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    )
    return hkdf.derive(secret)


def derive_envelope_key(
    shared_secret: bytes,
    document_id: str,
    version_id: str,
    recipient_fingerprint: str,
    salt: Optional[bytes] = None,
    length: int = 32,
) -> bytes:
    """Derive context-bound wrapping key for recipient CEK envelope.

    Binds document ID, version ID, and recipient fingerprint using domain separation.

    Args:
        shared_secret: KEM shared secret or intermediate key material.
        document_id: Unique document identifier.
        version_id: Document version identifier.
        recipient_fingerprint: SHA3-256 or SHA-256 fingerprint of recipient's public key.
        salt: Optional salt.
        length: Desired key length in bytes (default 32).

    Returns:
        32-byte derived envelope key.

    Raises:
        ValueError: If any parameter is empty or invalid.
    """
    if not document_id or not document_id.strip():
        raise ValueError("document_id must not be empty.")
    if not version_id or not version_id.strip():
        raise ValueError("version_id must not be empty.")
    if not recipient_fingerprint or not recipient_fingerprint.strip():
        raise ValueError("recipient_fingerprint must not be empty.")

    context_info = (
        DOMAIN_ENVELOPE
        + b"|doc:"
        + document_id.strip().encode("utf-8")
        + b"|ver:"
        + version_id.strip().encode("utf-8")
        + b"|recip:"
        + recipient_fingerprint.strip().encode("utf-8")
    )

    return derive_key(
        secret=shared_secret,
        salt=salt,
        info=context_info,
        length=length,
    )
