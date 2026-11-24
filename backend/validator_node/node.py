"""Standalone Validator Node application for OfflineTrace.

Provides isolated validator node API endpoints:
- GET  /health   -> NodeHealthResponse
- POST /propose  -> ValidatorSignature (or HTTP 400 with ErrorCode)
- POST /commit   -> accepts CommitCertificate (>=2 distinct signatures), commits block
- GET  /chain    -> committed blocks from isolated node DB
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..api.contracts import (
    CommitCertificate,
    ErrorCode,
    LedgerBlock,
    LedgerProposal,
    LedgerStatus,
    NodeHealthResponse,
    ValidatorSignature,
    canonical_json_bytes,
    sha3_256_hex,
)
from ..api.interfaces import CryptoProvider
from ..ledger.crypto_provider import DefaultCryptoProvider, default_crypto_provider
from ..ledger.models import build_ledger_block, verify_block_integrity
from ..storage.db import Database


def create_validator_app(
    node_id: str,
    db_path: str,
    validator_key_id: str = "key-default",
    crypto_provider: Optional[CryptoProvider] = None,
) -> FastAPI:
    """Factory to create an isolated validator node FastAPI app."""
    app = FastAPI(title=f"OfflineTrace Validator Node [{node_id}]", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_origin_regex=r".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.node_id = node_id
    app.state.db_path = db_path
    app.state.key_id = validator_key_id
    app.state.crypto = crypto_provider or default_crypto_provider
    app.state.start_time = time.time()
    app.state.db = Database(db_path=db_path, node_id=node_id)
    # Cache pending proposals for commit lookup: proposal_id -> (proposal, block, block_hash)
    app.state.pending_proposals: Dict[str, Any] = {}

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        mapping = {
            400: ErrorCode.INVALID_REQUEST,
            401: ErrorCode.UNAUTHORIZED,
            404: ErrorCode.NOT_FOUND,
            500: ErrorCode.INTERNAL_ERROR,
            502: ErrorCode.BAD_GATEWAY,
        }
        error_code = mapping.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error_code.value, "detail": exc.detail},
        )

    @app.get("/health", response_model=NodeHealthResponse, tags=["Validator"])
    async def health() -> NodeHealthResponse:
        height = app.state.db.chain_height()
        latest = app.state.db.latest_block()
        latest_hash = latest[1] if latest else ("0" * 64)
        uptime = int(time.time() - app.state.start_time)
        heartbeat = datetime.now(timezone.utc).isoformat()
        return NodeHealthResponse(
            node_id=app.state.node_id,
            status="HEALTHY",
            uptime_seconds=uptime,
            last_heartbeat=heartbeat,
            chain_height=height,
            latest_hash=latest_hash,
        )

    @app.post("/propose", response_model=ValidatorSignature, status_code=status.HTTP_200_OK, tags=["Validator"])
    async def propose(proposal: LedgerProposal) -> ValidatorSignature:
        # 1. Event uniqueness / replay prevention
        if app.state.db.has_event_id(proposal.event.event_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replay detected: event_id '{proposal.event.event_id}' has already been committed",
            )

        # 2. Check chain height and previous hash
        height = app.state.db.chain_height()
        latest = app.state.db.latest_block()
        expected_prev_hash = latest[1] if latest else ("0" * 64)

        # 3. Deterministic block building
        block, block_hash = build_ledger_block(
            sequence=height,
            previous_hash=expected_prev_hash,
            proposals=[proposal],
            status=LedgerStatus.PENDING,
        )

        # Verify block integrity
        if not verify_block_integrity(block, block_hash, expected_prev_hash, height):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Block integrity verification failed during proposal evaluation",
            )

        # 4. Cache proposal for commit step
        app.state.pending_proposals[proposal.proposal_id] = {
            "proposal": proposal,
            "block": block,
            "block_hash": block_hash,
            "sequence": height,
            "previous_hash": expected_prev_hash,
        }

        # 5. Sign the proposal using the validator's key
        sig = app.state.crypto.sign_validator_proposal(proposal, app.state.node_id)
        return sig

    @app.post("/commit", status_code=status.HTTP_200_OK, tags=["Validator"])
    async def commit(certificate: CommitCertificate) -> Dict[str, Any]:
        # 1. Quorum verification: at least 2 signatures
        if len(certificate.signatures) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient signatures for quorum: received {len(certificate.signatures)}, required >= 2",
            )

        # 2. Distinct validator identities
        val_ids = [s.validator_id for s in certificate.signatures]
        if len(set(val_ids)) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate validator signatures detected: quorum requires >= 2 distinct validator identities",
            )

        # 3. Retrieve cached proposal
        cached = app.state.pending_proposals.get(certificate.proposal_id)
        if not cached:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown proposal_id '{certificate.proposal_id}' or proposal expired",
            )

        proposal = cached["proposal"]
        block = cached["block"]
        block_hash = cached["block_hash"]
        proposal_bytes = canonical_json_bytes(proposal.model_dump())

        # 4. Verify each validator signature against the proposal bytes
        valid_count = 0
        distinct_valid_ids = set()
        for sig_entry in certificate.signatures:
            if app.state.crypto.verify_mldsa_signature(
                proposal_bytes, sig_entry.signature, sig_entry.validator_id
            ):
                distinct_valid_ids.add(sig_entry.validator_id)
                valid_count += 1

        if len(distinct_valid_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cryptographic verification failed: only {len(distinct_valid_ids)} valid signatures found, required >= 2",
            )

        # 5. Commit block to SQLite DB
        block.status = LedgerStatus.COMMITTED
        app.state.db.append_block(block, block_hash)

        # Record commit certificate
        sigs_raw = [s.model_dump() for s in certificate.signatures]
        app.state.db.conn.cursor().execute(
            """
            INSERT OR REPLACE INTO commit_certificates (certificate_id, proposal_id, signatures, quorum)
            VALUES (?, ?, ?, ?)
            """,
            (
                certificate.certificate_id,
                certificate.proposal_id,
                canonical_json_bytes(sigs_raw).decode("utf-8"),
                certificate.quorum,
            ),
        )
        app.state.db.conn.commit()

        # Clean up cache
        del app.state.pending_proposals[certificate.proposal_id]

        return {
            "status": "COMMITTED",
            "block_id": block.block_id,
            "block_hash": block_hash,
            "chain_height": app.state.db.chain_height(),
        }

    @app.get("/chain", tags=["Validator"])
    async def get_chain() -> List[Dict[str, Any]]:
        return app.state.db.get_blocks()

    return app


# Default standalone app configured from environment
node_id_env = os.environ.get("NODE_ID", "validator-1")
db_path_env = os.environ.get("DB_PATH", f"validator_data/{node_id_env}.db")
key_id_env = os.environ.get("VALIDATOR_KEY_ID", f"key-{node_id_env}")

app = create_validator_app(
    node_id=node_id_env,
    db_path=db_path_env,
    validator_key_id=key_id_env,
)
