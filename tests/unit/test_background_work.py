from __future__ import annotations

import time

from aavc.jobs import JobManager
from aavc.jobs.background_call import BackgroundCall
from aavc.presentation.windows.ai_native_motion_window import AiNativeMotionMainWindow
from aavc.presentation.windows.background_work_window import BackgroundWorkMainWindow


def _wait(call: BackgroundCall[object], timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if call.snapshot().done:
            return
        time.sleep(0.01)
    raise AssertionError("background call did not finish in time")


def test_background_runtime_preserves_ai_native_motion_layer() -> None:
    assert issubclass(BackgroundWorkMainWindow, AiNativeMotionMainWindow)


def test_background_call_returns_result_through_canonical_job_manager() -> None:
    jobs = JobManager(max_workers=1)
    try:
        call: BackgroundCall[object] = BackgroundCall(
            jobs,
            lambda: {"ok": True},
            name="render-test",
        )
        call.start()
        _wait(call)

        snapshot = call.snapshot()
        assert snapshot.done is True
        assert snapshot.result == {"ok": True}
        assert snapshot.error is None
        assert call.job_id is not None
        assert any(item.name == "render-test" for item in jobs.snapshots())
    finally:
        jobs.shutdown()


def test_background_call_surfaces_worker_error() -> None:
    jobs = JobManager(max_workers=1)

    def fail() -> object:
        raise ValueError("render failed")

    try:
        call: BackgroundCall[object] = BackgroundCall(jobs, fail, name="failing-render")
        call.start()
        _wait(call)

        snapshot = call.snapshot()
        assert snapshot.done is True
        assert snapshot.result is None
        assert isinstance(snapshot.error, ValueError)
        assert str(snapshot.error) == "render failed"
    finally:
        jobs.shutdown()


def test_background_call_cannot_start_twice() -> None:
    jobs = JobManager(max_workers=1)
    try:
        call: BackgroundCall[object] = BackgroundCall(jobs, lambda: 1)
        call.start()
        try:
            call.start()
        except RuntimeError as error:
            assert "sekali" in str(error)
        else:
            raise AssertionError("second start should fail")
        _wait(call)
    finally:
        jobs.shutdown()


def test_finished_unpolled_call_still_occupies_window_slot() -> None:
    jobs = JobManager(max_workers=1)
    try:
        call: BackgroundCall[object] = BackgroundCall(jobs, lambda: 1)
        window = object.__new__(BackgroundWorkMainWindow)
        window._background_call = call

        call.start()
        _wait(call)

        assert call.snapshot().done is True
        assert window._background_busy() is True

        window._background_call = None
        assert window._background_busy() is False
    finally:
        jobs.shutdown()
