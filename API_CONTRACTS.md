# API Contracts

This file documents the standardized API contracts between the frontend and backend micro-services for OfflineTrace.

## Conventions

- Base URL: `http://127.0.0.1:8000`
- API prefix: `/api/v1`
- JSON uses `snake_case` field names.
- IDs are opaque strings; clients must not parse their internal format.
- Timestamps are ISO-8601 UTC strings.
- Errors use FastAPI's standard `detail` response until a common error envelope is adopted.

## Health

`GET /health`

```json
{"status": "ok", "service": "OfflineTrace"}
```

## Dashboard

`GET /api/v1/dashboard/summary`

Planned response:

```json
{
  "documents_total": 0,
  "recipients_total": 0,
  "investigations_total": 0,
  "ledger_status": "not_configured"
}
```

## Documents

Implemented routes:
- `POST /api/v1/documents/upload` — upload/register a document with AES-256-GCM encryption and ML-KEM-768 multi-recipient envelopes.
- `GET /api/v1/documents` — list all registered documents with envelope rosters.
- `GET /api/v1/documents/{document_id}` — retrieve document metadata and authorized recipient envelopes.

## Recipients

Implemented routes:
- `POST /api/v1/recipients` — register recipient identity and metadata.
- `GET /api/v1/recipients` — list enrolled recipients with ML-KEM-768 and ML-DSA-65 public key fingerprints.
- `POST /api/v1/recipients/{recipient_id}/keys` — generate and register post-quantum key pairs.
- `POST /api/v1/recipients/{recipient_id}/revoke` — revoke an officer's keys (marks compromised/revoked while preserving audit trails).
- `POST /api/v1/recipients/{recipient_id}/rotate` — rotate keypairs, generating fresh ML-KEM and ML-DSA keys.
- `DELETE /api/v1/recipients/{recipient_id}` — permanently purge a recipient record and keys from keystore storage.

*Security Invariant:* Private key material is never exposed or returned by any API endpoint.

## Investigation

Implemented routes:
- `POST /api/v1/investigations` — submit a leaked PDF document for forensic non-blind watermark extraction.
- `GET /api/v1/investigations/{investigation_id}` — retrieve forensic confidence report, bit error rates, and ledger verification.

*Forensic Invariant:* Extracted watermarks are presented with strict statistical confidence and ledger cryptographic audit trails.

## Ledger & Consensus

Implemented routes:
- `GET /api/v1/ledger/status` — report 2-of-3 quorum cluster status, block height, and active node consensus.
- `GET /api/v1/ledger/chain` — retrieve the cryptographic block chain with Merkle roots, SHA3-256 block hashes, and ML-DSA validator signatures.
- `GET /api/v1/nodes/health` — retrieve live status of all 3 independent physical/local validator nodes.
- `POST /api/v1/ledger/propose` — submit a signed event proposal for validator quorum consensus.


## Contract change checklist

- [ ] Update this document.
- [ ] Update Pydantic schemas and route implementation.
- [ ] Update frontend service functions and types/validation.
- [ ] Add API integration tests.
- [ ] Notify all three members before merging a breaking change.
