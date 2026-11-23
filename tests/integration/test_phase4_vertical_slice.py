"""Phase 4 Integration Tests: First Vertical Slice (A + B + C).

Verification criteria per Phase 4 specification:
1. End-to-end flow:
   Recipient-local decrypt -> unique watermark -> output hash -> canonical event ->
   recipient signature -> 2-of-3 quorum commit -> release output.
2. Full flow passes twice consecutively on synthetic PDF fixtures.
3. Strict fail-closed release gate: No output is released before valid quorum!
4. Forensic extractability: Watermark extracted from released PDF matches session token.
"""

import base64
from io import BytesIO
from pathlib import Path
import shutil
import tempfile
import httpx
from pypdf import PdfWriter
import pytest

from backend.app.crypto.encryption import encrypt_document, generate_cek
from backend.app.crypto.envelope import create_recipient_envelope
from backend.app.crypto.key_manager import KeyManager
from backend.app.crypto.signatures import verify_signature
from backend.app.services.recipient_workflow import (
    RecipientWorkflowOrchestrator,
    VerticalSliceError,
)
from backend.app.watermark.extract import extract_watermark
from backend.ledger.quorum import QuorumCoordinator
from backend.storage.db import Database
from backend.validator_node.node import create_validator_app


def create_synthetic_pdf(title: str = "Classified Fleet Orders") -> bytes:
    """Generate a clean synthetic single-page PDF fixture."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()


@pytest.fixture
def cluster_env():
    """Create a temporary 3-validator cluster and recipient keystore."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="phase4_slice_"))
    db_paths = [
        str(tmp_dir / "val1.db"),
        str(tmp_dir / "val2.db"),
        str(tmp_dir / "val3.db"),
    ]
    apps = [
        create_validator_app(node_id="val-1", db_path=db_paths[0]),
        create_validator_app(node_id="val-2", db_path=db_paths[1]),
        create_validator_app(node_id="val-3", db_path=db_paths[2]),
    ]
    urls = ["http://val-1", "http://val-2", "http://val-3"]
    clients = {
        urls[0]: httpx.AsyncClient(transport=httpx.ASGITransport(app=apps[0]), base_url=urls[0]),
        urls[1]: httpx.AsyncClient(transport=httpx.ASGITransport(app=apps[1]), base_url=urls[1]),
        urls[2]: httpx.AsyncClient(transport=httpx.ASGITransport(app=apps[2]), base_url=urls[2]),
    }
    km = KeyManager(keystore_dir=tmp_dir / "keystore")

    yield {
        "tmp_dir": tmp_dir,
        "db_paths": db_paths,
        "apps": apps,
        "urls": urls,
        "clients": clients,
        "key_manager": km,
    }

    # Teardown
    for app in apps:
        app.state.db.close()
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.mark.anyio
async def test_vertical_slice_full_flow_passes_twice(cluster_env):
    """Phase 4 release gate: Full flow passes twice consecutively on synthetic fixtures."""
    km = cluster_env["key_manager"]
    urls = cluster_env["urls"]
    clients = cluster_env["clients"]

    # Enroll test recipient with ML-KEM-768 and ML-DSA-65 keys
    rec_pub = km.create_recipient_keys(
        recipient_id="recip_wesee_alpha",
        name="Capt. A. Verma",
        email="a.verma@wesee.navy.in",
        passphrase="test-passphrase",
    )
    kem_ek = base64.b64decode(rec_pub.kem_public_key_b64)
    dsa_pk = base64.b64decode(rec_pub.dsa_public_key_b64)

    coordinator = QuorumCoordinator(validator_urls=urls, clients=clients)
    orchestrator = RecipientWorkflowOrchestrator(key_manager=km, quorum_coordinator=coordinator)

    # Run the full vertical slice twice consecutively with different documents
    for run_idx in (1, 2):
        doc_id = f"doc-synthetic-mission-{run_idx}"
        pdf_bytes = create_synthetic_pdf(f"Mission Directive {run_idx}")

        # 1. Sender encrypts once with fresh random 32-byte CEK
        cek = generate_cek()
        encrypted_doc = encrypt_document(pdf_bytes, cek)

        # 2. Sender creates recipient envelope (ML-KEM-768 + HKDF-SHA-256)
        envelope = create_recipient_envelope(
            cek=cek,
            recipient_id="recip_wesee_alpha",
            recipient_kem_public_key=kem_ek,
            document_id=doc_id,
            version_id="v1",
        )

        # 3. Recipient executes complete vertical slice
        result = await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="recip_wesee_alpha",
            envelope=envelope,
            encrypted_document_bytes=encrypted_doc,
            document_id=doc_id,
            version_id="v1",
            passphrase="test-passphrase",
        )

        # --- Assertions on Released Output ---
        assert result.released_document is not None
        assert result.released_document.startswith(b"%PDF-")

        # --- Forensic Watermark Check ---
        extracted_token = extract_watermark(result.released_document)
        assert extracted_token == result.session_watermark_token

        # --- 2-of-3 Quorum Certificate Check ---
        assert len(result.commit_certificate.signatures) >= 2
        assert result.commit_certificate.quorum == 2
        assert result.commit_certificate.proposal_id.startswith("prop-")

        # --- ML-DSA-65 Recipient Signature Verification ---
        from backend.api.contracts import canonical_json_bytes

        sig_bytes = base64.b64decode(result.recipient_signature_b64)
        canonical_bytes = canonical_json_bytes(result.canonical_event)
        assert verify_signature(dsa_pk, canonical_bytes, sig_bytes) is True


@pytest.mark.anyio
async def test_vertical_slice_fails_closed_no_output_before_quorum(cluster_env):
    """Release invariant: No output released if 2-of-3 quorum cannot be reached."""
    km = cluster_env["key_manager"]
    urls = cluster_env["urls"]

    rec_pub = km.create_recipient_keys("recip_beta", "Lieut. B", "b@navy.mil")
    kem_ek = base64.b64decode(rec_pub.kem_public_key_b64)

    # Simulate network partition: only val-1 is online; val-2 and val-3 fail (1-of-3 only)
    broken_clients = {
        urls[0]: cluster_env["clients"][urls[0]],
        urls[1]: httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(503))),
        urls[2]: httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(503))),
    }

    coordinator = QuorumCoordinator(validator_urls=urls, clients=broken_clients)
    orchestrator = RecipientWorkflowOrchestrator(key_manager=km, quorum_coordinator=coordinator)

    cek = generate_cek()
    pdf_bytes = create_synthetic_pdf()
    encrypted_doc = encrypt_document(pdf_bytes, cek)
    envelope = create_recipient_envelope(
        cek, "recip_beta", kem_ek, "doc-fail-closed", "v1"
    )

    # Must raise VerticalSliceError (fail-closed release gate)
    with pytest.raises(VerticalSliceError, match="Consensus quorum failed: release blocked"):
        await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="recip_beta",
            envelope=envelope,
            encrypted_document_bytes=encrypted_doc,
            document_id="doc-fail-closed",
            version_id="v1",
        )

    # Verify that NO block was committed to any validator node DB
    for db_path in cluster_env["db_paths"]:
        db = Database(db_path, node_id="audit")
        assert db.chain_height() == 0
        db.close()


@pytest.mark.anyio
async def test_vertical_slice_tampered_envelope_fails_closed(cluster_env):
    """Tampered envelope must fail closed before reaching quorum."""
    km = cluster_env["key_manager"]
    urls = cluster_env["urls"]
    clients = cluster_env["clients"]

    rec_pub = km.create_recipient_keys("recip_gamma", "Lieut. G", "g@navy.mil")
    kem_ek = base64.b64decode(rec_pub.kem_public_key_b64)

    coordinator = QuorumCoordinator(validator_urls=urls, clients=clients)
    orchestrator = RecipientWorkflowOrchestrator(key_manager=km, quorum_coordinator=coordinator)

    cek = generate_cek()
    pdf_bytes = create_synthetic_pdf()
    encrypted_doc = encrypt_document(pdf_bytes, cek)
    envelope = create_recipient_envelope(
        cek, "recip_gamma", kem_ek, "doc-tamper-test", "v1"
    )

    # Tamper with document ID in context binding
    with pytest.raises(VerticalSliceError, match="Local decryption failed"):
        await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="recip_gamma",
            envelope=envelope,
            encrypted_document_bytes=encrypted_doc,
            document_id="wrong-doc-id-tamper",
            version_id="v1",
        )
