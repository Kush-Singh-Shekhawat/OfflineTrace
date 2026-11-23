"""OfflineTrace Cryptography Package (Member A)."""

from .encryption import (
    DecryptionError,
    EncryptedPayload,
    decrypt_document,
    decrypt_payload,
    encrypt_document,
    encrypt_payload,
    generate_cek,
)
from .envelope import (
    RecipientEnvelope,
    create_recipient_envelope,
    open_recipient_envelope,
)
from .kem import (
    KEMError,
    ML_KEM_768_CIPHERTEXT_BYTES,
    ML_KEM_768_DK_BYTES,
    ML_KEM_768_EK_BYTES,
    ML_KEM_768_SHARED_SECRET_BYTES,
    decapsulate_key,
    encapsulate_key,
    generate_keypair as generate_kem_keypair,
)
from .key_derivation import (
    derive_envelope_key,
    derive_key,
)
from .signatures import (
    ML_DSA_65_PK_BYTES,
    ML_DSA_65_SIG_BYTES,
    ML_DSA_65_SK_BYTES,
    SignatureError,
    compute_fingerprint,
    generate_signing_keypair,
    sign_message,
    verify_signature,
)

__all__ = [
    # Encryption
    "DecryptionError",
    "EncryptedPayload",
    "generate_cek",
    "encrypt_payload",
    "decrypt_payload",
    "encrypt_document",
    "decrypt_document",
    # Key derivation
    "derive_key",
    "derive_envelope_key",
    # KEM (ML-KEM-768)
    "KEMError",
    "ML_KEM_768_EK_BYTES",
    "ML_KEM_768_DK_BYTES",
    "ML_KEM_768_CIPHERTEXT_BYTES",
    "ML_KEM_768_SHARED_SECRET_BYTES",
    "generate_kem_keypair",
    "encapsulate_key",
    "decapsulate_key",
    # Signatures (ML-DSA-65)
    "SignatureError",
    "ML_DSA_65_PK_BYTES",
    "ML_DSA_65_SK_BYTES",
    "ML_DSA_65_SIG_BYTES",
    "compute_fingerprint",
    "generate_signing_keypair",
    "sign_message",
    "verify_signature",
    # Envelopes
    "RecipientEnvelope",
    "create_recipient_envelope",
    "open_recipient_envelope",
]
