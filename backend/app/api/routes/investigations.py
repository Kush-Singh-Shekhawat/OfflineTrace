"""FastAPI routes for Forensic Investigation (Member B / Phase 5)."""

import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.api.contracts import InvestigationReport, InvestigationRequest
from backend.app.crypto.key_manager import KeyManager
from backend.app.services.investigation import investigate_pdf
from backend.app.watermark.embed import embed_watermark
from backend.storage.db import Database

router = APIRouter(prefix="/api/v1", tags=["Investigation"])

DEFAULT_DB_PATH = Path("storage_data/node1.db")
DEFAULT_KEYSTORE_DIR = Path("storage_data/keystore")

# In-memory investigation reports cache
_reports_cache: Dict[str, InvestigationReport] = {}


class InvestigationJsonRequest(BaseModel):
    document_id: str
    investigator_id: str = "investigator-unit-01"
    pdf_base64: str


def get_db() -> Optional[Database]:
    if DEFAULT_DB_PATH.exists():
        return Database(str(DEFAULT_DB_PATH), node_id="api-investigator")
    # Check any .db file in storage_data/
    for p in Path("storage_data").glob("*.db"):
        return Database(str(p), node_id="api-investigator")
    return None


@router.post("/investigations", response_model=InvestigationReport, status_code=status.HTTP_200_OK)
async def submit_investigation(
    file: Optional[UploadFile] = File(None),
    document_id: str = Form("doc-suspected-leak"),
    investigator_id: str = Form("investigator-01"),
) -> InvestigationReport:
    """Upload a suspected leaked PDF file and execute full cryptographic evidence verification."""
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No PDF file uploaded.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    inv_id = f"inv-{uuid.uuid4().hex[:10]}"
    req = InvestigationRequest(
        investigation_id=inv_id,
        document_id=document_id,
        investigator_id=investigator_id,
        requested_at=datetime.now(timezone.utc).isoformat(),
    )

    db = get_db()
    km = KeyManager(keystore_dir=DEFAULT_KEYSTORE_DIR)

    report = investigate_pdf(request=req, pdf_bytes=pdf_bytes, db=db, key_manager=km)
    _reports_cache[inv_id] = report
    return report


@router.post("/investigations/analyze-base64", response_model=InvestigationReport)
async def analyze_investigation_base64(req_body: InvestigationJsonRequest) -> InvestigationReport:
    """Analyze a suspected leak provided as base64-encoded PDF."""
    try:
        pdf_bytes = base64.b64decode(req_body.pdf_base64)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid base64 payload: {exc}") from exc

    inv_id = f"inv-{uuid.uuid4().hex[:10]}"
    req = InvestigationRequest(
        investigation_id=inv_id,
        document_id=req_body.document_id,
        investigator_id=req_body.investigator_id,
        requested_at=datetime.now(timezone.utc).isoformat(),
    )

    db = get_db()
    km = KeyManager(keystore_dir=DEFAULT_KEYSTORE_DIR)

    report = investigate_pdf(request=req, pdf_bytes=pdf_bytes, db=db, key_manager=km)
    _reports_cache[inv_id] = report
    return report


@router.get("/investigations/{investigation_id}", response_model=InvestigationReport)
async def get_investigation(investigation_id: str) -> InvestigationReport:
    """Retrieve report for a previously executed investigation."""
    if investigation_id in _reports_cache:
        return _reports_cache[investigation_id]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation {investigation_id} not found.")


@router.post("/investigations/simulate-preset")
def simulate_investigation_preset(preset_type: str = "known_leak") -> Dict[str, Any]:
    """Demo helper: Returns a base64 synthetic PDF corresponding to preset investigation scenarios."""
    from io import BytesIO
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    stream = BytesIO()
    writer.write(stream)
    blank_pdf = stream.getvalue()

    if preset_type == "unrelated_clean":
        return {
            "preset_type": preset_type,
            "description": "Clean PDF without any watermark token.",
            "pdf_base64": base64.b64encode(blank_pdf).decode("ascii"),
            "expected_outcome": "NO_MATCH (confidence 0.0)",
        }
    elif preset_type == "ambiguous_unregistered":
        rogue_pdf = embed_watermark(blank_pdf, "unregistered-test-token-777")
        return {
            "preset_type": preset_type,
            "description": "PDF containing a watermark token that was never committed to the ledger.",
            "pdf_base64": base64.b64encode(rogue_pdf).decode("ascii"),
            "expected_outcome": "INCONCLUSIVE (confidence <= 0.25)",
        }
    else:
        # Default: sample token
        sample_pdf = embed_watermark(blank_pdf, "OFFLINETRACE-DEMO-LEAK-TOKEN-99")
        return {
            "preset_type": "sample_leak",
            "description": "Sample suspected PDF with candidate watermark token.",
            "pdf_base64": base64.b64encode(sample_pdf).decode("ascii"),
            "expected_outcome": "Analyzed against ledger",
        }
