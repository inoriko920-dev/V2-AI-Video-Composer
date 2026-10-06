# ARCHITECTURE — AI Automatic Video Composer

Architecture ID: **ARCH-AAVC-v1.0**  
Status: **PASS**  
Blueprint: PB-AAVC-v1.0 / UIF-AAVC-v1.0

## Chosen Architecture
Modular monolith Windows desktop app. Presentation (PySide6 Qt Widgets) -> Application commands/use-cases -> Domain. Infrastructure implements ports/adapters for filesystem, persistence, FFmpeg/ffprobe process execution, HTTP providers, secure credentials, diagnostics, jobs and paths.

## Chosen Stack
- Python 3.12 x64; exact patch pinned at repository foundation.
- PySide6 Qt Widgets.
- External ffmpeg/ffprobe CLI discovered through centralized ToolRegistry/ProcessRunner. AAVC supports the app-local `tools/ffmpeg/` slot or system `PATH`, but does not redistribute the binaries.
- Versioned JSON `.aavcproj`, atomic save + separate recovery snapshots.
- RationalTime `{num, den}` canonical time model.
- Windows Credential Manager for raw API keys.
- PyInstaller `onedir` portable folder, then ZIP + checksums.
- GitHub Actions Windows build/test/package.

## Non-negotiable Dependency Direction
`presentation -> application -> domain`

Infrastructure implements ports; domain never imports Qt, HTTP, filesystem details, provider SDK, or FFmpeg. No raw subprocess outside ProcessRunner. No raw provider transport outside providers.

## Media Strategy
A backend-neutral immutable RenderPlan is compiled from ProjectState. Runtime preview builds a ScenePreviewPlan from the same canonical Scene/layout data, renders native motion directly with Qt pixmaps/evaluators, and can synchronize narration/subtitle timing through Qt Multimedia. Final render uses the FFmpeg graph + ASS/libass subtitle compilation. Shared layout/animation contracts keep preview intent aligned with final render without claiming frame-perfect WYSIWYG parity.

## External Compatibility Watch
1. Re-check FFmpeg/ffprobe capability and licensing whenever the supported external tool profile changes.
2. Preserve preview-vs-final behavioral parity for canonical SINGLE/DOUBLE layouts, native motion, and subtitle timing while keeping the documented non-WYSIWYG boundary.
3. Re-check pinned Python/PySide6/provider compatibility before later release publication.

These are maintenance watches, not blockers for the completed 0.2 source/test-build line.


## V2 Wave B — Backend Capability Boundary

Status: **PASS — WAVE B IMPLEMENTED**

V2 keeps the existing modular monolith and the proven FFmpeg command path. Wave B
adds an explicit, backend-neutral capability boundary without changing final-render
behavior.

- `aavc.media.capabilities` owns immutable/versioned backend capability data.
- `aavc.media.ports` owns protocols for ProbeService, PreviewFrameSource,
  RenderBackend, EffectCompiler, AudioPipeline, SubtitlePipeline, TimelineAdapter,
  and ToolCapabilityService.
- Contracts contain no Qt, subprocess, provider SDK, libopenshot, MLT, or PyAV
  types.
- `ffmpeg_reference_capabilities()` describes only capabilities already backed
  by the current FFmpeg/ffprobe implementation.
- FFmpeg remains the reference/default behavior. Wave B does not route exports
  through a new backend implementation and does not add a runtime dependency.
- Capability negotiation is additive architecture infrastructure for later waves;
  UI exposure changes are outside Wave B and still require the UI gate.


### Wave B evidence

- Contract implementation commit: `d51d0d36707720c93a3d0f6b9e27fc66618ea780`.
- Windows CI `37516960210`: PASS.
- CodeQL `37516960048`: PASS.
- No dependency manifest or current FFmpeg export-path changes were introduced.


### Wave B closure

PR #3 was merged to `main` at `79a688194b2c38ec4eb74ca6b4818bdb7938eb7f`. Final PR-head validation:
Windows CI `37517200788` PASS and CodeQL `37517200581` PASS. The FFmpeg
reference export implementation and dependency manifests remained unchanged.


## V2 Wave C — Render Hardening

Status: **PASS — WAVE C IMPLEMENTED**

Wave C keeps FFmpeg/ffprobe as the reference toolchain. It adds ffprobe validation of staged output before atomic finalization, managed subprocess cancellation/progress, cached FFmpeg version availability probing, and a standard 10/100/500-scene benchmark harness. No alternate backend or new runtime dependency is introduced.


### Wave C evidence

PR #4 validation on implementation head `7d1307ee52a2fe8433c75b5f8ae2bcd191336f1d`: Windows CI `37519985006` PASS and CodeQL `37519985054` PASS. The dependency manifests remained unchanged and FFmpeg/ffprobe remain the reference media toolchain.


### Wave C closure

PR #4 was merged to `main` at `6c703538a16f7fe0ea56186a16d812f36a26ee7e`. Final PR-head validation:
Windows CI `37520211708` PASS and CodeQL `37520211301` PASS. FFmpeg/ffprobe
remain the reference toolchain, dependency manifests are unchanged, and no
alternate backend was adopted.


## V2 Wave D — Animation/Keyframe Data Model

Status: **IMPLEMENTATION IN PROGRESS**

Wave D introduces a backend-neutral keyframe storage contract without activating it
in preview or FFmpeg rendering. Existing `AnimationAssignment` fields remain
canonical for current effects.

- keyframe time is normalized to scene time `0.0..1.0`;
- scalar tracks cover position, scale, rotation, opacity, crop, blur, shadow,
  glow, and mask progress;
- interpolation/easing plus optional velocity/overshoot are persisted;
- project schema advances to v3 through explicit v1 -> v2 -> v3 migration;
- the first save over a valid older schema preserves a
  `.pre-schema-v3.bak` backup without clobbering an existing backup;
- renderer/compiler behavior remains intentionally unchanged until Wave E.
