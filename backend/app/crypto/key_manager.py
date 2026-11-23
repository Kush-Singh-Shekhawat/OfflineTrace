"""Key metadata and lifecycle management for OfflineTrace (Member A).

Enforces:
- Cryptographic isolation: Private keys never leave the local keystore and are never
  exposed via public API endpoints or logs.
- Key generation produces:
  - 1 ML-KEM-768 key pair (1,184B ek, 2,400B dk)
  - 1 ML-DSA-65 key pair (1,952B pk, 4,032B sk)
- SHA3-256 fingerprints computed for public keys.
- Private keys at rest are protected with AES-256-GCM using PBKDF2-HMAC-SHA256.
- Lifecycle actions: generate, load, list, revoke, rotate.
"""

import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .encryption import DecryptionError
from .kem import (
    ML_KEM_768_DK_BYTES,
    ML_KEM_768_EK_BYTES,
    generate_kem_keypair,
)
from .signatures import (
    ML_DSA_65_PK_BYTES,
    ML_DSA_65_SK_BYTES,
    compute_fingerprint,
    generate_signing_keypair,
)

DEFAULT_KEYSTORE_DIR = Path("storage_data/keystore")
PBKDF2_ITERATIONS = 100_000


class KeyManagerError(Exception):
    """Base exception for KeyManager failures."""
    pass


@dataclass(frozen=True)
class RecipientPublicRecord:
    """Publicly safe recipient record. Contains NO private key material."""

    recipient_id: str
    name: str
    email: str
    status: str  # "active", "revoked", "rotated"
    kem_algorithm: str
    dsa_algorithm: str
    kem_public_key_b64: str
    dsa_public_key_b64: str
    kem_fingerprint: str
    dsa_fingerprint: str
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecipientPublicRecord":
        return cls(**data)


class KeyManager:
    """Manages recipient key lifecycle and secure local persistence."""

    def __init__(self, keystore_dir: Path = DEFAULT_KEYSTORE_DIR):
        self.keystore_dir = Path(keystore_dir)
        self.keystore_dir.mkdir(parents=True, exist_ok=True)

    def _recipient_dir(self, recipient_id: str) -> Path:
        clean_id = recipient_id.strip()
        if not clean_id or ".." in clean_id or "/" in clean_id or "\\" in clean_id:
            raise ValueError(f"Invalid recipient_id: {recipient_id}")
        path = self.keystore_dir / clean_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _derive_storage_key(passphrase: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        return kdf.derive(passphrase.encode("utf-8"))

    def create_recipient_keys(
        self,
        recipient_id: str,
        name: str,
        email: str,
        passphrase: Optional[str] = "offline-trace-default-passphrase",
    ) -> RecipientPublicRecord:
        """Generate ML-KEM-768 and ML-DSA-65 keys and persist them.

        Args:
            recipient_id: Unique opaque identifier.
            name: Human-readable name.
            email: Contact/organizational email.
            passphrase: Password to protect private keys at rest.

        Returns:
            RecipientPublicRecord (public metadata only).
        """
        r_dir = self._recipient_dir(recipient_id)
        pub_file = r_dir / "public_record.json"
        priv_file = r_dir / "private_keys.enc"

        if pub_file.exists():
            raise KeyManagerError(f"Recipient '{recipient_id}' already exists.")

        # 1. Generate ML-KEM-768 keypair
        kem_ek, kem_dk = generate_kem_keypair()
        kem_fp = compute_fingerprint(kem_ek)

        # 2. Generate ML-DSA-65 keypair
        dsa_pk, dsa_sk = generate_signing_keypair()
        dsa_fp = compute_fingerprint(dsa_pk)

        now_iso = datetime.now(timezone.utc).isoformat()

        # 3. Create public metadata record (NEVER contains private keys)
        public_record = RecipientPublicRecord(
            recipient_id=recipient_id,
            name=name,
            email=email,
            status="active",
            kem_algorithm="ML-KEM-768",
            dsa_algorithm="ML-DSA-65",
            kem_public_key_b64=base64.b64encode(kem_ek).decode("ascii"),
            dsa_public_key_b64=base64.b64encode(dsa_pk).decode("ascii"),
            kem_fingerprint=kem_fp,
            dsa_fingerprint=dsa_fp,
            created_at=now_iso,
            updated_at=now_iso,
        )

        with open(pub_file, "w", encoding="utf-8") as f:
            json.dump(public_record.to_dict(), f, indent=2)

        # 4. Encrypt private keys at rest
        self._save_private_keys(priv_file, kem_dk, dsa_sk, passphrase or "")

        return public_record

    def _save_private_keys(
        self,
        priv_file: Path,
        kem_dk: bytes,
        dsa_sk: bytes,
        passphrase: str,
    ) -> None:
        salt = os.urandom(16)
        wrapping_key = self._derive_storage_key(passphrase, salt)

        # Private bundle format: kem_dk + dsa_sk
        raw_bundle = kem_dk + dsa_sk
        nonce = os.urandom(12)
        aesgcm = AESGCM(wrapping_key)
        encrypted_bundle = aesgcm.encrypt(nonce, raw_bundle, None)

        storage_data = {
            "salt": base64.b64encode(salt).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "data": base64.b64encode(encrypted_bundle).decode("ascii"),
        }
        with open(priv_file, "w", encoding="utf-8") as f:
            json.dump(storage_data, f, indent=2)

    def load_private_keys(
        self,
        recipient_id: str,
        passphrase: Optional[str] = "offline-trace-default-passphrase",
    ) -> Tuple[bytes, bytes]:
        """Decrypt and load recipient private keys locally.

        Returns:
            Tuple of (kem_dk, dsa_sk) in bytes.

        Raises:
            KeyManagerError: If keys do not exist or passphrase is invalid.
        """
        r_dir = self._recipient_dir(recipient_id)
        priv_file = r_dir / "private_keys.enc"

        if not priv_file.exists():
            raise KeyManagerError(f"No private keys found for recipient '{recipient_id}'.")

        with open(priv_file, "r", encoding="utf-8") as f:
            storage_data = json.load(f)

        salt = base64.b64decode(storage_data["salt"])
        nonce = base64.b64decode(storage_data["nonce"])
        encrypted_bundle = base64.b64decode(storage_data["data"])

        wrapping_key = self._derive_storage_key(passphrase or "", salt)
        aesgcm = AESGCM(wrapping_key)

        try:
            raw_bundle = aesgcm.decrypt(nonce, encrypted_bundle, None)
        except Exception as exc:
            raise KeyManagerError("Failed to decrypt private keys: incorrect passphrase or corrupted file.") from exc

        expected_len = ML_KEM_768_DK_BYTES + ML_DSA_65_SK_BYTES
        if len(raw_bundle) != expected_len:
            raise KeyManagerError(f"Corrupted private key bundle: expected {expected_len} bytes, got {len(raw_bundle)}.")

        kem_dk = raw_bundle[:ML_KEM_768_DK_BYTES]
        dsa_sk = raw_bundle[ML_KEM_768_DK_BYTES:]
        return kem_dk, dsa_sk

    def get_public_record(self, recipient_id: str) -> RecipientPublicRecord:
        """Retrieve public metadata for a recipient."""
        r_dir = self._recipient_dir(recipient_id)
        pub_file = r_dir / "public_record.json"
        if not pub_file.exists():
            raise KeyManagerError(f"Recipient '{recipient_id}' not found.")

        with open(pub_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return RecipientPublicRecord.from_dict(data)

    def list_public_records(self) -> List[RecipientPublicRecord]:
        """List all registered recipient public records."""
        records: List[RecipientPublicRecord] = []
        if not self.keystore_dir.exists():
            return records

        for item in sorted(self.keystore_dir.iterdir()):
            if item.is_dir():
                pub_file = item / "public_record.json"
                if pub_file.exists():
                    try:
                        with open(pub_file, "r", encoding="utf-8") as f:
                            records.append(RecipientPublicRecord.from_dict(json.load(f)))
                    except Exception:
                        continue
        return records

    def revoke_recipient(self, recipient_id: str) -> RecipientPublicRecord:
        """Mark a recipient's keys as revoked."""
        record = self.get_public_record(recipient_id)
        updated = RecipientPublicRecord(
            recipient_id=record.recipient_id,
            name=record.name,
            email=record.email,
            status="revoked",
            kem_algorithm=record.kem_algorithm,
            dsa_algorithm=record.dsa_algorithm,
            kem_public_key_b64=record.kem_public_key_b64,
            dsa_public_key_b64=record.dsa_public_key_b64,
            kem_fingerprint=record.kem_fingerprint,
            dsa_fingerprint=record.dsa_fingerprint,
            created_at=record.created_at,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        r_dir = self._recipient_dir(recipient_id)
        with open(r_dir / "public_record.json", "w", encoding="utf-8") as f:
            json.dump(updated.to_dict(), f, indent=2)
        return updated

    def rotate_recipient_keys(
        self,
        recipient_id: str,
        passphrase: Optional[str] = "offline-trace-default-passphrase",
    ) -> RecipientPublicRecord:
        """Rotate keys for an existing recipient, archiving old keys."""
        record = self.get_public_record(recipient_id)
        r_dir = self._recipient_dir(recipient_id)

        # Archive old private keys
        priv_file = r_dir / "private_keys.enc"
        if priv_file.exists():
            archive_name = f"private_keys_{int(datetime.now().timestamp())}.enc.bak"
            priv_file.rename(r_dir / archive_name)

        # Generate fresh pairs
        kem_ek, kem_dk = generate_kem_keypair()
        kem_fp = compute_fingerprint(kem_ek)
        dsa_pk, dsa_sk = generate_signing_keypair()
        dsa_fp = compute_fingerprint(dsa_pk)

        now_iso = datetime.now(timezone.utc).isoformat()
        updated = RecipientPublicRecord(
            recipient_id=record.recipient_id,
            name=record.name,
            email=record.email,
            status="active",
            kem_algorithm="ML-KEM-768",
            dsa_algorithm="ML-DSA-65",
            kem_public_key_b64=base64.b64encode(kem_ek).decode("ascii"),
            dsa_public_key_b64=base64.b64encode(dsa_pk).decode("ascii"),
            kem_fingerprint=kem_fp,
            dsa_fingerprint=dsa_fp,
            created_at=record.created_at,
            updated_at=now_iso,
        )

        with open(r_dir / "public_record.json", "w", encoding="utf-8") as f:
            json.dump(updated.to_dict(), f, indent=2)

        self._save_private_keys(priv_file, kem_dk, dsa_sk, passphrase or "")
        return updated
