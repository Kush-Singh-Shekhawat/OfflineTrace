"""API route manifest – frozen contract skeletons.

Only route signatures and OpenAPI metadata are defined. All handlers raise
`HTTPException(status_code=501)` indicating the contract is frozen and not yet
implemented.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from typing import List

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

router = APIRouter(prefix="/api", tags=["OfflineTrace"])

# ---------------------------------------------------------------------------
# Recipients
# ---------------------------------------------------------------------------
@router.post("/recipients", response_model=RecipientResponse, status_code=status.HTTP_201_CREATED)
async def register_recipient(payload: RecipientRegisterRequest):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")

@router.get("/recipients", response_model=List[RecipientResponse])
async def list_recipients():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")

# ---------------------------------------------------------------------------
# Documents & Flow
# ---------------------------------------------------------------------------
@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")

@router.get("/documents", response_model=List[DocumentUploadResponse])
async def list_documents():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")

@router.post("/documents/{doc_id}/release", response_model=DecryptReleaseResponse)
async def release_document(doc_id: str, payload: DecryptReleaseRequest):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")

# ---------------------------------------------------------------------------
# Ledger & Nodes
# ---------------------------------------------------------------------------
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
# Forensics
# ---------------------------------------------------------------------------
@router.post("/investigate", response_model=InvestigationReport, status_code=status.HTTP_202_ACCEPTED)
async def investigate(payload: InvestigationRequest):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Frozen contract – not implemented")
