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

Status: **PASS — WAVE D IMPLEMENTED**

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


### Wave D evidence

PR #5 validation on implementation head `29c45921ba53fdce3d96c3bc80b6965127236c53`: Windows CI
`37522687807` PASS and CodeQL `37522687755` PASS. The project schema is v3,
v1/v2 migration is explicit and tested, and current FFmpeg effect semantics remain
unchanged because keyframe tracks are intentionally not consumed until Wave E.


### Wave D closure

PR #5 was merged to `main` at `358f488ab6fe07366794063a2c5140b2ac4a4ba5`. Final PR-head validation:
Windows CI `37523013810` PASS and CodeQL `37523013790` PASS. Keyframe tracks
remain persisted-only in Wave D; preview and FFmpeg consumption are deliberately
deferred to Wave E so the existing effect behavior remains the reference baseline.


## V2 Wave E — Foundational Keyframe Motion

Status: **PASS — WAVE E IMPLEMENTED**

Wave E activates the first schema-v3 keyframe capability group in both preview and
the FFmpeg final-render compiler: normalized X/Y position, scale, and rotation.

Production support is intentionally narrow:
- hold and linear interpolation;
- linear/ease-in/ease-out/ease-in-out easing;
- conservative shared safety clamps: position +/-10% frame, scale 0.75-1.50,
  rotation +/-30 degrees;
- additive composition with existing enter/exit effect behavior.

Schema-v3 tracks outside this production group remain persisted but fail-soft with
an explicit preflight warning. Bezier, velocity, overshoot, opacity, crop, blur,
shadow, glow, and mask/reveal keyframes are not claimed as render-ready in Wave E.
No UI or project schema change is introduced.


### Wave E evidence

PR #6 validation on implementation head `fea8ef55428594fb0a153d5c281a15d1419f168b`: Windows CI
`37527046276` PASS and CodeQL `37527046425` PASS. All 580 cheap regression
tests passed (1 deselected). Foundational keyframe X/Y position, scale, and
rotation are now consumed by both preview intent and the FFmpeg final compiler,
while unsupported schema-v3 tracks remain fail-soft with explicit preflight
warnings.


### Wave E closure

PR #6 was merged to `main` at `02d7c452f3a797d41cac7dd27c34a556601d2cea`. Final PR-head validation:
Windows CI `37527374856` PASS and CodeQL `37527374907` PASS, with 580
cheap regression tests passing. Foundational position X/Y, scale, and rotation
keyframes now have matched preview intent and FFmpeg compiler support; unsupported
schema-v3 tracks remain fail-soft and are not advertised as production-ready.


## V2 Wave F — Transactional Manual Editing and Validation UX

Status: **PASS — WAVE F IMPLEMENTED**

Wave F keeps the existing timeline architecture and adds bounded manual-editing
primitives instead of replacing it with a generic NLE.

- `ProjectTransaction` groups multiple immutable commands into one history entry;
- `SetSceneDurationsBatch` validates all targets before any state change;
- `CopySceneAnimations` maps assignments by asset slot, preserves keyframe tracks,
  and respects locked target assignments;
- the Edit menu exposes Undo/Redo plus Scene animation copy/paste using the current
  selected Scene;
- live validation now detects configured media that disappeared from disk and
  schema-v3 keyframe tracks that are not production-ready;
- Validation Center actions can relink media, open the affected Scene, or reopen
  media import without changing the frozen reference dialog layout.

No project schema, render compiler, backend dependency, or timeline storage model is
changed in Wave F.


### Wave F evidence

PR #7 validation on implementation head `44356c6b06830c9657f08571f64040d48cb82ef4`: Windows CI
`37530396553` PASS and CodeQL `37530396523` PASS. All 589 cheap regression
tests passed (1 deselected). Transactional manual edits are one-step undoable,
Scene animation copy/paste preserves keyframe assignments while respecting locked
targets, and live validation can navigate directly to Scene/media repair actions.


### Wave F closure

PR #7 was merged to `main` at `fe9a70656232e3dc2f3231b1b3d1c06c0e5ee2c5`. Final PR-head validation:
Windows CI `37530741442` PASS and CodeQL `37530741447` PASS, with 589
cheap regression tests passing. Manual multi-command changes now have atomic
single-step history semantics, Scene animation copy/paste preserves keyframe
assignments and lock protection, and Validation Center routes users directly to
repair/navigation actions without changing the project schema or render backend.


## V2 Wave G — AI Job and Key-Pool Hardening

Status: **PASS — WAVE G IMPLEMENTED**

Wave G keeps Gemini as the only configured AI provider and hardens the existing
provider boundary rather than expanding product scope.

- Gemini Auto uses the canonical BackgroundCall/JobManager runtime path with
  cooperative cancellation and progress;
- each configured slot can be attempted at most once per job, up to the existing
  100-slot pool limit;
- runtime key health is secret-free: AVAILABLE, COOLDOWN, or DISABLED;
- attempt diagnostics record only slot/key IDs, outcome classification and bounded
  cooldown values;
- quota/retryable failures cool down; invalid/missing/unreadable credentials disable
  only that runtime key entry;
- provider error text is redacted using both existing patterns and exact active
  credential replacement;
- successful AI output still passes strict structured parsing and application-command
  validation before mutation; stale project results are discarded.

No project schema, render path, timeline model, animation compiler, provider set, or
credential storage mechanism changes in Wave G.


### Wave G evidence

PR #8 validation on implementation head `a1934c277736a90344eb77733d52a8ea2ba018e8`: Windows CI
`37532793976` PASS and CodeQL `37532794112` PASS. 596 cheap tests passed
with 1 deselected. Gemini Auto now uses cancellable background job orchestration,
all configured slots can participate in bounded one-pass failover up to 100, and
provider/key-pool diagnostics remain secret-free.


### Wave G closure

PR #8 was merged to `main` at `de18f02b3403696fdb88da7a57ca7e254c7ad7e6`. Final PR-head validation:
Windows CI `37533078793` PASS and CodeQL `37533078907` PASS, with 596
cheap regression tests passing and 1 deselected. Gemini Auto now uses the canonical
background job path with progress/cancellation and bounded up-to-100-slot failover;
runtime diagnostics remain secret-free and no new provider or plaintext credential
fallback was added.


## V2 Wave H — UI/UX Parity and Professional Interaction Hardening

Status: **PASS — WAVE H IMPLEMENTED**

Wave H does not create a new visual design. The frozen UI-001..UI-042 set remains
the source of truth, with the eight STEP09 representative states used as automated
Qt rendering smoke evidence.

The bounded hardening in this wave:
- restores Scene animation copy/paste actions at the final GuardedMainWindow layer,
  where the Edit menu is rebuilt;
- adds truthful enable/disable state for animation copy/paste, background-job cancel,
  and the animation-mode selector;
- extends the existing white/blue QSS with restrained focus and disabled states plus
  consistent selection/tooltips;
- keeps the same shell geometry, navigation routes, panels, dialogs, and runtime
  widget architecture.

No new UI prompt/image package, layout redesign, project schema, runtime dependency,
render path, timeline model, animation compiler, or provider behavior is introduced.


### Wave H evidence

PR #9 validation on implementation head `05312888fe1b5cd4386c2ca793cd2353e9a01ebf`: Windows CI
`37535304722` PASS and CodeQL `37535304543` PASS. All 602 cheap regression
tests passed (1 deselected), and all eight representative STEP09 1920x1080 Qt
screenshots were captured and verified. The wave restored guarded-menu Scene
animation copy/paste parity, made interaction availability truthful, and added
restrained focus/disabled styling without introducing a new UI design.


### Wave H closure and sequence reconciliation

PR #9 merged to `main` at `07087c742557d7d461cacf69aa27ea6dbaca6351`.
Final PR-head validation: Windows CI `37535631061` PASS, CodeQL
`37535630968` PASS, 602 cheap tests PASS, and all eight STEP09 screenshots PASS.

STEP13 originally ordered the optional mature-backend spike before UI polish. The
executed history used Wave H for the approved UI polish. Merged history is not renamed;
the still-unexecuted optional mature-backend/dependency spike is therefore assigned to
Wave I, and Wave J remains the release/final-regression wave.


## V2 Wave I — Optional Mature Backend Dependency Gate

Status: **IMPLEMENTATION IN PROGRESS**

Wave I does not change the production backend. FFmpeg/ffprobe CLI remains the
reference and fallback final-render path.

PyAV 19.0.1 is the only candidate selected for an isolated Windows/Python 3.12
spike because a binary Windows x64 wheel exists and the package license is
BSD-3-Clause. The spike lives outside `src/` and is installed only by a dedicated
CI workflow. libopenshot 1.0.1 and MLT 7.42.0 remain deferred because their
current release packaging presents a larger native-library and redistribution
surface than the application presently needs.

A passing spike is evidence of technical feasibility only. It does not add PyAV
to application dependencies or authorize replacement of the FFmpeg reference path.


### Wave I dependency-gate evidence

PR #10 validation on implementation head `50921e920559dff80dabbe1ecc61b7ed2a6848e7` passed all three gates:
Windows CI `37537178052`, CodeQL `37537178050`, and Optional Backend Spike
`37537178273`.

The isolated PyAV 19.0.1 Windows/Python 3.12 test imported in ~0.727 seconds,
encoded/decoded a three-frame 64x64 MPEG-4 sample in ~0.011 seconds total, and
measured an installed distribution footprint of 71,471,760 bytes. Package metadata
reported BSD-3-Clause and linked FFmpeg library versions were visible.

Decision: technical feasibility is proven, but PyAV is **not promoted** into the
application runtime because there is no measured product requirement that justifies
the extra dependency/portable footprint yet. FFmpeg/ffprobe CLI remains the
reference and fallback final-render path.
