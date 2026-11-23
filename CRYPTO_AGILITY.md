# OfflineTrace — Cryptographic Agility & Standards Manifest

This manifest documents the exact cryptographic primitives, parameters, and standards implemented in **OfflineTrace (SIH26237 - Ministry of Defence / WESEE)**, satisfying **Member A Task 10**.

---

## 1. Primary Cryptographic Suite (FIPS / Post-Quantum Standardized)

| Role | Primitive | Specification / Standard | Key / Parameter Sizes | Security Category |
|---|---|---|---|---|
| **Symmetric Bulk Encryption** | `AES-256-GCM` | NIST FIPS 197 / SP 800-38D | 256-bit Key, 96-bit Nonce, 128-bit GHASH Tag | 256-bit Classical / Post-Quantum |
| **Post-Quantum Key Encapsulation (KEM)** | `ML-KEM-768` | NIST FIPS 203 (2024) | Public Key: 1,184 Bytes<br>Private Key: 2,400 Bytes<br>Ciphertext: 1,088 Bytes<br>Shared Secret: 32 Bytes | NIST Category 3 (~192-bit Quantum Safe) |
| **Post-Quantum Digital Signatures (DSA)** | `ML-DSA-65` | NIST FIPS 204 (2024) | Public Key: 1,952 Bytes<br>Private Key: 4,032 Bytes<br>Signature: 3,309 Bytes | NIST Category 3 (~192-bit Quantum Safe) |
| **Key Derivation Function (KDF)** | `HKDF-SHA-256` | RFC 5869 / NIST SP 800-56C | Extract-and-Expand with Context Binding | 256-bit Security |
| **Integrity & Fingerprint Hashing** | `SHA3-256` | NIST FIPS 202 (2015) | 256-bit Sponge Output (Keccak) | Pre-image: 256-bit, Collision: 128-bit |
| **Keystore at Rest Protection** | `PBKDF2-HMAC-SHA256` + `AES-256-GCM` | NIST SP 800-132 | 100,000 Iterations, 128-bit Salt, 256-bit Derived Key | High-entropy password-protected key wrapping |

---

## 2. Cryptographic Agility & Migration Roadmap

OfflineTrace is built with **modular cryptographic providers** (`backend/app/crypto/`), enabling seamless algorithm swaps without altering application schemas or database tables:

```
+-----------------------------------------------------------+
|              OfflineTrace Application Layer               |
+-----------------------------+-----------------------------+
                              |
     +------------------------+------------------------+
     |                                                 |
     v                                                 v
[ ML-KEM-768 (Active) ]                       [ ML-DSA-65 (Active) ]
  • NIST Category 3                             • NIST Category 3
  • FIPS 203                                    • FIPS 204
     |                                                 |
     v Upgradeable to:                                 v Upgradeable to:
[ ML-KEM-1024 / HQC ]                         [ ML-DSA-87 / SLH-DSA ]
  • NIST Category 5                             • NIST Category 5
```

### Supported Agility Configurations

1. **Category 5 Ultra-High Security Profile**:
   - KEM: `ML-KEM-1024` (Public Key: 1568 B, Ciphertext: 1568 B)
   - Signature: `ML-DSA-87` (Public Key: 2592 B, Signature: 4595 B)
2. **Constrained Hardware / Edge Node Profile**:
   - Symmetric: `ChaCha20-Poly1305` (RFC 8439) for devices lacking hardware AES-NI acceleration.
   - KEM: `ML-KEM-512` (NIST Category 1, smaller keys).

---

## 3. Pinned Library Dependencies & Compatibility

All algorithms have been tested and verified under **Python 3.12.10 (64-bit win32)**:

| Library | Pinned Version | Purpose |
|---|---|---|
| `cryptography` (PyCA) | `>=42.0.0` | AES-256-GCM, HKDF-SHA-256, PBKDF2 |
| `kyber-py` | `==1.2.0` | Clean pure-Python implementation of NIST FIPS 203 ML-KEM-768 |
| `dilithium-py` | `==1.5.1` | Clean pure-Python implementation of NIST FIPS 204 ML-DSA-65 |
| `hashlib` | Python 3.12 Standard | SHA3-256 Keccak sponge implementation |
| `pypdf` | `>=4.0.0` | PDF page handling, metadata extraction and validation |

---

## 4. Invariant Verification

The cryptographic engine enforces:
- **Zero Secret Custody:** No raw CEK or private key bytes are stored in the database, logged in application outputs, or transmitted over REST APIs.
- **Fail-Closed Execution:** Any tag corruption in AES-GCM or KEM decapsulation divergence raises `InvalidTag` / `DecryptionError` and releases zero bytes of plaintext.
- **Domain Separation:** Every envelope derivation cryptographically binds `document_id`, `version_id`, and `recipient_fingerprint` into HKDF context parameters, preventing cross-document key reuse.
