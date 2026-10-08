# STEP 07 — Release Candidate Acceptance and Final Publication Gate

Status: **RC ACCEPTED / FINAL PUBLICATION NOT YET PERFORMED**.

## Frozen RC validation

- RC source SHA: `607fb5b59f6788892b60027d736cf99b8898c6a7`.
- Immutable RC source branch: `release/v0.2.2-rc-source-w06e-607fb5b59f67`.
- Read-only validation branch: `release/v0.2.2-step07-rc-validation` (the workflow branch itself is not release source).
- Verified workflow run: `37725077066`, conclusion SUCCESS.
- 795 technical tests passed, FFmpeg 9.0.2 reference, scanned Windows build, packaged EXE smoke, PATH/app-local FFmpeg precedence, checksum-verified portable+source ZIPs.
- Extracted portable smoke matrix: ASCII, spaces, apostrophe, Unicode and deep paths; all five PASS; Unicode packaged UI capture PASS.
- Archived GitHub Actions candidate evidence: artifact `11527950278`, digest `sha256:860e58228cff566f8e323873e335dea74eec223bee926b4a0e271b5384327f5e`.
- Main pre-final-docs SHA `607fb5b59f6788892b60027d736cf99b8898c6a7` push CI `37724784652` and CodeQL `37724784710`: PASS.
- Prior stable tag `v0.2.1` remains unchanged at `eb94efebf142ba8203dfc3ae3c5fa861222a0926`.

## Final documentation and source decision

Release notes and manifest must not call a published stable artifact PRE-RELEASE. This STEP therefore prepares accurate final documentation in a separate branch, without altering the previously frozen RC source.

After the final documentation PR is accepted, freeze the *new* exact final-source merge commit. The final publication must build from that exact commit, not reuse the older RC archive under a different source identity. The full SHA must be recorded in BUILD_INFO and verified in both the final source ZIP and GitHub tag.

The RC is validation evidence; the final executable must undergo its own code/security/Windows/build/source/checksum gates before the publisher obtains write permissions.

## Publication prerequisites

- Final docs PR approved with CI, CodeQL and Windows acceptance PASS.
- Windows final build from exact frozen final source, with 795 tests (or increased count), real FFmpeg reference and 21 effects, Qt offscreen UI launch, metadata, and credential scans PASS.
- STEP07 special path matrix evidence preserved, and no reintroduction of forbidden files.
- Final candidate ZIP and exact-source ZIP hashed; downloaded bundle checksum revalidated by the publisher.
- Preexisting tag/release `v0.2.2` absent; `v0.2.0`/`v0.2.1` immutable; publisher never moves/overwrites them.
- Publication job alone gets `contents: write`, and only after all verification jobs PASS.
- Published tag points to exact final source and GitHub Release is verified neither draft nor prerelease.
- Final URL, tag SHA, workflow ID, checksums, artifact ID/digest recorded in post-publication closure.

## Deferred/known limitations

GAP-03A production autosave scheduler and startup recovery UI are not part of 0.2.2. Python security-line updates, setuptools backend alignment, broad dependency refresh and optional Ruff update remain deferred. Benchmark command building for 500 scenes is not an actual 500-scene render claim.

## Stop conditions

Any failed source identity, test, tool/reference, credential, path, checksum, tag-immutability, or release-publication permission check **stops** publication. Do not mark STEP07 completed simply because the RC workflow passed.
