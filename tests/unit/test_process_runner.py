from __future__ import annotations

import sys
import threading
import time

import pytest

from aavc.platform.process_runner import ProcessCancelledError, ProcessRunner


def test_process_runner_replaces_undecodable_child_output() -> None:
    runner = ProcessRunner()
    result = runner.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.stderr.buffer.write(bytes([0x81])); sys.stderr.flush()",
        ]
    )

    assert result.returncode == 0
    assert isinstance(result.stderr, str)
    assert result.stderr



def test_managed_process_can_be_cancelled_cooperatively() -> None:
    runner = ProcessRunner()
    cancelled = threading.Event()
    timer = threading.Timer(0.2, cancelled.set)
    timer.start()
    started = time.monotonic()
    try:
        with pytest.raises(ProcessCancelledError):
            runner.run_managed(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                cancel_requested=cancelled.is_set,
                poll_interval_seconds=0.02,
            )
    finally:
        timer.cancel()

    assert time.monotonic() - started < 5.0
