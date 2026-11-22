"""Ledger block data structure placeholder."""

from dataclasses import dataclass

@dataclass(frozen=True)
class Block:
    index: int
    timestamp: str
    payload_hash: str
    previous_hash: str
    block_hash: str
