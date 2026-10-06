from __future__ import annotations

import subprocess
import time
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from threading import Thread
from typing import TextIO


@dataclass(frozen=True, slots=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str


class ProcessCancelledError(RuntimeError):
    """Raised after a managed child process is terminated for cancellation."""


def windows_command_units(argv: Sequence[str]) -> int:
    """Return CreateProcessW UTF-16 command units including the NUL terminator."""

    rendered = subprocess.list2cmdline(list(argv))
    return len(rendered.encode("utf-16-le")) // 2 + 1


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2.0)


class ProcessRunner:
    """The only repository owner allowed to execute child processes."""

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        completed = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=timeout_seconds,
        )
        return ProcessResult(completed.returncode, completed.stdout, completed.stderr)

    def run_managed(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
        cancel_requested: Callable[[], bool] | None = None,
        stdout_line_callback: Callable[[str], None] | None = None,
        poll_interval_seconds: float = 0.05,
    ) -> ProcessResult:
        """Run a child process with cooperative cancellation and line progress.

        The legacy run path remains unchanged. Managed execution is opt-in for
        long-running work such as V2 renders.
        """

        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds harus > 0")

        process = subprocess.Popen(
            list(argv),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            bufsize=1,
        )
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def consume(
            stream: TextIO | None,
            target: list[str],
            callback: Callable[[str], None] | None = None,
        ) -> None:
            if stream is None:
                return
            try:
                for line in stream:
                    target.append(line)
                    if callback is not None:
                        with suppress(Exception):
                            callback(line.rstrip("\r\n"))
            finally:
                stream.close()

        stdout_thread = Thread(
            target=consume,
            args=(process.stdout, stdout_lines, stdout_line_callback),
            daemon=True,
        )
        stderr_thread = Thread(
            target=consume,
            args=(process.stderr, stderr_lines),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()

        started = time.monotonic()
        cancelled = False
        timed_out = False
        while process.poll() is None:
            if cancel_requested is not None and cancel_requested():
                cancelled = True
                _terminate_process(process)
                break
            if timeout_seconds is not None and time.monotonic() - started > timeout_seconds:
                timed_out = True
                _terminate_process(process)
                break
            time.sleep(poll_interval_seconds)

        stdout_thread.join(timeout=2.0)
        stderr_thread.join(timeout=2.0)

        if cancelled:
            raise ProcessCancelledError("Proses eksternal dibatalkan")
        if timed_out:
            raise subprocess.TimeoutExpired(list(argv), timeout_seconds)

        return ProcessResult(
            process.returncode if process.returncode is not None else -1,
            "".join(stdout_lines),
            "".join(stderr_lines),
        )
