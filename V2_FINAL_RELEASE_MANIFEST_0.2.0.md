# V2 Final Release Manifest — AI Automatic Video Composer 0.2.0

Status before publication: **FINAL GATE IN PROGRESS**

## Release contract

- Version: `0.2.0`
- Git tag: `v0.2.0`
- Platform: Windows 11 x64
- Packaging: PyInstaller onedir -> portable ZIP
- Source backup: exact final-release commit via `git archive`
- Integrity: SHA-256 for portable and source archives
- FFmpeg policy: external binary via app-local `tools/ffmpeg/` or Windows PATH
- Provider: Gemini only; credentials remain outside project files
- Release notes: `RELEASE_NOTES_0.2.0.md`

## Accepted RC evidence

- Delegated Windows acceptance PR: #14
- Tested head: `1463c2a8718d88768939df33f075f22d54d726c6`
- Automated acceptance run: `37577634087` — PASS
- Full technical suite: 630 PASS
- Real 21-effect FFmpeg render: PASS
- Real Selection In/Out render: PASS
- Packaged EXE UI launch: PASS
- Acceptance artifact: `11463332035`
- Acceptance digest: `sha256:151d8a08b9fed90d663833706ce3beb5abab8a55930616a2f3d8269262ad649f`

## Final publication rule

The canonical V2 final workflow must pass its own Windows final gate and CodeQL gate.
Publication is guarded: an existing `v0.2.0` tag/release must never be overwritten or
moved. The release is published only from the exact final source commit after both jobs
succeed.
