from __future__ import annotations

import json
from dataclasses import asdict

from aavc.rendering.benchmark import benchmark_standard_scene_counts


def main() -> int:
    results = [asdict(item) for item in benchmark_standard_scene_counts()]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
