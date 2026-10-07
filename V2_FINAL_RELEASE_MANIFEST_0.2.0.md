# V2 Final Release Manifest — AI Automatic Video Composer 0.2.0

Status: **PASS / PUBLISHED / VERIFIED**

## Release identity

- Version: `0.2.0`
- Git tag: `v0.2.0`
- Release commit: `c6ad75308d302cd816301a2a7a34ebe7eb4148a7`
- Platform: Windows 11 x64
- Packaging: PyInstaller onedir -> portable ZIP
- Source backup: exact release commit via `git archive`
- FFmpeg policy: external binary via app-local `tools/ffmpeg/` or Windows PATH
- Provider: Gemini only; credentials remain outside project files

## Accepted RC / user acceptance evidence

- Delegated Windows acceptance PR: #14
- Automated acceptance run: `37577634087` — PASS
- Full technical suite: 630 PASS
- Real 21-effect FFmpeg render: PASS
- Real Selection In/Out render: PASS
- Packaged EXE UI launch: PASS

## Canonical final evidence

- Final workflow run: `37579907844` — PASS
- normal main CI: `37579907856` — PASS
- normal main CodeQL: `37579907845` — PASS
- Windows archive SHA-256:
  `eea46b42400c91e22d731c8261b9d7f29933ee0f94d45bcaa331a001805c525c`
- Source archive SHA-256:
  `fbdabd43c71f1585e817ce30f27d611668ecb0dc3c39df0b19a441968f0f7fe9`
- Final candidate artifact: `11463714566`
- Final UI evidence artifact: `11464770244`

The tag and GitHub Release are immutable. Any future correction must use a new
patch/minor version rather than moving or replacing `v0.2.0`.
