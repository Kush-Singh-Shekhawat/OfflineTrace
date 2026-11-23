"""ML-KEM-768 (FIPS 203) Key Encapsulation Mechanism for OfflineTrace (Member A).

Standard parameters for ML-KEM-768:
- Encapsulation Key (public key, ek): 1,184 bytes
- Decapsulation Key (private key, dk): 2,400 bytes
- Ciphertext (c): 1,088 bytes
- Shared Secret (K): 32 bytes
"""

from typing import Tuple
from kyber_py.ml_kem import ML_KEM_768

# Exact NIST FIPS 203 parameter lengths for ML-KEM-768
ML_KEM_768_EK_BYTES = 1184
ML_KEM_768_DK_BYTES = 2400
ML_KEM_768_CIPHERTEXT_BYTES = 1088
ML_KEM_768_SHARED_SECRET_BYTES = 32


class KEMError(Exception):
    """Raised when key encapsulation or decapsulation fails."""
    pass


def generate_keypair() -> Tuple[bytes, bytes]:
    """Generate an ML-KEM-768 key pair.

    Returns:
        Tuple of (encapsulation_key, decapsulation_key) where:
        - encapsulation_key is 1,184 bytes (public)
        - decapsulation_key is 2,400 bytes (private)
    """
    ek, dk = ML_KEM_768.keygen()
    return ek, dk


# Alias for explicit clarity alongside signature key generation
generate_kem_keypair = generate_keypair


def encapsulate_key(public_key: bytes) -> Tuple[bytes, bytes]:
    """Encapsulate a random shared secret against an ML-KEM-768 public key.

    Args:
        public_key: 1,184-byte encapsulation key (ek).

    Returns:
        Tuple of (shared_secret, ciphertext) where:
        - shared_secret is 32 bytes
        - ciphertext is 1,088 bytes

    Raises:
        ValueError: If public_key length is invalid.
        KEMError: If encapsulation fails.
    """
    if len(public_key) != ML_KEM_768_EK_BYTES:
        raise ValueError(
            f"Invalid ML-KEM-768 public key length: expected {ML_KEM_768_EK_BYTES} bytes, got {len(public_key)}."
        )

    try:
        shared_secret, ciphertext = ML_KEM_768.encaps(public_key)
        return shared_secret, ciphertext
    except Exception as exc:
        raise KEMError(f"ML-KEM-768 encapsulation failed: {exc}") from exc


def decapsulate_key(private_key: bytes, ciphertext: bytes) -> bytes:
    """Decapsulate an ML-KEM-768 ciphertext using recipient private key.

    Args:
        private_key: 2,400-byte decapsulation key (dk).
        ciphertext: 1,088-byte KEM ciphertext.

    Returns:
        32-byte recovered shared secret.

    Raises:
        ValueError: If private_key or ciphertext length is invalid.
        KEMError: If decapsulation fails.
    """
    if len(private_key) != ML_KEM_768_DK_BYTES:
        raise ValueError(
            f"Invalid ML-KEM-768 private key length: expected {ML_KEM_768_DK_BYTES} bytes, got {len(private_key)}."
        )
    if len(ciphertext) != ML_KEM_768_CIPHERTEXT_BYTES:
        raise ValueError(
            f"Invalid ML-KEM-768 ciphertext length: expected {ML_KEM_768_CIPHERTEXT_BYTES} bytes, got {len(ciphertext)}."
        )

    try:
        shared_secret = ML_KEM_768.decaps(private_key, ciphertext)
        return shared_secret
    except Exception as exc:
        raise KEMError(f"ML-KEM-768 decapsulation failed: {exc}") from exc
