"""Unit tests for Member A crypto modules:
- AES-256-GCM encryption & decryption
- HKDF-SHA-256 context-bound derivation
- ML-KEM-768 key encapsulation & decapsulation (FIPS 203)
- ML-DSA-65 digital signatures & fingerprinting (FIPS 204)
- Per-recipient CEK envelopes (1 ciphertext, N envelopes)
"""

import base64
import hashlib
import pytest
from backend.app.crypto.encryption import (
    CEK_LENGTH_BYTES,
    DecryptionError,
    EncryptedPayload,
    decrypt_document,
    decrypt_payload,
    encrypt_document,
    encrypt_payload,
    generate_cek,
)
from backend.app.crypto.envelope import (
    RecipientEnvelope,
    create_recipient_envelope,
    open_recipient_envelope,
)
from backend.app.crypto.key_manager import KeyManager, KeyManagerError
from backend.app.services.recipient_crypto import RecipientCryptoService, RecipientServiceError
from backend.app.crypto.kem import (
    ML_KEM_768_CIPHERTEXT_BYTES,
    ML_KEM_768_DK_BYTES,
    ML_KEM_768_EK_BYTES,
    ML_KEM_768_SHARED_SECRET_BYTES,
    decapsulate_key,
    encapsulate_key,
    generate_kem_keypair,
)
from backend.app.crypto.key_derivation import (
    derive_envelope_key,
    derive_key,
)
from backend.app.crypto.signatures import (
    ML_DSA_65_PK_BYTES,
    ML_DSA_65_SIG_BYTES,
    ML_DSA_65_SK_BYTES,
    compute_fingerprint,
    generate_signing_keypair,
    sign_message,
    verify_signature,
)


class TestKeyDerivation:
    """Tests for HKDF-SHA-256 key derivation."""

    def test_derive_key_length_and_determinism(self):
        secret = b"sample_shared_secret_material_32B!"
        salt = b"test_salt_123"
        info = b"test_info_context"

        k1 = derive_key(secret, salt=salt, info=info, length=32)
        k2 = derive_key(secret, salt=salt, info=info, length=32)

        assert len(k1) == 32
        assert k1 == k2

    def test_derive_key_different_inputs_produce_different_keys(self):
        secret1 = b"shared_secret_1"
        secret2 = b"shared_secret_2"

        k1 = derive_key(secret1, length=32)
        k2 = derive_key(secret2, length=32)
        assert k1 != k2

    def test_derive_envelope_key_context_binding(self):
        secret = b"shared_kem_secret_for_testing_only"
        doc_id = "doc-uuid-001"
        ver_id = "v1"
        fp1 = "sha3_256_recipient_fingerprint_aaa"
        fp2 = "sha3_256_recipient_fingerprint_bbb"

        key_recip1 = derive_envelope_key(secret, doc_id, ver_id, fp1)
        key_recip2 = derive_envelope_key(secret, doc_id, ver_id, fp2)

        assert len(key_recip1) == 32
        assert len(key_recip2) == 32
        assert key_recip1 != key_recip2

        key_other_doc = derive_envelope_key(secret, "doc-uuid-002", ver_id, fp1)
        assert key_recip1 != key_other_doc

        key_other_ver = derive_envelope_key(secret, doc_id, "v2", fp1)
        assert key_recip1 != key_other_ver

    def test_derive_key_invalid_inputs(self):
        with pytest.raises(ValueError, match="must not be empty"):
            derive_key(b"")

        with pytest.raises(ValueError, match="must be positive"):
            derive_key(b"secret", length=0)

        with pytest.raises(ValueError, match="document_id must not be empty"):
            derive_envelope_key(b"secret", "", "v1", "fp")


class TestEncryption:
    """Tests for AES-256-GCM encryption and decryption."""

    def test_generate_cek(self):
        cek1 = generate_cek()
        cek2 = generate_cek()
        assert len(cek1) == CEK_LENGTH_BYTES
        assert len(cek2) == CEK_LENGTH_BYTES
        assert cek1 != cek2

    def test_round_trip_payload(self):
        key = generate_cek()
        plaintext = b"Top secret synthetic document payload for SIH26237"
        aad = b"doc_metadata_binding"

        payload = encrypt_payload(plaintext, key, associated_data=aad)
        decrypted = decrypt_payload(payload, key)

        assert decrypted == plaintext
        assert len(payload.nonce) == 12
        assert len(payload.tag) == 16

    def test_round_trip_document_packed(self):
        key = generate_cek()
        plaintext = b"%PDF-1.4 synthetic test content for document encryption"
        packed = encrypt_document(plaintext, key)

        decrypted = decrypt_document(packed, key)
        assert decrypted == plaintext

    def test_fail_closed_tampered_ciphertext(self):
        key = generate_cek()
        plaintext = b"Sensitive payload"
        payload = encrypt_payload(plaintext, key)

        tampered_ct = bytearray(payload.ciphertext)
        tampered_ct[0] ^= 0xFF
        bad_payload = EncryptedPayload(
            ciphertext=bytes(tampered_ct),
            nonce=payload.nonce,
            tag=payload.tag,
            associated_data=payload.associated_data,
        )

        with pytest.raises(DecryptionError, match="AEAD verification failed"):
            decrypt_payload(bad_payload, key)

    def test_fail_closed_tampered_tag(self):
        key = generate_cek()
        plaintext = b"Sensitive payload"
        payload = encrypt_payload(plaintext, key)

        tampered_tag = bytearray(payload.tag)
        tampered_tag[0] ^= 0xFF
        bad_payload = EncryptedPayload(
            ciphertext=payload.ciphertext,
            nonce=payload.nonce,
            tag=bytes(tampered_tag),
            associated_data=payload.associated_data,
        )

        with pytest.raises(DecryptionError, match="AEAD verification failed"):
            decrypt_payload(bad_payload, key)

    def test_fail_closed_wrong_key(self):
        key = generate_cek()
        wrong_key = generate_cek()
        plaintext = b"Classified document"
        packed = encrypt_document(plaintext, key)

        with pytest.raises(DecryptionError):
            decrypt_document(packed, wrong_key)

    def test_fail_closed_tampered_associated_data(self):
        key = generate_cek()
        plaintext = b"Bound document"
        payload = encrypt_payload(plaintext, key, associated_data=b"recipient_A")

        bad_payload = EncryptedPayload(
            ciphertext=payload.ciphertext,
            nonce=payload.nonce,
            tag=payload.tag,
            associated_data=b"recipient_B",
        )

        with pytest.raises(DecryptionError):
            decrypt_payload(bad_payload, key)

    def test_invalid_key_length(self):
        with pytest.raises(ValueError, match="Invalid key length"):
            encrypt_payload(b"data", key=b"short_key")


class TestMLKEM768:
    """Tests for ML-KEM-768 Post-Quantum Key Encapsulation (FIPS 203)."""

    def test_kem_keygen_and_lengths(self):
        ek, dk = generate_kem_keypair()
        assert len(ek) == ML_KEM_768_EK_BYTES
        assert len(dk) == ML_KEM_768_DK_BYTES

    def test_kem_encaps_decaps_round_trip(self):
        ek, dk = generate_kem_keypair()
        ss_enc, ct = encapsulate_key(ek)

        assert len(ss_enc) == ML_KEM_768_SHARED_SECRET_BYTES
        assert len(ct) == ML_KEM_768_CIPHERTEXT_BYTES

        ss_dec = decapsulate_key(dk, ct)
        assert ss_enc == ss_dec

    def test_kem_wrong_private_key_fails(self):
        ek1, dk1 = generate_kem_keypair()
        _, dk2 = generate_kem_keypair()

        ss_enc, ct = encapsulate_key(ek1)
        # ML-KEM implicit rejection: decaps with wrong dk produces different pseudorandom key
        ss_wrong = decapsulate_key(dk2, ct)
        assert ss_wrong != ss_enc

    def test_kem_invalid_lengths(self):
        with pytest.raises(ValueError, match="Invalid ML-KEM-768 public key length"):
            encapsulate_key(b"short_key")

        with pytest.raises(ValueError, match="Invalid ML-KEM-768 private key length"):
            decapsulate_key(b"short_key", b"0" * ML_KEM_768_CIPHERTEXT_BYTES)


class TestMLDSA65:
    """Tests for ML-DSA-65 Post-Quantum Digital Signatures (FIPS 204)."""

    def test_dsa_keygen_and_lengths(self):
        pk, sk = generate_signing_keypair()
        assert len(pk) == ML_DSA_65_PK_BYTES
        assert len(sk) == ML_DSA_65_SK_BYTES

    def test_dsa_sign_and_verify_round_trip(self):
        pk, sk = generate_signing_keypair()
        message = b'{"event_id": "evt-001", "action": "decrypted", "timestamp": "2026-11-23T00:00:00Z"}'

        sig = sign_message(message, sk)
        assert len(sig) == ML_DSA_65_SIG_BYTES

        is_valid = verify_signature(pk, message, sig)
        assert is_valid is True

    def test_dsa_tampered_message_fails(self):
        pk, sk = generate_signing_keypair()
        message = b"Canonical event payload"
        sig = sign_message(message, sk)

        assert verify_signature(pk, b"Tampered event payload", sig) is False

    def test_dsa_tampered_signature_fails(self):
        pk, sk = generate_signing_keypair()
        message = b"Canonical event payload"
        sig = sign_message(message, sk)

        tampered_sig = bytearray(sig)
        tampered_sig[10] ^= 0xFF
        assert verify_signature(pk, message, bytes(tampered_sig)) is False

    def test_dsa_wrong_public_key_fails(self):
        pk1, sk1 = generate_signing_keypair()
        pk2, _ = generate_signing_keypair()
        message = b"Canonical event payload"
        sig = sign_message(message, sk1)

        assert verify_signature(pk2, message, sig) is False

    def test_dsa_fingerprint(self):
        pk, _ = generate_signing_keypair()
        fp = compute_fingerprint(pk)
        assert isinstance(fp, str)
        assert len(fp) == 64  # SHA3-256 produces 64 hex characters


class TestRecipientEnvelope:
    """Tests for 1-ciphertext, N-envelope distribution model (Task 5)."""

    def test_one_ciphertext_multiple_recipient_envelopes(self):
        # 1 shared CEK for the document
        cek = generate_cek()
        doc_id = "doc-uuid-999"
        ver_id = "v1"

        # 3 distinct recipients with ML-KEM-768 keys
        r1_ek, r1_dk = generate_kem_keypair()
        r2_ek, r2_dk = generate_kem_keypair()
        r3_ek, r3_dk = generate_kem_keypair()

        # Create 3 envelopes under the same CEK
        env1 = create_recipient_envelope(cek, "recipient_1", r1_ek, doc_id, ver_id)
        env2 = create_recipient_envelope(cek, "recipient_2", r2_ek, doc_id, ver_id)
        env3 = create_recipient_envelope(cek, "recipient_3", r3_ek, doc_id, ver_id)

        # Envelopes must be distinct
        assert env1.kem_ciphertext != env2.kem_ciphertext
        assert env1.wrapped_cek != env2.wrapped_cek
        assert env2.kem_ciphertext != env3.kem_ciphertext

        # Each recipient recovers the exact same CEK locally
        recovered_cek_1 = open_recipient_envelope(env1, r1_dk, doc_id, ver_id)
        recovered_cek_2 = open_recipient_envelope(env2, r2_dk, doc_id, ver_id)
        recovered_cek_3 = open_recipient_envelope(env3, r3_dk, doc_id, ver_id)

        assert recovered_cek_1 == cek
        assert recovered_cek_2 == cek
        assert recovered_cek_3 == cek

    def test_wrong_recipient_cannot_open_envelope(self):
        cek = generate_cek()
        doc_id = "doc-uuid-888"
        ver_id = "v1"

        r1_ek, _ = generate_kem_keypair()
        _, r2_dk = generate_kem_keypair()

        env1 = create_recipient_envelope(cek, "recipient_1", r1_ek, doc_id, ver_id)

        # Recipient 2 attempts to open Recipient 1's envelope -> fail closed
        with pytest.raises(DecryptionError):
            open_recipient_envelope(env1, r2_dk, doc_id, ver_id)

    def test_envelope_tampered_context_fails(self):
        cek = generate_cek()
        doc_id = "doc-uuid-777"
        ver_id = "v1"

        r1_ek, r1_dk = generate_kem_keypair()
        env = create_recipient_envelope(cek, "recipient_1", r1_ek, doc_id, ver_id)

        # Attempt to open with wrong document_id or version_id -> fail closed
        with pytest.raises(DecryptionError):
            open_recipient_envelope(env, r1_dk, "wrong-doc-id", ver_id)

        with pytest.raises(DecryptionError):
            open_recipient_envelope(env, r1_dk, doc_id, "v2")

    def test_envelope_tampered_payload_fails(self):
        cek = generate_cek()
        doc_id = "doc-uuid-666"
        ver_id = "v1"

        r1_ek, r1_dk = generate_kem_keypair()
        env = create_recipient_envelope(cek, "recipient_1", r1_ek, doc_id, ver_id)

        # Tamper wrapped_cek
        bad_wrapped = bytearray(env.wrapped_cek)
        bad_wrapped[5] ^= 0xFF
        bad_env = RecipientEnvelope(
            recipient_id=env.recipient_id,
            recipient_fingerprint=env.recipient_fingerprint,
            kem_ciphertext=env.kem_ciphertext,
            wrapping_nonce=env.wrapping_nonce,
            wrapped_cek=bytes(bad_wrapped),
        )

        with pytest.raises(DecryptionError):
            open_recipient_envelope(bad_env, r1_dk, doc_id, ver_id)

    def test_envelope_serialization_round_trip(self):
        cek = generate_cek()
        r_ek, _ = generate_kem_keypair()
        env = create_recipient_envelope(cek, "recipient_1", r_ek, "doc-1", "v1")

        env_dict = env.to_dict()
        assert isinstance(env_dict["kem_ciphertext"], str)

        reconstructed = RecipientEnvelope.from_dict(env_dict)
        assert reconstructed == env


class TestKeyManager:
    """Tests for recipient key lifecycle and secure local keystore (Task 7)."""

    def test_create_and_load_keys(self, tmp_path):
        km = KeyManager(keystore_dir=tmp_path / "keystore")
        passphrase = "test-secret-passphrase"

        rec = km.create_recipient_keys(
            recipient_id="recip_001",
            name="Alice Defender",
            email="alice@mod.gov.in",
            passphrase=passphrase,
        )

        # Public record checks: no private keys present
        assert rec.recipient_id == "recip_001"
        assert rec.name == "Alice Defender"
        assert rec.status == "active"
        assert rec.kem_algorithm == "ML-KEM-768"
        assert rec.dsa_algorithm == "ML-DSA-65"
        assert len(rec.kem_fingerprint) == 64
        assert len(rec.dsa_fingerprint) == 64
        assert not hasattr(rec, "kem_private_key")
        assert not hasattr(rec, "dsa_private_key")

        # Load private keys with correct passphrase
        kem_dk, dsa_sk = km.load_private_keys("recip_001", passphrase=passphrase)
        assert len(kem_dk) == ML_KEM_768_DK_BYTES
        assert len(dsa_sk) == ML_DSA_65_SK_BYTES

        # Load with wrong passphrase fails closed
        with pytest.raises(KeyManagerError, match="Failed to decrypt private keys"):
            km.load_private_keys("recip_001", passphrase="wrong-passphrase")

    def test_list_and_revoke_keys(self, tmp_path):
        km = KeyManager(keystore_dir=tmp_path / "keystore")
        km.create_recipient_keys("r1", "User 1", "u1@navy.mil")
        km.create_recipient_keys("r2", "User 2", "u2@navy.mil")

        records = km.list_public_records()
        assert len(records) == 2
        ids = [r.recipient_id for r in records]
        assert "r1" in ids and "r2" in ids

        revoked = km.revoke_recipient("r1")
        assert revoked.status == "revoked"
        fetched = km.get_public_record("r1")
        assert fetched.status == "revoked"

    def test_rotate_keys(self, tmp_path):
        km = KeyManager(keystore_dir=tmp_path / "keystore")
        old_rec = km.create_recipient_keys("r_rotate", "User R", "r@navy.mil")

        new_rec = km.rotate_recipient_keys("r_rotate")
        assert new_rec.recipient_id == "r_rotate"
        assert new_rec.status == "active"
        # Fingerprints must be refreshed after rotation
        assert new_rec.kem_fingerprint != old_rec.kem_fingerprint
        assert new_rec.dsa_fingerprint != old_rec.dsa_fingerprint


class TestRecipientCryptoService:
    """Tests for recipient-local decryption & provenance signing service boundary (Task 8)."""

    def test_end_to_end_local_decryption_and_signing(self, tmp_path):
        import base64
        import hashlib

        km = KeyManager(keystore_dir=tmp_path / "keystore")
        rec = km.create_recipient_keys("recip_pilot", "Commander Dave", "dave@wesee.mod")
        recipient_kem_ek = base64.b64decode(rec.kem_public_key_b64)

        # 1. Sender encrypts document once with CEK
        cek = generate_cek()
        original_pdf_bytes = b"%PDF-1.7 Synthetic Classified Navy Mission Directive Payload"
        doc_id = "doc-mission-alpha"
        ver_id = "v1"
        packed_doc = encrypt_document(original_pdf_bytes, cek)

        # 2. Sender creates recipient envelope
        envelope = create_recipient_envelope(
            cek=cek,
            recipient_id="recip_pilot",
            recipient_kem_public_key=recipient_kem_ek,
            document_id=doc_id,
            version_id=ver_id,
        )

        # 3. Recipient local crypto service invocation
        service = RecipientCryptoService(key_manager=km)
        watermark_token = "opaque-session-token-random-xyz123"

        result = service.decrypt_and_sign_provenance(
            recipient_id="recip_pilot",
            envelope=envelope,
            packed_encrypted_document=packed_doc,
            document_id=doc_id,
            version_id=ver_id,
            watermark_token=watermark_token,
        )

        # Decrypted payload matches original
        assert result.decrypted_document == original_pdf_bytes

        # Provenance event checks
        assert result.canonical_event["document_id"] == doc_id
        assert result.canonical_event["recipient_id"] == "recip_pilot"
        assert result.canonical_event["action"] == "DOCUMENT_DECRYPTED"
        expected_digest = hashlib.sha3_256(watermark_token.encode("utf-8")).hexdigest()
        assert result.canonical_event["token_digest"] == expected_digest

        # ML-DSA-65 signature on canonical bytes verifies with recipient's public key
        assert verify_signature(
            result.recipient_dsa_public_key,
            result.canonical_event_bytes,
            result.signature,
        ) is True

        # Ensure provenance payload format is ready for ledger submission
        payload = result.to_provenance_payload()
        assert "signature_b64" in payload
        assert "canonical_event" in payload
        assert payload["recipient_dsa_fingerprint"] == rec.dsa_fingerprint

    def test_recipient_service_fails_on_mismatch_or_tamper(self, tmp_path):
        km = KeyManager(keystore_dir=tmp_path / "keystore")
        rec = km.create_recipient_keys("recip_pilot", "Dave", "dave@wesee.mod")
        recipient_kem_ek = base64.b64decode(rec.kem_public_key_b64)

        cek = generate_cek()
        packed_doc = encrypt_document(b"payload", cek)
        envelope = create_recipient_envelope(
            cek, "recip_pilot", recipient_kem_ek, "doc-1", "v1"
        )
        service = RecipientCryptoService(key_manager=km)

        # Wrong recipient ID fails
        with pytest.raises(RecipientServiceError, match="recipient mismatch"):
            service.decrypt_and_sign_provenance(
                recipient_id="wrong_user",
                envelope=envelope,
                packed_encrypted_document=packed_doc,
                document_id="doc-1",
                version_id="v1",
            )

        # Tampered document ciphertext fails closed
        tampered_doc = bytearray(packed_doc)
        tampered_doc[20] ^= 0xFF
        with pytest.raises(RecipientServiceError, match="Document decryption failed"):
            service.decrypt_and_sign_provenance(
                recipient_id="recip_pilot",
                envelope=envelope,
                packed_encrypted_document=bytes(tampered_doc),
                document_id="doc-1",
                version_id="v1",
            )

    def test_key_manager_delete_recipient(self, tmp_path):
        km = KeyManager(keystore_dir=tmp_path / "keystore")
        km.create_recipient_keys("recip_del", "Delete Me", "del@wesee.mod")
        assert len(km.list_public_records()) == 1

        km.delete_recipient("recip_del")
        assert len(km.list_public_records()) == 0

        with pytest.raises(KeyManagerError, match="not found"):
            km.delete_recipient("recip_del")

