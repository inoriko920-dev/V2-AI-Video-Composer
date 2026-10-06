from pathlib import Path


def test_presentation_does_not_import_infrastructure_owners() -> None:
    root = Path(__file__).parents[2] / "src" / "aavc" / "presentation"
    forbidden = ["aavc.providers", "aavc.rendering", "aavc.import_pipeline", "subprocess", "requests"]
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path} contains forbidden dependency {token}"
