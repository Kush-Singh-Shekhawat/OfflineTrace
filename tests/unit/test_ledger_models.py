"""Unit tests for ledger models, SHA3-256 block hashing, and hash-chain integrity."""

import pytest
from backend.api.contracts import (
    LedgerBlock,
    LedgerEvent,
    LedgerProposal,
    LedgerStatus,
)
from backend.ledger.models import (
    build_ledger_block,
    compute_merkle_root,
    verify_block_integrity,
    verify_chain_integrity,
)


def _make_proposal(event_id: str, doc_id: str = "doc-test") -> LedgerProposal:
    return LedgerProposal(
        proposal_id=f"prop-{event_id}",
        event=LedgerEvent(
            event_id=event_id,
            event_type="PROPOSAL",
            timestamp="2026-11-23T06:00:00Z",
        ),
        document_id=doc_id,
        validator_signatures=[],
    )


def test_genesis_block_and_subsequent_blocks_hashing():
    """Verify genesis block (seq 0) and multiple subsequent blocks form a valid SHA3-256 hash chain."""
    genesis_prev = "0" * 64
    prop0 = _make_proposal("ev-0")
    b0, h0 = build_ledger_block(0, genesis_prev, [prop0], LedgerStatus.COMMITTED)
    assert verify_block_integrity(b0, h0, genesis_prev, 0)

    # Block 1 links to h0
    prop1 = _make_proposal("ev-1")
    b1, h1 = build_ledger_block(1, h0, [prop1], LedgerStatus.COMMITTED)
    assert verify_block_integrity(b1, h1, h0, 1)

    # Block 2 links to h1
    prop2 = _make_proposal("ev-2")
    b2, h2 = build_ledger_block(2, h1, [prop2], LedgerStatus.COMMITTED)
    assert verify_block_integrity(b2, h2, h1, 2)

    # Chain verification
    chain = [
        {"sequence": 0, "previous_hash": genesis_prev, "block_hash": h0, "data": b0.model_dump()},
        {"sequence": 1, "previous_hash": h0, "block_hash": h1, "data": b1.model_dump()},
        {"sequence": 2, "previous_hash": h1, "block_hash": h2, "data": b2.model_dump()},
    ]
    assert verify_chain_integrity(chain) is True


def test_chain_tamper_previous_hash_breaks_continuity():
    """Modifying previous_hash in any block must break chain integrity."""
    genesis_prev = "0" * 64
    b0, h0 = build_ledger_block(0, genesis_prev, [_make_proposal("ev-0")], LedgerStatus.COMMITTED)
    b1, h1 = build_ledger_block(1, h0, [_make_proposal("ev-1")], LedgerStatus.COMMITTED)

    # Corrupt previous_hash of block 1
    corrupt_chain = [
        {"sequence": 0, "previous_hash": genesis_prev, "block_hash": h0, "data": b0.model_dump()},
        {"sequence": 1, "previous_hash": "a" * 64, "block_hash": h1, "data": b1.model_dump()},
    ]
    assert verify_chain_integrity(corrupt_chain) is False


def test_chain_tamper_sequence_out_of_order_fails():
    """Non-sequential block sequence numbers must fail chain integrity."""
    genesis_prev = "0" * 64
    b0, h0 = build_ledger_block(0, genesis_prev, [_make_proposal("ev-0")], LedgerStatus.COMMITTED)
    b1, h1 = build_ledger_block(1, h0, [_make_proposal("ev-1")], LedgerStatus.COMMITTED)

    # Out-of-order sequence (skip 1, set to 2)
    corrupt_chain = [
        {"sequence": 0, "previous_hash": genesis_prev, "block_hash": h0, "data": b0.model_dump()},
        {"sequence": 2, "previous_hash": h0, "block_hash": h1, "data": b1.model_dump()},
    ]
    assert verify_chain_integrity(corrupt_chain) is False


def test_chain_tamper_proposal_payload_detected():
    """Altering proposal contents inside a committed block invalidates merkle root and hash."""
    genesis_prev = "0" * 64
    b0, h0 = build_ledger_block(0, genesis_prev, [_make_proposal("ev-0")], LedgerStatus.COMMITTED)

    # Tamper with proposal event_id
    tampered_data = b0.model_dump()
    tampered_data["proposals"][0]["event"]["event_id"] = "ev-tampered"

    chain = [
        {"sequence": 0, "previous_hash": genesis_prev, "block_hash": h0, "data": tampered_data},
    ]
    assert verify_chain_integrity(chain) is False
