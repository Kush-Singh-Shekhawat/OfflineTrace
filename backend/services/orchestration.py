"""Cross-domain orchestration pipeline for OfflineTrace.

Coordinates the end-to-end flow:
Decryption Event -> Proposal Creation -> 2-of-3 Quorum Consensus -> Fail-Closed Release.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..api.contracts import (
    CommitCertificate,
    LedgerEvent,
    LedgerProposal,
    ValidatorSignature,
)
from ..ledger.quorum import QuorumCoordinator, QuorumFailedError


class ReleaseOrchestrator:
    """Orchestrates decryption event commitment and fail-closed document release."""

    def __init__(self, coordinator: QuorumCoordinator) -> None:
        self.coordinator = coordinator

    async def commit_decryption_event(
        self,
        event: LedgerEvent,
        document_id: str,
        recipient_signature: Optional[ValidatorSignature] = None,
    ) -> CommitCertificate:
        """Package a decryption event into a proposal and commit via 2-of-3 quorum.

        Fails closed: if 2-of-3 quorum is not reached, raises QuorumFailedError
        and does not permit document release.
        """
        signatures: List[ValidatorSignature] = []
        if recipient_signature:
            signatures.append(recipient_signature)

        proposal = LedgerProposal(
            proposal_id=f"prop-{event.event_id}",
            event=event,
            document_id=document_id,
            validator_signatures=signatures,
        )

        # QuorumCoordinator enforces >= 2 distinct signatures and fails closed
        certificate = await self.coordinator.propose_and_commit(proposal)
        return certificate
