"""Regression tests for scanning the actual Windows portable output tree."""
from __future__ import annotations

from pathlib import Path

from scripts.verify_artifact_security import (
    CHUNK_SIZE,
    forbidden_path,
    main,
    scan_artifact,
)


def test_built_artifact_scan_passes_clean_binary_and_docs(tmp_path: Path) -> None:
    (tmp_path / "AI Automatic Video Composer.exe").write_bytes(b"\x00\xfe\x80clean")
    docs = tmp_path / "tools" / "ffmpeg"
    docs.mkdir(parents=True)
    (docs / "README.md").write_text("External FFmpeg only", encoding="utf-8")
    assert scan_artifact(tmp_path) == []
    assert main([str(tmp_path)]) == 0


def test_content_scan_finds_google_key_in_binary_without_printing_value(
    tmp_path: Path, capsys
) -> None:
    secret = "AIza" + ("A" * 35)
    (tmp_path / "packed.bin").write_bytes(b"\xff\x00" + secret.encode() + b"\x00")
    assert scan_artifact(tmp_path) == [("packed.bin", "google-api-key")]
    assert main([str(tmp_path)]) == 1
    result = capsys.readouterr()
    assert secret not in result.out + result.err
    assert "google-api-key" in result.err


def test_chunk_boundary_does_not_hide_embedded_credential(tmp_path: Path) -> None:
    token = ("sk-" + ("B" * 40)).encode()
    (tmp_path / "large.dll").write_bytes(b"_" * (CHUNK_SIZE - 3) + b"\n" + token + b" ")
    assert scan_artifact(tmp_path) == [("large.dll", "openai-or-openrouter-key")]


def test_forbidden_runtime_paths_and_ffmpeg_binaries(tmp_path: Path) -> None:
    for relative in (
        "tools/ffmpeg/ffmpeg.exe",
        "tools/ffmpeg/ffprobe.exe",
        ".env.production",
        "runtime_data/session.json",
        "logs/private.log",
        "project.aavcproj.autosave",
        "private.pem",
    ):
        assert forbidden_path(Path(relative))
        file = tmp_path / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"content")
    findings = scan_artifact(tmp_path)
    assert len(findings) == 7
    assert {kind for _, kind in findings} == {"forbidden-runtime-path"}


def test_nonexistent_artifact_is_an_error(tmp_path: Path) -> None:
    assert main([str(tmp_path / "missing")]) == 1
