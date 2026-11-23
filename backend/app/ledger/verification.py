"""Ledger verification service for entry lookup and integrity verification."""

from __future__ import annotations

from typing import Any, Dict, Optional
from backend.storage.db import Database
from backend.ledger.models import verify_block_integrity, verify_chain_integrity


def verify_entry(entry_id: str, db: Optional[Database] = None) -> Dict[str, Any]:
    """Look up an event entry and verify its cryptographic and chain integrity."""
    if db is None:
        return {"entry_id": entry_id, "verified": False, "reason": "No database provided"}

    blocks = db.get_blocks()
    if not verify_chain_integrity(blocks):
        return {"entry_id": entry_id, "verified": False, "reason": "Chain integrity compromised"}

    for b in blocks:
        proposals = b["data"].get("proposals", [])
        for p in proposals:
            event = p.get("event", {})
            if event.get("event_id") == entry_id:
                return {
                    "entry_id": entry_id,
                    "verified": True,
                    "block_id": b["block_id"],
                    "sequence": b["sequence"],
                    "block_hash": b["block_hash"],
                    "document_id": p.get("document_id"),
                }

    return {"entry_id": entry_id, "verified": False, "reason": "Entry not found in committed blocks"}
