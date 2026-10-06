from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_wave_i_keeps_optional_backends_out_of_runtime_dependencies() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    lock = (ROOT / "requirements.lock").read_text(encoding="utf-8")

    lowered = (pyproject + "\n" + lock).lower()
    assert "\nav==" not in lowered
    assert '"av==' not in lowered
    assert "libopenshot" not in lowered
    assert "\nmlt==" not in lowered


def test_wave_i_spike_isolated_from_runtime_package() -> None:
    script = ROOT / "spikes" / "pyav" / "verify_pyav.py"
    workflow = ROOT / ".github" / "workflows" / "backend-spike.yml"

    assert script.is_file()
    assert workflow.is_file()
    assert not str(script.relative_to(ROOT)).startswith("src/")
    assert "av==19.0.1" in workflow.read_text(encoding="utf-8")
    assert "--only-binary=:all:" in workflow.read_text(encoding="utf-8")


def test_wave_i_decision_keeps_ffmpeg_as_reference_and_fallback() -> None:
    decision = (
        ROOT / "docs" / "V2_WAVE_I_BACKEND_SPIKE_DECISION.md"
    ).read_text(encoding="utf-8")

    assert "FFmpeg/ffprobe CLI" in decision
    assert "KEEP as production reference/fallback" in decision
    assert "PyAV remains **not adopted** in Wave I" in decision
