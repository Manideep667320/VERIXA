"""Run a historical cases CSV through the agent in shadow mode."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.agent.shadow import import_history_csv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="CSV with request,human_decision,human_action columns")
    args = parser.parse_args()
    states = asyncio.run(import_history_csv(args.csv_path))
    print(f"Imported {len(states)} historical cases into shadow mode.")


if __name__ == "__main__":
    main()
