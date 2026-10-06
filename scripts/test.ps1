$ErrorActionPreference = "Stop"
$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
& $python -m compileall -q src
& $python -m ruff check src tests
& $python -m mypy src/aavc
& $python -m pytest -m "not integration and not visual and not e2e" -q
