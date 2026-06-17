from __future__ import annotations

# ruff: noqa: E402, I001

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from crispasr_agent_transcriber.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
