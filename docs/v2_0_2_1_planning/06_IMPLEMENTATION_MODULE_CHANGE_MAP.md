# STEP 06 — Implementation Module & Change Map

Status: **PASS**

Detailed artifact:
`06_V2_0.2.1_IMPLEMENTATION_MODULE_AND_CHANGE_MAP.docx`

## Scope
STEP 06 maps exact code ownership before SOL implementation. No production code is authorized by this STEP.

## Architectural rules
- v0.2.0 remains immutable.
- schema v3 remains legacy-compatible.
- schema v4 + `metadata["animation_keyframe_contract"]="advanced-v1"` activates advanced semantics.
- copied UI / UI-001 through UI-042 remain the only visual source of truth.
- FFmpeg remains the final/reference renderer.
- current schema-v3 filter graph is a regression baseline and must not be rewritten merely to support advanced-v1.

## New modules planned
1. `src/aavc/animation/contract.py`
   - schema/marker constants;
   - advanced-track detection;
   - dormant-track scan;
   - contract-state validation.

2. `src/aavc/application/commands/animation_keyframes.py`
   - track-level manual edits/removal;
   - first advanced promotion transaction;
   - typed activation-required signal.

3. `src/aavc/rendering/advanced_capabilities.py`
   - feature/micro-render FFmpeg probes;
   - advanced capability result;
   - executable fingerprint/cache.

4. `src/aavc/rendering/advanced_filters.py`
   - active advanced-v1 per-asset crop/mask/opacity/blur/shadow/glow graph fragments;
   - final stage ordering from STEP 02.

5. `src/aavc/rendering/render_workspace.py`
   - hidden per-render workspace;
   - sendcmd sidecars;
   - Windows-safe path and cleanup lifecycle.

6. `src/aavc/presentation/advanced_motion_preview.py`
   - advanced Qt preview state;
   - heavy Approx/Exact utilities using the existing JobManager;
   - no second main UI.

## Existing owners to extend
- `animation/keyframes.py`: canonical scalar evaluator + limits + Bezier/velocity/overshoot.
- `animation/compiler/ffmpeg.py`: foundational/preset expressions + advanced scalar expressions.
- `persistence/serializer.py`: v3 default / max-readable v4 / backup / downgrade protection.
- `persistence/migrations/__init__.py`: automatic migrations stop at v3.
- `persistence/recovery.py`: exact schema/marker autosave and explicit cross-version recovery.
- `rendering/render_plan.py`: carry resolved schema/contract into render.
- `rendering/preflight.py`: contract-aware warnings/errors.
- `rendering/ffmpeg_builder.py`: legacy v3 path unchanged; delegate active v4 assets to advanced filters.
- `rendering/selection.py`: preserve canonical composition then final trim, with advanced workspace passthrough.
- `application/services/export_service.py` and `selection_export_service.py`: own render-workspace lifetime and advanced capability preflight.
- `presentation/motion_preview.py` and `native_motion_playback.py`: project-contract-aware preview on the existing canvas.
- `presentation/dialogs/asset_motion.py`: copied UI entry point; minimal advanced controls in existing style.
- `presentation/windows/native_motion_window.py`: execute advanced keyframe commands and activation confirmation.
- `application/services/validation.py` + `presentation/dialogs/validation_center.py`: new advanced issue mapping in existing Project/Render categories.

## Critical preset-editor preservation fix
Current `build_asset_motion_assignment()` creates a fresh assignment and therefore can drop existing `keyframe_tracks`.

v0.2.1 must change preset editing to preserve all existing keyframe tracks unless the user explicitly removes them.

## Render contract
For schema v3:
- use the existing `_scaled_asset_clause` / `_overlay_clause` path;
- preserve existing 21-effect and foundational-keyframe behavior.

For advanced-v1:
1. Decode / RGBA / setpts
2. crop visibility clip
3. blur
4. scale
5. rotation
6. mask progress
7. shadow + glow
8. opacity
9. position / overlay

Heavy blur schedule:
- sample canonical evaluator at output frame timestamps;
- map normalized value to STEP 01 sigma;
- round to 0.01 px;
- dedupe equal adjacent commands;
- write unique named-filter sendcmd sidecar in RenderWorkspace.

## Preview
- lightweight properties use Qt live preview;
- blur/shadow/glow may be approximate during interaction;
- exact heavy truth preview uses FFmpeg in existing background-job infrastructure;
- debounce target ~250ms;
- revision/generation IDs discard stale results;
- cache is bounded and keyed by source/scene revision/resolution/FFmpeg capability fingerprint.

## UI
- no UI-043–UI-052 generation;
- no new permanent main-window panel;
- no redesign;
- UI-001–UI-042 and copied Qt implementation remain visually authoritative;
- advanced controls inherit current widget/style grammar.

## Implementation waves
- K0: contract + capability scaffolding
- K1: opacity
- K2: crop
- K3: blur — STOP unless Windows sendcmd/gblur timing proof passes
- K4: shadow + glow — STOP if transparent-edge artifacts exceed tolerance
- K5: mask progress
- K6: Bezier / velocity / overshoot
- K7: copied UI + transactions
- K8: Windows acceptance / v0.2.1 RC

Do not expose K7 UI controls for a property before that property's evaluator/render backend wave is green.

## Required new tests
- `test_v2_schema_v4_contract.py`
- `test_v2_schema_v4_save_recovery.py`
- `test_v2_advanced_keyframe_math.py`
- `test_v2_advanced_animation_commands.py`
- `test_v2_advanced_capabilities.py`
- `test_v2_advanced_ffmpeg_graph.py`
- `test_v2_advanced_preview.py`
- `test_v2_asset_motion_keyframes.py`
- `test_v2_advanced_ffmpeg_render.py`

Existing mandatory regression gates include Wave E, visual motion FFmpeg, schema v3 migration/validation, Wave F copy/transactions, recovery, atomic render executor, native preview/editor, background cancellation and the all-21-effects user acceptance render.

## Protected areas
- do not rename/remove the 21 effect registry;
- no multitrack NLE expansion;
- no Gemini provider redesign;
- no subtitle/audio redesign;
- preserve final output atomicity;
- never move/republish stable tag v0.2.0;
- no Pillow/OpenCV dependency unless a later STOP gate proves Qt+FFmpeg impossible.

## STEP 06 gate
- data/persistence ownership: PASS
- activation/history ownership: PASS
- evaluator/compiler ownership: PASS
- advanced FFmpeg isolation: PASS
- capability/workspace ownership: PASS
- preview ownership: PASS
- copied UI integration ownership: PASS
- test ownership: PASS
- K0–K8 order: PASS
- production coding: **BLOCKED**

## Next exact action
**STEP 07 — Verification, Regression & Release Gate Plan**

STEP 07 must freeze the complete proof matrix, performance budgets, parity tolerances, Windows/real-FFmpeg coverage, recovery/cancellation cases, 21-effect regressions, Selection In/Out regressions, and explicit PASS/STOP criteria before v0.2.1 RC.

Binary planning DOCXs remain mandatory to synchronize into the repository before implementation begins.
