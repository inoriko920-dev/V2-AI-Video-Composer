param(
  [ValidateSet("rc", "final-verification")]
  [string]$Channel = "rc"
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$dist = Join-Path $root "dist\AI Automatic Video Composer"
$release = Join-Path $root "release_candidate_0_3_0"

if (-not (Test-Path (Join-Path $dist "AI Automatic Video Composer.exe"))) {
  throw "Portable must be built and verified before candidate packaging"
}
$python = if (Test-Path (Join-Path $root ".venv\Scripts\python.exe")) {
  Join-Path $root ".venv\Scripts\python.exe"
} else { "python" }

Push-Location $root
try {
  & $python -m scripts.verify_artifact_security $dist
  if ($LASTEXITCODE -ne 0) { throw "Portable content security verification failed" }

  $packageVersion = (& $python -c "from importlib.metadata import version; print(version('ai-automatic-video-composer'))").Trim()
  $runtimeVersion = (& $python -c "from aavc import __version__; print(__version__)").Trim()
  if ($packageVersion -ne "0.3.0" -or $runtimeVersion -ne "0.3.0") {
    throw "Version mismatch: package=$packageVersion runtime=$runtimeVersion"
  }

  # Immutable published baseline and no accidental public 0.3.0 tag reuse.
  $priorTag = (git rev-parse "refs/tags/v0.2.2^{commit}").Trim()
  if ($LASTEXITCODE -ne 0 -or $priorTag -ne "eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef") {
    throw "Immutable v0.2.2 release tag changed"
  }
  $existing = @(git tag --list "v0.3.0")
  if ($existing -contains "v0.3.0") {
    throw "v0.3.0 already tagged: RC builder must not overwrite/publicize it"
  }

  $commit = (git rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[0-9a-f]{40}$') {
    throw "Missing exact source commit"
  }
  if (Test-Path $release) { throw "Candidate directory already exists: refuse overwrite" }
  New-Item -ItemType Directory -Force $release | Out-Null

  $portableName = "AI-Automatic-Video-Composer-0.3.0-win64.zip"
  $sourceName = "AI-Automatic-Video-Composer-0.3.0-source.zip"
  $portable = Join-Path $release $portableName
  $source = Join-Path $release $sourceName

  Compress-Archive -Path (Join-Path $dist "*") -DestinationPath $portable -CompressionLevel Optimal
  git archive --format=zip "--output=$source" HEAD
  if ($LASTEXITCODE -ne 0) { throw "git archive exact source failed" }

  # Do not claim these to be published/immutable. STEP07 owns publication.
  Copy-Item "RELEASE_NOTES_0.3.0.md" (Join-Path $release "RELEASE_NOTES_0.3.0.md")
  Copy-Item "V2_FINAL_RELEASE_MANIFEST_0.3.0.md" (Join-Path $release "V2_FINAL_RELEASE_MANIFEST_0.3.0.md")
  Copy-Item "docs\USER_GUIDE.md" (Join-Path $release "USER_GUIDE.md")
  Copy-Item "MAINTENANCE.md" (Join-Path $release "MAINTENANCE.md")
  Copy-Item "BACKUP_AND_RECOVERY.md" (Join-Path $release "BACKUP_AND_RECOVERY.md")

  $pythonVersion = (& $python --version).Trim()
  $pyside = (& $python -c "import PySide6; print(PySide6.__version__)").Trim()
  $pyinstaller = (& $python -c "from importlib.metadata import version; print(version('pyinstaller'))").Trim()
  $ffmpegReference = if ($env:FFMPEG_REFERENCE) { $env:FFMPEG_REFERENCE } else { "9.0.2" }
  if ($ffmpegReference -ne "9.0.2") { throw "FFmpeg reference may not drift" }
  @(
    "version=0.3.0",
    "channel=$Channel",
    "release_commit=$commit",
    "schema_max=4",
    "animation_contract=advanced-v1",
    "python=$pythonVersion",
    "pyside6=$pyside",
    "pyinstaller=$pyinstaller",
    "ffmpeg_reference=$ffmpegReference",
    "ffmpeg_distribution=external-only",
    "publication_status=NOT_PUBLISHED"
  ) | Set-Content (Join-Path $release "BUILD_INFO.txt") -Encoding utf8

  Add-Type -AssemblyName System.IO.Compression
  $archive = [System.IO.Compression.ZipFile]::OpenRead($portable)
  try {
    $entries = @($archive.Entries | ForEach-Object { $_.FullName.ToLowerInvariant() })
    if (-not ($entries | Where-Object { $_ -eq "ai automatic video composer.exe" })) {
      throw "Portable ZIP missing root executable"
    }
    if (-not ($entries | Where-Object { $_ -eq "tools/ffmpeg/readme.md" })) {
      throw "Portable ZIP missing FFmpeg external-install instructions"
    }
    if ($entries | Where-Object { $_ -match '(^|/)(ffmpeg|ffprobe)\.exe$' }) {
      throw "Portable ZIP illegally contains FFmpeg/ffprobe executables"
    }
  }
  finally { $archive.Dispose() }

  $checksumLines = foreach ($file in @($portable, $source)) {
    $sha = (Get-FileHash $file -Algorithm SHA256).Hash.ToLowerInvariant()
    "$sha  $([System.IO.Path]::GetFileName($file))"
  }
  $checksumFile = Join-Path $release "SHA256SUMS.txt"
  $checksumLines | Set-Content $checksumFile -Encoding utf8
  foreach ($line in Get-Content $checksumFile) {
    $parts = $line -split '\s+', 2
    if ($parts.Count -ne 2) { throw "Invalid SHA256SUMS record" }
    $actual = (Get-FileHash (Join-Path $release $parts[1]) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($parts[0] -ne $actual) { throw "Archive checksum verification failed" }
  }

  Write-Host "STEP07_RC_CANDIDATE_HASHES_PASS"
  Write-Host "STEP07_RC_CANDIDATE_EXACT_COMMIT=$commit"
  Write-Host "STEP07_RC_CANDIDATE_NON_PUBLISHING=$Channel"
}
finally { Pop-Location }
