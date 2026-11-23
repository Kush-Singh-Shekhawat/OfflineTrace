# Development Status

**Current team phase:** Phase 2 (Independent Foundations) & Phase 3 (Core Module Tests)

## Project Phase Overview

| Phase | Description | Status | Member A Standing |
|---|---|---|---|
| **Phase 0** | Team baseline (repo, venv, Python 3.12, Node/Vite, `.gitignore`, scaffolding) | ✅ **Completed** | Baseline verified & operational |
| **Phase 1** | Contract freeze (crypto algorithms, API schemas, canonical JSON, invariants) | ✅ **Completed** | Interfaces agreed & implemented |
| **Phase 2** | Independent foundations (A: crypto/KEM/envelopes; B: PDF watermark; C: ledger model) | ✅ **Completed (All)** | All 3 foundations verified |
| **Phase 3** | Core module tests (A: tamper/wrong key; B: watermark metrics; C: 2-of-3 quorum) | ✅ **Completed (All)** | All 47 tests passing |
| **Phase 4** | First vertical slice (decrypt → watermark → output hash → canonical event → signature → quorum commit) | 🚀 **Next Up** | Ready for end-to-end slice |
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

- **2026-11-23 (Full Team Integration - Member A, B, C)**: `pytest -v`
  - **47 passed** in 2.62s (Python 3.12.10, pytest-8.4.2)
  - **Member A (32 tests)**: AES-256-GCM, HKDF-SHA-256, ML-KEM-768 (FIPS 203), ML-DSA-65 (FIPS 204), CEK Envelopes, KeyManager keystore, RecipientCryptoService local boundary.
  - **Member B (5 tests)**: Watermark embed/extract round-trip, invalid PDF rejection, empty token rejection.
  - **Member C (10 tests)**: 2-of-3 validator quorum commit & persistence across restart, 1-validator fail closed, replay event rejection, tamper divergence detection, DB isolation, block hash determinism.

## Integration checklist

- [ ] All members use the same repository and branch naming convention.
- [ ] API contracts are agreed before parallel implementation.
- [ ] Each member commits only their assigned files plus agreed shared changes.
- [ ] Feature branches are merged through pull requests.
- [ ] Backend imports and frontend build work from a clean checkout.
- [ ] Offline demo check passes.
- [ ] Test report and demo instructions are updated.

Update this file whenever ownership, status, blockers, or integration decisions change.
