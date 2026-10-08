"""W06-A deterministic contract: RED before the recovery coordinator exists.

Only application scheduling is covered here. No real filesystem, dialogs, Qt
timers, snapshot sidecars or recovery/restore transaction is exercised.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aavc.application.commands import SetSceneDuration
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.recovery_coordinator import RecoveryCoordinator, SnapshotRequest
from aavc.domain.project.models import ProjectState, Scene


@dataclass
class FakeClock:
    seconds: float = 0.0

    def __call__(self) -> float:
        return self.seconds

    def advance(self, seconds: float) -> None:
        self.seconds += seconds


def _project() -> ProjectState:
    return ProjectState(
        schema_version=3,
        title="W06-A synthetic fixture",
        source_docx="synthetic.docx",
        asset_directory="synthetic_assets",
        scenes=(Scene(1, ("asset1",), ("synthetic",), 3.0),),
        bindings=(),
        metadata={"fixture": "synthetic"},
    )


def _session(path: Path | None) -> ProjectSession:
    s = ProjectSession()
    s.start(_project(), path)
    return s


def _change(s: ProjectSession, duration: float) -> None:
    s.execute(SetSceneDuration(1, duration))


def _scheduled(c: RecoveryCoordinator, s: ProjectSession) -> SnapshotRequest:
    request = c.tick(s)
    assert isinstance(request, SnapshotRequest)
    return request


def test_sch_01_rcv_03_debounce_20s(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "demo.aavcproj")
    coordinator = RecoveryCoordinator(clock=clock)
    _change(session, 4.0)
    assert coordinator.tick(session) is None
    clock.advance(19.999)
    assert coordinator.tick(session) is None
    clock.advance(0.001)
    request = _scheduled(coordinator, session)
    assert request.path == session.path
    assert request.revision == 1
    assert coordinator.inflight is request
    assert session.is_dirty


def test_sch_02_rcv_03_latest_edit_resets_debounce(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4.0)
    assert c.tick(session) is None
    clock.advance(15)
    _change(session, 5.0)
    assert c.tick(session) is None
    clock.advance(19)
    assert c.tick(session) is None
    clock.advance(1)
    assert _scheduled(c, session).revision == 2


def test_sch_03_rcv_03_continuous_edits_hard_cap_120s(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4.0)
    c.tick(session)
    for i in range(1, 12):
        clock.advance(10)
        _change(session, 4.0 + i)
        assert c.tick(session) is None
    clock.advance(10)
    _change(session, 20.0)
    assert _scheduled(c, session).revision == 13


def test_sch_04_poll_60s_does_not_force_duplicate_write(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4)
    assert c.tick(session) is None
    assert c.next_poll_at == 60
    clock.advance(20)
    req = _scheduled(c, session)
    assert c.complete(req, success=True)
    clock.advance(40)
    assert c.tick(session) is None
    assert c.last_success_revision == req.revision
    assert c.next_poll_at == 120
    clock.advance(180)
    assert c.tick(session) is None
    assert c.next_poll_at == 300


def test_sch_05_retry_30_120_300_seconds(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4)
    c.tick(session)
    clock.advance(20)
    req = _scheduled(c, session)
    assert c.complete(req, success=False)
    assert c.next_retry_at == 50
    clock.advance(29)
    assert c.tick(session) is None
    clock.advance(1)
    req = _scheduled(c, session)
    assert c.complete(req, success=False)
    assert c.next_retry_at == 170
    clock.advance(119)
    assert c.tick(session) is None
    clock.advance(1)
    req = _scheduled(c, session)
    assert c.complete(req, success=False)
    assert c.next_retry_at == 470
    clock.advance(299)
    assert c.tick(session) is None
    clock.advance(1)
    req = _scheduled(c, session)
    assert c.complete(req, success=True)
    assert c.next_retry_at is None


def test_sch_06_rcv_02_clean_and_no_path_never_schedule(tmp_path: Path) -> None:
    clock = FakeClock()
    clean = _session(tmp_path / "clean.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    assert c.tick(clean) is None
    clock.advance(200)
    assert c.tick(clean) is None
    unsaved = _session(None)
    _change(unsaved, 4)
    assert c.tick(unsaved) is None
    clock.advance(200)
    assert c.tick(unsaved) is None
    assert c.inflight is None


def test_sch_07_rcv_21_undo_to_saved_cancels_pending(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4)
    c.tick(session)
    clock.advance(10)
    session.undo()
    assert not session.is_dirty
    assert c.tick(session) is None
    clock.advance(200)
    assert c.tick(session) is None
    assert c.next_due_at is None


def test_sch_08_rcv_21_noop_and_poll_ticks_do_not_create_revisions(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    session.execute(SetSceneDuration(1, 3.0))
    assert c.tick(session) is None
    clock.advance(300)
    assert c.tick(session) is None
    assert c.revision == 0
    _change(session, 4)
    c.tick(session)
    clock.advance(2)
    session.execute(SetSceneDuration(1, 4.0))
    assert c.tick(session) is None
    assert c.revision == 1
    clock.advance(18)
    assert _scheduled(c, session).revision == 1


def test_sch_09_rcv_15_single_global_inflight_writer(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "a.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4)
    c.tick(session)
    clock.advance(20)
    first = _scheduled(c, session)
    assert c.tick(session) is None
    _change(session, 5)
    assert c.tick(session) is None  # observe committed edit while writer owns slot
    clock.advance(20)
    assert c.tick(session) is None
    assert c.complete(first, success=True)
    next_job = _scheduled(c, session)
    assert next_job is not first
    assert next_job.revision == 2


def test_sch_10_rcv_22_old_epoch_completion_cannot_mark_current_success(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "a.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4)
    c.tick(session)
    clock.advance(20)
    pending = _scheduled(c, session)
    session.save()
    assert c.tick(session) is None
    _change(session, 5)
    assert c.tick(session) is None
    assert c.complete(pending, success=True) is False
    assert c.last_success_revision is None
    clock.advance(20)
    assert _scheduled(c, session).revision >= 1


def test_sch_11_rcv_15_switch_paths_fences_old_job(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "a.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4)
    c.tick(session)
    clock.advance(20)
    job_a = _scheduled(c, session)
    session.start(_project(), tmp_path / "b.aavcproj")
    _change(session, 5)
    assert c.tick(session) is None
    clock.advance(20)
    assert c.tick(session) is None
    assert c.complete(job_a, success=True) is False
    job_b = _scheduled(c, session)
    assert job_b.path.name == "b.aavcproj"
    assert job_b.epoch != job_a.epoch


def test_sch_12_close_blocks_and_invalidates_late_completion(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "a.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4)
    c.tick(session)
    clock.advance(20)
    req = _scheduled(c, session)
    c.close()
    assert c.complete(req, success=True) is False
    assert c.tick(session) is None
    assert c.last_success_revision is None


def test_rcv_01_snapshot_dispatch_does_not_change_session_or_disk(tmp_path: Path) -> None:
    clock = FakeClock()
    project_file = tmp_path / "demo.aavcproj"
    project_file.write_bytes(b"original disk bytes")
    session = _session(project_file)
    _change(session, 4)
    before = project_file.read_bytes()
    can_undo = session.can_undo
    c = RecoveryCoordinator(clock=clock)
    c.tick(session)
    clock.advance(20)
    req = _scheduled(c, session)
    assert req.project_state.scenes[0].duration_seconds == 4
    assert session.is_dirty and session.can_undo == can_undo
    assert project_file.read_bytes() == before
    assert list(tmp_path.iterdir()) == [project_file]


def test_snapshot_request_defensively_copies_mutable_metadata(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "demo.aavcproj")
    _change(session, 4)
    c = RecoveryCoordinator(clock=clock)
    c.tick(session)
    clock.advance(20)
    req = _scheduled(c, session)
    assert req.project_state is not session.current
    assert session.current is not None
    session.current.metadata["fixture"] = "modified after capture"
    assert req.project_state.metadata["fixture"] == "synthetic"


def test_blocked_modal_pauses_dispatch_but_not_dirty_state(tmp_path: Path) -> None:
    clock = FakeClock()
    session = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(session, 4)
    c.tick(session)
    c.set_paused(True)
    clock.advance(130)
    assert c.tick(session) is None
    assert session.is_dirty
    c.set_paused(False)
    assert _scheduled(c, session).revision == 1


def test_repeated_wrong_completion_cannot_release_writer(tmp_path: Path) -> None:
    clock = FakeClock()
    s = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(s, 4)
    c.tick(s)
    clock.advance(20)
    req = _scheduled(c, s)
    fake = SnapshotRequest(req.epoch, req.revision, req.path, req.project_state, req.first_dirty_at)
    assert c.complete(fake, success=True) is False
    assert c.inflight is req
    assert c.complete(req, success=True)
    assert c.complete(req, success=True) is False


def test_reset_session_same_path_invalidates_inflight(tmp_path: Path) -> None:
    clock = FakeClock()
    s = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(s, 4)
    c.tick(s)
    clock.advance(20)
    req = _scheduled(c, s)
    c.reset_session()
    assert c.complete(req, success=True) is False
    assert c.last_success_revision is None


def test_clock_regression_is_rejected(tmp_path: Path) -> None:
    clock = FakeClock()
    s = _session(tmp_path / "demo.aavcproj")
    c = RecoveryCoordinator(clock=clock)
    _change(s, 4)
    c.tick(s)
    clock.advance(-1)
    import pytest

    with pytest.raises(ValueError, match="monotonic"):
        c.tick(s)
