"""SQLite storage helpers for OfflineTrace.

Each validator node gets its own isolated DB file (passed via ``db_path``). The
module provides a thin, type‑annotated wrapper around the standard ``sqlite3``
module – no ORM, no logging of secrets.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, List, Tuple

from ..api.contracts import (
    ErrorCode,
    LedgerBlock,
    RecipientResponse,
    DocumentStatus,
    KeyStatus,
    EncryptedEnvelope,
)


class Database:
    """Simple SQLite wrapper.

    Parameters
    ----------
    db_path: str
        Path to the SQLite file for this node.
    node_id: str
        Identifier for the node – used for ``created_at`` timestamps and health
        reporting. The ``node_id`` does **not** appear in any stored secret.
    """

    def __init__(self, db_path: str, node_id: str) -> None:
        self.node_id = node_id
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    # ---------------------------------------------------------------------
    # Schema creation / migration
    # ---------------------------------------------------------------------
    def _migrate(self) -> None:
        cur = self.conn.cursor()
        # Recipients – public information only.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS recipients (
                recipient_id TEXT PRIMARY KEY,
                public_key TEXT DEFAULT "",
                key_status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        # Documents – status tracking.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                recipient_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (recipient_id) REFERENCES recipients(recipient_id)
            )
            """
        )
        # Envelopes – never store raw CEK or watermark token.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS envelopes (
                envelope_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                encrypted_key TEXT NOT NULL,
                ciphertext TEXT NOT NULL,
                token_digest TEXT NOT NULL,
                kem_algorithm TEXT NOT NULL,
                symmetric_algorithm TEXT NOT NULL,
                kdf_algorithm TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(document_id)
            )
            """
        )
        # Ledger blocks – immutable once committed.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_blocks (
                block_id TEXT PRIMARY KEY,
                sequence INTEGER NOT NULL,
                previous_hash TEXT NOT NULL,
                merkle_root TEXT NOT NULL,
                status TEXT NOT NULL,
                block_hash TEXT NOT NULL,
                raw_json TEXT NOT NULL
            )
            """
        )
        # Proposals (optional – stored as JSON for debugging).
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS proposals (
                proposal_id TEXT PRIMARY KEY,
                block_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                FOREIGN KEY (block_id) REFERENCES ledger_blocks(block_id)
            )
            """
        )
        # Commit certificates – stored as JSON array of signatures.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS commit_certificates (
                certificate_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                signatures TEXT NOT NULL,
                quorum INTEGER NOT NULL,
                FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
            )
            """
        )
        self.conn.commit()

    # ---------------------------------------------------------------------
    # Recipient helpers
    # ---------------------------------------------------------------------
    def insert_recipient(self, resp: RecipientResponse) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO recipients (recipient_id, key_status, created_at) VALUES (?,?,?)",
            (resp.recipient_id, resp.key_status.value, resp.created_at),
        )
        self.conn.commit()

    def get_recipient(self, recipient_id: str) -> RecipientResponse | None:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM recipients WHERE recipient_id = ?",
            (recipient_id,),
        )
        row = cur.fetchone()
        if row:
            return RecipientResponse(
                recipient_id=row["recipient_id"],
                key_status=KeyStatus(row["key_status"]),
                created_at=row["created_at"],
            )
        return None

    # ---------------------------------------------------------------------
    # Document / envelope helpers (write‑only, no secret leakage)
    # ---------------------------------------------------------------------
    def insert_document(
        self,
        document_id: str,
        recipient_id: str,
        status: DocumentStatus,
        created_at: str,
    ) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO documents (document_id, recipient_id, status, created_at) VALUES (?,?,?,?)",
            (document_id, recipient_id, status.value, created_at),
        )
        self.conn.commit()

    def insert_envelope(self, env: EncryptedEnvelope) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO envelopes (
                envelope_id, document_id, encrypted_key, ciphertext, token_digest,
                kem_algorithm, symmetric_algorithm, kdf_algorithm
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                env.envelope_id,
                env.document_id,
                env.encrypted_key,
                env.ciphertext,
                env.token_digest,
                env.kem_algorithm.value,
                env.symmetric_algorithm.value,
                env.kdf_algorithm.value,
            ),
        )
        self.conn.commit()

    # ---------------------------------------------------------------------
    # Ledger helpers
    # ---------------------------------------------------------------------
    def append_block(self, block: LedgerBlock, block_hash: str) -> None:
        """Insert a committed ledger block.

        ``block_hash`` is the SHA3‑256 hash computed by ``build_ledger_block``.
        The block ``sequence`` is derived from the current chain height.
        """
        sequence = self.chain_height()
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO ledger_blocks (
                block_id, sequence, previous_hash, merkle_root, status, block_hash, raw_json
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (
                block.block_id,
                sequence,
                block.previous_hash,
                block.merkle_root,
                block.status.value,
                block_hash,
                block.json(),
            ),
        )
        self.conn.commit()

    def latest_block(self) -> Tuple[int, str] | None:
        """Return ``(sequence, block_hash)`` of the most recent block or ``None``."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT sequence, block_hash FROM ledger_blocks ORDER BY sequence DESC LIMIT 1"
        )
        row = cur.fetchone()
        return (row["sequence"], row["block_hash"]) if row else None

    def chain_height(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ledger_blocks")
        return cur.fetchone()[0]

    # ---------------------------------------------------------------------
    # Generic utilities
    # ---------------------------------------------------------------------
    def close(self) -> None:
        self.conn.close()
