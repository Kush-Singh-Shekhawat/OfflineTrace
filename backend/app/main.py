from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import recipients
from .crypto.key_manager import KeyManager

app = FastAPI(title="OfflineTrace API", version="0.1.0")
key_manager = KeyManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(recipients.router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "OfflineTrace"}

@app.get("/api/v1/dashboard/summary")
def dashboard_summary() -> dict[str, object]:
    recipients_count = len(key_manager.list_public_records())
    return {
        "documents_total": 0,
        "recipients_total": recipients_count,
        "investigations_total": 0,
        "ledger_status": "not_configured",
    }

@app.get("/api/v1/ledger/status")
def ledger_status() -> dict[str, str]:
    return {"status": "not_configured", "message": "Ledger implementation is pending."}
