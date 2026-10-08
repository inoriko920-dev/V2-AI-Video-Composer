# v0.3.0 RC only: extracted/copy portable smoke for Windows special paths.
# No user projects, no FFmpeg binaries redistributed, no release publication.
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$source = Join-Path $root "dist\AI Automatic Video Composer"
$sourceExe = Join-Path $source "AI Automatic Video Composer.exe"
if (-not (Test-Path $sourceExe)) { throw "Portable must be built first" }

$base = Join-Path $root "artifacts\v030_path_matrix"
if (Test-Path $base) { throw "Existing path matrix directory; refuse overwrite" }
New-Item -ItemType Directory -Path $base | Out-Null

$cases = @(
  @{ id = "ASCII"; relative = "Ascii" },
  @{ id = "SPACES"; relative = "Folder With Spaces" },
  @{ id = "APOSTROPHE"; relative = "O'Brien Folder" },
  @{ id = "UNICODE"; relative = "Bojonegoro-日本語" },
  @{ id = "DEEP"; relative = "a-long-nested-folder-for-portable-validation/second-layer/third-layer/fourth-layer" }
)
$reports = @()
foreach ($case in $cases) {
  $destination = Join-Path $base $case.relative
  New-Item -ItemType Directory -Force -Path $destination | Out-Null
  Copy-Item -Path (Join-Path $source "*") -Destination $destination -Recurse -Force
  $exe = Join-Path $destination "AI Automatic Video Composer.exe"
  $marker = Join-Path $destination "portable-marker.txt"
  if (-not (Test-Path $exe)) { throw "Portable EXE absent for $($case.id)" }
  $args = @("--foundation-smoke", "--foundation-smoke-file", ('"' + $marker + '"'))
  $process = Start-Process -FilePath $exe -ArgumentList $args -Wait -PassThru
  if ($process.ExitCode -ne 0) { throw "RC special-path smoke failed: $($case.id)" }
  if (-not (Test-Path $marker)) { throw "Marker absent: $($case.id)" }
  if ((Get-Content $marker -Raw) -notmatch "AAVC_FOUNDATION_SMOKE_OK") {
    throw "Marker invalid: $($case.id)"
  }
  $reports += "$($case.id)=PASS"
  Remove-Item -Path $destination -Recurse -Force
}
$reports += "SPECIAL_PATH_MATRIX=5/5_PASS"
$reports | Set-Content (Join-Path $base "SPECIAL_PATH_MATRIX.txt") -Encoding utf8
$reports | ForEach-Object { Write-Host $_ }
