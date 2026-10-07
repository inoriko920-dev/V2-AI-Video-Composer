# V2 IMPLEMENTATION STATUS

Last updated: 2026-10-07  
Repository: `inoriko920-dev/V2-AI-Video-Composer`

## Repository rule
All V2 development happens only in this repository.  
`inoriko920-dev/AI-Automatic-Video-Composer` is a read-only legacy reference and must not be modified.

## Baseline provenance
- Legacy main commit imported: `7d77fc9f724d359c7da6c4796dffce5104740952`
- Exact imported root tree: `7abd82b4a69428a0b1bd25a8d992f402cb0a2ff8`
- V2 migration commit: `835130da71b5a2114100ada903f524dd926a068a`
- Planning/source-of-truth main baseline before Wave A: `192e3d5ac9db73b1d0bd51301df29978cbade232`

## Planning gate
- STEP 00–13 DOCX: present in `docs/v2_planning/`
- Master planning index: present
- Visual QA of planning DOCX: PASS
- STEP 13 CODING GATE: **PASS**
- Approval basis: explicit user instruction to continue after planning completion on 2026-10-07

## Current wave
**Wave J — AUTOMATED WINDOWS USER ACCEPTANCE PASS / FINAL RELEASE GATE READY: 0.2.0rc1**

Baseline evidence:
- Wave A documentation commit: `bdcfb34191f10bd8debbfc23ea88b821a101ce89`
- Pull request: `#2`
- Windows CI run: `37515351345` — **PASS**
- CodeQL run: `37515351222` — **PASS**
- Secret scan, dependency graph, compile, Ruff, strict mypy, cheap pytest, STEP09 UI capture, screenshot verification, and artifact upload: **PASS**
- Diff scope before the gate: documentation only; no `src/`, `tests/`, workflow, dependency-manifest, runtime, render, animation, timeline, UI implementation, or project-schema changes.

Allowed:
- clarify V2 repository identity and handoff rules;
- record current wave/gates/rollback point;
- run the inherited CI against the unchanged application baseline.

Not allowed in Wave A:
- source-code behavior changes;
- dependency changes;
- render/animation/timeline/UI changes;
- project-schema changes;
- package/release redesign.

## Wave A acceptance criteria
1. V2 source of truth clearly points all future work to V2 only.
2. `src/`, `tests/`, dependency manifests, and runtime behavior remain unchanged from the planning baseline.
3. A V2 pull request runs the inherited Windows CI.
4. Compile, Ruff, strict mypy, cheap pytest, and STEP09 screenshot checks pass.
5. Gate result and exact next action are recorded.

## Rollback point
If Wave A documentation or CI setup causes an unintended issue, reset the V2 work branch to:
`192e3d5ac9db73b1d0bd51301df29978cbade232`

No rollback action may target the legacy repository.

## Wave A closure
- PR #2 merged to `main`.
- Merge/squash commit: `1c32cc810cca433fd3238e0c8268b1f3e642a62b`.
- No functional application code was changed in Wave A.
- Legacy repository remained read-only.

## Wave B scope
Allowed:
- add immutable/versioned backend capability descriptors;
- add backend-neutral media protocol contracts;
- add a static FFmpeg reference capability descriptor;
- add contract/unit tests and architecture documentation.

Forbidden in Wave B:
- no new runtime dependency;
- no libopenshot/MLT/PyAV adoption or packaging;
- no change to `render_project()`, FFmpeg command construction, or output semantics;
- no animation, timeline, project-schema, or UI behavior change.

## Wave B acceptance criteria
1. Ports exist for the planned media boundaries without leaking Qt/backend library types.
2. FFmpeg reference capabilities map to the currently render-backed effect set.
3. Existing FFmpeg export path is untouched.
4. Ruff, strict mypy, cheap pytest, UI screenshot checks, and CodeQL pass.
5. Diff remains reviewable and dependency manifests remain unchanged.

## Wave B rollback point
`9ec2c1c61d0890464a70b71eb22738069255d852`

## Wave B evidence
- Implementation commit: `d51d0d36707720c93a3d0f6b9e27fc66618ea780`
- Pull request: `#3`
- Windows CI run: `37516960210` — **PASS**
- CodeQL run: `37516960048` — **PASS**
- Compile, Ruff, strict mypy, cheap pytest, STEP09 screenshot capture/verification, and artifact upload: **PASS**
- Dependency manifests unchanged.
- Existing `render_project()`, FFmpeg builder/executor, project schema, timeline behavior, animation behavior, and UI behavior unchanged.

## Wave B closure
- PR #3 merged to `main`.
- Merge/squash commit: `79a688194b2c38ec4eb74ca6b4818bdb7938eb7f`.
- Final PR-head Windows CI run: `37517200788` — **PASS**.
- Final PR-head CodeQL run: `37517200581` — **PASS**.
- No new runtime dependency was adopted.
- FFmpeg export behavior remained unchanged.
- Legacy repository remained read-only.

## Wave C scope
Allowed: staged-output ffprobe validation before atomic replace; cooperative FFmpeg cancellation/progress; cached FFmpeg availability/version probing; 10/100/500-scene benchmark harness; focused regression tests.

Forbidden: new runtime dependencies, optional backend adoption, animation/keyframe schema changes, timeline redesign, or visual UI redesign.

## Wave C acceptance criteria
1. Invalid/truncated staged output cannot replace a valid destination.
2. Managed external processes can be cancelled cooperatively.
3. Render progress is observable while the legacy non-progress path remains available.
4. FFmpeg availability/version probing is cached and refreshable.
5. Benchmark harness covers 10/100/500 scenes and long Windows-style paths with spaces/apostrophe/Unicode.
6. Windows CI and CodeQL pass; dependency manifests remain unchanged.

## Wave C rollback point
`a2b69fb4a79c9e0216207463b48b88a741c8729e`

## Wave C evidence
- Core render safety commit: `42c95723f57a52ff46a20ac9469d8465e1be052f`.
- Integration commit: `7863099ecfcf8d5d8e2cac6dbf784348ff783850`.
- Final tested PR head before evidence update: `7d1307ee52a2fe8433c75b5f8ae2bcd191336f1d`.
- Pull request: `#4`.
- Windows CI run `37519985006`: **PASS**.
- CodeQL run `37519985054`: **PASS**.
- Compile, Ruff, strict mypy, cheap pytest, STEP09 screenshot capture/verification, and artifact upload: **PASS**.
- Dependency manifests unchanged; no optional backend adopted.

## Wave C closure
- PR #4 merged to `main`.
- Merge/squash commit: `6c703538a16f7fe0ea56186a16d812f36a26ee7e`.
- Final PR-head Windows CI run: `37520211708` — **PASS**.
- Final PR-head CodeQL run: `37520211301` — **PASS**.
- Staged render output is validated before atomic replacement.
- Managed subprocess execution supports cancellation/progress while the legacy run path remains available.
- FFmpeg availability/version probing is cached and refreshable.
- Benchmark harness covers 10/100/500 scenes and stressed Windows-style Unicode/apostrophe/long paths.
- No runtime dependency or optional backend was added.
- Legacy repository remained read-only.

## Wave D scope
Allowed:
- add backend-neutral normalized keyframe and transform-track domain data;
- extend AnimationAssignment additively while preserving enter/exit/intensity/lock semantics;
- introduce explicit project schema v3 migration v1 -> v2 -> v3;
- preserve a pre-migration backup before first overwrite of a legacy schema file;
- add migration/validation/render-parity regression tests.

Forbidden in Wave D:
- no new visual effects;
- no FFmpeg/preview consumption of keyframe tracks yet;
- no animation UI changes;
- no timeline redesign;
- no runtime dependency or optional media backend.

## Wave D acceptance criteria
1. Existing v1/v2 projects open as schema v3 without losing current animation semantics.
2. Schema v3 keyframe data round-trips with strict normalized-time/property/easing validation.
3. Existing legacy effects compile to the same FFmpeg graph whether keyframe data is present or absent.
4. First save over a legacy schema preserves a non-clobbering pre-v3 backup.
5. Future schemas remain rejected.
6. Windows CI, strict mypy, regression tests, screenshot gate, and CodeQL pass.

## Wave D rollback point
`5d7389596cd28d1fd3b59184f0dd2088e7a6d301`

## Wave D evidence
- Domain keyframe model commit: `9ffe4cd1e26ff7a36add652899860ed3ace0d4e6`.
- Schema v3 migration commit: `a3390bf216b30a49e8c1e002f7130ce6b1523176`.
- Test/model integration head: `29c45921ba53fdce3d96c3bc80b6965127236c53`.
- Pull request: `#5`.
- Windows CI run `37522687807`: **PASS**.
- CodeQL run `37522687755`: **PASS**.
- Compile, Ruff, strict mypy, 572 cheap tests, STEP09 screenshot capture/verification, and artifact upload: **PASS**.
- Existing FFmpeg effect semantics remain unchanged when keyframe tracks are present.
- Dependency manifests unchanged; no new effect/backend/UI implementation introduced.

## Wave D closure
- PR #5 merged to `main`.
- Merge/squash commit: `358f488ab6fe07366794063a2c5140b2ac4a4ba5`.
- Final PR-head Windows CI run: `37523013810` — **PASS**.
- Final PR-head CodeQL run: `37523013790` — **PASS**.
- Project schema is now v3 with explicit v1 -> v2 -> v3 migration.
- Legacy enter/exit/intensity/lock effect semantics remain unchanged.
- Keyframe tracks remain persisted-only and are not consumed by preview/FFmpeg yet.
- First overwrite of a valid legacy-schema project preserves a non-clobbering pre-v3 backup.
- No runtime dependency, new visual effect, alternate backend, timeline redesign, or UI redesign was introduced.
- Legacy repository remained read-only.

## Wave E scope
Production-ready capability group:
- position_x / position_y normalized keyframe motion;
- scale keyframe motion;
- rotation_degrees keyframe motion;
- hold + linear interpolation;
- linear / ease_in / ease_out / ease_in_out easing;
- additive composition with current legacy enter/exit effects.

Safety limits:
- position: -0.10 .. +0.10 frame;
- scale: 0.75 .. 1.50;
- rotation: -30 .. +30 degrees.

Fail-soft, not production-ready in Wave E:
- opacity/crop/blur/shadow/glow/mask_progress keyframe tracks;
- bezier interpolation;
- velocity and overshoot parameters.

Forbidden in Wave E:
- no UI redesign or new animation controls;
- no new runtime dependency or optional backend;
- no project-schema change beyond existing v3;
- no timeline/manual-editing work;
- no silent support claims for tracks without preview + final compiler parity.

## Wave E acceptance criteria
1. Supported transform tracks evaluate identically in preview intent and FFmpeg expression semantics.
2. Supported keyframes work even when legacy effect intensity is zero.
3. Legacy effects remain unchanged and combine additively when keyframes coexist.
4. Unsupported keyframe tracks are ignored with explicit preflight warning.
5. Safety bounds clamp preview and final render consistently.
6. Windows CI, strict mypy, full cheap regression tests, screenshot gate, and CodeQL pass.

## Wave E rollback point
`8afb9c0d1ecfc4f16c3f41522a84014273cf7aa0`

## Wave E evidence
- Core activation commit: `d1cce4a090c03c72701a28aa630055883f1c218c`.
- Legacy-guard fix commit: `85097b3570c142b26160d2d7b56b8348da7451e9`.
- Final tested implementation head: `fea8ef55428594fb0a153d5c281a15d1419f168b`.
- Pull request: `#6`.
- Windows CI run `37527046276`: **PASS**.
- CodeQL run `37527046425`: **PASS**.
- Compile, Ruff, strict mypy, 580 cheap tests, STEP09 screenshot capture/verification, and artifact upload: **PASS**.
- Supported X/Y position, scale, and rotation keyframes are active in preview + FFmpeg compiler.
- Legacy effect behavior remains unchanged when active keyframe tracks are absent.
- Unsupported keyframe properties/interpolation parameters remain fail-soft with preflight warnings.
- Dependency manifests, project schema v3, timeline, and UI remain unchanged.

## Wave E closure
- PR #6 merged to `main`.
- Merge/squash commit: `02d7c452f3a797d41cac7dd27c34a556601d2cea`.
- Final PR-head Windows CI run: `37527374856` — **PASS**.
- Final PR-head CodeQL run: `37527374907` — **PASS**.
- 580 cheap regression tests passed; 1 deselected.
- position_x / position_y, scale, and rotation_degrees keyframes now run in preview + FFmpeg final compiler.
- Shared safety limits and supported easing/interpolation are consistent across preview/final intent.
- Legacy enter/exit effects remain unchanged when no active keyframe track exists and combine additively when tracks coexist.
- Unsupported schema-v3 tracks remain persisted and fail-soft with explicit preflight warnings.
- Project schema remains v3; dependency manifests, timeline behavior, and UI layout remain unchanged.
- Legacy repository remained read-only.

## Wave F scope
Allowed:
- atomic multi-command project transactions as one undo/redo step;
- batch Scene duration editing with validation-before-mutation;
- copy/paste Scene animation assignments by stable asset slot;
- preserve keyframe tracks and existing assignment semantics during copy/paste;
- Validation Center detection for missing configured narration/subtitle and missing READY files;
- Validation Center surfacing for unsupported keyframe tracks;
- direct Validation Center actions: Relink, Buka Scene, Impor Media;
- connect Edit menu Undo/Redo + Salin/Tempel Animasi Scene without redesigning layout.

Forbidden in Wave F:
- no project schema change;
- no render/animation compiler redesign;
- no unrestricted multitrack NLE;
- no new runtime dependency/backend;
- no AI/provider/job-pool changes;
- no broad UI redesign.

## Wave F acceptance criteria
1. Multi-command edits are atomic and create exactly one undo/redo entry.
2. Failed batch edits leave ProjectState/history untouched.
3. Copy/paste animation maps by asset slot, preserves keyframes, and never overwrites a conflicting locked assignment.
4. Validation detects configured-but-missing narration/subtitle and READY bindings whose file disappeared.
5. Unsupported keyframe tracks appear in live validation with a direct Scene navigation action.
6. Existing relink and validation flows remain compatible.
7. Windows CI, strict mypy, full cheap regression tests, screenshot gate, and CodeQL pass.

## Wave F rollback point
`8b38e2896f537f187ca745d54b347bf2c018f15b`

## Wave F evidence
- Core implementation commit: `27dffd785b6f8ac308903c94f7dce780065f7a41`.
- Test integration commit: `f6610706533558774c7202a1a4bc495baf11df63`.
- Final tested implementation head: `44356c6b06830c9657f08571f64040d48cb82ef4`.
- Pull request: `#7`.
- Windows CI run `37530396553`: **PASS**.
- CodeQL run `37530396523`: **PASS**.
- Compile, Ruff, strict mypy, 589 cheap tests, STEP09 screenshot capture/verification, and artifact upload: **PASS**.
- Multi-command transactions are atomic and one-step undo/redo.
- Batch duration edits validate before mutation.
- Scene animation copy/paste preserves keyframes, maps by asset slot, and protects locked targets.
- Live validation detects missing configured media and unsupported keyframe tracks.
- Validation Center routes to Relink / Buka Scene / Impor Media without redesigning the frozen reference layout.
- Project schema, render compiler, runtime dependencies, and backend selection remain unchanged.

## Wave F closure
- PR #7 merged to `main`.
- Merge/squash commit: `fe9a70656232e3dc2f3231b1b3d1c06c0e5ee2c5`.
- Final PR-head Windows CI run: `37530741442` — **PASS**.
- Final PR-head CodeQL run: `37530741447` — **PASS**.
- 589 cheap regression tests passed; 1 deselected.
- Multi-command edits are atomic and one-step undo/redo.
- Batch Scene-duration updates validate all targets before mutation.
- Scene animation copy/paste maps by asset slot, preserves keyframes, and respects locked targets.
- Validation detects configured-but-missing narration/subtitle and READY media whose file disappeared.
- Unsupported keyframe tracks surface in live validation with direct Scene navigation.
- Validation Center repair actions include Relink / Buka Scene / Impor Media.
- Edit menu now exposes Undo/Redo and Salin/Tempel Animasi Scene without broad UI redesign.
- Project schema, render compiler, backend selection, and runtime dependency manifests remain unchanged.
- Legacy repository remained read-only.

## Wave G scope
Allowed:
- run Gemini Auto through the canonical background JobManager path;
- cooperative cancellation between provider attempts and progress reporting;
- deterministic failover across configured Gemini slots, each slot at most once per job;
- support all configured slots up to the existing 100-slot limit;
- secret-free provider attempt diagnostics and key-pool health states;
- classify runtime key health as available / cooldown / disabled with sanitized failure reason;
- surface success diagnostics in user-facing status without exposing secret material;
- preserve stale-result rejection before ProjectState mutation;
- provide a visible "Batalkan Pekerjaan Berjalan" AI-menu action.

Forbidden in Wave G:
- no new AI provider;
- no project schema change;
- no render/timeline/animation behavior change;
- no plaintext credential fallback;
- no raw secret in ProjectState, diagnostics, logs, or status;
- no automatic destructive/bulk project mutation outside validated application commands;
- no broad UI redesign.

## Wave G acceptance criteria
1. Long Gemini Auto work runs outside the GUI thread through JobManager/BackgroundCall.
2. User cancellation stops failover before another key attempt and cancelled results never mutate ProjectState.
3. Provider failover can rotate through up to 100 configured slots, each at most once per job.
4. Key health/attempt diagnostics contain no raw secret values.
5. Quota/retryable failures enter bounded cooldown; invalid/missing credentials become disabled for that runtime pool.
6. Provider error text is sanitized, including exact active credential replacement.
7. Existing bounded AI JSON validation + locked-target protection + stale-project guard remain intact.
8. Windows CI, strict mypy, full cheap regression tests, screenshot gate, and CodeQL pass.

## Wave G rollback point
`0018ac66ce60aeda5215ae449a911ee10ae62bcc`

## Wave G evidence
- Provider diagnostics/cancellation commit: `ddfc0eaf667aec70c1cc4a13b168f387ca359c07`.
- Background Auto (AI) integration commit: `122dc4241aabde8d3832db6cb6d4d0c40c16c239`.
- Secret redaction hardening commit: `9e802f6e0f17937b04b776741c118bd23d4d0283`.
- Pull request: `#8`.
- Windows CI run `37532793976`: **PASS**.
- CodeQL run `37532794112`: **PASS**.
- Compile, Ruff, strict mypy, 596 cheap tests, STEP09 screenshot capture/verification, and artifact upload: **PASS**.
- One Gemini job can rotate through all configured slots up to 100, each slot at most once.
- Cancellation stops failover before another key attempt.
- Runtime diagnostics expose only secret-free key IDs/status/outcomes.
- Active credential text is explicitly redacted from provider errors.
- Existing strict AI response validation, locked-target protection, and stale-project rejection remain intact.

## Wave G closure
- PR #8 merged to `main`.
- Merge/squash commit: `de18f02b3403696fdb88da7a57ca7e254c7ad7e6`.
- Final PR-head Windows CI run: `37533078793` — **PASS**.
- Final PR-head CodeQL run: `37533078907` — **PASS**.
- 596 cheap regression tests passed; 1 deselected.
- Gemini Auto runs through BackgroundCall/JobManager with progress and cooperative cancellation.
- One job can rotate through all configured Gemini slots up to 100, each slot at most once.
- Runtime key health is secret-free and classified as available / cooldown / disabled.
- Provider errors redact the exact active credential plus existing secret patterns.
- Strict structured AI validation, locked-target protection, and stale-result rejection remain intact.
- No new provider, schema change, plaintext fallback, render/timeline/animation change, or runtime dependency was introduced.
- Legacy repository remained read-only.

## Wave H scope
Allowed:
- use the existing frozen 42-reference UI set only; no new UI prompt/image generation;
- restore Scene animation copy/paste actions lost by the GuardedMainWindow menu rebuild;
- keep copy/paste actions truthfully enabled only when source/target state is valid;
- keep background cancel action disabled unless a Render/Auto (AI) job is actually active;
- disable the animation-mode selector when no project is active;
- add restrained focus, disabled, selection, and tooltip styling using the existing white/blue design tokens;
- preserve the current 1920x1080 reference shell and 1280x720 minimum viewport contract;
- run all 8 STEP09 Qt screenshot captures as the visual smoke gate.

Forbidden in Wave H:
- no new UI images/prompts;
- no layout redesign, panel replacement, or navigation model change;
- no new product feature or project schema change;
- no render/timeline/animation/provider behavior change;
- no runtime dependency change;
- no static PNG runtime screens.

## Wave H acceptance criteria
1. Final runtime Edit menu contains Salin/Tempel Animasi Scene after the guarded-menu rebuild.
2. Copy is enabled only for a selected Scene that owns animation assignments.
3. Paste is enabled only when the copied source still exists and the selected target is different.
4. Background cancel is actionable only while a background job is active.
5. Animation mode selector is disabled without an active project.
6. Keyboard focus/disabled visual states remain consistent with frozen white/blue direction.
7. All 8 representative STEP09 screenshots render successfully at 1920x1080 with no startup/QSS regression.
8. Windows CI, Ruff, strict mypy, full cheap tests, screenshot gate, and CodeQL pass.

## Wave H rollback point
`a2a82e4fbfee5276075c79789657a3d70bdaab9c`

## Wave H evidence
- UI parity/action-state implementation commit: `d68c5cb330df101e3b111e6a1a0fe545148108bd`.
- UI contract tests commit: `c03bbfb18db81ff0ab6651fb1114fb7493e6cda6`.
- Mypy declaration fix: `05312888fe1b5cd4386c2ca793cd2353e9a01ebf`.
- Final tested implementation head: `05312888fe1b5cd4386c2ca793cd2353e9a01ebf`.
- Pull request: `#9`.
- Windows CI run `37535304722`: **PASS**.
- CodeQL run `37535304543`: **PASS**.
- Secret scan, dependency graph, compile, Ruff, strict mypy, 602 cheap tests, all 8 STEP09 screenshot captures/verification, and artifact upload: **PASS**.
- Guarded runtime Edit menu now retains Salin/Tempel Animasi Scene.
- Copy/paste availability reflects live selected Scene, animation clipboard source, and target validity.
- Background cancel action reflects live job state; animation-mode selector requires an active project.
- Focus/disabled QSS remains inside the existing frozen white/blue token system.
- No new UI prompt/image package, layout redesign, schema change, runtime dependency, render/timeline/animation/provider behavior change was introduced.

## Wave H closure
- PR #9 merged to `main`.
- Merge/squash commit: `07087c742557d7d461cacf69aa27ea6dbaca6351`.
- Final PR-head Windows CI run: `37535631061` — **PASS**.
- Final PR-head CodeQL run: `37535630968` — **PASS**.
- 602 cheap regression tests passed; 1 deselected.
- All 8 representative STEP09 1920x1080 Qt screenshots captured and verified.
- Guarded runtime Edit menu retains Salin/Tempel Animasi Scene with truthful state.
- Background cancel and animation-mode selector now reflect actual runtime availability.
- Focus/disabled/selection/tooltip styling remains within the frozen white/blue design language.
- No new UI prompt/image package, layout redesign, schema change, runtime dependency, or media/render behavior change was introduced.
- Legacy repository remained read-only.

## Wave numbering reconciliation
STEP13 originally listed mature-backend spike(s) as Wave H and UI polish as Wave I. The
executed repository history used Wave H for the approved UI polish/parity work. To avoid
rewriting merged history while still completing every planned workstream, the remaining
optional mature-backend dependency spike is assigned to **Wave I**. Wave J remains the
full regression / Windows packaging / user test / release-candidate / final-release wave.

## Wave I scope
Allowed:
- verify current mature-backend release/license/Windows packaging evidence;
- run an isolated PyAV 19.0.1 Windows/Python 3.12 binary-wheel spike;
- test import, FFmpeg library visibility, synthetic encode/decode, latency, and installed footprint;
- record an explicit accept/defer decision for PyAV, libopenshot, MLT, and OpenTimelineIO;
- preserve FFmpeg CLI as the production reference and fallback path.

Forbidden in Wave I:
- no new application runtime dependency;
- no replacement of FFmpeg final rendering;
- no ProjectState/schema/UI/timeline/provider behavior change;
- no GPL openshot-qt code;
- no bundling of LGPL native libraries without a separate packaging/license gate.

## Wave I acceptance criteria
1. Normal app dependency manifests remain unchanged.
2. Isolated Windows spike installs PyAV only as a binary wheel on Python 3.12.
3. PyAV metadata/license and linked FFmpeg libraries are recorded.
4. Synthetic encode/decode succeeds within conservative latency/footprint guardrails.
5. Candidate decision record names reasons for defer/promotion and an explicit rollback path.
6. Existing Windows CI, screenshot gate, and CodeQL remain PASS.
7. Passing the spike does not silently promote PyAV into production runtime.

## Wave I rollback point
`80d02aa711ddf66b109d9b492c2b7cc43aa505b0`

## Wave I evidence
- Isolated spike implementation commit: `50921e920559dff80dabbe1ecc61b7ed2a6848e7`.
- Pull request: `#10`.
- Windows CI run `37537178052`: **PASS**.
- CodeQL run `37537178050`: **PASS**.
- Optional Backend Spike run `37537178273`: **PASS**.
- 605 cheap regression tests passed; 1 deselected.
- PyAV version: `19.0.1`; Python: `3.12.10`; license metadata: `BSD-3-Clause`.
- PyAV import latency: ~0.727 s.
- Synthetic MPEG-4 encode: ~0.0092 s; decode: ~0.0020 s; total round-trip: ~0.0112 s.
- 3/3 synthetic frames decoded at 64x64.
- Installed PyAV distribution footprint: 71,471,760 bytes (~68.2 MiB).
- Linked FFmpeg libraries exposed by PyAV: libavcodec/libavdevice/libavfilter/libavformat 63.1.102, libavutil 61.1.102, libswresample 7.1.102, libswscale 10.1.102.
- Runtime dependency manifests remain unchanged; PyAV is **not adopted** into production runtime.
- libopenshot 1.0.1 and MLT 7.42.0 remain deferred; OpenTimelineIO remains unnecessary for the current focused timeline.
- FFmpeg/ffprobe CLI remains the production reference/fallback final-render strategy.

## Wave I closure
- PR #10 merged to `main`.
- Merge/squash commit: `89467dbea58bc0b6392fb6da53af31570e31917b`.
- Final PR-head Windows CI run: `37537445801` — **PASS**.
- Final PR-head CodeQL run: `37537445861` — **PASS**.
- Final PR-head Optional Backend Spike run: `37537445804` — **PASS**.
- 605 cheap regression tests passed; 1 deselected.
- PyAV 19.0.1 proved technically feasible on Windows/Python 3.12, but remains **not adopted** as an application runtime dependency.
- FFmpeg/ffprobe CLI remains the production reference and fallback final-render path.
- libopenshot 1.0.1 and MLT 7.42.0 remain deferred; OpenTimelineIO remains unnecessary for the current focused timeline.
- Runtime dependency manifests, ProjectState/schema, UI, timeline, render behavior, and provider behavior remain unchanged.
- Legacy repository remained read-only.

## Wave J scope
Phase 1 (current):
- set V2 RC version to 0.2.0rc1;
- run compile, Ruff, strict mypy, regression tests, STEP09 screenshot gate;
- build/verify Windows 11 x64 PyInstaller onedir portable;
- create portable ZIP + exact-commit source ZIP + SHA256SUMS + BUILD_INFO;
- upload a user-test RC artifact without publishing a GitHub Release.

Final publication remains blocked until the RC user-test has no blocker.

## Wave J rollback point
`7e7eb21a77d68849990082fe4aca6219c23cd1bb`

## Next exact action
Open the Wave J RC pull request, require CI + CodeQL + RC packaging gate PASS,
then merge the RC source only if every automated gate passes. Do not publish v0.2.0
until user-test acceptance.


## Wave J RC evidence — automated gate 1
- RC implementation head: `7b1d31f54d6f39051502954c3f21c1f61441e797`.
- Pull request: `#12`.
- Windows CI run `37540224041`: **PASS**.
- CodeQL run `37540224055`: **PASS**.
- Wave J RC package run `37540224017`: **PASS**.
- 605 regression tests passed; 1 deselected.
- STEP09 screenshot gate: **PASS**.
- PyInstaller onedir build: **PASS**.
- Portable foundation smoke/content/secret gate: **PASS**.
- RC bundle/checksum preparation: **PASS**.
- User-test workflow artifact ID: `11448397150`.
- User-test workflow artifact digest: `sha256:a04f4052cb8182960b75b729acef2e3318c1e9baf55e06557ee3c733488f64b0`.
- STEP09 evidence artifact ID: `11448272439`.
- Final v0.2.0 publication remains **BLOCKED** pending RC user acceptance.

## Next exact action
Re-run CI, CodeQL, and the Wave J RC package workflow on this evidence commit. Merge
the 0.2.0rc1 source to main only if all three gates remain PASS. Then provide the
final RC artifact from the merged/evidence-equivalent source for user testing. Do not
publish v0.2.0 yet.


## Wave J RC merge closure
- PR #12 merged to `main`.
- Merge/squash commit: `87423af0972d525ac913c1f3f60131c307dfd14b`.
- Final PR-head Windows CI run: `37540612107` — **PASS**.
- Final PR-head CodeQL run: `37540612532` — **PASS**.
- Final PR-head Wave J RC package run: `37540612157` — **PASS**.
- 605 regression tests passed; 1 deselected.
- STEP09 screenshot gate: **PASS**.
- Windows PyInstaller onedir build: **PASS**.
- Packaged EXE foundation smoke/content/secret gate: **PASS**.
- Final user-test artifact ID: `11448575102`.
- Final user-test artifact digest: `sha256:eb0ffb8aba66228ff451e242ef8469fd1e11084003c42460a43b850021f4fbc9`.
- Final STEP09 evidence artifact ID: `11447914213`.
- Existing published v0.1.0/v0.1.1 tags/releases remain untouched.
- Final `v0.2.0` publication is **BLOCKED** pending user-test acceptance.

## Next exact action
Give the 0.2.0rc1 Windows user-test artifact to the user. Do not publish final
`v0.2.0` until the user reports that no blocker remains. If the user reports a
blocker, fix it in V2 and repeat the RC gate before any final release.


## Wave J animation blocker closure — 21/21 native effects
- User-test blocker: the canonical registry exposed 21 effects while only 9 had native preview/final-render capability coverage.
- Pull request: `#13`.
- Final tested PR head: `5d0703cf65385b87e07badc5488e27a783fdd561`.
- Merge/squash commit: `ebbf68ff4210c02012e0ea74b44a72438c7e5c8c`.
- PR-head tree and merged-main tree are identical: `a42635184b752fa1aeb61de2ddaf7a42605f845f`.
- Windows CI run `37570283898`: **PASS**.
- CodeQL run `37570283899`: **PASS**.
- Optional Backend Spike run `37570283887`: **PASS**.
- Wave J refreshed RC package run `37570283870`: **PASS**.
- Regression tests: **627 passed, 1 deselected**.
- STEP09 8-screenshot gate: **PASS**.
- Windows PyInstaller onedir build + portable smoke/content/secret verification: **PASS**.
- Refreshed user-test artifact ID: `11459479975`.
- Refreshed artifact digest: `sha256:be9a8a11c7517b4f209969dc8546c80069b81342cfbfa5bf5d7e285816cf4f79`.
- STEP09 evidence artifact ID: `11459594823`.
- All 21 canonical registry effects now participate in native preview/FFmpeg capability coverage; unknown legacy/future effect names retain explicit fail-soft fallback warnings.
- No new runtime dependency, project-schema change, broad UI redesign, or legacy-repository modification was introduced.
- Foundational keyframes remain production-ready for position X/Y, scale, and rotation; advanced keyframe properties/interpolation remain a separate future capability and are not silently claimed.

## Next exact action
Give the refreshed `0.2.0rc1` Windows artifact `11459479975` to the user and repeat
user testing with emphasis on all 21 animation choices, Manual/Random/AI assignment,
preview, short render, copy/paste animation, and locked-target behavior. Final
`v0.2.0` publication remains **BLOCKED** until the refreshed RC has no user-test blocker.


## Wave J delegated Windows user acceptance closure
- The user delegated the RC user-test execution to the implementation agent.
- Acceptance harness PR: `#14`.
- Final tested PR head: `1463c2a8718d88768939df33f075f22d54d726c6`.
- Merge/squash commit: `54d6cb49ceca001bb68e5f29a88869d3972a4861`.
- Tested PR-head tree and merged-main tree are identical: `458b52265ea74ceca443edaebd6d7b0cc3fd4d8b`.
- Windows Automated User Acceptance run `37577634087`: **PASS**.
- Full non-visual technical suite: **630 passed**.
- Real FFmpeg version used on Windows acceptance: **9.0.2 essentials build**.
- All 21 canonical effects completed a real FFmpeg render and verified output: **PASS**.
- Real Selection In/Out render and output verification: **PASS**.
- Windows portable build + foundation smoke/content/secret checks: **PASS**.
- Packaged EXE itself launched with Qt offscreen and produced a real UI screenshot: **PASS** (47,565 bytes).
- Acceptance evidence artifact ID: `11463332035`.
- Acceptance evidence digest: `sha256:151d8a08b9fed90d663833706ce3beb5abab8a55930616a2f3d8269262ad649f`.
- Concurrent CI run `37577634089`: **PASS**.
- Concurrent CodeQL run `37577634074`: **PASS**.
- Concurrent Wave J RC package run `37577634102`: **PASS**.
- Concurrent Optional Backend Spike run `37577634083`: **PASS**.
- Refreshed acceptance-source RC artifact ID: `11463282189`.
- Refreshed acceptance-source RC artifact digest: `sha256:3788ec3a807bdeea165fca7c6d92303dfa0ea7eb5b2cc73d2378cc6687ba1c9a`.
- The acceptance harness changes only tests/workflow evidence; no production source, schema, runtime dependency, or visual UI behavior changed.

## Next exact action
Run the final `v0.2.0` release gate from the accepted source line. Final publication
must use the canonical final-release workflow/gate and must not bypass checksum,
portable, CI, CodeQL, or source-provenance verification.
