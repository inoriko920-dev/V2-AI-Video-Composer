from pathlib import Path

import pytest

from aavc.application.commands import SetNarrationAudio, SetSubtitleSource
from aavc.application.services.media_import import classify_media_path
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _session() -> ProjectSession:
    project = create_project_state(
        title="media-import",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )
    session = ProjectSession()
    session.start(project)
    return session


def test_classify_supported_media_types(tmp_path: Path) -> None:
    subtitle = tmp_path / "dialog.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nHalo\n", encoding="utf-8")
    audio = tmp_path / "voice.MP3"
    audio.write_bytes(b"audio")

    assert classify_media_path(subtitle) == "subtitle"
    assert classify_media_path(audio) == "narration"


def test_classify_rejects_unsupported_media(tmp_path: Path) -> None:
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"video")

    with pytest.raises(ValueError, match="Format media belum didukung"):
        classify_media_path(video)


def test_media_commands_participate_in_undo_redo_history(tmp_path: Path) -> None:
    audio = tmp_path / "voice.wav"
    audio.write_bytes(b"audio")
    subtitle = tmp_path / "caption.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nHalo\n", encoding="utf-8")
    session = _session()

    session.execute(SetNarrationAudio(str(audio)))
    assert session.current is not None
    assert session.current.narration_audio == str(audio.resolve())

    session.execute(SetSubtitleSource(str(subtitle)))
    assert session.current.subtitle_source == str(subtitle.resolve())

    session.undo()
    assert session.current.subtitle_source is None
    assert session.current.narration_audio == str(audio.resolve())

    session.undo()
    assert session.current.narration_audio is None

    session.redo()
    assert session.current.narration_audio == str(audio.resolve())


def test_commands_reject_wrong_media_role(tmp_path: Path) -> None:
    subtitle = tmp_path / "caption.srt"
    subtitle.write_text("subtitle", encoding="utf-8")
    session = _session()

    with pytest.raises(ValueError, match="bukan audio narasi"):
        session.execute(SetNarrationAudio(str(subtitle)))
