"""OfflineTrace API Contracts (Phase 1 - Freeze Contracts)

Defines canonical data structures, helper utilities and enums used across the service.
All models are strict Pydantic v2 definitions with exact field names.
"""

from __future__ import annotations

import json
import hashlib
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

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

# Algorithm identifiers (forced to specific values)
class KEMAlgorithm(str, Enum):
    ML_KEM_768 = "ML-KEM-768"

class SignatureAlgorithm(str, Enum):
    ML_DSA_65 = "ML-DSA-65"

class SymmetricAlgorithm(str, Enum):
    AES_256_GCM = "AES-256-GCM"

class KDFAlgorithm(str, Enum):
    HKDF_SHA_256 = "HKDF-SHA-256"

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
    document_id: str = Field(..., description="ID of the document this envelope protects")
    encrypted_key: str = Field(..., description="Base64‑encoded CEK wrapped for the recipient")
    ciphertext: str = Field(..., description="Base64‑encoded encrypted document payload")
    token_digest: str = Field(..., description="SHA3‑256 hex digest of the watermark token")
    kem_algorithm: KEMAlgorithm = Field(default=KEMAlgorithm.ML_KEM_768, description="Key encapsulation algorithm")
    symmetric_algorithm: SymmetricAlgorithm = Field(default=SymmetricAlgorithm.AES_256_GCM, description="Symmetric encryption algorithm")
    kdf_algorithm: KDFAlgorithm = Field(default=KDFAlgorithm.HKDF_SHA_256, description="Key derivation function algorithm")

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
    model_config = {"extra": "allow"}
    event_id: str
    event_type: Literal["PROPOSAL", "COMMIT", "REJECTION"]
    timestamp: str
    token_digest: Optional[str] = Field(default=None, description="SHA3-256 digest of watermark token")
    recipient_id: Optional[str] = Field(default=None, description="Recipient identifier")

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
    block_hash: str = Field(default="", description="SHA3-256 hash of the block committed")

class LedgerBlock(BaseModel):
    block_id: str
    previous_hash: str = Field(..., description="SHA3‑256 of previous block")
    proposals: List[LedgerProposal]
    merkle_root: str = Field(..., description="SHA3‑256 merkle root of proposals")
    status: LedgerStatus = LedgerStatus.PENDING

class NodeHealthResponse(BaseModel):
    node_id: str
    status: Literal["HEALTHY", "UNHEALTHY", "UNKNOWN"]
    uptime_seconds: int = Field(default=0, description="Node uptime in seconds")
    last_heartbeat: str = Field(default="", description="ISO-8601 UTC timestamp")
    chain_height: int = Field(default=0, description="Current height of the committed block chain")
    latest_hash: str = Field(default="", description="SHA3-256 hash of the latest committed block")

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


# Eagerly rebuild models to resolve forward annotations
LedgerEvent.model_rebuild()
LedgerProposal.model_rebuild()
LedgerBlock.model_rebuild()
InvestigationReport.model_rebuild()

