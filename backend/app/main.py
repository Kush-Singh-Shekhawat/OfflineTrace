"""Main entrypoint for backend.app - delegates to backend.api.main.app."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure workspace root and backend directory are in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
for p in (str(root_dir), str(backend_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.api.main import app  # noqa: E402

__all__ = ["app"]
