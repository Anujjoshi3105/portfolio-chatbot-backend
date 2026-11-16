"""Local API smoke test; starts no server and validates the app contract."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from service.service import app


def main() -> int:
    with TestClient(app) as client:
        response = client.get("/openapi.json")
        response.raise_for_status()
        paths = response.json()["paths"]
        required = {"/info", "/health", "/voice/transcribe", "/voice/synthesize"}
        missing = required - paths.keys()
        if missing:
            print(f"missing paths: {sorted(missing)}")
            return 1
        print(f"smoke ok ({len(paths)} routes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
