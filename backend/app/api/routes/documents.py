"""FastAPI routes for Document Upload, AES-256-GCM Encryption, and Multi-Recipient PQC Envelopes (Member C / Phase 2+4 Integration)."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from pypdf import PdfWriter

from backend.api.contracts import (
    DocumentStatus,
    EncryptedEnvelope,
    KEMAlgorithm,
    KDFAlgorithm,
    SymmetricAlgorithm,
    sha3_256_hex,
)
from backend.app.crypto.encryption import encrypt_document, generate_cek
from backend.app.crypto.envelope import create_recipient_envelope
from backend.app.crypto.key_manager import KeyManager, KeyManagerError
from backend.storage.db import Database, get_db

router = APIRouter(prefix="/api/v1", tags=["Documents & Flow"])
key_manager = KeyManager()

# In-memory document storage fallback
_in_memory_documents: Dict[str, Dict[str, Any]] = {}


class DocumentSummary(BaseModel):
    document_id: str
    title: str
    recipient_ids: List[str]
    status: str
    ciphertext_size_bytes: int
    created_at: str
    envelopes_count: int


def _get_active_db() -> Database:
    try:
        return get_db()
    except Exception:
        db_path = Path("storage_data/node1.db")
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
        return Database(str(db_path), node_id="doc-service")


@router.get("/documents", response_model=List[DocumentSummary])
async def list_documents() -> List[DocumentSummary]:
    """List all encrypted documents and their recipient distribution envelopes."""
    db = _get_active_db()
    docs_map: Dict[str, Dict[str, Any]] = dict(_in_memory_documents)

    try:
        cur = db.conn.cursor()
        cur.execute("SELECT document_id, recipient_id, status, created_at FROM documents")
        for row in cur.fetchall():
            doc_id = row["document_id"]
            if doc_id not in docs_map:
                docs_map[doc_id] = {
                    "document_id": doc_id,
                    "title": f"Mission Directive {doc_id[:8]}",
                    "recipient_ids": [row["recipient_id"]],
                    "status": row["status"],
                    "ciphertext_size_bytes": 1024,
                    "created_at": row["created_at"],
                    "envelopes_count": 1,
                }
            else:
                if row["recipient_id"] not in docs_map[doc_id]["recipient_ids"]:
                    docs_map[doc_id]["recipient_ids"].append(row["recipient_id"])
                    docs_map[doc_id]["envelopes_count"] = len(docs_map[doc_id]["recipient_ids"])
    except Exception:
        pass

    return [DocumentSummary(**d) for d in docs_map.values()]


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_and_protect_document(
    title: str = Form("Naval Tactical Directive"),
    recipient_ids: str = Form(""),  # Comma-separated recipient IDs
    file: Optional[UploadFile] = File(None),
) -> Dict[str, Any]:
    """Upload a PDF, encrypt with a random 32-byte CEK (AES-256-GCM), and encapsulate with ML-KEM-768 for each selected recipient."""
    # 1. Acquire PDF bytes
    if file and file.filename:
        pdf_bytes = await file.read()
    else:
        # Generate synthetic PDF
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        stream = BytesIO()
        writer.write(stream)
        pdf_bytes = stream.getvalue()

    if not pdf_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document payload is empty.")

    # 2. Parse selected recipients (supports JSON list or comma-separated string)
    target_recipients = []
    if recipient_ids:
        raw_str = recipient_ids.strip()
        if raw_str.startswith("[") and raw_str.endswith("]"):
            try:
                parsed = json.loads(raw_str)
                if isinstance(parsed, list):
                    target_recipients = [str(r).strip() for r in parsed if str(r).strip()]
            except Exception:
                pass
        if not target_recipients:
            target_recipients = [r.strip().strip('"').strip("'") for r in raw_str.split(",") if r.strip()]
    if not target_recipients:
        # Default to first active recipient
        records = key_manager.list_public_records()
        active = [r.recipient_id for r in records if r.status == "active"]
        if not active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active recipients enrolled. Please enroll recipients first on the Recipients screen.",
            )
        target_recipients = [active[0]]

    # 3. Generate fresh random 32-byte CEK and encrypt payload (1-ciphertext)
    cek = generate_cek()
    encrypted_document_bytes = encrypt_document(pdf_bytes, cek)
    encrypted_doc_b64 = base64.b64encode(encrypted_document_bytes).decode("ascii")

    doc_id = f"doc-{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    db = _get_active_db()

    created_envelopes: List[Dict[str, Any]] = []

    # 4. Generate N recipient-specific envelopes (ML-KEM-768 + HKDF-SHA-256)
    for rec_id in target_recipients:
        try:
            pub_rec = key_manager.get_public_record(rec_id)
            if pub_rec.status != "active":
                continue
            kem_ek = base64.b64decode(pub_rec.kem_public_key_b64)
            envelope = create_recipient_envelope(
                cek=cek,
                recipient_id=rec_id,
                recipient_kem_public_key=kem_ek,
                document_id=doc_id,
                version_id="v1",
            )
            created_envelopes.append({
                "recipient_id": rec_id,
                "recipient_name": pub_rec.name,
                "envelope": envelope.to_dict(),
            })

            # Store in DB
            db.insert_document(
                document_id=doc_id,
                recipient_id=rec_id,
                status=DocumentStatus.ENCRYPTED,
                created_at=now_iso,
            )
            contract_envelope = EncryptedEnvelope(
                envelope_id=f"env-{doc_id}-{rec_id}",
                document_id=doc_id,
                encrypted_key=base64.b64encode(envelope.wrapped_cek).decode("ascii"),
                ciphertext=encrypted_doc_b64,
                token_digest=sha3_256_hex(b"pending-session-digest"),
                kem_algorithm=KEMAlgorithm.ML_KEM_768,
                symmetric_algorithm=SymmetricAlgorithm.AES_256_GCM,
                kdf_algorithm=KDFAlgorithm.HKDF_SHA_256,
            )
            db.insert_envelope(contract_envelope)
        except KeyManagerError:
            continue
        except Exception:
            pass

    if not created_envelopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create envelopes for selected recipients (invalid or inactive keys).",
        )

    doc_entry = {
        "document_id": doc_id,
        "title": title,
        "recipient_ids": target_recipients,
        "status": "ENCRYPTED",
        "ciphertext_size_bytes": len(encrypted_document_bytes),
        "created_at": now_iso,
        "envelopes_count": len(created_envelopes),
        "envelopes": created_envelopes,
        "encrypted_document_b64": encrypted_doc_b64,
    }
    _in_memory_documents[doc_id] = doc_entry

    return {
        "status": "success",
        "message": f"Document encrypted once with AES-256-GCM; {len(created_envelopes)} ML-KEM-768 envelopes created.",
        "document": doc_entry,
    }


@router.get("/documents/{document_id}")
async def get_document_details(document_id: str) -> Dict[str, Any]:
    """Retrieve metadata and envelopes for an encrypted document."""
    if document_id in _in_memory_documents:
        return _in_memory_documents[document_id]

    db = _get_active_db()
    if db.has_document(document_id):
        env = db.get_envelope(document_id)
        doc = db.get_document(document_id)
        return {
            "document_id": document_id,
            "title": f"Protected Mission Document {document_id}",
            "recipient_ids": [doc["recipient_id"]] if doc else [],
            "status": "ENCRYPTED",
            "created_at": doc["created_at"] if doc else datetime.now(timezone.utc).isoformat(),
            "envelopes_count": 1,
            "ciphertext_size_bytes": len(env.get("ciphertext", "")) if env else 0,
        }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")
