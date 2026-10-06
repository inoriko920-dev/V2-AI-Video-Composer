from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "aavc"

FORBIDDEN_DOMAIN_ROOTS = {"PySide6", "subprocess", "requests", "httpx"}


def imports_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_domain_has_no_infrastructure_imports() -> None:
    violations: list[str] = []
    for path in (SRC / "domain").rglob("*.py"):
        for name in imports_in(path):
            root = name.split(".")[0]
            if root in FORBIDDEN_DOMAIN_ROOTS or name.startswith("aavc.presentation"):
                violations.append(f"{path.relative_to(SRC)} -> {name}")
    assert violations == []


def test_raw_subprocess_is_owned_only_by_process_runner() -> None:
    violations: list[str] = []
    owner = (SRC / "platform" / "process_runner.py").resolve()
    for path in SRC.rglob("*.py"):
        if path.resolve() == owner:
            continue
        if any(name == "subprocess" or name.startswith("subprocess.") for name in imports_in(path)):
            violations.append(str(path.relative_to(SRC)))
    assert violations == []


FORBIDDEN_MEDIA_CONTRACT_ROOTS = {
    "PySide6",
    "subprocess",
    "requests",
    "httpx",
    "av",
    "openshot",
    "mlt",
}


def test_v2_media_contracts_do_not_import_backend_or_ui_libraries() -> None:
    violations: list[str] = []
    roots = [SRC / "media", SRC / "application" / "ports"]
    for root_path in roots:
        for path in root_path.rglob("*.py"):
            for name in imports_in(path):
                import_root = name.split(".")[0]
                if import_root in FORBIDDEN_MEDIA_CONTRACT_ROOTS:
                    violations.append(f"{path.relative_to(SRC)} -> {name}")
                if name.startswith("aavc.presentation") or name.startswith("aavc.platform"):
                    violations.append(f"{path.relative_to(SRC)} -> {name}")
    assert violations == []
