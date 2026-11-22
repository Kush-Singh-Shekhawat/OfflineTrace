# API Contracts

This file is the shared agreement between frontend and backend. Update it before making
breaking changes. Initial routes are placeholders and may return scaffold responses.

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

Planned routes:
- `POST /api/v1/documents` — upload/register a document.
- `GET /api/v1/documents` — list documents.
- `GET /api/v1/documents/{document_id}` — document metadata.

Upload limits, file validation, and storage behavior must be specified before implementation.

## Recipients

Planned routes:
- `POST /api/v1/recipients` — register recipient metadata.
- `GET /api/v1/recipients` — list recipient metadata.
- `POST /api/v1/recipients/{recipient_id}/keys` — create/register key metadata.

Private key material must never be returned by an API list/detail endpoint.

## Investigation

Planned routes:
- `POST /api/v1/investigations` — submit a synthetic or authorized PDF for analysis.
- `GET /api/v1/investigations/{investigation_id}` — retrieve investigation status/result.

An extracted watermark is evidence for review, not automatic proof of who leaked a document.

## Ledger

Planned routes:
- `GET /api/v1/ledger/status` — report local ledger status.
- `GET /api/v1/ledger/entries` — list verifiable entries.
- `POST /api/v1/ledger/verify` — verify chain integrity.

## Contract change checklist

- [ ] Update this document.
- [ ] Update Pydantic schemas and route implementation.
- [ ] Update frontend service functions and types/validation.
- [ ] Add API integration tests.
- [ ] Notify all three members before merging a breaking change.
