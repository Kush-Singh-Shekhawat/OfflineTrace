"""Unit test to verify contracts_v1.json fixture validity against Pydantic schemas."""

import json
from pathlib import Path

from backend.api.contracts import (
    CommitCertificate,
    EncryptedEnvelope,
    InvestigationReport,
    LedgerProposal,
    RecipientRegisterRequest,
    RecipientResponse,
)


def test_contracts_v1_fixture():
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "contracts_v1.json"
    assert fixture_path.exists(), "contracts_v1.json fixture must exist"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("schema_version") == "1.0.0"

    # Validate recipient
    rec = data["recipient"]
    reg_req = RecipientRegisterRequest.model_validate(rec)
    rec_resp = RecipientResponse.model_validate(rec)
    assert reg_req.recipient_id == rec["recipient_id"]
    assert rec_resp.recipient_id == rec["recipient_id"]

    # Validate encrypted envelope
    env = EncryptedEnvelope.model_validate(data["encrypted_envelope"])
    assert env.envelope_id == data["encrypted_envelope"]["envelope_id"]
    assert env.kem_algorithm.value == "ML-KEM-768"
    assert env.symmetric_algorithm.value == "AES-256-GCM"
    assert env.kdf_algorithm.value == "HKDF-SHA-256"

    # Validate ledger proposal
    prop = LedgerProposal.model_validate(data["ledger_proposal"])
    assert prop.proposal_id == data["ledger_proposal"]["proposal_id"]

    # Validate commit certificate
    cert = CommitCertificate.model_validate(data["commit_certificate"])
    assert cert.proposal_id == data["commit_certificate"]["proposal_id"]
    assert cert.quorum == 2

    # Validate investigation report
    inv = InvestigationReport.model_validate(data["investigation_report"])
    assert inv.investigation_id == data["investigation_report"]["investigation_id"]
    assert inv.confidence == 0.94
