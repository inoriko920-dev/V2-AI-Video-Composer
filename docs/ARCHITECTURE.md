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

Status: **IMPLEMENTATION IN PROGRESS**

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
