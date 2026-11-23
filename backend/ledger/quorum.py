"""Quorum coordinator and consensus engine for OfflineTrace.

Coordinates proposals across 3 independent validator nodes, enforces 2-of-3 quorum,
fails closed if quorum is not reached, and detects replica divergence across nodes.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
import httpx

from ..api.contracts import (
    CommitCertificate,
    LedgerProposal,
    ValidatorSignature,
    canonical_json_bytes,
)
from ..api.interfaces import CryptoProvider
from .crypto_provider import default_crypto_provider


class QuorumFailedError(Exception):
    """Raised when 2-of-3 validator quorum cannot be achieved (fail-closed)."""
    pass


class QuorumCoordinator:
    """Orchestrates proposal distribution, signature aggregation, and block commits."""

    def __init__(
        self,
        validator_urls: List[str],
        clients: Optional[Dict[str, httpx.AsyncClient]] = None,
        crypto: Optional[CryptoProvider] = None,
    ) -> None:
        self.validator_urls = validator_urls
        self.clients = clients or {}
        self.crypto = crypto or default_crypto_provider

    def _get_client(self, url: str) -> httpx.AsyncClient:
        if url in self.clients:
            return self.clients[url]
        # Return a standard client if not in injected clients
        return httpx.AsyncClient(base_url=url, timeout=5.0)

    async def propose_and_commit(self, proposal: LedgerProposal) -> CommitCertificate:
        """Broadcast proposal to all 3 nodes, verify 2-of-3 quorum, and broadcast commit."""
        # Step 1: Broadcast proposal concurrently
        async def _send_proposal(url: str) -> Optional[ValidatorSignature]:
            client = self._get_client(url)
            try:
                resp = await client.post("/propose", json=proposal.model_dump())
                if resp.status_code == 200:
                    data = resp.json()
                    return ValidatorSignature(**data)
            except Exception:
                pass
            return None

        tasks = [_send_proposal(url) for url in self.validator_urls]
        results = await asyncio.gather(*tasks)

        # Step 2: Validate signatures and enforce 2-of-3 quorum
        proposal_bytes = canonical_json_bytes(proposal.model_dump())
        valid_signatures: List[ValidatorSignature] = []
        seen_validators = set()

        for sig in results:
            if sig is not None:
                if sig.validator_id not in seen_validators:
                    # Cryptographic verification
                    if self.crypto.verify_mldsa_signature(
                        proposal_bytes, sig.signature, sig.validator_id
                    ):
                        seen_validators.add(sig.validator_id)
                        valid_signatures.append(sig)

        # Fail closed if fewer than 2 valid distinct validator signatures
        if len(valid_signatures) < 2:
            raise QuorumFailedError(
                f"Quorum failed: required >= 2 distinct signatures, obtained {len(valid_signatures)} from {list(seen_validators)}"
            )

        # Step 3: Create commit certificate
        certificate = CommitCertificate(
            certificate_id=f"cert-{proposal.proposal_id}",
            proposal_id=proposal.proposal_id,
            signatures=valid_signatures,
            quorum=2,
        )

        # Step 4: Broadcast commit certificate to all validator nodes
        async def _send_commit(url: str):
            client = self._get_client(url)
            try:
                await client.post("/commit", json=certificate.model_dump())
            except Exception:
                pass

        commit_tasks = [_send_commit(url) for url in self.validator_urls]
        await asyncio.gather(*commit_tasks)

        return certificate

    async def check_divergence(self) -> Dict[str, Any]:
        """Fetch health from all nodes and check for state divergence."""
        async def _get_health(url: str) -> Optional[Dict[str, Any]]:
            client = self._get_client(url)
            try:
                resp = await client.get("/health")
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass
            return None

        tasks = [_get_health(url) for url in self.validator_urls]
        results = await asyncio.gather(*tasks)

        node_reports: Dict[str, Any] = {}
        height_hash_map: Dict[int, set] = {}
        divergence_detected = False
        details: List[str] = []

        for url, report in zip(self.validator_urls, results):
            if report:
                node_reports[url] = report
                h = report.get("chain_height", 0)
                lh = report.get("latest_hash", "")
                if h not in height_hash_map:
                    height_hash_map[h] = set()
                height_hash_map[h].add(lh)
            else:
                node_reports[url] = {"status": "UNREACHABLE"}

        # Check if any height has multiple distinct hashes
        for h, hashes in height_hash_map.items():
            if len(hashes) > 1:
                divergence_detected = True
                details.append(
                    f"Divergence at height {h}: conflicting block hashes {list(hashes)}"
                )

        return {
            "divergence_detected": divergence_detected,
            "nodes": node_reports,
            "details": "; ".join(details) if details else "No divergence detected",
        }
