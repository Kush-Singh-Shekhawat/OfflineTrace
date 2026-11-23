"""AES-256-GCM payload encryption and decryption for OfflineTrace (Member A).

Enforces:
- 32-byte random CEK (Content Encryption Key).
- 12-byte unique nonce per encryption.
- Authenticated encryption with associated data (AEAD).
- Fail-closed behavior: Any authentication or integrity failure raises DecryptionError
  and never returns partial or unauthenticated plaintext.
"""

from dataclasses import dataclass
import os
from typing import Optional
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CEK_LENGTH_BYTES = 32
GCM_NONCE_LENGTH_BYTES = 12
GCM_TAG_LENGTH_BYTES = 16


class DecryptionError(Exception):
    """Raised when ciphertext authentication or decryption fails."""
    pass


@dataclass(frozen=True)
class EncryptedPayload:
    """Structured representation of an AES-GCM encrypted payload."""

    ciphertext: bytes
    nonce: bytes
    tag: bytes
    associated_data: Optional[bytes] = None

    def serialize(self) -> bytes:
        """Serializes payload as nonce (12B) + tag (16B) + ciphertext."""
        return self.nonce + self.tag + self.ciphertext

    @classmethod
    def deserialize(
        cls, packed_data: bytes, associated_data: Optional[bytes] = None
    ) -> "EncryptedPayload":
        """Deserializes nonce (12B) + tag (16B) + ciphertext into EncryptedPayload."""
        header_len = GCM_NONCE_LENGTH_BYTES + GCM_TAG_LENGTH_BYTES
        if len(packed_data) < header_len:
            raise DecryptionError(
                f"Data too short: expected at least {header_len} bytes, got {len(packed_data)}."
            )
        nonce = packed_data[:GCM_NONCE_LENGTH_BYTES]
        tag = packed_data[GCM_NONCE_LENGTH_BYTES:header_len]
        ciphertext = packed_data[header_len:]
        return cls(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            associated_data=associated_data,
        )


def generate_cek() -> bytes:
    """Generate a cryptographically secure 32-byte (256-bit) Content Encryption Key."""
    return os.urandom(CEK_LENGTH_BYTES)


def encrypt_payload(
    plaintext: bytes,
    key: bytes,
    associated_data: Optional[bytes] = None,
    nonce: Optional[bytes] = None,
) -> EncryptedPayload:
    """Encrypt plaintext using AES-256-GCM.

    Args:
        plaintext: Raw data bytes to encrypt.
        key: 32-byte AES key.
        associated_data: Optional authenticated data (AAD) bound to the ciphertext.
        nonce: Optional 12-byte nonce (if None, a fresh random nonce is generated).

    Returns:
        EncryptedPayload with separated ciphertext, nonce, and tag.

    Raises:
        ValueError: If key or nonce lengths do not meet AES-256-GCM requirements.
    """
    if len(key) != CEK_LENGTH_BYTES:
        raise ValueError(
            f"Invalid key length: expected {CEK_LENGTH_BYTES} bytes (AES-256), got {len(key)}."
        )

    if nonce is None:
        nonce = os.urandom(GCM_NONCE_LENGTH_BYTES)
    elif len(nonce) != GCM_NONCE_LENGTH_BYTES:
        raise ValueError(
            f"Invalid nonce length: expected {GCM_NONCE_LENGTH_BYTES} bytes, got {len(nonce)}."
        )

    aesgcm = AESGCM(key)
    # cryptography's AESGCM.encrypt returns ciphertext + 16-byte tag
    ct_with_tag = aesgcm.encrypt(nonce, plaintext, associated_data)
    ciphertext = ct_with_tag[:-GCM_TAG_LENGTH_BYTES]
    tag = ct_with_tag[-GCM_TAG_LENGTH_BYTES:]

    return EncryptedPayload(
        ciphertext=ciphertext,
        nonce=nonce,
        tag=tag,
        associated_data=associated_data,
    )


def decrypt_payload(
    payload: EncryptedPayload,
    key: bytes,
) -> bytes:
    """Decrypt an EncryptedPayload using AES-256-GCM.

    Fails closed: Any authentication tag mismatch or corruption raises DecryptionError.

    Args:
        payload: EncryptedPayload containing ciphertext, nonce, tag, and optional AAD.
        key: 32-byte AES key.

    Returns:
        Decrypted plaintext bytes.

    Raises:
        ValueError: If key is not 32 bytes.
        DecryptionError: If tag authentication fails or data is corrupted.
    """
    if len(key) != CEK_LENGTH_BYTES:
        raise ValueError(
            f"Invalid key length: expected {CEK_LENGTH_BYTES} bytes (AES-256), got {len(key)}."
        )

    if len(payload.nonce) != GCM_NONCE_LENGTH_BYTES:
        raise DecryptionError(
            f"Invalid nonce length in payload: expected {GCM_NONCE_LENGTH_BYTES}, got {len(payload.nonce)}."
        )

    if len(payload.tag) != GCM_TAG_LENGTH_BYTES:
        raise DecryptionError(
            f"Invalid tag length in payload: expected {GCM_TAG_LENGTH_BYTES}, got {len(payload.tag)}."
        )

    aesgcm = AESGCM(key)
    # Reassemble ciphertext + tag for cryptography's AESGCM.decrypt
    ct_with_tag = payload.ciphertext + payload.tag
    try:
        return aesgcm.decrypt(payload.nonce, ct_with_tag, payload.associated_data)
    except InvalidTag as exc:
        raise DecryptionError("AEAD verification failed: tag mismatch or corrupted ciphertext.") from exc


def encrypt_document(
    data: bytes,
    key: bytes,
    associated_data: Optional[bytes] = None,
) -> bytes:
    """Convenience function: Encrypts document bytes and returns packed binary.

    Packed format: nonce (12 bytes) + tag (16 bytes) + ciphertext.
    """
    payload = encrypt_payload(data, key, associated_data=associated_data)
    return payload.serialize()


def decrypt_document(
    packed_data: bytes,
    key: bytes,
    associated_data: Optional[bytes] = None,
) -> bytes:
    """Convenience function: Unpacks binary (nonce + tag + ciphertext) and decrypts.

    Fails closed on any authentication error.
    """
    payload = EncryptedPayload.deserialize(packed_data, associated_data=associated_data)
    return decrypt_payload(payload, key)
