param(
  [ValidateSet("system", "both")][string]$Mode = "both"
)
$ErrorActionPreference = "Stop"
$expected = "9.0.2"
if ($env:FFMPEG_REFERENCE -and $env:FFMPEG_REFERENCE -ne $expected) {
  throw "FFMPEG_REFERENCE must remain the reviewed $expected for v0.2.2"
}

# PATH mode uses the same tools as the real render acceptance suite.
$systemTools = @{}
foreach ($name in @("ffmpeg", "ffprobe")) {
  $command = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $command) { throw "$name missing from PATH; reference $expected is required" }
  $binary = $command.Source
  $line = [string]((& $binary -version | Select-Object -First 1))
  $escaped = [regex]::Escape($expected)
  if ($line -notmatch "^$name version $escaped(?:[-+ ]|$)") {
    throw "$name version mismatch; required $expected"
  }
  $hash = (Get-FileHash $binary -Algorithm SHA256).Hash.ToLowerInvariant()
  $systemTools[$name] = $binary
  Write-Host "$($name.ToUpperInvariant())_REFERENCE=$expected"
  Write-Host "$($name.ToUpperInvariant())_PATH=$binary"
  Write-Host "$($name.ToUpperInvariant())_SHA256=$hash"
}
Write-Host "FFMPEG_REFERENCE=$expected"

if ($Mode -eq "system") { exit 0 }

$dist = Join-Path $PSScriptRoot "..\dist\AI Automatic Video Composer"
$exe = Join-Path $dist "AI Automatic Video Composer.exe"
if (-not (Test-Path $exe)) { throw "Portable EXE required for app-local precedence proof" }

$slot = Join-Path $dist "tools\ffmpeg"
New-Item -ItemType Directory -Force $slot | Out-Null
foreach ($name in @("ffmpeg", "ffprobe")) {
  if (Test-Path (Join-Path $slot "$name.exe")) {
    throw "Distributable unexpectedly already contains $name.exe"
  }
}

# The Chocolatey shim may not be relocatable; stage actual executable payloads.
$choco = if ($env:ChocolateyInstall) { $env:ChocolateyInstall } else { "C:\ProgramData\chocolatey" }
$chocoTools = Join-Path $choco "lib\ffmpeg\tools"
if (-not (Test-Path $chocoTools)) { throw "Reference package payload not found: $chocoTools" }
$physical = @{}
foreach ($name in @("ffmpeg", "ffprobe")) {
  $candidates = @(Get-ChildItem $chocoTools -Recurse -File -Filter "$name.exe")
  if ($candidates.Count -eq 0) { throw "Physical $name.exe not found in reviewed Chocolatey package" }
  $physical[$name] = $candidates[0].FullName
}

try {
  foreach ($name in @("ffmpeg", "ffprobe")) {
    Copy-Item $physical[$name] (Join-Path $slot "$name.exe") -Force
    $line = [string]((& (Join-Path $slot "$name.exe") -version | Select-Object -First 1))
    if ($line -notmatch "^$name version 9\.0\.2(?:[-+ ]|$)") {
      throw "Staged app-local $name has unexpected version"
    }
  }

  # Exercise real frozen-runtime path order without modifying application code.
  $env:AAVC_W06D_EXE = $exe
  $env:AAVC_W06D_SLOT = $slot
  $probe = @'
import os, sys
from pathlib import Path
from aavc.platform.tool_registry import resolve_ffmpeg, resolve_ffprobe
sys.frozen = True
sys.executable = os.environ["AAVC_W06D_EXE"]
slot = Path(os.environ["AAVC_W06D_SLOT"]).resolve()
for resolution in (resolve_ffmpeg(), resolve_ffprobe()):
    assert resolution.source == "app-local", resolution
    assert Path(resolution.path).parent == slot, resolution
print("FFMPEG_APP_LOCAL_PRECEDENCE_PASS")
'@
  $probe | python -
  if ($LASTEXITCODE -ne 0) { throw "app-local/PATH precedence probe failed" }
}
finally {
  Remove-Item (Join-Path $slot "ffmpeg.exe") -Force -ErrorAction SilentlyContinue
  Remove-Item (Join-Path $slot "ffprobe.exe") -Force -ErrorAction SilentlyContinue
  Remove-Item Env:\AAVC_W06D_EXE -ErrorAction SilentlyContinue
  Remove-Item Env:\AAVC_W06D_SLOT -ErrorAction SilentlyContinue
}
foreach ($name in @("ffmpeg", "ffprobe")) {
  if (Test-Path (Join-Path $slot "$name.exe")) { throw "Staged tool was not removed" }
}
python -m scripts.verify_artifact_security $dist
if ($LASTEXITCODE -ne 0) { throw "Artifact scan failed after app-local FFmpeg test" }
Write-Host "FFMPEG_PATH_AND_APP_LOCAL_PASS"
