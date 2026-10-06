# DATA_FLOW

## Manual edit
Widget action → application command → validate → ProjectSession transaction → ProjectState new revision → state event → UI refresh → autosave schedule.

## Random animation
UI scope/seed → RandomizeAnimationCommand → lock checks → AnimationPlanner → one compound state patch → preview refresh; renderer never randomizes.

## AI edit
Auto (AI) action → bounded ProviderRequest → background JobManager → ProviderManager/key pool → Gemini → fully validated native animation assignments → SetAnimationAssignmentsBatch → one compound undo checkpoint → UI refresh. Stale results are discarded if project state changes while the provider request is running.

## Import
Wizard → ImportProjectCommand → worker probes DOCX/assets/media → normalized ImportResult → UI review/errors → CommitImportCommand.

## Preview
ProjectState/selected Scene → ScenePreviewPlan → canonical layout solver → Qt native-motion/subtitle evaluator → preview canvas. Timeline/playhead drives scene-local time; narration preview uses Qt Multimedia when a valid narration file is available.

## Render
Export options → compile RenderPlan → preflight → background JobManager → ProcessRunner/FFmpeg → verify successful process and non-empty output → UI success/error result.
