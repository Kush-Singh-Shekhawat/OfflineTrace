from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OfflineTrace API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "OfflineTrace"}

@app.get("/api/v1/dashboard/summary")
def dashboard_summary() -> dict[str, object]:
    return {
        "documents_total": 0,
        "recipients_total": 0,
        "investigations_total": 0,
        "ledger_status": "not_configured",
    }

@app.get("/api/v1/ledger/status")
def ledger_status() -> dict[str, str]:
    return {"status": "not_configured", "message": "Ledger implementation is pending."}
