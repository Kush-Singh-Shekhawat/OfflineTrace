# Project Context

## Purpose

OfflineTrace is a local-first prototype for controlled document distribution and later
forensic investigation. The intended workflow is:

1. A sender selects a PDF and recipient(s).
2. The system prepares recipient-specific protected document copies.
3. A recipient receives the authorized copy and associated verification material.
4. If a leaked copy is found, the investigation workflow attempts to extract identifying
   watermark evidence and records the investigation result.
5. A ledger records integrity-relevant events so that later verification can detect
   unauthorized changes.

## Design principles

- Offline-capable local development; no cloud dependency is required for the demo.
- Clear separation between cryptography, watermarking, ledger, storage, API, and UI.
- Explicit interfaces between team-owned modules.
- Synthetic data and test documents only.
- Fail closed when integrity or verification checks fail.
- Keep secrets out of source control and logs.

## Team boundaries

### Member A — Cryptography and recipient/key management
Owns `backend/app/crypto/` and `frontend/src/features/recipients/`.
Coordinates algorithms, key lifecycle, recipient identity references, and crypto-related API
schemas with Member C.

### Member B — PDF watermarking and forensic investigation
Owns `backend/app/watermark/` and `frontend/src/features/investigation/`.
Defines embedding/extraction metadata, PDF handling, quality checks, and investigation
result schemas with Member C.

### Member C — FastAPI, ledger, integration
Owns `backend/app/ledger/`, API wiring, shared application integration, and
`frontend/src/features/ledger/`. Maintains common contracts and integrates A/B screens.

## Non-goals for the initial scaffold

- Production-grade key custody or certificate authority.
- Legal attribution or proof of identity based solely on a watermark.
- Distributed consensus across untrusted machines.
- Guaranteed watermark survival under every PDF transformation.
- Production deployment, multi-tenant authentication, or cloud storage.

## Definition of done

A task is complete when its agreed interface is implemented, tests pass, errors are handled,
documentation is updated, and another team member can run it from a clean checkout.
