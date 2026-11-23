"""Typed interfaces for OfflineTrace backend contracts.

These protocols define the abstract contracts that concrete implementations must
fulfil. No implementation is provided – the bodies are ellipsis so that static
type‑checkers can enforce the signatures.
"""

from __future__ import annotations

from typing import Protocol

from .contracts import (
    RecipientRegisterRequest,
    RecipientResponse,
    DocumentUploadResponse,
    EncryptedEnvelope,
    DecryptReleaseRequest,
    DecryptReleaseResponse,
    LedgerProposal,
    CommitCertificate,
    LedgerBlock,
    InvestigationRequest,
    InvestigationReport,
    ValidatorSignature,
    LedgerEvent,
)

# ---------------------------------------------------------------------------
# Crypto Provider – Member A responsibilities
# ---------------------------------------------------------------------------
class CryptoProvider(Protocol):
    """Interface for cryptographic operations used by the service."""

    def encrypt_document(self, plaintext: bytes) -> EncryptedEnvelope: ...

    def wrap_cek_for_recipient(self, recipient_id: str, cek: bytes) -> str: ...

    def verify_mldsa_signature(self, data: bytes, signature: str, validator_id: str) -> bool: ...

    def sign_validator_proposal(self, proposal: LedgerProposal, validator_id: str) -> ValidatorSignature: ...

# ---------------------------------------------------------------------------
# Watermark Provider – Member B responsibilities
# ---------------------------------------------------------------------------
class WatermarkProvider(Protocol):
    """Interface for watermark handling and token‑digest computation."""

    def embed_watermark(self, document: bytes, token: str) -> bytes: ...

    def extract_watermark(self, document: bytes) -> str | None: ...

    def compute_token_digest(self, token: str) -> str: ...
