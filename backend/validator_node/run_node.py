"""Standalone CLI entry point to launch an isolated OfflineTrace Validator Node.

Usage:
    python -m backend.validator_node.run_node --node-id val-1 --port 8001
    python -m backend.validator_node.run_node --node-id val-2 --port 8002
    python -m backend.validator_node.run_node --node-id val-3 --port 8003
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import uvicorn
from backend.validator_node.node import create_validator_app


def main():
    parser = argparse.ArgumentParser(description="OfflineTrace Isolated Validator Node")
    parser.add_argument("--node-id", default="val-1", help="Unique validator node ID (e.g. val-1, val-2, val-3)")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on (e.g. 8001, 8002, 8003)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--db-path", default=None, help="Path to node SQLite database")
    args = parser.parse_args()

    db_path = args.db_path or f"validator_data/{args.node_id}.db"
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    app = create_validator_app(node_id=args.node_id, db_path=db_path)
    print(f"\n==================================================================")
    print(f"🏛️  OfflineTrace Validator Node: [{args.node_id}]")
    print(f"🔒  PQC Signature Suite: ML-DSA-65 (NIST FIPS 204)")
    print(f"📦  Database Path: {db_path}")
    print(f"🌐  Socket: http://{args.host}:{args.port}")
    print(f"==================================================================\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
