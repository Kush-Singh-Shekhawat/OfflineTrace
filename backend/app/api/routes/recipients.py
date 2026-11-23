"""FastAPI routes for Recipient and Key Management (Member A)."""

import base64
from typing import Any, Dict, Optional
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


@router.post("/recipient/tamper-test")
def simulate_tamper_attack(attack_type: str, recipient_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute live cryptographic tamper attacks and demonstrate fail-closed invariant."""
    records = key_manager.list_public_records()
    active_records = [r for r in records if r.status == "active"]
    if not active_records:
        rec = key_manager.create_recipient_keys(
            recipient_id="demo_target_officer",
            name="Capt. Demo Target",
            email="target@wesee.navy.in",
        )
    else:
        rec = active_records[0]
        if recipient_id:
            for r in records:
                if r.recipient_id == recipient_id:
                    rec = r
                    break

    target_id = rec.recipient_id
    ek_bytes = base64.b64decode(rec.kem_public_key_b64)
    doc_id = "doc-tamper-classified-brief"
    ver_id = "v1"

    cek = generate_cek()
    sample_pdf = b"%PDF-1.7 Top Secret Naval Movement Directive"
    ciphertext = encrypt_document(sample_pdf, cek)
    envelope = create_recipient_envelope(cek, target_id, ek_bytes, doc_id, ver_id)

    if attack_type == "ciphertext_bitflip":
        attack_name = "AES-256-GCM Ciphertext Bit-Flipping Attack"
        defense = "Galois/Counter Mode (GCM) GHASH 128-bit Authentication Tag"
        tampered = bytearray(ciphertext)
        tampered[len(tampered) // 2] ^= 0x01
        try:
            recipient_service.decrypt_and_sign_provenance(
                recipient_id=target_id,
                envelope=envelope,
                packed_encrypted_document=bytes(tampered),
                document_id=doc_id,
                version_id=ver_id,
            )
            return {"attack_type": attack_type, "detected": False, "plaintext_leaked_bytes": len(sample_pdf)}
        except Exception as exc:
            return {
                "attack_type": attack_type,
                "attack_name": attack_name,
                "defense_mechanism": defense,
                "detected": True,
                "exception_type": type(exc).__name__,
                "exception_detail": str(exc),
                "plaintext_leaked_bytes": 0,
                "security_verdict": "FAIL_CLOSED_CONFIRMED",
            }

    elif attack_type == "kem_tamper":
        attack_name = "ML-KEM-768 Ciphertext Corruption Attack"
        defense = "Module Lattice-based Key Encapsulation (FIPS 203) & AEAD Key Derivation"
        tampered_ct = bytearray(envelope.kem_ciphertext)
        tampered_ct[10] ^= 0xFF
        bad_envelope = RecipientEnvelope(
            recipient_id=envelope.recipient_id,
            recipient_fingerprint=envelope.recipient_fingerprint,
            kem_ciphertext=bytes(tampered_ct),
            wrapping_nonce=envelope.wrapping_nonce,
            wrapped_cek=envelope.wrapped_cek,
        )
        try:
            recipient_service.decrypt_and_sign_provenance(
                recipient_id=target_id,
                envelope=bad_envelope,
                packed_encrypted_document=ciphertext,
                document_id=doc_id,
                version_id=ver_id,
            )
            return {"attack_type": attack_type, "detected": False, "plaintext_leaked_bytes": len(sample_pdf)}
        except Exception as exc:
            return {
                "attack_type": attack_type,
                "attack_name": attack_name,
                "defense_mechanism": defense,
                "detected": True,
                "exception_type": type(exc).__name__,
                "exception_detail": str(exc),
                "plaintext_leaked_bytes": 0,
                "security_verdict": "FAIL_CLOSED_CONFIRMED",
            }

    elif attack_type == "impersonation":
        attack_name = "Unauthorized Recipient Key Impersonation Attack"
        defense = "Cryptographic Recipient Boundary & Asymmetric Key Encapsulation"
        rogue_id = "rogue_adversary_agent"
        try:
            key_manager.get_public_record(rogue_id)
        except Exception:
            key_manager.create_recipient_keys(
                recipient_id=rogue_id,
                name="Adversary Infiltrator",
                email="adversary@threat.net",
            )
        try:
            recipient_service.decrypt_and_sign_provenance(
                recipient_id=rogue_id,
                envelope=envelope,
                packed_encrypted_document=ciphertext,
                document_id=doc_id,
                version_id=ver_id,
            )
            return {"attack_type": attack_type, "detected": False, "plaintext_leaked_bytes": len(sample_pdf)}
        except Exception as exc:
            return {
                "attack_type": attack_type,
                "attack_name": attack_name,
                "defense_mechanism": defense,
                "detected": True,
                "exception_type": type(exc).__name__,
                "exception_detail": str(exc),
                "plaintext_leaked_bytes": 0,
                "security_verdict": "FAIL_CLOSED_CONFIRMED",
            }

    elif attack_type == "context_mismatch":
        attack_name = "HKDF-SHA-256 Context Binding Confusion Attack"
        defense = "RFC 5869 HKDF Domain Separation & Context Binding (doc_id + version_id + fingerprint)"
        try:
            recipient_service.decrypt_and_sign_provenance(
                recipient_id=target_id,
                envelope=envelope,
                packed_encrypted_document=ciphertext,
                document_id=doc_id,
                version_id="v2-substituted",
            )
            return {"attack_type": attack_type, "detected": False, "plaintext_leaked_bytes": len(sample_pdf)}
        except Exception as exc:
            return {
                "attack_type": attack_type,
                "attack_name": attack_name,
                "defense_mechanism": defense,
                "detected": True,
                "exception_type": type(exc).__name__,
                "exception_detail": str(exc),
                "plaintext_leaked_bytes": 0,
                "security_verdict": "FAIL_CLOSED_CONFIRMED",
            }

    elif attack_type == "revoked_credential":
        attack_name = "Revoked Recipient Credential Usage Attack"
        defense = "Local Keystore Access Control & Cryptographic Revocation Invariants"
        rev_id = "revoked_officer_sample"
        try:
            key_manager.create_recipient_keys(rev_id, "Dismissed Officer", "dismissed@navy.mil")
        except Exception:
            pass
        key_manager.revoke_recipient(rev_id)
        try:
            key_manager.load_private_keys(rev_id)
            return {"attack_type": attack_type, "detected": False, "plaintext_leaked_bytes": 100}
        except Exception as exc:
            return {
                "attack_type": attack_type,
                "attack_name": attack_name,
                "defense_mechanism": defense,
                "detected": True,
                "exception_type": type(exc).__name__,
                "exception_detail": str(exc),
                "plaintext_leaked_bytes": 0,
                "security_verdict": "FAIL_CLOSED_CONFIRMED",
            }

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown attack type '{attack_type}'")

