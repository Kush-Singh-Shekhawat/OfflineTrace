"""Phase 5 Unit Tests: Forensic Investigation & Evidence Verification.

Exit criteria per Phase 5 specification:
1. Known leak matches (confidence 1.0, signature, quorum, and chain verified).
2. Unrelated sample no-match (confidence 0.0, no watermark found).
3. Ambiguous sample inconclusive (watermark present in PDF, but not committed on ledger).
"""

import base64
from io import BytesIO
from pathlib import Path
import shutil
import tempfile
import httpx
from pypdf import PdfWriter
import pytest

from backend.api.contracts import InvestigationRequest
from backend.app.crypto.encryption import encrypt_document, generate_cek
from backend.app.crypto.envelope import create_recipient_envelope
from backend.app.crypto.key_manager import KeyManager
from backend.app.services.investigation import investigate_pdf
from backend.app.services.recipient_workflow import RecipientWorkflowOrchestrator
from backend.app.watermark.embed import embed_watermark
from backend.ledger.quorum import QuorumCoordinator
from backend.storage.db import Database
from backend.validator_node.node import create_validator_app


def create_blank_pdf() -> bytes:
    """Create a minimal blank PDF."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()


@pytest.fixture
def test_investigation_env():
    """Create a temporary test cluster, DB, and keystore for investigation tests."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="investigation_test_"))
    db_paths = [
        str(tmp_dir / "val1.db"),
        str(tmp_dir / "val2.db"),
        str(tmp_dir / "val3.db"),
    ]
    apps = [
        create_validator_app(node_id="val-1", db_path=db_paths[0]),
        create_validator_app(node_id="val-2", db_path=db_paths[1]),
        create_validator_app(node_id="val-3", db_path=db_paths[2]),
    ]
    urls = ["http://val-1", "http://val-2", "http://val-3"]
    clients = {
        urls[0]: httpx.AsyncClient(transport=httpx.ASGITransport(app=apps[0]), base_url=urls[0]),
        urls[1]: httpx.AsyncClient(transport=httpx.ASGITransport(app=apps[1]), base_url=urls[1]),
        urls[2]: httpx.AsyncClient(transport=httpx.ASGITransport(app=apps[2]), base_url=urls[2]),
    }
    km = KeyManager(keystore_dir=tmp_dir / "keystore")
    db1 = Database(db_paths[0], node_id="val-1")

    yield {
        "tmp_dir": tmp_dir,
        "db": db1,
        "db_paths": db_paths,
        "urls": urls,
        "clients": clients,
        "key_manager": km,
    }

    # Teardown
    db1.close()
    for app in apps:
        app.state.db.close()
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_investigation_unrelated_sample_no_match(test_investigation_env):
    """Exit criterion 2: Unrelated clean PDF results in NO_MATCH (confidence 0.0)."""
    db = test_investigation_env["db"]
    clean_pdf = create_blank_pdf()

    req = InvestigationRequest(
        investigation_id="inv-unrelated-001",
        document_id="doc-unknown",
        investigator_id="inv-agent-47",
        requested_at="2026-11-23T06:00:00Z",
    )

    report = investigate_pdf(request=req, pdf_bytes=clean_pdf, db=db)

    assert report.confidence == 0.0
    assert report.signature_verified is False
    assert report.quorum_verified is False
    assert report.chain_verified is False
    assert "NO_MATCH" in report.diagnostics


def test_investigation_ambiguous_sample_inconclusive(test_investigation_env):
    """Exit criterion 3: PDF with uncommitted watermark results in INCONCLUSIVE."""
    db = test_investigation_env["db"]
    blank_pdf = create_blank_pdf()
    watermarked_pdf = embed_watermark(blank_pdf, "uncommitted-rogue-token-xyz")

    req = InvestigationRequest(
        investigation_id="inv-ambiguous-002",
        document_id="doc-rogue",
        investigator_id="inv-agent-47",
        requested_at="2026-11-23T06:00:00Z",
    )

    report = investigate_pdf(request=req, pdf_bytes=watermarked_pdf, db=db)

    assert report.confidence <= 0.25
    assert report.signature_verified is False
    assert "INCONCLUSIVE" in report.diagnostics


@pytest.mark.anyio
async def test_investigation_known_leak_exact_match(test_investigation_env):
    """Exit criterion 1: Known leak committed on ledger results in EXACT_MATCH (confidence 1.0)."""
    km = test_investigation_env["key_manager"]
    db = test_investigation_env["db"]
    urls = test_investigation_env["urls"]
    clients = test_investigation_env["clients"]

    # 1. Enroll recipient and prepare document
    rec_pub = km.create_recipient_keys("recip_target", "Cmdr. T", "t@navy.mod")
    kem_ek = base64.b64decode(rec_pub.kem_public_key_b64)

    coordinator = QuorumCoordinator(validator_urls=urls, clients=clients)
    orchestrator = RecipientWorkflowOrchestrator(key_manager=km, quorum_coordinator=coordinator)

    cek = generate_cek()
    raw_pdf = create_blank_pdf()
    enc_doc = encrypt_document(raw_pdf, cek)
    doc_id = "doc-leaked-navy-manifest"

    envelope = create_recipient_envelope(
        cek=cek,
        recipient_id="recip_target",
        recipient_kem_public_key=kem_ek,
        document_id=doc_id,
        version_id="v1",
    )

    # 2. Complete Phase 4 vertical slice (decrypt, embed watermark, quorum commit)
    slice_result = await orchestrator.execute_recipient_decrypt_and_release(
        recipient_id="recip_target",
        envelope=envelope,
        encrypted_document_bytes=enc_doc,
        document_id=doc_id,
        version_id="v1",
    )

    leaked_pdf = slice_result.released_document

    # 3. Investigator investigates the leaked PDF
    req = InvestigationRequest(
        investigation_id="inv-known-leak-003",
        document_id=doc_id,
        investigator_id="inv-officer-99",
        requested_at="2026-11-23T06:15:00Z",
    )

    db_paths = test_investigation_env["db_paths"]
    db_fresh = Database(db_paths[0], node_id="audit-investigator")

    report = investigate_pdf(
        request=req,
        pdf_bytes=leaked_pdf,
        db=db_fresh,
        key_manager=km,
    )
    db_fresh.close()

    # Verification checks
    assert report.confidence == 1.0
    assert report.signature_verified is True
    assert report.quorum_verified is True
    assert report.chain_verified is True
    assert "EXACT_MATCH" in report.diagnostics
