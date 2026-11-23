"""FastAPI routes for Recipient and Key Management (Member A)."""

import base64
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from ..schemas.recipient_schemas import (
    CreateRecipientRequest,
    DecryptActionRequest,
    DecryptActionResponse,
    RecipientEnvelopeSchema,
    RecipientListResponse,
    RecipientResponse,
)
from ...crypto.encryption import encrypt_document, generate_cek
from ...crypto.envelope import RecipientEnvelope, create_recipient_envelope
from ...crypto.key_manager import KeyManager, KeyManagerError
from ...services.recipient_crypto import RecipientCryptoService, RecipientServiceError

router = APIRouter(prefix="/api/v1", tags=["Recipients & Keys"])
key_manager = KeyManager()
recipient_service = RecipientCryptoService(key_manager=key_manager)


@router.get("/recipients", response_model=RecipientListResponse)
def list_recipients() -> RecipientListResponse:
    """List all registered recipient public records and key fingerprints."""
    records = key_manager.list_public_records()
    items = [RecipientResponse(**r.to_dict()) for r in records]
    return RecipientListResponse(recipients=items, total=len(items))


@router.post("/recipients", response_model=RecipientResponse, status_code=status.HTTP_201_CREATED)
def create_recipient(req: CreateRecipientRequest) -> RecipientResponse:
    """Enroll a new recipient and generate local ML-KEM-768 and ML-DSA-65 keypairs."""
    try:
        record = key_manager.create_recipient_keys(
            recipient_id=req.recipient_id,
            name=req.name,
            email=req.email,
            passphrase=req.passphrase,
        )
        return RecipientResponse(**record.to_dict())
    except KeyManagerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/recipients/{recipient_id}", response_model=RecipientResponse)
def get_recipient(recipient_id: str) -> RecipientResponse:
    """Retrieve public metadata and fingerprints for a specific recipient."""
    try:
        record = key_manager.get_public_record(recipient_id)
        return RecipientResponse(**record.to_dict())
    except KeyManagerError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/recipients/{recipient_id}/revoke", response_model=RecipientResponse)
def revoke_recipient(recipient_id: str) -> RecipientResponse:
    """Revoke recipient cryptographic keys."""
    try:
        updated = key_manager.revoke_recipient(recipient_id)
        return RecipientResponse(**updated.to_dict())
    except KeyManagerError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/recipients/{recipient_id}/rotate", response_model=RecipientResponse)
def rotate_recipient(recipient_id: str, passphrase: str = "offline-trace-default-passphrase") -> RecipientResponse:
    """Rotate recipient cryptographic keys, generating fresh ML-KEM and ML-DSA pairs."""
    try:
        updated = key_manager.rotate_recipient_keys(recipient_id, passphrase=passphrase)
        return RecipientResponse(**updated.to_dict())
    except KeyManagerError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/recipient/decrypt", response_model=DecryptActionResponse)
def decrypt_recipient_document(req: DecryptActionRequest) -> DecryptActionResponse:
    """Execute recipient-local decryption and provenance event signing."""
    try:
        envelope = RecipientEnvelope.from_dict(req.envelope.model_dump())
        ciphertext_bytes = base64.b64decode(req.encrypted_document_b64)

        result = recipient_service.decrypt_and_sign_provenance(
            recipient_id=req.recipient_id,
            envelope=envelope,
            packed_encrypted_document=ciphertext_bytes,
            document_id=req.document_id,
            version_id=req.version_id,
            watermark_token=req.watermark_token,
            passphrase=req.passphrase,
        )

        return DecryptActionResponse(
            success=True,
            document_id=req.document_id,
            version_id=req.version_id,
            canonical_event=result.canonical_event,
            signature_b64=base64.b64encode(result.signature).decode("ascii"),
            recipient_dsa_public_key_b64=base64.b64encode(result.recipient_dsa_public_key).decode("ascii"),
            recipient_dsa_fingerprint=result.recipient_dsa_fingerprint,
            token_digest=result.token_digest,
            decrypted_size_bytes=len(result.decrypted_document),
        )
    except RecipientServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Decryption error: {exc}") from exc


@router.post("/recipient/simulate-envelope")
def simulate_test_envelope(recipient_id: str, document_title: str = "Synthetic Mission Brief") -> Dict[str, Any]:
    """Demo helper: Generates a test encrypted payload and recipient envelope."""
    try:
        rec = key_manager.get_public_record(recipient_id)
        if rec.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Recipient is {rec.status}")

        ek_bytes = base64.b64decode(rec.kem_public_key_b64)
        doc_id = "doc-demo-fixture-01"
        ver_id = "v1"

        # Generate sample PDF payload and encrypt with random CEK
        sample_pdf_payload = f"%PDF-1.7 OfflineTrace Synthetic Document: {document_title}".encode("utf-8")
        cek = generate_cek()
        packed_doc = encrypt_document(sample_pdf_payload, cek)

        envelope = create_recipient_envelope(
            cek=cek,
            recipient_id=recipient_id,
            recipient_kem_public_key=ek_bytes,
            document_id=doc_id,
            version_id=ver_id,
        )

        return {
            "document_id": doc_id,
            "version_id": ver_id,
            "document_title": document_title,
            "encrypted_document_b64": base64.b64encode(packed_doc).decode("ascii"),
            "envelope": envelope.to_dict(),
        }
    except KeyManagerError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
