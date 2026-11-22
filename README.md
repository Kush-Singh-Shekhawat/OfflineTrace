# OfflineTrace

OfflineTrace is a prototype for secure document distribution, recipient/key management,
PDF watermarking and forensic investigation, and a tamper-evident verification ledger.

> **Status:** Starter repository scaffold. Core cryptographic, watermarking, ledger, and
> persistence implementations are intentionally placeholders until their interfaces and
> threat model are reviewed by the team.

## Team ownership

| Member | Primary ownership | Frontend ownership |
|---|---|---|
| A | Cryptography, KEM/key management, signatures | Recipient/key-management screen |
| B | PDF watermarking, extraction, forensic investigation | Watermark investigation screen |
| C | FastAPI, ledger integration, shared frontend integration | Ledger screen and integration |

Members A and B build feature screens in their respective folders. Member C integrates them
into the common React application; integration does not mean Member C must implement every
frontend feature.

## Repository layout

- `frontend/` — React + Vite application
- `backend/` — FastAPI application and domain modules
- `validator_data/`, `storage_data/` — local runtime data (never commit)
- `tests/` — unit, integration, and security tests
- `scripts/` — Windows setup and run helpers
- `docs/` — architecture, decisions, test reports, and demo notes

## Quick start (Windows PowerShell)

1. Install Python 3.11+ and Node.js 20+.
2. Copy `.env.example` to `.env` and review the values.
3. Run `scripts\setup_windows.ps1`.
4. In separate terminals run `scripts\run_backend.ps1` and `scripts\run_frontend.ps1`.
5. Open the Vite URL printed in the frontend terminal. FastAPI docs are at
   `http://127.0.0.1:8000/docs`.

## Manual setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
npm --prefix frontend install
Copy-Item .env.example .env
```

Run the backend:

```powershell
$env:PYTHONPATH = "$PWD\backend"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run the frontend:

```powershell
cd frontend
npm run dev
```

## Development rules

- Read `PROJECT_CONTEXT.md`, `AI_RULES.md`, and `API_CONTRACTS.md` before implementing a task.
- Use synthetic/sample PDFs only. Do not commit confidential documents, private keys,
  credentials, real recipient data, or runtime database files.
- Do not claim a cryptographic or watermarking feature is secure until it has been reviewed
  and tested against a documented threat model.
- Keep API contracts stable. Coordinate breaking changes before merging.
- Add tests for every behavior change.

## Tests

```powershell
$env:PYTHONPATH = "$PWD\backend"
pytest
```

## GitHub workflow

```powershell
git init
git add .
git commit -m "chore: initialize OfflineTrace repository"
git branch -M main
git remote add origin https://github.com/<YOUR-ORG-OR-USERNAME>/OfflineTrace.git
git push -u origin main
```

Replace the remote URL with your actual GitHub repository URL.
