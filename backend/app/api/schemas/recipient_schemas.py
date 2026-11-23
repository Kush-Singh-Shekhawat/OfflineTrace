"""Pydantic schemas for recipient and cryptographic key management (Member A)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateRecipientRequest(BaseModel):
    """Payload to register a recipient and generate post-quantum keypairs."""

    recipient_id: str = Field(..., description="Unique opaque recipient identifier", min_length=2)
    name: str = Field(..., description="Full name or unit title", min_length=2)
    email: str = Field(..., description="Official or organizational email address", min_length=3)
    passphrase: Optional[str] = Field(
        default="offline-trace-default-passphrase",
        description="Passphrase to protect recipient private keys at rest",
    )


class RecipientResponse(BaseModel):
    """Public recipient metadata. Never contains private keys or CEKs."""

    recipient_id: str
    name: str
    email: str
    status: str
    kem_algorithm: str
    dsa_algorithm: str
    kem_public_key_b64: str
    dsa_public_key_b64: str
    kem_fingerprint: str
    dsa_fingerprint: str
    created_at: str
    updated_at: str


class RecipientListResponse(BaseModel):
    """List of all registered recipient public records."""

    recipients: List[RecipientResponse]
    total: int


class RecipientEnvelopeSchema(BaseModel):
    """Base64-encoded KEM envelope for a single recipient."""

    recipient_id: str
    recipient_fingerprint: str
    kem_ciphertext: str
    wrapping_nonce: str
    wrapped_cek: str


class DecryptActionRequest(BaseModel):
    """Trigger recipient-local decryption and provenance signing."""

    recipient_id: str
    document_id: str
    version_id: str
    envelope: RecipientEnvelopeSchema
    encrypted_document_b64: str
    watermark_token: Optional[str] = None
    passphrase: Optional[str] = "offline-trace-default-passphrase"


class DecryptActionResponse(BaseModel):
    """Safe provenance result of a local decryption operation."""

    success: bool
    document_id: str
    version_id: str
    canonical_event: Dict[str, Any]
    signature_b64: str
    recipient_dsa_public_key_b64: str
    recipient_dsa_fingerprint: str
    token_digest: Optional[str]
    decrypted_size_bytes: int
