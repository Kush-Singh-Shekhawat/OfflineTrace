# OfflineTrace

**Tactical Controlled Document Distribution & Post-Quantum Forensic Attribution**  
*Problem Statement ID: SIH26237 — Ministry of Defence / WESEE*

[![Tests](https://img.shields.io/badge/tests-78%20passed-brightgreen)](#automated-testing--security-verification)
[![NIST Standard](https://img.shields.io/badge/PQC-NIST%20FIPS%20203%20%7C%20204-blue)](#cryptographic-architecture)
[![Consensus](https://img.shields.io/badge/Consensus-2--of--3%20BFT%20Quorum-orange)](#distributed-consensus-ledger)
[![Network](https://img.shields.io/badge/Environment-Air--Gapped%20%2F%20WAN--Disconnected-lightgrey)](#air-gapped-lan-deployment)

---

## 1. Executive Summary

In high-security defence and tactical environments, classified orders and intelligence directives must be distributed across isolated local networks with **zero internet or cloud dependency**. Traditional document security systems suffer from two critical vulnerabilities:
1. **Centralized Secret Custody:** Servers or gateways store private keys or plaintext symmetric keys, representing a single point of compromise.
2. **Quantum Vulnerability:** Classical asymmetric schemes (RSA, ECDSA, ECDH) are provably broken by Shor's algorithm on quantum architectures.

**OfflineTrace** is a local-first, air-gapped prototype that bridges post-quantum cryptography with verifiable distributed ledger consensus and forensic watermark provenance:
- **Zero Plaintext Custody:** Content Encryption Keys (CEK) and private keys never leave the recipient officer's local security boundary.
- **Post-Quantum Hybrid Cryptography:** Bulk payloads are protected with **AES-256-GCM**, while keys are encapsulated using **NIST FIPS 203 ML-KEM-768** and signed with **NIST FIPS 204 ML-DSA-65**.
- **2-of-3 Byzantine Quorum Gate:** Strict fail-closed release—a document is never decrypted or released unless at least 2 independent validator nodes cryptographically verify and commit the provenance event.
- **Court of Inquiry Evidence Dossier:** Deterministic watermark token digests link leaked documents to an immutable ledger block, producing tamper-evident, court-admissible dossiers with SHA3-256 digital seals.

---

## 2. Cryptographic Architecture

```
                                [ SENDER / ADMIN ]
                                        │
           Uploads Document Payload (PDF) + Selects N Cleared Recipients
                                        │
                       Generates Random 32-Byte CEK
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
     [ AES-256-GCM ]                                        [ ML-KEM-768 ]
  Encrypts Bulk Payload Once                          Per-Recipient Envelopes
(1 Shared Ciphertext: 128-bit Tag)              (Encapsulates CEK via HKDF Context Binding)
             │                                                     │
             └──────────────────────────┬──────────────────────────┘
                                        ▼
                           [ RECIPIENT LOCAL BOUNDARY ]
                                        │
                       Local KEM Decapsulation & Unwrapping
                                        │
                     Unique Session Watermark Embedding (FEC)
                                        │
                 Canonical Event Signed via ML-DSA-65 Private Key
                                        │
                                        ▼
                  [ 2-of-3 BYZANTINE VALIDATOR CLUSTER ]
                     (Node 1: 8001 | Node 2: 8002 | Node 3: 8003)
                                        │
                       Consensus Quorum Achieved (>= 2 Sigs)
                                        │
                       Committed into Immutable Block (SHA3-256)
                                        │
                                        ▼
                           [ DOCUMENT RELEASED TO OFFICER ]
```

### Cryptographic Standards & Parameter Sizes

| Role | Standard / Primitive | Parameters / Key Sizes |
|---|---|---|
| **Bulk Symmetric Cipher** | `AES-256-GCM` (NIST FIPS 197) | 256-bit Key, 96-bit Nonce, 128-bit GHASH Tag |
| **Post-Quantum KEM** | `ML-KEM-768` (NIST FIPS 203) | Public Key: 1,184 B \| Private Key: 2,400 B \| Ciphertext: 1,088 B |
| **Post-Quantum Signature** | `ML-DSA-65` (NIST FIPS 204) | Public Key: 1,952 B \| Private Key: 4,032 B \| Signature: 3,309 B |
| **Key Derivation (KDF)** | `HKDF-SHA-256` (RFC 5869) | Context binding: `doc_id` + `version_id` + `recipient_fingerprint` |
| **Integrity Hashing** | `SHA3-256` (NIST FIPS 202) | Keccak Sponge Construction |
| **Keystore at Rest** | `PBKDF2-HMAC-SHA256` + `AES-GCM` | 100,000 Iterations, Salted, AES-256-GCM encrypted |

*Detailed specifications and migration paths are documented in [CRYPTO_AGILITY.md](CRYPTO_AGILITY.md).*

---

## 3. Core Feature Walkthrough

### 1. Command Dashboard (`/`)
- Real-time command center monitoring **Protected Directives**, **Enrolled Officers**, **Committed Blocks**, and **Forensic Inquiries**.
- Displays air-gap status and quorum node health.

### 2. Document Protection & Distribution (`/documents`)
- Senders upload classified directives or generate standardized naval operational templates.
- Select authorized officers from the PQC key registry.
- Encrypts payload once with **AES-256-GCM** and wraps individual **ML-KEM-768 envelopes** per recipient.
- Displays full cryptographic packaging details and envelope breakdown.

### 3. Officer Key Roster & Adversarial Security (`/recipients`)
- Manage post-quantum keypairs, view **SHA3-256 public key fingerprints**, rotate keys, and enforce revocation.
- **Local Decryption Simulator:** Demonstrates zero-custody local unwrapping and provenance event signing.
- **Adversarial Tamper Simulator:** Test 5 live attack vectors (**Bit-Flip**, **KEM Tampering**, **Key Impersonation**, **Context Confusion**, **Revoked Credentials**) proving **0 Bytes Plaintext Leaked** (Fail-Closed).

### 4. Forensic Investigation & Court of Inquiry (`/investigation`)
- Intake suspected leaked PDFs, extract forensic watermark tokens with repetition error correction.
- Search ledger blocks, verify recipient ML-DSA-65 digital signature, 2-of-3 quorum certificate, and hash chain continuity.
- **Court of Inquiry Dossier:** Generate formal military tribunal evidence packages with **SHA3-256 tamper-evident digital seals** and print preview.

### 5. Immutable Ledger Explorer (`/ledger`)
- 3-Node validator cluster monitor (`val-1`, `val-2`, `val-3`).
- Visual block timeline displaying Block Sequence, Previous Hash, Merkle Root, and Validator Consensus Signatures.

---

## 4. Automated Testing & Security Verification

The entire repository enforces strict automated test verification across unit, integration, and security boundaries.

```powershell
pytest -v
```

### Test Suite Breakdown (78 Tests Passing):
- **Core Cryptography (32 tests):** AES-256-GCM AEAD, ML-KEM-768 round-trip/rejection, ML-DSA-65 sign/verify, HKDF context separation, envelope serialization, PBKDF2 keystore lifecycle.
- **Phase 6 Adversarial Tamper Harness (7 tests):** Mathematical verification of fail-closed behavior under bit-flipping, KEM ciphertext corruption, unauthorized impersonation, HKDF context bypass, signature repudiation, revoked keys, and Byzantine partition.
- **Watermarking & FEC (7 tests):** Invisible metadata embedding, token extraction, 3× repetition encoding, and majority voting recovery.
- **Consensus & Quorum (10 tests):** 2-of-3 validator commit, 1-validator fail closed, replay attack rejection, ledger persistence across node restart, and divergence detection.
- **Vertical Slice & Investigation (22 tests):** End-to-end decrypt-watermark-sign-commit flows, API contracts, and forensic report schema persistence.

---

## 5. Quick Start (Local Development)

### Prerequisites
- Python 3.12 (64-bit Windows / Linux / macOS)
- Node.js 20+ (for local Vite dev server)

### 1. Environment Setup
```powershell
# Clone the repository
git clone https://github.com/Kush-Singh-Shekhawat/OfflineTrace.git
cd OfflineTrace

# Setup Python Virtual Environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Install Frontend Dependencies
cd frontend
npm install
cd ..
```

### 2. Run the Application
In separate terminals:

```powershell
# Terminal 1: Backend API
.\.venv\Scripts\Activate.ps1
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend Web App
cd frontend
npm run dev
```

Open your browser at `http://localhost:5173`.

---

## 6. Air-Gapped LAN Deployment (Final Evaluation Setup)

For physical demonstration across **3 separate laptops** with WAN disconnected:

1. Connect all 3 laptops to a local Wi-Fi router or hotspot (**No internet connection required**).
2. Follow the detailed physical startup commands and 5-minute evaluator pitch script in **`phase7_final_demo_runbook.md`**.

---

## 7. Project Ownership & Architecture Boundaries

- **Cryptography & Recipient Security:** Core cryptographic primitives (`backend/app/crypto/`), key lifecycle (`KeyManager`), recipient boundary, and `RecipientsPage.jsx`.
- **Watermarking & Forensics:** Watermark carrier (`backend/app/watermark/`), error correction (`error_correction.py`), and `InvestigationPage.jsx`.
- **App Shell & Consensus Ledger:** Distributed validator nodes (`backend/validator_node/`), 2-of-3 quorum coordinator (`backend/ledger/`), storage (`backend/storage/`), and integration views (`DocumentsPage.jsx`, `LedgerPage.jsx`, `DashboardPage.jsx`).
