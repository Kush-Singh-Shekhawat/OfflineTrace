"""Integration tests for Phase 3: 3-Node Quorum & Fail-Closed Consensus.

Verifies:
- 1-of-3 approval fails closed and commits nothing to the ledger.
- 2-of-3 approvals commit the block and persist across node restart.
- Replaying the same event_id is rejected by the validator nodes.
- Tampering with one node's SQLite block is detected by check_divergence().
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest
import httpx

from backend.api.contracts import (
    LedgerEvent,
    LedgerProposal,
    ValidatorSignature,
)
from backend.storage.db import Database
from backend.validator_node.node import create_validator_app
from backend.ledger.quorum import QuorumCoordinator, QuorumFailedError


@pytest.fixture
def test_cluster():
    """Create 3 isolated validator node instances with temporary SQLite databases."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="quorum_test_"))
    db_paths = [
        str(tmp_dir / "node1.db"),
        str(tmp_dir / "node2.db"),
        str(tmp_dir / "node3.db"),
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

    yield {
        "tmp_dir": tmp_dir,
        "db_paths": db_paths,
        "apps": apps,
        "urls": urls,
        "clients": clients,
    }

    # Teardown
    for app in apps:
        app.state.db.close()
    shutil.rmtree(tmp_dir, ignore_errors=True)


def make_proposal(event_id: str = "ev-001", doc_id: str = "doc-001") -> LedgerProposal:
    return LedgerProposal(
        proposal_id=f"prop-{event_id}",
        event=LedgerEvent(
            event_id=event_id,
            event_type="PROPOSAL",
            timestamp="2026-11-23T05:00:00Z",
        ),
        document_id=doc_id,
        validator_signatures=[],
    )


@pytest.mark.anyio
async def test_single_validator_fails_closed(test_cluster):
    """1-of-3 approval (2 nodes unreachable/offline) must fail closed and commit nothing."""
    urls = test_cluster["urls"]
    # Provide clients where only val-1 is reachable; val-2 and val-3 raise error
    broken_clients = {
        urls[0]: test_cluster["clients"][urls[0]],
        urls[1]: httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(500))),
        urls[2]: httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(500))),
    }
    coordinator = QuorumCoordinator(validator_urls=urls, clients=broken_clients)
    proposal = make_proposal(event_id="ev-fail-closed")

    # Must raise QuorumFailedError
    with pytest.raises(QuorumFailedError):
        await coordinator.propose_and_commit(proposal)

    # Verify no block was committed to any of the databases
    for db_path in test_cluster["db_paths"]:
        db = Database(db_path, node_id="check")
        assert db.chain_height() == 0
        db.close()


@pytest.mark.anyio
async def test_quorum_2_of_3_commits_and_persists_across_restart(test_cluster):
    """2-of-3 approvals must commit the block and persist across node restart."""
    urls = test_cluster["urls"]
    # val-1 and val-2 are online, val-3 is offline
    two_node_clients = {
        urls[0]: test_cluster["clients"][urls[0]],
        urls[1]: test_cluster["clients"][urls[1]],
        urls[2]: httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(503))),
    }
    coordinator = QuorumCoordinator(validator_urls=urls, clients=two_node_clients)
    proposal = make_proposal(event_id="ev-commit-success")

    cert = await coordinator.propose_and_commit(proposal)
    assert cert.proposal_id == proposal.proposal_id
    assert len(cert.signatures) >= 2

    # Verify val-1 and val-2 committed the block
    for i in (0, 1):
        db_path = test_cluster["db_paths"][i]
        # Simulate restart: open a fresh DB connection
        fresh_db = Database(db_path, node_id=f"restarted-{i}")
        assert fresh_db.chain_height() == 1
        latest = fresh_db.latest_block()
        assert latest is not None
        assert latest[0] == 0  # sequence 0 (genesis block)
        assert len(latest[1]) == 64  # SHA3-256 hash length
        assert fresh_db.has_event_id("ev-commit-success")
        fresh_db.close()


@pytest.mark.anyio
async def test_replay_event_id_rejected(test_cluster):
    """Replaying an already committed event_id must be rejected with HTTP 400."""
    urls = test_cluster["urls"]
    coordinator = QuorumCoordinator(validator_urls=urls, clients=test_cluster["clients"])
    proposal = make_proposal(event_id="ev-unique-replay")

    # First commitment succeeds
    await coordinator.propose_and_commit(proposal)

    # Attempting to propose the exact same proposal again must fail
    with pytest.raises(QuorumFailedError):
        await coordinator.propose_and_commit(proposal)


@pytest.mark.anyio
async def test_tampering_caught_by_check_divergence(test_cluster):
    """Tampering with a block on one node must be detected as divergence."""
    urls = test_cluster["urls"]
    coordinator = QuorumCoordinator(validator_urls=urls, clients=test_cluster["clients"])
    proposal = make_proposal(event_id="ev-divergence-test")

    # Commit on all 3 nodes
    await coordinator.propose_and_commit(proposal)

    # Pre-tampering check: clean state, no divergence
    div_pre = await coordinator.check_divergence()
    assert div_pre["divergence_detected"] is False

    # Tamper with node 3's latest block hash directly in its SQLite database
    node3_db = test_cluster["apps"][2].state.db
    cur = node3_db.conn.cursor()
    cur.execute("UPDATE ledger_blocks SET block_hash = ? WHERE sequence = 0", ("f" * 64,))
    node3_db.conn.commit()

    # Post-tampering check: divergence must be detected!
    div_post = await coordinator.check_divergence()
    assert div_post["divergence_detected"] is True
    assert "Divergence at height 1" in div_post["details"] or "conflicting" in div_post["details"]
