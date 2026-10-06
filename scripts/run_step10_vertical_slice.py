from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aavc.application.services.vertical_slice import run_vertical_slice  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run STEP 10 end-to-end vertical slice")
    parser.add_argument("--docx", required=True)
    parser.add_argument("--assets", required=True)
    parser.add_argument("--audio")
    parser.add_argument("--srt")
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="STEP 10 Demo")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    result = run_vertical_slice(
        title=args.title,
        scene_docx=args.docx,
        asset_directory=args.assets,
        narration_audio=args.audio,
        subtitle_srt=args.srt,
        output_directory=args.out,
        ffmpeg=args.ffmpeg,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
