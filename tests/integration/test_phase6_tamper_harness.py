"""Phase 6 Adversarial Cryptographic Tamper & Stress Test Harness (Member A).

Validates strict fail-closed security invariants across 7 adversarial attack vectors:
1. Ciphertext bit-flipping attack (AES-256-GCM AEAD tag failure).
2. KEM ciphertext tampering (ML-KEM-768 invalid ciphertext / decapsulation divergence).
3. Recipient key impersonation (unauthorized recipient opening victim's envelope).
4. HKDF context binding bypass (version / document ID substitution).
5. Canonical event tampering / ML-DSA-65 signature repudiation.
6. Revoked recipient key enforcement.
7. Byzantine validator partition & quorum failure resistance.
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
import shutil
import tempfile
import uuid
import httpx
from pypdf import PdfWriter
import pytest

from backend.api.contracts import canonical_json_bytes, sha3_256_hex
from backend.app.crypto.encryption import (
    decrypt_document,
    encrypt_document,
    generate_cek,
)
from backend.app.crypto.envelope import (
    RecipientEnvelope,
    create_recipient_envelope,
    open_recipient_envelope,
)
from backend.app.crypto.key_manager import KeyManager, KeyManagerError
from backend.app.crypto.signatures import sign_message, verify_signature
from backend.app.services.recipient_workflow import (
    RecipientWorkflowOrchestrator,
    VerticalSliceError,
)
from backend.ledger.quorum import QuorumCoordinator
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
    tmp_dir = Path(tempfile.mkdtemp(prefix="phase6_tamper_"))
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


# ---------------------------------------------------------------------------
# Attack 1: AES-256-GCM Bit-Flip Ciphertext Tampering
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_tamper_aes_gcm_ciphertext_bitflip(cluster_env):
    """Attack 1: Flipping a single byte in ciphertext must fail AEAD tag check and release zero bytes."""
    km = cluster_env["key_manager"]
    urls = cluster_env["urls"]
    clients = cluster_env["clients"]

    rec_pub = km.create_recipient_keys("recip_tamper_1", "Lt. Alpha", "alpha@navy.mil")
    kem_ek = base64.b64decode(rec_pub.kem_public_key_b64)

    coordinator = QuorumCoordinator(validator_urls=urls, clients=clients)
    orchestrator = RecipientWorkflowOrchestrator(key_manager=km, quorum_coordinator=coordinator)

    cek = generate_cek()
    pdf_bytes = create_synthetic_pdf()
    encrypted_doc = bytearray(encrypt_document(pdf_bytes, cek))

    # Bit-flip attack: flip byte at middle of ciphertext
    flip_index = len(encrypted_doc) // 2
    encrypted_doc[flip_index] ^= 0x01

    envelope = create_recipient_envelope(cek, "recip_tamper_1", kem_ek, "doc-bitflip", "v1")

    with pytest.raises(VerticalSliceError, match="Local decryption failed"):
        await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="recip_tamper_1",
            envelope=envelope,
            encrypted_document_bytes=bytes(encrypted_doc),
            document_id="doc-bitflip",
            version_id="v1",
        )


# ---------------------------------------------------------------------------
# Attack 2: KEM Ciphertext Tampering
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_tamper_kem_ciphertext_fails_closed(cluster_env):
    """Attack 2: Tampering with ML-KEM-768 encapsulated key fails decapsulation or unwraps garbage CEK."""
    km = cluster_env["key_manager"]
    urls = cluster_env["urls"]
    clients = cluster_env["clients"]

    rec_pub = km.create_recipient_keys("recip_tamper_2", "Lt. Beta", "beta@navy.mil")
    kem_ek = base64.b64decode(rec_pub.kem_public_key_b64)

    coordinator = QuorumCoordinator(validator_urls=urls, clients=clients)
    orchestrator = RecipientWorkflowOrchestrator(key_manager=km, quorum_coordinator=coordinator)

    cek = generate_cek()
    pdf_bytes = create_synthetic_pdf()
    encrypted_doc = encrypt_document(pdf_bytes, cek)

    envelope = create_recipient_envelope(cek, "recip_tamper_2", kem_ek, "doc-kem-tamper", "v1")

    # Corrupt the KEM encapsulated ciphertext bytes
    kem_ct_bytes = bytearray(envelope.kem_ciphertext)
    kem_ct_bytes[10] ^= 0xFF
    tampered_envelope = RecipientEnvelope(
        recipient_id=envelope.recipient_id,
        recipient_fingerprint=envelope.recipient_fingerprint,
        kem_ciphertext=bytes(kem_ct_bytes),
        wrapping_nonce=envelope.wrapping_nonce,
        wrapped_cek=envelope.wrapped_cek,
    )

    with pytest.raises(VerticalSliceError, match="Local decryption failed"):
        await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="recip_tamper_2",
            envelope=tampered_envelope,
            encrypted_document_bytes=encrypted_doc,
            document_id="doc-kem-tamper",
            version_id="v1",
        )


# ---------------------------------------------------------------------------
# Attack 3: Unauthorized Recipient Impersonation
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_tamper_unauthorized_recipient_impersonation(cluster_env):
    """Attack 3: Recipient Bob cannot decrypt an envelope encrypted for Recipient Alice."""
    km = cluster_env["key_manager"]
    urls = cluster_env["urls"]
    clients = cluster_env["clients"]

    alice_pub = km.create_recipient_keys("alice", "Capt. Alice", "alice@navy.mil")
    bob_pub = km.create_recipient_keys("bob", "Cmdr. Bob", "bob@navy.mil")
    alice_kem_ek = base64.b64decode(alice_pub.kem_public_key_b64)

    coordinator = QuorumCoordinator(validator_urls=urls, clients=clients)
    orchestrator = RecipientWorkflowOrchestrator(key_manager=km, quorum_coordinator=coordinator)

    cek = generate_cek()
    pdf_bytes = create_synthetic_pdf()
    encrypted_doc = encrypt_document(pdf_bytes, cek)

    # Envelope generated strictly for Alice
    alice_envelope = create_recipient_envelope(cek, "alice", alice_kem_ek, "doc-confidential", "v1")

    # Scenario A: Bob passes his own recipient_id with Alice's envelope -> ID mismatch
    with pytest.raises(VerticalSliceError, match="Recipient ID mismatch"):
        await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="bob",
            envelope=alice_envelope,
            encrypted_document_bytes=encrypted_doc,
            document_id="doc-confidential",
            version_id="v1",
        )

    # Scenario B: Bob rewrites recipient_id in envelope to "bob", but tries opening with Bob's private key
    spoofed_envelope = RecipientEnvelope(
        recipient_id="bob",
        recipient_fingerprint=bob_pub.kem_fingerprint,
        kem_ciphertext=alice_envelope.kem_ciphertext,
        wrapping_nonce=alice_envelope.wrapping_nonce,
        wrapped_cek=alice_envelope.wrapped_cek,
    )

    with pytest.raises(VerticalSliceError, match="Local decryption failed"):
        await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="bob",
            envelope=spoofed_envelope,
            encrypted_document_bytes=encrypted_doc,
            document_id="doc-confidential",
            version_id="v1",
        )


# ---------------------------------------------------------------------------
# Attack 4: HKDF Context Binding Bypass (Version / Document Confusion)
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_tamper_hkdf_context_binding_mismatch(cluster_env):
    """Attack 4: An envelope bound to doc-A v1 cannot be used to decrypt doc-B or doc-A v2."""
    km = cluster_env["key_manager"]
    urls = cluster_env["urls"]
    clients = cluster_env["clients"]

    rec_pub = km.create_recipient_keys("recip_ctx", "Major C", "c@navy.mil")
    kem_ek = base64.b64decode(rec_pub.kem_public_key_b64)

    coordinator = QuorumCoordinator(validator_urls=urls, clients=clients)
    orchestrator = RecipientWorkflowOrchestrator(key_manager=km, quorum_coordinator=coordinator)

    cek = generate_cek()
    pdf_bytes = create_synthetic_pdf()
    encrypted_doc = encrypt_document(pdf_bytes, cek)

    envelope = create_recipient_envelope(cek, "recip_ctx", kem_ek, "doc-original", "v1")

    # Attempt with altered document_id
    with pytest.raises(VerticalSliceError, match="Local decryption failed"):
        await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="recip_ctx",
            envelope=envelope,
            encrypted_document_bytes=encrypted_doc,
            document_id="doc-substituted",
            version_id="v1",
        )

    # Attempt with altered version_id
    with pytest.raises(VerticalSliceError, match="Local decryption failed"):
        await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="recip_ctx",
            envelope=envelope,
            encrypted_document_bytes=encrypted_doc,
            document_id="doc-original",
            version_id="v2",
        )


# ---------------------------------------------------------------------------
# Attack 5: ML-DSA-65 Signature Repudiation / Canonical Event Tampering
# ---------------------------------------------------------------------------
def test_tamper_mldsa_canonical_event_repudiation(cluster_env):
    """Attack 5: Altering any single byte in canonical event invalidates the recipient ML-DSA-65 signature."""
    km = cluster_env["key_manager"]
    rec_pub = km.create_recipient_keys("recip_sig_test", "Capt. S", "s@navy.mil")
    kem_dk, dsa_sk = km.load_private_keys("recip_sig_test")
    dsa_pk = base64.b64decode(rec_pub.dsa_public_key_b64)

    original_event = {
        "action": "DOCUMENT_DECRYPTED",
        "document_id": "doc-audit-100",
        "event_id": "evt-orig-1234",
        "output_hash": "a" * 64,
        "recipient_id": "recip_sig_test",
        "timestamp": "2026-11-23T12:00:00Z",
    }
    canonical_bytes = canonical_json_bytes(original_event)
    sig = sign_message(canonical_bytes, dsa_sk)

    # Legitimate signature must verify
    assert verify_signature(dsa_pk, canonical_bytes, sig) is True

    # Tamper 1: Alter document_id in event
    tampered_event = dict(original_event)
    tampered_event["document_id"] = "doc-audit-999"
    assert verify_signature(dsa_pk, canonical_json_bytes(tampered_event), sig) is False

    # Tamper 2: Alter output_hash in event
    tampered_event_2 = dict(original_event)
    tampered_event_2["output_hash"] = "b" * 64
    assert verify_signature(dsa_pk, canonical_json_bytes(tampered_event_2), sig) is False

    # Tamper 3: Random/forged signature bytes
    forged_sig = bytearray(sig)
    forged_sig[100] ^= 0x55
    assert verify_signature(dsa_pk, canonical_bytes, bytes(forged_sig)) is False


# ---------------------------------------------------------------------------
# Attack 6: Revoked Recipient Key Enforcement
# ---------------------------------------------------------------------------
def test_tamper_revoked_recipient_keys_blocked(cluster_env):
    """Attack 6: Revoked recipient status prevents loading or using private keys."""
    km = cluster_env["key_manager"]
    rec_pub = km.create_recipient_keys("recip_revoked", "Ex-Agent R", "r@navy.mil")
    assert rec_pub.status == "active"

    # Revoke recipient
    revoked_pub = km.revoke_recipient("recip_revoked")
    assert revoked_pub.status == "revoked"

    # Keystore load must reject revoked recipient
    with pytest.raises(KeyManagerError, match="Recipient 'recip_revoked' is revoked"):
        km.load_private_keys("recip_revoked")


# ---------------------------------------------------------------------------
# Attack 7: Byzantine Validator Partition (Quorum Failure Rejection)
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_tamper_byzantine_quorum_partition_blocks_release(cluster_env):
    """Attack 7: Byzantine nodes refusing consensus must fail closed without releasing document."""
    km = cluster_env["key_manager"]
    urls = cluster_env["urls"]

    rec_pub = km.create_recipient_keys("recip_byzantine", "Cmdr. B", "b@navy.mil")
    kem_ek = base64.b64decode(rec_pub.kem_public_key_b64)

    # Simulate 2 of 3 Byzantine validators returning HTTP 500 error
    byzantine_clients = {
        urls[0]: cluster_env["clients"][urls[0]],
        urls[1]: httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(500, json={"detail": "Byzantine drop"}))),
        urls[2]: httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(500, json={"detail": "Byzantine drop"}))),
    }

    coordinator = QuorumCoordinator(validator_urls=urls, clients=byzantine_clients)
    orchestrator = RecipientWorkflowOrchestrator(key_manager=km, quorum_coordinator=coordinator)

    cek = generate_cek()
    pdf_bytes = create_synthetic_pdf()
    encrypted_doc = encrypt_document(pdf_bytes, cek)
    envelope = create_recipient_envelope(cek, "recip_byzantine", kem_ek, "doc-byzantine", "v1")

    # Execution must fail closed with VerticalSliceError
    with pytest.raises(VerticalSliceError, match="Consensus quorum failed: release blocked"):
        await orchestrator.execute_recipient_decrypt_and_release(
            recipient_id="recip_byzantine",
            envelope=envelope,
            encrypted_document_bytes=encrypted_doc,
            document_id="doc-byzantine",
            version_id="v1",
        )
