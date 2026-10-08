from __future__ import annotations

from pathlib import Path

from aavc.presentation.windows.narration_recording_window import (
    NarrationRecordingMainWindow,
    default_narration_recording_path,
    ensure_wav_suffix,
    finalize_narration_recording,
    narration_recording_enabled,
    narration_staging_path,
)
from aavc.presentation.windows.project_action_state_window import (
    ProjectActionStateMainWindow,
)


def test_narration_recording_runtime_preserves_project_action_state_layer() -> None:
    assert issubclass(NarrationRecordingMainWindow, ProjectActionStateMainWindow)


def test_narration_recording_requires_active_project() -> None:
    assert narration_recording_enabled(has_project=False) is False
    assert narration_recording_enabled(has_project=True) is True


def test_ensure_wav_suffix_normalizes_destination(tmp_path: Path) -> None:
    expected = (tmp_path / "take.wav").resolve()
    assert ensure_wav_suffix(tmp_path / "take") == expected
    assert ensure_wav_suffix(tmp_path / "take.MP3") == expected
    assert ensure_wav_suffix(tmp_path / "take.WAV") == expected
    assert ensure_wav_suffix(tmp_path / "take.WaV") == expected
    assert ensure_wav_suffix(tmp_path / "take.wav") == expected


def test_default_recording_path_prefers_project_directory(tmp_path: Path) -> None:
    project_dir = tmp_path / "project-dir"
    source_dir = tmp_path / "source-dir"
    project_dir.mkdir()
    source_dir.mkdir()

    result = default_narration_recording_path(
        project_path=project_dir / "sample.aavcproj",
        source_docx=source_dir / "scene.docx",
        project_title="My Project 01",
    )

    assert result == project_dir / "My_Project_01_narration.wav"


def test_default_recording_path_falls_back_to_docx_directory(tmp_path: Path) -> None:
    source_dir = tmp_path / "source-dir"
    source_dir.mkdir()

    result = default_narration_recording_path(
        project_path=None,
        source_docx=source_dir / "scene.docx",
        project_title="  ",
    )

    assert result == source_dir / "project_narration.wav"



def test_narration_staging_path_is_hidden_sibling_wav(tmp_path: Path) -> None:
    destination = tmp_path / "voice.wav"

    staging = narration_staging_path(destination)

    assert staging.parent == destination.parent
    assert staging.suffix == ".wav"
    assert staging.name.startswith(".voice.aavc-recording-")
    assert staging != destination


def test_finalize_narration_recording_replaces_existing_destination_atomically(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "voice.wav"
    destination.write_bytes(b"old-valid-audio")
    staging = narration_staging_path(destination)
    staging.write_bytes(b"new-valid-audio")

    finalized = finalize_narration_recording(staging, destination)

    assert finalized == destination.resolve()
    assert destination.read_bytes() == b"new-valid-audio"
    assert not staging.exists()


def test_invalid_staging_does_not_clobber_existing_narration(tmp_path: Path) -> None:
    destination = tmp_path / "voice.wav"
    destination.write_bytes(b"old-valid-audio")
    staging = narration_staging_path(destination)
    staging.write_bytes(b"")

    try:
        finalize_narration_recording(staging, destination)
    except ValueError as error:
        assert "tidak valid" in str(error)
    else:
        raise AssertionError("empty recording must be rejected")

    assert destination.read_bytes() == b"old-valid-audio"
    assert staging.exists()
