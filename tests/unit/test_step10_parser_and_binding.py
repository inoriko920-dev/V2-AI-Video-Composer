import zipfile
from pathlib import Path

import pytest

from aavc.domain.errors import ImportError as AAVCImportError
from aavc.importing.assets import bind_assets
from aavc.importing.docx_scene import parse_scene_docx

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def test_docx_parses_single_and_double_scene() -> None:
    scenes = parse_scene_docx(FIXTURE / "scene_asset_demo.docx")
    assert [scene.mode for scene in scenes] == ["SINGLE", "DOUBLE"]
    assert scenes[0].asset_ids == ("A001",)
    assert scenes[1].asset_ids == ("A002", "A003")


def test_asset_binding_is_ready() -> None:
    scenes = parse_scene_docx(FIXTURE / "scene_asset_demo.docx")
    bindings = bind_assets(scenes, FIXTURE / "assets")
    assert [binding.status for binding in bindings] == ["READY", "READY", "READY"]



def test_malformed_docx_xml_is_reported_as_safe_import_error(tmp_path: Path) -> None:
    broken = tmp_path / "broken.docx"
    with zipfile.ZipFile(broken, "w") as archive:
        archive.writestr("word/document.xml", "<w:document><broken>")

    with pytest.raises(AAVCImportError, match="DOCX tidak dapat dibaca"):
        parse_scene_docx(broken)
