"""FastAPI entry point for OfflineTrace.

Mounts the frozen API routes, enables CORS for the local Vite dev server,
provides health checks, and translates internal ``ErrorCode``
enumerations into JSON error responses.
"""

from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .routes_manifest import router as api_router, legacy_router
from .contracts import ErrorCode

app = FastAPI(title="OfflineTrace API", version="1.0.0")

# CORS – allow Vite dev server to call the API locally.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the frozen route manifest (/api/v1) and legacy routes (/api)
app.include_router(api_router)
app.include_router(legacy_router)


# ---------------------------------------------------------------------------
# Health endpoint – lightweight status check.
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


@app.get("/api/v1/health", tags=["Health"], include_in_schema=False)
async def api_health_check():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Standardized JSON error handling.
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    mapping = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.UNAUTHORIZED,
        404: ErrorCode.NOT_FOUND,
        500: ErrorCode.INTERNAL_ERROR,
        501: ErrorCode.INVALID_REQUEST,  # Default for not implemented in test contracts
        502: ErrorCode.BAD_GATEWAY,
    }
    error_code = mapping.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_code.value, "detail": exc.detail},
    )
