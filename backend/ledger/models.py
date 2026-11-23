"""Ledger helper models for OfflineTrace.

Functions for building deterministic ledger blocks, computing their SHA3‑256
hashes, and verifying integrity. They operate on the Pydantic contracts
defined in ``backend.api.contracts`` but do **not** modify the contract file.
"""

from __future__ import annotations

import json
from typing import Any, List, Tuple

from ..api.contracts import (
    LedgerBlock,
    LedgerProposal,
    LedgerStatus,
    canonical_json_bytes,
    sha3_256_hex,
)

# ---------------------------------------------------------------------------
# Block construction utilities
# ---------------------------------------------------------------------------

def _proposal_digest(proposal: LedgerProposal) -> str:
    """Return a deterministic digest for a single proposal.

    The digest is the SHA3‑256 hex of the canonical JSON representation of the
    proposal (excluding any mutable runtime fields). This provides a stable
    identifier for the merkle‑root calculation.
    """
    data = json.loads(proposal.model_dump_json())
    return sha3_256_hex(canonical_json_bytes(data))


def compute_merkle_root(proposals: List[LedgerProposal]) -> str:
    """Compute a simple merkle‑root style hash over the list of proposals.

    For the purpose of this phase we concatenate the individual proposal
    digests in order and hash the resulting byte string. The result is a 64‑hex
    string.
    """
    concatenated = "".join(_proposal_digest(p) for p in proposals).encode()
    return sha3_256_hex(concatenated)


def build_ledger_block(
    sequence: int,
    previous_hash: str,
    proposals: List[LedgerProposal],
    status: LedgerStatus = LedgerStatus.PENDING,
) -> Tuple[LedgerBlock, str]:
    """Create a :class:`LedgerBlock` and its SHA3‑256 block hash.

    The block hash is computed over a canonical JSON payload containing the
    *sequence*, *previous_hash*, *merkle_root*, *status* and the list of
    proposal digests. The function returns the ``LedgerBlock`` instance and the
    computed ``block_hash`` as a hex string.
    """
    merkle_root = compute_merkle_root(proposals)
    block = LedgerBlock(
        block_id=f"block-{sequence}",
        previous_hash=previous_hash,
        proposals=proposals,
        merkle_root=merkle_root,
        status=status,
    )
    payload = {
        "sequence": sequence,
        "previous_hash": previous_hash,
        "merkle_root": merkle_root,
        "status": status.value,
        "proposals": [_proposal_digest(p) for p in proposals],
    }
    block_hash = sha3_256_hex(canonical_json_bytes(payload))
    return block, block_hash


def verify_block_integrity(
    block: LedgerBlock,
    stored_hash: str,
    expected_prev_hash: str,
    sequence: int,
) -> bool:
    """Check that *block* matches its stored hash and chain linkage.

    Returns ``True`` only if:
    * ``block.previous_hash`` equals ``expected_prev_hash``
    * recomputed hash over the canonical payload matches ``stored_hash``
    * the merkle root matches the proposals contained in the block
    """
    if block.previous_hash != expected_prev_hash:
        return False
    if block.merkle_root != compute_merkle_root(block.proposals):
        return False
    payload = {
        "sequence": sequence,
        "previous_hash": block.previous_hash,
        "merkle_root": block.merkle_root,
        "status": block.status.value,
        "proposals": [_proposal_digest(p) for p in block.proposals],
    }
    recomputed = sha3_256_hex(canonical_json_bytes(payload))
    return recomputed == stored_hash


def verify_chain_integrity(chain: List[Any]) -> bool:
    """Verify hash-link continuity, sequence monotonicity, and block integrity for an entire chain.

    Accepts:
    - List of dicts (as returned by Database.get_blocks())
    - Or List of tuples: (LedgerBlock, stored_hash, sequence)

    Returns True if valid, False otherwise.
    """
    if not chain:
        return True

    expected_prev = "0" * 64
    for i, item in enumerate(chain):
        if isinstance(item, dict):
            seq = item["sequence"]
            prev_hash = item["previous_hash"]
            stored_hash = item["block_hash"]
            block_data = item.get("data") or item
            block = LedgerBlock.model_validate(block_data)
        elif isinstance(item, tuple):
            block, stored_hash, seq = item
            prev_hash = block.previous_hash
        else:
            return False

        if seq != i:
            return False
        if prev_hash != expected_prev:
            return False
        if not verify_block_integrity(block, stored_hash, expected_prev, seq):
            return False
        expected_prev = stored_hash

    return True
