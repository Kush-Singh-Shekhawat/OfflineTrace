"""ML-DSA-65 (FIPS 204) Digital Signatures and Fingerprinting for OfflineTrace (Member A).

Standard parameters for ML-DSA-65 (Security Category 3):
- Public Key (pk): 1,952 bytes
- Private Signing Key (sk): 4,032 bytes
- Signature: 3,309 bytes
- Fingerprint: SHA3-256 hex digest of public key bytes
"""

import hashlib
from typing import Tuple
from dilithium_py.ml_dsa import ML_DSA_65

# Exact NIST FIPS 204 parameter lengths for ML-DSA-65
ML_DSA_65_PK_BYTES = 1952
ML_DSA_65_SK_BYTES = 4032
ML_DSA_65_SIG_BYTES = 3309


class SignatureError(Exception):
    """Raised when signature creation or validation encounters an error."""
    pass


def compute_fingerprint(public_key: bytes) -> str:
    """Compute the canonical SHA3-256 fingerprint for a public key.

    Returns:
        64-character lowercase hex digest.
    """
    if not public_key:
        raise ValueError("Public key must not be empty.")
    return hashlib.sha3_256(public_key).hexdigest()


def generate_signing_keypair() -> Tuple[bytes, bytes]:
    """Generate an ML-DSA-65 signing key pair.

    Returns:
        Tuple of (public_key, private_key) where:
        - public_key is 1,952 bytes
        - private_key is 4,032 bytes
    """
    pk, sk = ML_DSA_65.keygen()
    return pk, sk


def sign_message(message: bytes, private_key: bytes) -> bytes:
    """Sign canonical message bytes using ML-DSA-65.

    Args:
        message: Raw message bytes to sign.
        private_key: 4,032-byte ML-DSA-65 private signing key (sk).

    Returns:
        3,309-byte signature.

    Raises:
        ValueError: If private_key length is invalid.
        SignatureError: If signing operation fails.
    """
    if len(private_key) != ML_DSA_65_SK_BYTES:
        raise ValueError(
            f"Invalid ML-DSA-65 private key length: expected {ML_DSA_65_SK_BYTES} bytes, got {len(private_key)}."
        )

    try:
        signature = ML_DSA_65.sign(private_key, message)
        return signature
    except Exception as exc:
        raise SignatureError(f"ML-DSA-65 signing failed: {exc}") from exc


def verify_signature(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Verify an ML-DSA-65 signature against message and public key.

    Args:
        public_key: 1,952-byte ML-DSA-65 verification key (pk).
        message: Raw message bytes that were signed.
        signature: 3,309-byte signature.

    Returns:
        True if signature is valid, False otherwise.
    """
    if len(public_key) != ML_DSA_65_PK_BYTES:
        return False
    if len(signature) != ML_DSA_65_SIG_BYTES:
        return False

    try:
        return bool(ML_DSA_65.verify(public_key, message, signature))
    except Exception:
        return False
