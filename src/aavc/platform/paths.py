from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PathService:
    """Resolve application-owned paths without embedding developer absolute paths."""

    executable_dir: Path

    @classmethod
    def discover(cls) -> PathService:
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).resolve().parent
        else:
            base = Path(__file__).resolve().parents[3]
        return cls(executable_dir=base)

    def resources_dir(self) -> Path:
        return self.executable_dir / "resources"

    def tools_dir(self) -> Path:
        return self.executable_dir / "tools"
