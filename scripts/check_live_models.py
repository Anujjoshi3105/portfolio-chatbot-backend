"""Validate configured models without making an LLM request."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core import settings


def main() -> int:
    print(f"default_model={settings.DEFAULT_MODEL}")
    print(f"available_models={len(settings.AVAILABLE_MODELS)}")
    if not settings.DEFAULT_MODEL or settings.DEFAULT_MODEL not in settings.AVAILABLE_MODELS:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
