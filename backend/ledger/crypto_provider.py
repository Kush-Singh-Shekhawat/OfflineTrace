"""Default cryptographic provider for validator signing and verification.

Implements the CryptoProvider protocol defined in backend.api.interfaces.
Uses SHA3-256 deterministic signatures as a clean interface stub so Member A
can plug in liboqs (ML-DSA-65 and ML-KEM-768) without modifying quorum or node logic.
"""

from __future__ import annotations

import base64
import hashlib
from typing import Optional

from ..api.contracts import (
    EncryptedEnvelope,
    LedgerProposal,
    ValidatorSignature,
    canonical_json_bytes,
    sha3_256_hex,
)
from ..api.interfaces import CryptoProvider


class DefaultCryptoProvider:
    """Deterministic cryptographic provider matching CryptoProvider protocol."""

    def __init__(self, secret_seed: str = "offlinetrace-val-seed") -> None:
        self.secret_seed = secret_seed

    def sign_validator_proposal(
        self, proposal: LedgerProposal, validator_id: str
    ) -> ValidatorSignature:
        """Create a deterministic validator signature over the proposal."""
        proposal_bytes = canonical_json_bytes(proposal.model_dump())
        digest = sha3_256_hex(proposal_bytes)
        token = f"ML-DSA-65:{validator_id}:{digest}:{self.secret_seed}".encode("utf-8")
        sig_bytes = hashlib.sha3_256(token).digest()
        sig_b64 = base64.b64encode(sig_bytes).decode("ascii")
        return ValidatorSignature(validator_id=validator_id, signature=sig_b64)

    def verify_mldsa_signature(
        self, data: bytes, signature: str, validator_id: str
    ) -> bool:
        """Verify an ML-DSA-65 signature for data and validator_id."""
        if not signature or not validator_id:
            return False
        # Calculate expected signature
        digest = sha3_256_hex(data)
        token = f"ML-DSA-65:{validator_id}:{digest}:{self.secret_seed}".encode("utf-8")
        expected_bytes = hashlib.sha3_256(token).digest()
        expected_b64 = base64.b64encode(expected_bytes).decode("ascii")
        return signature == expected_b64

    def wrap_cek_for_recipient(self, recipient_id: str, cek: bytes) -> str:
        """Stub for Member A ML-KEM-768 CEK wrapping."""
        token = f"ML-KEM-768:{recipient_id}".encode("utf-8") + cek
        wrapped = hashlib.sha3_256(token).digest()
        return base64.b64encode(wrapped).decode("ascii")

    def encrypt_document(self, plaintext: bytes) -> EncryptedEnvelope:
        """Stub for Member A AES-256-GCM encryption."""
        token_digest = sha3_256_hex(b"watermark-token-stub")
        encrypted_key = base64.b64encode(b"wrapped-cek-stub").decode("ascii")
        ciphertext = base64.b64encode(plaintext).decode("ascii")
        return EncryptedEnvelope(
            envelope_id="env-stub-001",
            document_id="doc-stub-001",
            encrypted_key=encrypted_key,
            ciphertext=ciphertext,
            token_digest=token_digest,
        )


# Global default instance
default_crypto_provider = DefaultCryptoProvider()
