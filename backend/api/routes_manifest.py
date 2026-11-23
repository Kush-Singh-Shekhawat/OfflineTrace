"""API route manifest – frozen contract skeletons.

Defines route signatures and OpenAPI metadata matching API_CONTRACTS.md.
All unimplemented handlers raise `HTTPException(status_code=501)`
indicating the contract is frozen and pending module implementation.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

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
)

# Standard API router with /api/v1 prefix per API_CONTRACTS.md
router = APIRouter(prefix="/api/v1", tags=["OfflineTrace"])

# Legacy /api alias router for backward-compatibility with Phase 1 tests
legacy_router = APIRouter(prefix="/api", include_in_schema=False)


# ---------------------------------------------------------------------------
# Health & Dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard/summary", response_model=Dict[str, Any])
async def dashboard_summary():
    return {
        "documents_total": 0,
        "recipients_total": 0,
        "investigations_total": 0,
        "ledger_status": "not_configured",
    }


# ---------------------------------------------------------------------------
# Recipients
# ---------------------------------------------------------------------------
@router.post("/recipients", response_model=RecipientResponse, status_code=status.HTTP_201_CREATED)
async def register_recipient(payload: RecipientRegisterRequest):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.get("/recipients", response_model=List[RecipientResponse])
async def list_recipients():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.post("/recipients/{recipient_id}/keys", status_code=status.HTTP_201_CREATED)
async def register_recipient_key(recipient_id: str, payload: Dict[str, Any]):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


# ---------------------------------------------------------------------------
# Documents & Flow
# ---------------------------------------------------------------------------
@router.post("/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED, include_in_schema=False)
async def upload_document_alias():
    return await upload_document()


@router.get("/documents", response_model=List[DocumentUploadResponse])
async def list_documents():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.get("/documents/{document_id}", response_model=DocumentUploadResponse)
async def get_document_metadata(document_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.post("/documents/{doc_id}/release", response_model=DecryptReleaseResponse)
async def release_document(doc_id: str, payload: DecryptReleaseRequest):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


# ---------------------------------------------------------------------------
# Ledger & Nodes
# ---------------------------------------------------------------------------
@router.get("/ledger/status", response_model=Dict[str, Any])
async def ledger_status():
    return {"status": "not_configured", "message": "Ledger implementation is pending."}


@router.get("/ledger/entries", response_model=List[LedgerBlock])
async def ledger_entries():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.post("/ledger/verify", response_model=Dict[str, Any])
async def ledger_verify():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.post("/ledger/propose", response_model=LedgerProposal, status_code=status.HTTP_202_ACCEPTED)
async def propose_ledger(payload: LedgerProposal):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.get("/ledger/chain", response_model=List[LedgerBlock])
async def get_ledger_chain():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.get("/nodes/health", response_model=List[dict])
async def get_node_health():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


# ---------------------------------------------------------------------------
# Forensics / Investigations
# ---------------------------------------------------------------------------
@router.post("/investigations", response_model=InvestigationReport, status_code=status.HTTP_202_ACCEPTED)
async def investigate(payload: InvestigationRequest):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


@router.get("/investigations/{investigation_id}", response_model=InvestigationReport)
async def get_investigation(investigation_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")


# ---------------------------------------------------------------------------
# Legacy Route Bindings (pointing to /api/*)
# ---------------------------------------------------------------------------
@legacy_router.post("/recipients", response_model=RecipientResponse, status_code=status.HTTP_201_CREATED)
async def legacy_register_recipient(payload: RecipientRegisterRequest):
    return await register_recipient(payload)


@legacy_router.get("/recipients", response_model=List[RecipientResponse])
async def legacy_list_recipients():
    return await list_recipients()


@legacy_router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def legacy_upload_document():
    return await upload_document()


@legacy_router.get("/documents", response_model=List[DocumentUploadResponse])
async def legacy_list_documents():
    return await list_documents()


@legacy_router.post("/documents/{doc_id}/release", response_model=DecryptReleaseResponse)
async def legacy_release_document(doc_id: str, payload: DecryptReleaseRequest):
    return await release_document(doc_id, payload)


@legacy_router.post("/ledger/propose", response_model=LedgerProposal, status_code=status.HTTP_202_ACCEPTED)
async def legacy_propose_ledger(payload: LedgerProposal):
    return await propose_ledger(payload)


@legacy_router.get("/ledger/chain", response_model=List[LedgerBlock])
async def legacy_get_ledger_chain():
    return await get_ledger_chain()


@legacy_router.get("/nodes/health", response_model=List[dict])
async def legacy_get_node_health():
    return await get_node_health()


@legacy_router.post("/investigate", response_model=InvestigationReport, status_code=status.HTTP_202_ACCEPTED)
async def legacy_investigate(payload: InvestigationRequest):
    return await investigate(payload)
