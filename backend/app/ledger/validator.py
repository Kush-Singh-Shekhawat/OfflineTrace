"""Ledger validation logic for chain integrity and hash continuity."""

from __future__ import annotations

from typing import Any, List
from backend.ledger.models import verify_chain_integrity


def validate_chain(blocks: List[Any]) -> bool:
    """Verify hash-link and payload verification across a sequence of blocks."""
    return verify_chain_integrity(blocks)
