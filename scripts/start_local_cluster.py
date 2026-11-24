"""Launch the 3-node OfflineTrace Validator Cluster on a single machine.

Runs:
- Node val-1 on http://127.0.0.1:8001 (DB: validator_data/val1.db)
- Node val-2 on http://127.0.0.1:8002 (DB: validator_data/val2.db)
- Node val-3 on http://127.0.0.1:8003 (DB: validator_data/val3.db)

Enables Byzantine 2-of-3 Quorum Consensus verification on a single PC.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

NODES = [
    {"node_id": "val-1", "port": 8001, "db": "validator_data/val1.db"},
    {"node_id": "val-2", "port": 8002, "db": "validator_data/val2.db"},
    {"node_id": "val-3", "port": 8003, "db": "validator_data/val3.db"},
]


def main():
    print("=" * 70)
    print("🚀 OFFLINETRACE // LOCAL 3-VALIDATOR CLUSTER LAUNCHER")
    print("   Consensus: 2-of-3 Byzantine Quorum (NIST FIPS 204 ML-DSA-65)")
    print("=" * 70)

    processes = []
    py_executable = sys.executable

    # Ensure validator_data directory exists
    Path("validator_data").mkdir(exist_ok=True)

    try:
        for node in NODES:
            cmd = [
                py_executable,
                "-m",
                "backend.validator_node.run_node",
                "--node-id",
                node["node_id"],
                "--port",
                str(node["port"]),
                "--db-path",
                node["db"],
            ]
            print(f"[*] Starting {node['node_id']} on http://127.0.0.1:{node['port']} ...")
            proc = subprocess.Popen(cmd)
            processes.append(proc)
            time.sleep(0.5)

        print("\n" + "=" * 70)
        print("✅ ALL 3 VALIDATOR NODES ARE ACTIVE ON THIS PC:")
        print("   - val-1: http://127.0.0.1:8001/health")
        print("   - val-2: http://127.0.0.1:8002/health")
        print("   - val-3: http://127.0.0.1:8003/health")
        print("   Press Ctrl+C to terminate the local cluster.")
        print("=" * 70 + "\n")

        # Keep alive until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[*] Shutting down local validator cluster...")
    finally:
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                proc.kill()
        print("[*] All validator node processes cleanly terminated.")


if __name__ == "__main__":
    main()
