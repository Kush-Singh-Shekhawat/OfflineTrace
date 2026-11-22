"""OfflineTrace API Contracts (Phase 1 - Freeze Contracts)

Defines canonical data structures, helper utilities and enums used across the service.
All models are strict Pydantic v2 definitions with exact field names.
"""

from __future__ import annotations

import json
import hashlib
from enum import Enum
from typing import List, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------
SCHEMA_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class KeyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    ENCRYPTED = "ENCRYPTED"
    RELEASED = "RELEASED"
    DECRYPTED = "DECRYPTED"

class VerificationStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    LIKELY_MATCH = "LIKELY_MATCH"
    INCONCLUSIVE = "INCONCLUSIVE"
    NO_MATCH = "NO_MATCH"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"

class LedgerStatus(str, Enum):
    PENDING = "PENDING"
    COMMITTED = "COMMITTED"
    REJECTED_QUORUM = "REJECTED_QUORUM"
    DIVERGENCE_DETECTED = "DIVERGENCE_DETECTED"

class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BAD_GATEWAY = "BAD_GATEWAY"

# ---------------------------------------------------------------------------
# Helper utilities – canonical JSON and SHA3‑256 digests
# ---------------------------------------------------------------------------
def canonical_json_bytes(data: dict) -> bytes:
    """Return a canonical JSON representation of *data* as UTF‑8 bytes.

    The representation uses deterministic key ordering and the most compact
    separators (no whitespace) so that the same logical payload always hashes to
    the same value.
    """
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha3_256_hex(data: bytes) -> str:
    """Calculate a SHA3‑256 digest and return the lower‑case hexadecimal string."""
    return hashlib.sha3_256(data).hexdigest()

# ---------------------------------------------------------------------------
# Pydantic models – exact field names as required by the contract
# ---------------------------------------------------------------------------
class RecipientRegisterRequest(BaseModel):
    recipient_id: str = Field(..., description="Globally unique identifier for the recipient")
    public_key: str = Field(..., description="Base64‑encoded RSA or EC public key")
    key_status: KeyStatus = Field(..., description="Initial status of the recipient's key")

class RecipientResponse(BaseModel):
    recipient_id: str
    key_status: KeyStatus
    created_at: str = Field(..., description="ISO‑8601 timestamp of registration")

class EncryptedEnvelope(BaseModel):
    envelope_id: str
    encrypted_key: str = Field(..., description="Base64‑encoded CEK wrapped for the recipient")
    ciphertext: str = Field(..., description="Base64‑encoded encrypted document payload")
    token_digest: str = Field(..., description="SHA3‑256 hex digest of the watermark token")

class DocumentUploadResponse(BaseModel):
    document_id: str
    envelope: EncryptedEnvelope
    status: DocumentStatus = DocumentStatus.UPLOADED

class DecryptReleaseRequest(BaseModel):
    document_id: str
    recipient_id: str
    token_digest: str = Field(..., description="Digest of the token supplied by the requester")

class DecryptReleaseResponse(BaseModel):
    document_id: str
    plaintext_hash: str = Field(..., description="SHA3‑256 hex of the plaintext payload")
    verification_status: VerificationStatus

class ValidatorSignature(BaseModel):
    validator_id: str
    signature: str = Field(..., description="Base64‑encoded ML‑DSA signature")

class LedgerEvent(BaseModel):
    event_id: str
    event_type: Literal["PROPOSAL", "COMMIT", "REJECTION"]
    timestamp: str

class LedgerProposal(BaseModel):
    proposal_id: str
    event: LedgerEvent
    document_id: str
    validator_signatures: List[ValidatorSignature]

class CommitCertificate(BaseModel):
    certificate_id: str
    proposal_id: str
    signatures: List[ValidatorSignature]
    quorum: int = Field(..., ge=1, description="Number of signatures required for acceptance")

class LedgerBlock(BaseModel):
    block_id: str
    previous_hash: str = Field(..., description="SHA3‑256 of previous block")
    proposals: List[LedgerProposal]
    merkle_root: str = Field(..., description="SHA3‑256 merkle root of proposals")
    status: LedgerStatus = LedgerStatus.PENDING

class NodeHealthResponse(BaseModel):
    node_id: str
    status: Literal["HEALTHY", "UNHEALTHY", "UNKNOWN"]
    uptime_seconds: int
    last_heartbeat: str

class InvestigationRequest(BaseModel):
    investigation_id: str
    document_id: str
    investigator_id: str
    requested_at: str

class InvestigationReport(BaseModel):
    investigation_id: str
    document_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    diagnostics: str
    signature_verified: bool
    quorum_verified: bool
    chain_verified: bool
    generated_at: str
