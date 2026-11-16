"""Smoke test the deployed backend API end-to-end.

Calls /info and /health, verifies the service is reachable and responding.
Usage:
    uv run python scripts/smoke_live_app.py [URL]

The URL defaults to the deployed backend, or set LIVE_APP_URL. For local testing:
    uv run python scripts/smoke_live_app.py http://localhost:7860

Exits 0 on pass, 1 on fail.
"""

import os
import sys

import httpx

DEFAULT_URL = "https://portfolio-chatbot-backend.hf.space"
TEST_MESSAGE = "ping"
RESPONSE_TIMEOUT_S = 30


def log(msg: str) -> None:
    print(f"[smoke_live_app] {msg}", flush=True)


def fail(reason: str) -> None:
    log(f"FAIL: {reason}")
    sys.exit(1)


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("LIVE_APP_URL", DEFAULT_URL)
    url = url.rstrip("/")
    log(f"target: {url}")

    try:
        with httpx.Client(timeout=RESPONSE_TIMEOUT_S) as client:
            # Health check
            try:
                resp = client.get(f"{url}/health")
                resp.raise_for_status()
                log(f"health ok: {resp.status_code}")
            except httpx.RequestError as e:
                fail(f"health check failed: {e}")

            # Info endpoint
            try:
                resp = client.get(f"{url}/info")
                resp.raise_for_status()
                data = resp.json()
                log(f"info ok: {list(data.keys())}")
            except httpx.RequestError as e:
                fail(f"info endpoint failed: {e}")

            log("PASS: backend responded successfully")
    except httpx.HTTPStatusError as e:
        fail(f"unexpected status {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        fail(f"unexpected error: {e}")


if __name__ == "__main__":
    main()
