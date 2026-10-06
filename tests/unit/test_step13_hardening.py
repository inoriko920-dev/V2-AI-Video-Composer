from __future__ import annotations

import time
import zipfile
from pathlib import Path
from threading import Event

from aavc.diagnostics import redact_text, write_diagnostics_bundle
from aavc.domain.project.models import RenderQualitySettings
from aavc.jobs import CancellationToken, JobManager, JobStatus
from aavc.rendering import (
    PreflightSeverity,
    RenderPlan,
    SceneRenderPlan,
    validate_render_plan,
)


def _plan(tmp_path: Path, asset: Path) -> RenderPlan:
    return RenderPlan(
        width=1920,
        height=1080,
        fps=30,
        scenes=(
            SceneRenderPlan(
                scene_number=1,
                duration_seconds=3.0,
                asset_paths=(str(asset),),
                placements=(),
            ),
        ),
        narration_audio=None,
        subtitle_ass=None,
        output_path=str(tmp_path / "output.mp4"),
        quality=RenderQualitySettings(),
    )


def test_render_preflight_passes_ready_plan(tmp_path: Path) -> None:
    asset = tmp_path / "A001.png"
    asset.write_bytes(b"png")
    report = validate_render_plan(_plan(tmp_path, asset))
    assert report.ok
    assert report.issues == ()


def test_render_preflight_blocks_missing_asset(tmp_path: Path) -> None:
    report = validate_render_plan(_plan(tmp_path, tmp_path / "missing.png"))
    assert not report.ok
    assert any(
        issue.code == "MISSING_ASSET" and issue.severity is PreflightSeverity.ERROR
        for issue in report.issues
    )


def test_redaction_removes_common_secret_shapes() -> None:
    explicit = "super-secret-value"
    source = (
        "api_key=super-secret-value Bearer abcdefghijklmnop "
        "AIza1234567890abcdefghijklmno"
    )
    result = redact_text(source, (explicit,))
    assert explicit not in result
    assert "abcdefghijklmnop" not in result
    assert "AIza1234567890" not in result
    assert result.count("[REDACTED]") >= 3


def test_diagnostics_bundle_never_writes_explicit_secret(tmp_path: Path) -> None:
    secret = "test-key-do-not-leak"
    output = write_diagnostics_bundle(
        tmp_path / "diag.zip",
        summary={"provider": "gemini", "detail": f"token={secret}"},
        logs=[f"Authorization: Bearer {secret}", f"raw {secret}"],
        explicit_secrets=(secret,),
    )
    with zipfile.ZipFile(output) as archive:
        combined = archive.read("summary.json") + archive.read("logs.txt")
    assert secret.encode() not in combined
    assert b"[REDACTED]" in combined


def test_job_manager_completes_and_cancels_cooperatively() -> None:
    manager = JobManager(max_workers=1)
    try:
        done_id = manager.submit("quick", lambda token: token.raise_if_cancelled())
        deadline = time.monotonic() + 2.0
        while manager.snapshot(done_id).status not in {JobStatus.COMPLETED, JobStatus.FAILED}:
            assert time.monotonic() < deadline
            time.sleep(0.01)
        assert manager.snapshot(done_id).status is JobStatus.COMPLETED

        started = Event()

        def cancellable(token: CancellationToken) -> None:
            started.set()
            while not token.is_cancelled:
                time.sleep(0.01)
            token.raise_if_cancelled()

        cancel_id = manager.submit("cancel-me", cancellable)
        assert started.wait(1.0)
        assert manager.cancel(cancel_id)
        deadline = time.monotonic() + 2.0
        while manager.snapshot(cancel_id).status is not JobStatus.CANCELLED:
            assert time.monotonic() < deadline
            time.sleep(0.01)
        assert manager.snapshot(cancel_id).status is JobStatus.CANCELLED
    finally:
        manager.shutdown()
