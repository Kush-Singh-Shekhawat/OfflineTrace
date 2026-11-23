"""Integration tests for Investigation Service and FastAPI routes (Member C).

Covers:
1. Successful investigation request (valid document, signatures, 2-of-3 quorum, chain).
2. Invalid request payload.
3. Unknown document ID (HTTP 404).
4. Unauthorized investigator (HTTP 401).
5. Invalid validator signature (signature_verified=False).
6. Failed quorum (quorum_verified=False when < 2 valid signatures).
7. Broken ledger chain (chain_verified=False).
8. Service exception (HTTP 500).
9. Correct InvestigationReport schema and persistence lookup.
10. Database failure handling (HTTP 500).
"""

from __future__ import annotations

import sqlite3
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.contracts import (
    InvestigationRequest,
    InvestigationReport,
    DocumentStatus,
    KeyStatus,
    RecipientResponse,
    LedgerEvent,
    LedgerProposal,
    ValidatorSignature,
    LedgerStatus,
)
from backend.storage.db import Database, reset_global_db, set_db
from backend.ledger.models import build_ledger_block
from backend.ledger.crypto_provider import default_crypto_provider


@pytest.fixture
def test_db(tmp_path):
    """Provide an isolated database instance for each test."""
    db_path = str(tmp_path / "test_investigation.db")
    db = reset_global_db(db_path, node_id="test-node")
    set_db(db)
    yield db
    db.close()
    set_db(None)


@pytest.fixture
def client(test_db):
    """FastAPI test client."""
    return TestClient(app)


def seed_document_and_ledger(
    db: Database,
    doc_id: str = "doc-test-001",
    num_signatures: int = 2,
    tamper_sig: bool = False,
    break_chain: bool = False,
):
    """Helper to seed a document, recipient, proposal, and committed block."""
    # 1. Recipient
    recip = RecipientResponse(
        recipient_id="recip-001",
        key_status=KeyStatus.ACTIVE,
        created_at="2026-11-23T10:00:00Z",
    )
    db.insert_recipient(recip)

    # 2. Document
    db.insert_document(
        document_id=doc_id,
        recipient_id="recip-001",
        status=DocumentStatus.RELEASED,
        created_at="2026-11-23T10:05:00Z",
    )

    # 3. Proposal with validator signatures
    signatures = []
    prop_temp = LedgerProposal(
        proposal_id=f"prop-{doc_id}",
        event=LedgerEvent(
            event_id=f"event-{doc_id}",
            event_type="COMMIT",
            timestamp="2026-11-23T10:10:00Z",
        ),
        document_id=doc_id,
        validator_signatures=[],
    )

    for i in range(1, num_signatures + 1):
        val_id = f"validator-{i}"
        sig = default_crypto_provider.sign_validator_proposal(prop_temp, val_id)
        if tamper_sig and i == 1:
            sig = ValidatorSignature(validator_id=val_id, signature="dGFtcGVyZWQtc2lnbmF0dXJl")
        signatures.append(sig)

    proposal = LedgerProposal(
        proposal_id=f"prop-{doc_id}",
        event=prop_temp.event,
        document_id=doc_id,
        validator_signatures=signatures,
    )

    # 4. Commit into Block 0
    prev_hash = "0" * 64 if not break_chain else "f" * 64
    block, block_hash = build_ledger_block(
        sequence=0,
        previous_hash=prev_hash,
        proposals=[proposal],
        status=LedgerStatus.COMMITTED,
    )
    db.append_block(block, block_hash)
    return doc_id


# ---------------------------------------------------------------------------
# Test Cases 1 through 10
# ---------------------------------------------------------------------------

def test_successful_investigation(client, test_db):
    """1. Successful investigation request."""
    doc_id = seed_document_and_ledger(test_db, doc_id="doc-success", num_signatures=2)

    payload = {
        "investigation_id": "inv-test-001",
        "document_id": doc_id,
        "investigator_id": "lead-investigator-01",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp = client.post("/api/v1/investigator/verify", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["investigation_id"] == "inv-test-001"
    assert data["document_id"] == doc_id
    assert data["signature_verified"] is True
    assert data["quorum_verified"] is True
    assert data["chain_verified"] is True
    assert data["confidence"] >= 0.9
    assert "All signatures verified" in data["diagnostics"]


def test_invalid_request_payload(client, test_db):
    """2. Invalid request payload returns HTTP 400 or 422."""
    # Missing required field document_id
    resp = client.post(
        "/api/v1/investigator/verify",
        json={"investigation_id": "inv-bad", "investigator_id": "inv-1"},
    )
    assert resp.status_code in (400, 422)

    # Empty string values
    resp_empty = client.post(
        "/api/v1/investigator/verify",
        json={
            "investigation_id": "",
            "document_id": "   ",
            "investigator_id": "inv-1",
            "requested_at": "2026-11-23T12:00:00Z",
        },
    )
    assert resp_empty.status_code == 400


def test_unknown_document(client, test_db):
    """3. Unknown document ID returns HTTP 404."""
    payload = {
        "investigation_id": "inv-404",
        "document_id": "doc-does-not-exist",
        "investigator_id": "lead-investigator-01",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp = client.post("/api/v1/investigator/verify", json=payload)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_unauthorized_investigator(client, test_db):
    """4. Unauthorized investigator returns HTTP 401."""
    doc_id = seed_document_and_ledger(test_db, doc_id="doc-auth-test")

    payload = {
        "investigation_id": "inv-unauth",
        "document_id": doc_id,
        "investigator_id": "unauthorized-guest",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp = client.post("/api/v1/investigator/verify", json=payload)
    assert resp.status_code == 401
    assert "unauthorized" in resp.json()["detail"].lower()


def test_invalid_signature(client, test_db):
    """5. Invalid validator signature fails signature verification."""
    doc_id = seed_document_and_ledger(
        test_db, doc_id="doc-bad-sig", num_signatures=2, tamper_sig=True
    )

    payload = {
        "investigation_id": "inv-sig-fail",
        "document_id": doc_id,
        "investigator_id": "lead-investigator-01",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp = client.post("/api/v1/investigator/verify", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["signature_verified"] is False
    assert data["quorum_verified"] is False
    assert data["confidence"] == 0.0
    assert "signature" in data["diagnostics"].lower()


def test_failed_quorum(client, test_db):
    """6. Failed quorum (< 2 valid distinct validator signatures)."""
    # Only 1 validator signature provided
    doc_id = seed_document_and_ledger(test_db, doc_id="doc-low-quorum", num_signatures=1)

    payload = {
        "investigation_id": "inv-quorum-fail",
        "document_id": doc_id,
        "investigator_id": "lead-investigator-01",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp = client.post("/api/v1/investigator/verify", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["signature_verified"] is True
    assert data["quorum_verified"] is False
    assert "quorum" in data["diagnostics"].lower()


def test_broken_ledger_chain(client, test_db):
    """7. Broken ledger chain fails chain verification."""
    doc_id = seed_document_and_ledger(
        test_db, doc_id="doc-broken-chain", num_signatures=2, break_chain=True
    )

    payload = {
        "investigation_id": "inv-chain-fail",
        "document_id": doc_id,
        "investigator_id": "lead-investigator-01",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp = client.post("/api/v1/investigator/verify", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["chain_verified"] is False
    assert data["confidence"] == 0.0
    assert "chain" in data["diagnostics"].lower()


def test_service_exception(client, test_db, monkeypatch):
    """8. Unhandled service exception returns HTTP 500."""
    doc_id = seed_document_and_ledger(test_db, doc_id="doc-err")

    def _broken_investigate(*args, **kwargs):
        raise RuntimeError("Simulated internal component breakdown")

    monkeypatch.setattr("backend.api.routes_manifest.investigate_document", _broken_investigate)

    payload = {
        "investigation_id": "inv-err",
        "document_id": doc_id,
        "investigator_id": "lead-investigator-01",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp = client.post("/api/v1/investigator/verify", json=payload)
    assert resp.status_code == 500
    assert "exception" in resp.json()["detail"].lower()


def test_correct_investigation_report_schema_and_persistence(client, test_db):
    """9. Correct InvestigationReport response schema and persistent retrieval."""
    doc_id = seed_document_and_ledger(test_db, doc_id="doc-schema-test", num_signatures=3)

    payload = {
        "investigation_id": "inv-schema-001",
        "document_id": doc_id,
        "investigator_id": "lead-investigator-01",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp = client.post("/api/v1/investigator/verify", json=payload)
    assert resp.status_code == 200

    # Validate schema strictly via Pydantic model
    report = InvestigationReport.model_validate(resp.json())
    assert report.investigation_id == "inv-schema-001"
    assert report.document_id == doc_id
    assert 0.0 <= report.confidence <= 1.0
    assert isinstance(report.diagnostics, str)
    assert isinstance(report.signature_verified, bool)
    assert isinstance(report.quorum_verified, bool)
    assert isinstance(report.chain_verified, bool)
    assert isinstance(report.generated_at, str)

    # Verify report was persisted in DB and retrievable via GET /api/v1/investigations/{id}
    persisted = test_db.get_investigation("inv-schema-001")
    assert persisted is not None
    assert persisted.investigation_id == "inv-schema-001"

    get_resp = client.get("/api/v1/investigations/inv-schema-001")
    assert get_resp.status_code == 200
    assert get_resp.json()["investigation_id"] == "inv-schema-001"


def test_database_failure(client, test_db, monkeypatch):
    """10. Database failure handling returns HTTP 500."""
    def _failing_has_document(*args, **kwargs):
        raise sqlite3.OperationalError("Database disk image is malformed")

    monkeypatch.setattr(test_db, "has_document", _failing_has_document)

    payload = {
        "investigation_id": "inv-db-fail",
        "document_id": "doc-db-test",
        "investigator_id": "lead-investigator-01",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp = client.post("/api/v1/investigator/verify", json=payload)
    assert resp.status_code == 500
    assert "database" in resp.json()["detail"].lower()


def test_duplicate_investigation_id_handling(client, test_db):
    """Verify duplicate investigation IDs update safely without SQL collision."""
    doc_id = seed_document_and_ledger(test_db, doc_id="doc-dup-test", num_signatures=2)

    payload = {
        "investigation_id": "inv-dup-001",
        "document_id": doc_id,
        "investigator_id": "lead-investigator-01",
        "requested_at": "2026-11-23T12:00:00Z",
    }
    resp1 = client.post("/api/v1/investigator/verify", json=payload)
    assert resp1.status_code == 200

    resp2 = client.post("/api/v1/investigator/verify", json=payload)
    assert resp2.status_code == 200
    assert resp2.json()["investigation_id"] == "inv-dup-001"
