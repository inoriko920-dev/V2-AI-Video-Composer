from __future__ import annotations

import sys

from aavc.platform.process_runner import ProcessRunner


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
