from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

STATES = [
    "UI-002",
    "UI-003",
    "UI-010",
    "UI-013",
    "UI-014",
    "UI-027",
    "UI-035",
    "UI-041",
]
ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture representative STEP09 Qt UI screenshots")
    parser.add_argument(
        "--output",
        default=str(ROOT / "artifacts" / "step09_actual"),
        help="Directory for *_ACTUAL.png screenshots",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    for state in STATES:
        target = output / f"{state}_ACTUAL.png"
        cmd = [
            sys.executable,
            "-m",
            "aavc",
            "--ui-state",
            state,
            "--capture-path",
            str(target),
        ]
        print("RUN", " ".join(cmd))
        subprocess.run(cmd, cwd=ROOT, env=env, check=True)
    print(f"Captured {len(STATES)} screenshots in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
