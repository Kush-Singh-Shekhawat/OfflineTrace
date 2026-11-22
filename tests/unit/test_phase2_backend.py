"""Unit tests for Phase 2 Backend foundation.

The tests cover:
* SQLite isolation between two validator nodes.
* Deterministic genesis and subsequent block hashing using the ledger helper.
* Integrity verification failure when a block is tampered with.
* FastAPI health endpoint and OpenAPI schema loading via TestClient.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.storage.db import Database
from backend.ledger.models import build_ledger_block, verify_block_integrity
from backend.api.contracts import (LedgerEvent, 
    LedgerBlock,
    LedgerProposal,
    LedgerStatus,
    EncryptedEnvelope,
    RecipientResponse,
    KeyStatus,
    DocumentStatus,
)

# ---------------------------------------------------------------------------
# Fixtures – temporary isolated DB files for two validator nodes.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def node_dbs():
    tmp_dir = Path(tempfile.mkdtemp())
    db1_path = tmp_dir / "node1.db"
    db2_path = tmp_dir / "node2.db"
    db1 = Database(str(db1_path), node_id="node1")
    db2 = Database(str(db2_path), node_id="node2")
    yield db1, db2
    db1.close()
    db2.close()
    shutil.rmtree(tmp_dir)

# ---------------------------------------------------------------------------
# Helper to create a minimal envelope (no cryptographic material needed).
# ---------------------------------------------------------------------------
def dummy_envelope(doc_id: str) -> EncryptedEnvelope:
    return EncryptedEnvelope(
        envelope_id=f"env-{doc_id}",
        document_id=doc_id,
        encrypted_key="dummy_key",
        ciphertext="dummy_ct",
        token_digest="deadbeef" * 8,
        kem_algorithm="ML-KEM-768",
        symmetric_algorithm="AES-256-GCM",
        kdf_algorithm="HKDF-SHA-256",
    )

# ---------------------------------------------------------------------------
# Test DB isolation – inserting a recipient in one DB must not appear in the other.
# ---------------------------------------------------------------------------
def test_db_isolation(node_dbs):
    db1, db2 = node_dbs
    resp = RecipientResponse(
        recipient_id="rec-001",
        key_status=KeyStatus.ACTIVE,
        created_at="2026-01-01T00:00:00Z",
    )
    # Insert only into db1.
    db1.insert_recipient(resp)
    assert db1.get_recipient("rec-001") is not None
    assert db2.get_recipient("rec-001") is None

# ---------------------------------------------------------------------------
# Test deterministic block hashing – genesis block and a second block.
# ---------------------------------------------------------------------------
def test_block_hash_determinism():
    # Genesis block – empty proposal list, previous hash is all zeros.
    genesis_prev = "0" * 64
    genesis_block, genesis_hash = build_ledger_block(
        sequence=0,
        previous_hash=genesis_prev,
        proposals=[],
        status=LedgerStatus.PENDING,
    )
    assert isinstance(genesis_block, LedgerBlock)
    # Build a second block referencing the genesis hash.
    dummy_prop = LedgerProposal(
        proposal_id="prop-001",
        event=LedgerEvent.model_construct(event_id="ev-001", event_type="PROPOSAL", timestamp="2026-01-01T00:00:01Z"),
        document_id="doc-001",
        validator_signatures=[],
    )
    second_block, second_hash = build_ledger_block(
        sequence=1,
        previous_hash=genesis_hash,
        proposals=[dummy_prop],
        status=LedgerStatus.PENDING,
    )
    # Verify that recomputed hashes match stored ones.
    assert verify_block_integrity(genesis_block, genesis_hash, genesis_prev, 0)
    assert verify_block_integrity(second_block, second_hash, genesis_hash, 1)

# ---------------------------------------------------------------------------
# Tampering detection – modify a field and ensure integrity fails.
# ---------------------------------------------------------------------------
def test_block_tampering_detection():
    genesis_prev = "0" * 64
    block, block_hash = build_ledger_block(
        sequence=0,
        previous_hash=genesis_prev,
        proposals=[],
        status=LedgerStatus.PENDING,
    )
    # Tamper with previous_hash.
    block_tampered = block.model_copy(update={"previous_hash": "1" * 64})
    assert not verify_block_integrity(block_tampered, block_hash, genesis_prev, 0)
    # Tamper with merkle_root.
    block_tampered2 = block.model_copy(update={"merkle_root": "ff" * 32})
    assert not verify_block_integrity(block_tampered2, block_hash, genesis_prev, 0)

# ---------------------------------------------------------------------------
# FastAPI health endpoint and OpenAPI schema loading.
# ---------------------------------------------------------------------------
def test_fastapi_health_and_schema():
    client = TestClient(app)
    # Health endpoint.
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    # OpenAPI schema loads without error.
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert schema.json()["info"]["title"] == "OfflineTrace API"
