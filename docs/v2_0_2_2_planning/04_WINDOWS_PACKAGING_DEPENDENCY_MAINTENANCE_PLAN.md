# STEP 04 — V2 0.2.2 Windows Packaging / Dependency Maintenance Plan

Status: **PASS / PLANNING ONLY**

Audited main: `234fbd88717593b7393696dc35f9834176d0ca95`  
Frozen stable release: `v0.2.1` @ `eb94efebf142ba8203dfc3ae3c5fa861222a0926`

## Purpose

STEP 04 defines the Windows portable-build, dependency-maintenance, FFmpeg/ffprobe, artifact-integrity, and packaging-security contract for v0.2.2. No application runtime implementation is authorized in this STEP.

The goal is not to chase every new package version. The goal is to make the next patch release reproducible, explainable, least-privilege, and resistant to dependency/toolchain drift while preserving the v0.2.1 runtime contract.

## Current packaging baseline

The current V2 line uses:
- Windows 11 x64 target;
- Python 3.12.10 in CI/build workflows;
- PyInstaller onedir;
- portable ZIP distribution;
- PySide6 as the only direct runtime Python dependency;
- external FFmpeg/ffprobe discovered from app-local `tools/ffmpeg/` before system `PATH`;
- no FFmpeg binary redistribution in the AAVC release ZIP;
- exact source ZIP via `git archive`;
- SHA-256 for source and portable release ZIPs;
- packaged-EXE foundation smoke and UI capture;
- repository secret scan before build;
- file-name/path exclusion checks for runtime/user-data leakage.

The accepted v0.2.1 release evidence used FFmpeg 9.0.2 and passed the full Windows gate.

## Fresh dependency evidence — 2026-10-08

Current repository pins were compared with current upstream package records.

| Component | Repo pin | Current evidence | STEP 04 decision |
| --- | ---: | ---: | --- |
| PySide6 | 6.11.2 | 6.11.2 | KEEP |
| pytest | 9.1.1 | 9.1.1 | KEEP |
| mypy | 2.4.0 | 2.4.0 | KEEP |
| PyInstaller | 6.22.3 | 6.22.3 | KEEP |
| pyinstaller-hooks-contrib | 2026.8 | 2026.8 | KEEP |
| packaging | 26.3 | 26.3 | KEEP |
| setuptools in `requirements.lock` | 84.0.0 | 84.0.0 | KEEP |
| pip in workflows | 26.2.1 | 26.2.1 | KEEP |
| Ruff | 0.16.8 | 0.16.10 | PATCH CANDIDATE |
| Python CI toolchain | 3.12.10 | 3.12.10 is superseded by security-only 3.12.15 | EVALUATE, DO NOT AUTO-BUMP |

External freshness references:
- https://pypi.org/project/PySide6/
- https://pypi.org/project/pytest/
- https://pypi.org/project/mypy/
- https://pypi.org/project/pyinstaller/
- https://pypi.org/project/pyinstaller-hooks-contrib/
- https://pypi.org/project/packaging/
- https://pypi.org/project/setuptools/
- https://pypi.org/project/pip/
- https://pypi.org/project/ruff/
- https://www.python.org/downloads/release/python-31210/

## Confirmed packaging / maintenance gaps

### GAP-04A — FFmpeg installation in CI is not version-pinned

`v2-user-acceptance.yml` and the original v0.2.1 final workflow install FFmpeg through Chocolatey only when it is absent:

`choco install ffmpeg -y --no-progress`

This means a future runner can silently validate against a different FFmpeg build than the accepted v0.2.1 reference. The v0.2.1 evidence happened to use FFmpeg 9.0.2, but the workflow does not enforce that identity.

Decision:
- v0.2.2 acceptance must use an explicit reference FFmpeg/ffprobe identity;
- keep FFmpeg external to the published AAVC ZIP;
- record version/fingerprint in build evidence;
- do not silently accept a newer Chocolatey build.

### GAP-04B — packaged release documentation is hard-coded to 0.2.1

`aavc.spec` includes `RELEASE_NOTES_0.2.1.md`.  
`scripts/verify_portable.ps1` also requires `RELEASE_NOTES_0.2.1.md`.

A future v0.2.2 build can therefore accidentally contain or validate stale release notes unless these version-coupled paths are deliberately updated during release implementation.

Decision:
- v0.2.2 must have explicit synchronized release metadata;
- portable verification must assert the new version and new release-notes filename;
- do not change the frozen v0.2.1 historical artifacts.

### GAP-04C — `UPX=True` makes the spec environment-sensitive

`aavc.spec` enables UPX, but the workflow does not provision or pin an UPX build. PyInstaller behavior can therefore differ depending on whether UPX happens to exist in the builder environment.

Decision:
- for v0.2.2 prefer `upx=False` unless a specific pinned UPX toolchain is deliberately introduced and proven;
- a maintenance patch should favor deterministic packaging over opportunistic compression.

### GAP-04D — artifact secret scan is weaker than repository secret scan

`scripts/check_no_secrets.py` scans tracked repository text.  
`scripts/verify_portable.ps1` blocks suspicious file names/directories, but does not scan readable files inside the built portable tree for supported credential patterns.

Decision:
- add an artifact-level credential-pattern scan after PyInstaller build and before ZIP creation;
- do not echo secret values;
- continue blocking `.env`, key/pem files, autosave/recovery, cache/log/user-data paths.

### GAP-04E — app-local FFmpeg resolution is not exercised by the packaged gate

The portable artifact creates an app-local `tools/ffmpeg/` slot, but automated acceptance validates FFmpeg primarily from system `PATH`. The release contract says app-local takes precedence, yet that packaging path is not directly proven.

Decision:
- test both PATH and app-local resolution using the same approved reference binaries;
- stage FFmpeg/ffprobe only in a temporary verification copy or test workspace;
- remove/verify absence of those binaries from the final distributable ZIP.

### GAP-04F — build-tool version sources are partly duplicated

`requirements.lock` pins `setuptools==84.0.0`, while `[build-system]` in `pyproject.toml` pins `setuptools==80.10.2`.

This is not automatically a runtime bug because PEP 517 build isolation can intentionally use a separate backend version. However, it creates toolchain ambiguity for a patch-release reproducibility story.

Decision:
- test a deliberate alignment to `setuptools==84.0.0`;
- accept only if editable install, PyInstaller build, strict typing and full Windows acceptance remain PASS;
- otherwise retain 80.10.2 and document why the build backend remains intentionally separate.

### GAP-04G — backup workflow is still packaging the wrong app/release

As identified in STEP 01, `.github/workflows/backup-single-app.yml` still targets the legacy repository and `v0.1.1`, with unpinned action version tags.

Decision:
- correction remains required in the authorized implementation wave;
- the backup artifact must use V2 source, verified Git Bundle, and the latest stable build line;
- active workflow actions must be pinned by commit SHA.

### GAP-04H — generic package workflow does not represent a release candidate

`package-windows.yml` creates `AAVC-foundation-win64.zip`. This is useful as a manual packaging smoke, but it does not prove source identity, version metadata, FFmpeg identity, release notes, checksums, source archive, or release-manifest completeness.

Decision:
- keep it as a manual smoke if useful;
- v0.2.2 RC/final must use a separate versioned release workflow, not treat the foundation ZIP as canonical release evidence.

## Dependency update policy for v0.2.2

### Safe default

Do not perform broad upgrades merely because packages are newer.

Runtime dependency changes are especially sensitive because PySide6/Qt can change layout, plugin loading, rendering, and portable size. PySide6 6.11.2 is already current; keep it.

### Candidate D-01 — Ruff 0.16.8 -> 0.16.10

Ruff is dev-only and a patch-level update is available.

Acceptance:
- regenerate exact lock entry;
- run Ruff on `src` and `tests`;
- run full cheap suite and Windows acceptance;
- no source rewrite is required solely to satisfy new optional rules;
- if the newer Ruff introduces unrelated churn, defer it rather than expanding v0.2.2.

### Candidate D-02 — align PEP 517 setuptools backend to 84.0.0

This reduces the current 80.10.2 / 84.0.0 split.

Acceptance:
- clean install from fresh runner;
- editable install;
- `pip check`;
- PyInstaller build;
- packaged EXE launch;
- no dependency graph drift beyond the reviewed lock.

### Candidate D-03 — Python 3.12 security-line evaluation

Python 3.12.10 is the last full 3.12 maintenance release with binary installers and is now superseded by security-only 3.12 releases.

Policy:
- do not silently change the build interpreter in the same commit as unrelated application fixes;
- evaluate the newest supported 3.12 security release in an isolated Windows matrix;
- only adopt if setup-python, PyInstaller, PySide6, packaged EXE, real FFmpeg tests and source/build evidence all pass;
- if Windows toolchain reproducibility is weaker, keep 3.12.10 for v0.2.2 and document the deferred security-toolchain review.

### Keep current unless evidence changes

Keep:
- PySide6 6.11.2;
- pytest 9.1.1;
- mypy 2.4.0;
- PyInstaller 6.22.3;
- pyinstaller-hooks-contrib 2026.8;
- packaging 26.3;
- pip 26.2.1.

No runtime dependency may be added in v0.2.2 without a new planning decision.

## FFmpeg / ffprobe reference policy

The published AAVC ZIP continues not to redistribute FFmpeg.

For automated release gates:
1. choose one explicit reference FFmpeg/ffprobe build;
2. v0.2.1 reference identity is FFmpeg 9.0.2;
3. prefer keeping 9.0.2 for v0.2.2 unless a separately reviewed newer build is required;
4. record `ffmpeg -version` and `ffprobe -version`;
5. record executable path and fingerprint/hash when practical;
6. verify required filters/capabilities before the full suite;
7. verify both app-local and PATH resolution order;
8. final release ZIP must contain only the `tools/ffmpeg/README.md` slot, not the binaries.

A missing or wrong reference FFmpeg is a STOP, not an automatic install of an unreviewed latest version.

## Reproducibility model

v0.2.2 does not claim byte-for-byte deterministic PyInstaller ZIPs unless proven. Windows PE timestamps, ZIP metadata, and builder details can make byte hashes differ across legitimate rebuilds.

The release reproducibility contract is instead:
- exact source commit;
- exact dependency lock;
- exact build interpreter decision;
- exact PyInstaller/toolchain versions;
- exact reference FFmpeg identity for tests;
- version/schema/contract fields in BUILD_INFO;
- expected file inventory;
- source ZIP checksum;
- portable ZIP checksum;
- per-build manifest/evidence;
- successful clean-run verification from the same source.

If a second controlled build happens to be byte-identical, record it as additional evidence, not as an assumed guarantee.

## Planned Windows packaging matrix

### WPK-01 — exact source identity
Every RC/final workflow checks out and records the exact PR head/final commit.

### WPK-02 — version synchronization
Assert the same v0.2.2 version in:
- `pyproject.toml`;
- `src/aavc/__init__.py`;
- release workflow expectation;
- release notes;
- build manifest;
- artifact names.

### WPK-03 — clean pinned dependency install
Fresh Windows runner, pinned pip, exact lock, editable install, `pip check`.

### WPK-04 — dependency freshness decision evidence
Record KEEP / UPGRADE / DEFER for every direct/tooling dependency touched by STEP 04.

### WPK-05 — Ruff patch candidate
0.16.10 must pass without unrelated source churn or be explicitly deferred.

### WPK-06 — setuptools backend alignment candidate
84.0.0 must pass isolated clean-build validation or remain intentionally split.

### WPK-07 — Python security-line candidate
Evaluate a newer 3.12 security release separately from the stable 3.12.10 baseline.

### WPK-08 — PyInstaller onedir build
Clean build from reviewed spec, no stale `build/` or `dist/` content.

### WPK-09 — deterministic UPX policy
No opportunistic UPX. Prefer `upx=False` unless UPX is explicitly pinned/proven.

### WPK-10 — portable foundation smoke
Packaged EXE exits successfully and writes `AAVC_FOUNDATION_SMOKE_OK`.

### WPK-11 — packaged real UI launch
Launch EXE offscreen, capture UI-002, require non-empty valid PNG.

### WPK-12 — version-specific document inventory
Portable tree contains v0.2.2 release notes, user guide, maintenance, backup/recovery, schema and license/provenance records.

### WPK-13 — artifact path leak scan
No `.env`, key/pem, autosave/recovery, cache/log/user_data/runtime_data artifacts.

### WPK-14 — artifact credential-pattern scan
Scan readable built files for supported API-key/token signatures without echoing values.

### WPK-15 — external FFmpeg identity
Reference FFmpeg/ffprobe version/fingerprint is recorded and checked.

### WPK-16 — PATH FFmpeg mode
Real FFmpeg render tests pass when binaries are resolved from PATH.

### WPK-17 — app-local FFmpeg mode
Equivalent acceptance passes when reference binaries are staged in `tools/ffmpeg/`.

### WPK-18 — app-local precedence
When both exist, resolver selects the documented app-local copy.

### WPK-19 — final artifact excludes FFmpeg binaries
Final ZIP contains README slot only unless a future licensing/distribution plan explicitly changes policy.

### WPK-20 — missing FFmpeg failure
Packaged runtime reports a clear supported error instead of silent fallback.

### WPK-21 — source archive exactness
Source ZIP is produced from the exact final commit via `git archive`.

### WPK-22 — portable archive integrity
Generate SHA-256 after ZIP creation and immediately re-verify.

### WPK-23 — source archive integrity
Generate and re-verify SHA-256 for exact-source ZIP.

### WPK-24 — BUILD_INFO completeness
Include release commit, version, channel, schema max, animation contract, Python, PySide6, PyInstaller and reference FFmpeg identity.

### WPK-25 — dependency/provenance record
Update `LICENSES/dependency_provenance.csv` only for actual adopted toolchain changes.

### WPK-26 — Windows path matrix
Package/run representative ASCII, spaces, apostrophe, Unicode and deep-path cases.

### WPK-27 — no unpinned active GitHub Actions
Active v0.2.2 workflows must use reviewed commit SHAs for external actions.

### WPK-28 — backup workflow corrected
V2 backup must target the V2 repo and stable V2 line, create/verify full Git Bundle, and not package another repository.

### WPK-29 — historical workflows stay historical
Do not repurpose v0.2.0/v0.2.1 publication workflows for v0.2.2.

### WPK-30 — new guarded v0.2.2 RC/final workflow
Create new versioned workflow only after STEP 05/06 implementation is accepted. Publication must refuse an existing tag/release and verify final tag target.

## Planned implementation objects

Likely files after STEP 05 authorization:
- `requirements.lock`;
- `pyproject.toml`;
- `aavc.spec`;
- `scripts/package.ps1`;
- `scripts/verify_portable.ps1`;
- `scripts/check_no_secrets.py` or a new artifact-scan helper;
- `tools/ffmpeg/README.md`;
- `LICENSES/dependency_provenance.csv`;
- `.github/workflows/package-windows.yml`;
- `.github/workflows/v2-user-acceptance.yml`;
- `.github/workflows/backup-single-app.yml`;
- a new v0.2.2 RC/final workflow later in STEP 06/07;
- versioned release notes/manifest only when release implementation is authorized.

Do not modify historical v0.2.0/v0.2.1 tags/releases or their immutable evidence.

## Stop conditions

Implementation must STOP rather than broaden scope if:
- a dependency refresh requires runtime behavior changes unrelated to the maintenance goals;
- a PySide6/Qt bump is needed to make packaging work;
- FFmpeg must be redistributed to make tests pass;
- packaging requires schema/project-format changes;
- Windows portable requires an installer architecture rewrite;
- a newer Python 3.12 security build cannot be reproduced reliably on the supported Windows pipeline;
- secret-cleanliness can only be achieved by deleting user/runtime safeguards;
- the fix would require moving or replacing an existing release tag.

## STEP 04 gate

**PASS**

The Windows packaging/dependency surface is bounded. Most dependency pins are already current; the only straightforward dev-only update candidate is Ruff 0.16.10, with setuptools/Python toolchain changes isolated behind explicit proof gates.

The critical maintenance work is packaging hardening: pin the FFmpeg reference, remove opportunistic UPX behavior, add artifact-content secret scanning, prove app-local FFmpeg resolution, correct version-coupled portable docs, and correct the V2 backup workflow.

No application runtime code has been changed in STEP 04.

## Next exact STEP

**STEP 05 — Implementation Authorization + Module / Change Map**

STEP 05 must:
- consolidate STEP 00–04 findings;
- decide which GAP-02 / GAP-03 / GAP-04 items are authorized for v0.2.2;
- map exact files/tests per implementation wave;
- classify required vs deferred work;
- define failing-before evidence and promotion gates;
- confirm no UI-image prompt step is required;
- authorize coding only after all planning DOCX/source-of-truth files are present in the repo.

Do not begin STEP 06 implementation in the same turn.
