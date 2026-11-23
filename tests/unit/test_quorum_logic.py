"""Unit tests for Quorum Consensus logic, 1-signature rejection, and 2-signature commit."""

import shutil
import tempfile
from pathlib import Path
import pytest
import httpx
from fastapi.testclient import TestClient

from backend.api.contracts import (
    CommitCertificate,
    LedgerEvent,
    LedgerProposal,
    ValidatorSignature,
)
from backend.ledger.crypto_provider import default_crypto_provider
from backend.ledger.quorum import QuorumCoordinator, QuorumFailedError
from backend.services.orchestration import ReleaseOrchestrator
from backend.validator_node.node import create_validator_app


def _make_proposal(event_id: str = "ev-quorum-unit") -> LedgerProposal:
    return LedgerProposal(
        proposal_id=f"prop-{event_id}",
        event=LedgerEvent(
            event_id=event_id,
            event_type="PROPOSAL",
            timestamp="2026-11-23T06:15:00Z",
        ),
        document_id="doc-001",
        validator_signatures=[],
    )


@pytest.fixture
def tmp_node():
    tmp_dir = Path(tempfile.mkdtemp(prefix="val_node_test_"))
    db_path = str(tmp_dir / "node.db")
    app = create_validator_app(node_id="val-1", db_path=db_path)
    client = TestClient(app)
    yield {"app": app, "client": client, "db_path": db_path}
    app.state.db.close()
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_validator_node_commit_rejects_single_signature(tmp_node):
    """Validator /commit endpoint must reject a CommitCertificate with < 2 signatures with HTTP 400."""
    client = tmp_node["client"]
    cert = CommitCertificate(
        certificate_id="cert-single-sig",
        proposal_id="prop-nonexistent",
        signatures=[ValidatorSignature(validator_id="val-1", signature="sig1")],
        quorum=2,
    )
    resp = client.post("/commit", json=cert.model_dump())
    assert resp.status_code == 400
    assert "Insufficient signatures for quorum" in resp.json()["detail"]


def test_validator_node_commit_rejects_duplicate_validator_signatures(tmp_node):
    """Validator /commit endpoint must reject multiple signatures from the same validator identity."""
    client = tmp_node["client"]
    cert = CommitCertificate(
        certificate_id="cert-duplicate-val",
        proposal_id="prop-nonexistent",
        signatures=[
            ValidatorSignature(validator_id="val-1", signature="sig1"),
            ValidatorSignature(validator_id="val-1", signature="sig2"),
        ],
        quorum=2,
    )
    resp = client.post("/commit", json=cert.model_dump())
    assert resp.status_code == 400
    assert "Duplicate validator signatures detected" in resp.json()["detail"]


@pytest.mark.anyio
async def test_coordinator_rejects_duplicate_validator_signatures():
    """Coordinator must reject 2 signatures from the same validator ID as 1-of-3 (fail-closed)."""
    urls = ["http://val-1", "http://val-2", "http://val-3"]
    proposal = _make_proposal("ev-sybil")
    sig = default_crypto_provider.sign_validator_proposal(proposal, "val-1")

    # Mock responses where two nodes return the same validator_id 'val-1'
    mock_clients = {
        urls[0]: httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, json=sig.model_dump()))
        ),
        urls[1]: httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, json=sig.model_dump()))
        ),
        urls[2]: httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(500))
        ),
    }

    coordinator = QuorumCoordinator(validator_urls=urls, clients=mock_clients)
    with pytest.raises(QuorumFailedError) as exc_info:
        await coordinator.propose_and_commit(proposal)
    assert "required >= 2 distinct signatures" in str(exc_info.value)


@pytest.mark.anyio
async def test_coordinator_rejects_forged_signatures():
    """Signatures that fail cryptographic verification must not count toward quorum."""
    urls = ["http://val-1", "http://val-2", "http://val-3"]
    proposal = _make_proposal("ev-forged")
    valid_sig = default_crypto_provider.sign_validator_proposal(proposal, "val-1")
    forged_sig = ValidatorSignature(validator_id="val-2", signature="invalid_base64_forgery")

    mock_clients = {
        urls[0]: httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, json=valid_sig.model_dump()))
        ),
        urls[1]: httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, json=forged_sig.model_dump()))
        ),
        urls[2]: httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(500))
        ),
    }

    coordinator = QuorumCoordinator(validator_urls=urls, clients=mock_clients)
    with pytest.raises(QuorumFailedError) as exc_info:
        await coordinator.propose_and_commit(proposal)
    assert "required >= 2 distinct signatures" in str(exc_info.value)


@pytest.mark.anyio
async def test_orchestrator_fail_closed_release():
    """ReleaseOrchestrator must raise QuorumFailedError and block release when quorum is not met."""
    urls = ["http://val-1", "http://val-2", "http://val-3"]
    broken_clients = {
        u: httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(503)))
        for u in urls
    }
    coordinator = QuorumCoordinator(validator_urls=urls, clients=broken_clients)
    orchestrator = ReleaseOrchestrator(coordinator=coordinator)

    event = LedgerEvent(
        event_id="ev-orchestrator-test",
        event_type="PROPOSAL",
        timestamp="2026-11-23T06:20:00Z",
    )

    with pytest.raises(QuorumFailedError):
        await orchestrator.commit_decryption_event(event=event, document_id="doc-release-fail")
