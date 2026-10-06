# Wave I PyAV Windows Spike

This directory is an isolated dependency-gate experiment. It is **not** part of
the AAVC runtime package and does not change `pyproject.toml` or
`requirements.lock`.

The spike installs exactly `av==19.0.1` as a binary wheel on Windows/Python
3.12, then verifies:

- import succeeds;
- package metadata reports BSD-3-Clause;
- FFmpeg library versions are visible through PyAV;
- a synthetic 64x64 MPEG-4 clip can be encoded and decoded;
- import and round-trip latency stay below deliberately loose CI guardrails;
- installed distribution footprint stays below 250 MiB.

The result is uploaded as `artifacts/pyav_spike.json`.

Passing this spike does **not** make PyAV a runtime dependency and does **not**
authorize replacement of the FFmpeg CLI final-render path.
