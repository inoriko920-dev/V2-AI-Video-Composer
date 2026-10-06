$ErrorActionPreference = "Stop"
$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
& $python -m PyInstaller --clean --noconfirm aavc.spec

$dist = Join-Path $PSScriptRoot "..\dist\AI Automatic Video Composer"
$ffmpegSlot = Join-Path $dist "tools\ffmpeg"
New-Item -ItemType Directory -Force $ffmpegSlot | Out-Null
Copy-Item (Join-Path $PSScriptRoot "..\tools\ffmpeg\README.md") (Join-Path $ffmpegSlot "README.md") -Force
