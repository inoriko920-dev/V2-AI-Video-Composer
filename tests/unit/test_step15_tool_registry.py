from pathlib import Path

import pytest

from aavc.platform.tool_registry import ToolNotFoundError, resolve_media_tool


def test_resolver_prefers_app_local_tool(tmp_path: Path) -> None:
    local = tmp_path / "ffmpeg.exe"
    local.write_text("synthetic", encoding="utf-8")

    resolution = resolve_media_tool(
        "ffmpeg",
        extra_roots=(tmp_path,),
        which=lambda _: "C:/system/ffmpeg.exe",
    )

    assert resolution.path == str(local.resolve())
    assert resolution.source == "app-local"


def test_resolver_falls_back_to_system_path(tmp_path: Path) -> None:
    resolution = resolve_media_tool(
        "ffmpeg",
        extra_roots=(tmp_path,),
        which=lambda _: "C:/Tools/ffmpeg.exe",
    )

    assert resolution.path.endswith("ffmpeg.exe")
    assert resolution.source == "system-path"


def test_resolver_reports_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(ToolNotFoundError, match="tools/ffmpeg"):
        resolve_media_tool("ffmpeg", extra_roots=(tmp_path,), which=lambda _: None)
