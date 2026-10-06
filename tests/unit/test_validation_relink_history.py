import shutil
from pathlib import Path

from aavc.application.commands import RelinkAsset
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.validation import validate_project
from aavc.application.services.vertical_slice import create_project_state

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _missing_asset_ids(session: ProjectSession) -> set[str]:
    project = session.current
    assert project is not None
    return {
        issue.asset_id
        for issue in validate_project(project)
        if issue.code == "ASSET_NOT_READY" and issue.asset_id is not None
    }


def test_relink_resolves_live_validation_and_undo_restores_it(tmp_path: Path) -> None:
    asset_dir = tmp_path / "assets"
    asset_dir.mkdir()
    shutil.copy2(FIXTURE / "assets" / "A001.png", asset_dir / "A001.png")
    shutil.copy2(FIXTURE / "assets" / "A002.png", asset_dir / "A002.png")

    project = create_project_state(
        title="validation-relink",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=asset_dir,
    )
    session = ProjectSession()
    session.start(project)

    assert _missing_asset_ids(session) == {"A003"}

    session.execute(RelinkAsset("A003", str(FIXTURE / "assets" / "A003.png")))
    assert _missing_asset_ids(session) == set()

    session.undo()
    assert _missing_asset_ids(session) == {"A003"}
