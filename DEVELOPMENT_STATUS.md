# Development Status

**Current team phase:** Phase 2 (Independent Foundations) & Phase 3 (Core Module Tests)

## Project Phase Overview

| Phase | Description | Status | Member A Standing |
|---|---|---|---|
| **Phase 0** | Team baseline (repo, venv, Python 3.12, Node/Vite, `.gitignore`, scaffolding) | ✅ **Completed** | Baseline verified & operational |
| **Phase 1** | Contract freeze (crypto algorithms, API schemas, canonical JSON, invariants) | ✅ **Completed** | Interfaces agreed & implemented |
| **Phase 2** | Independent foundations (A: crypto/KEM/envelopes; B: PDF watermark; C: ledger model) | 🟡 **In Progress (Team)** | ✅ **100% Complete for Member A** |
| **Phase 3** | Core module tests (A: tamper/wrong key; B: watermark metrics; C: 2-of-3 quorum) | 🟡 **In Progress (Team)** | ✅ **100% Complete for Member A** (32/32 tests pass) |
| **Phase 4** | First vertical slice (decrypt → watermark → output hash → canonical event → signature → quorum commit) | ⏳ **Pending** | A's crypto service & envelope unwrap are ready |
| **Phase 5** | Investigation and UI integration (A's Recipient screen, B's Investigation screen, C's shell) | ⏳ **Pending** | ✅ **Recipient UI complete and live** |
| **Phase 6** | P1/P2 enhancements (FEC/redundancy, tamper harness, confidence metrics, export) | ⏳ **Pending** | Not started |
| **Phase 7** | LAN / offline freeze (1 validator per laptop, 3 laptops, WAN disconnected, persistence, rehearsal) | ⏳ **Pending** | Final release gate |

## Status by area

| Area | Owner | Status | Next step |
|---|---|---|---|
| Cryptography and key management | Member A | Complete (Phase 2 & Phase 3) | Ready for Phase 4 integration (first vertical slice) |
| Recipient screen | Member A | Complete (Frontend Screen) | Ready for team end-to-end integration |
| PDF watermarking | Member B | Scaffold | Select embedding/extraction approach and test PDFs |
| Investigation screen | Member B | Scaffold | Build upload and result UI |
| FastAPI and API contracts | Member C | Scaffold | Wire routes and schemas |
| Ledger | Member C | Scaffold | Define event schema and verification rules |
| Shared React integration | Member C | Scaffold | Integrate feature screens and navigation |
| Automated tests | All | Scaffold | Add unit/integration/security coverage |

## Test Execution Log

- **2026-11-23 (Member A)**: `pytest tests/unit/test_crypto.py -v`
  - 32 passed in 1.48s (Python 3.12.10, pytest-8.4.2)
  - Modules verified:
    - `backend/app/crypto/key_derivation.py` (HKDF-SHA-256 context binding & domain separation)
    - `backend/app/crypto/encryption.py` (AES-256-GCM authenticated payload & fail-closed decryptions)
    - `backend/app/crypto/kem.py` (ML-KEM-768 FIPS 203 keygen, encaps/decaps round-trip & implicit rejection)
    - `backend/app/crypto/signatures.py` (ML-DSA-65 FIPS 204 keygen, canonical signing, verification, SHA3-256 fingerprints)
    - `backend/app/crypto/envelope.py` (1-ciphertext N-envelopes, unwrap, tamper rejection)
    - `backend/app/crypto/key_manager.py` (encrypted keystore at rest, PBKDF2-HMAC-SHA256, listing, revocation, rotation)
    - `backend/app/services/recipient_crypto.py` (recipient local boundary, unwrap, document decryption, canonical event signing, token digest computation)

## Integration checklist

- [ ] All members use the same repository and branch naming convention.
- [ ] API contracts are agreed before parallel implementation.
- [ ] Each member commits only their assigned files plus agreed shared changes.
- [ ] Feature branches are merged through pull requests.
- [ ] Backend imports and frontend build work from a clean checkout.
- [ ] Offline demo check passes.
- [ ] Test report and demo instructions are updated.

Update this file whenever ownership, status, blockers, or integration decisions change.
