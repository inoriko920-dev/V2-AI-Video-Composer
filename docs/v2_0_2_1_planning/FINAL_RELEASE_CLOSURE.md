# V2 0.2.1 — Final Release Closure

Status: **COMPLETE / PUBLISHED / VERIFIED**

## Canonical release
- tag: `v0.2.1`
- release commit: `eb94efebf142ba8203dfc3ae3c5fa861222a0926`
- GitHub Release ID: `405901186`
- publication PR: `#29`
- final workflow: `37643499394` — **PASS**
- main CI: `37643499386` — **PASS**
- main CodeQL: `37643499315` — **PASS**

## Final Windows evidence
- version: `0.2.1`
- FFmpeg: 9.0.2
- full technical suite: **761 passed**
- 10/100/500 Scene benchmark: **PASS**
- 8 frozen STEP09 screenshots: **PASS**
- Windows portable build: **PASS**
- portable verifier: **PASS**
- packaged EXE launch + UI capture: **PASS**
- exact-source backup: **PASS**
- checksum generation + re-verification: **PASS**

## Published artifact integrity
- Windows ZIP:
  `172f392e5d2e555a1fe9968498cfcca17cc21889014685353ba5c9aea6de5503`
- Exact-source ZIP:
  `1b856f455ffff64e08d5abf6c6ae1995d66b97ee9062d9f8d9ac6d78a118495c`
- final candidate Actions artifact: `11492589609`
- final candidate digest:
  `sha256:c4f3e3d5e33eed6ccd9e617ad3b8ac6da709f9a8d932d316d300d5811b232c11`
- final UI evidence artifact: `11492889346`
- final UI digest:
  `sha256:eae909864cffd226acfa498646a339e9b1c432a422796c1dde4e3b398f0d417a`

## Publication verification
The push-triggered publish job downloaded the final candidate from the same workflow,
re-verified `SHA256SUMS.txt`, verified the exact release commit in `BUILD_INFO.txt`,
confirmed version/channel/schema/advanced-v1 metadata, guarded against any existing
conflicting tag/release, published `v0.2.1`, and verified the final tag target.

The published release is:
- not draft;
- not prerelease;
- exactly targeted at `eb94efebf142ba8203dfc3ae3c5fa861222a0926`.

## Immutable history
- `v0.2.1`: immutable
- `v0.2.0`: unchanged at `c6ad75308d302cd816301a2a7a34ebe7eb4148a7`
- `v0.1.1`: historical immutable
- `v0.1.0`: historical immutable

## Post-release repository policy
The one-shot v0.2.1 publisher is retired to a manual, read-only historical verifier.
It has no `contents: write` permission and cannot create or replace a Git tag or GitHub
Release.

The v0.2.1 implementation/planning/release cycle is closed. Future changes must begin
with a newly planned version; do not reopen, move, or overwrite `v0.2.1`.
