# CODE_CONSTITUTION — CC-AAVC-v1.0

Status: FROZEN FOR STEP 08 FOUNDATION
Architecture: ARCH-AAVC-v1.0
UI Blueprint: PB-AAVC-v1.0 / UIF-AAVC-v1.0

## 1. Search → Understand → Modify
Before adding any file/class/service/helper: search concept + synonyms; locate current owner/interface/tests/config/call-sites; read owner module and contract; explain why current owner is insufficient. Modify the canonical owner first.

## 2. Layer direction
Presentation -> Application -> Domain. Infrastructure implements ports. Bootstrap wires implementations and contains no business logic. Domain never imports Qt, filesystem, HTTP, provider SDKs or FFmpeg.

## 3. Canonical ownership
One concern has one canonical owner. Do not create parallel managers/services for the same concern. New ownership requires ADR or explicit STEP task.

## 4. Naming
- package/module/file: snake_case
- class/protocol/exception: PascalCase
- function/method/variable: snake_case
- constants: UPPER_SNAKE_CASE
- commands: VerbNounCommand (e.g. ApplyAnimationCommand)
- queries: VerbNounQuery or NounQuery
- DTO: NounDTO only at boundaries
- domain events: NounPastTense (e.g. ProjectSaved) only if an event is actually needed
- errors: specific *Error classes mapped into taxonomy; never generic silent except.

## 5. Public/internal APIs
Only package-level contracts needed by another package are public. Prefix private helpers with _ and avoid barrel exports that hide ownership. Provider/FFmpeg details never leak through application contracts.

## 6. Cohesion/size
Prefer small cohesive units, but no arbitrary line-count target. Split when a file owns more than one reason to change, mixes layers, or cannot be understood locally. Never split simply to satisfy a number.

## 7. State
ProjectState is the canonical mutable product state inside a ProjectSession transaction boundary. UI state is derived/presentation-local. RenderPlan is immutable. No hidden mutable globals/singletons.

## 8. Commands, transaction, undo/redo
All user/AI mutations enter through application commands. A compound user intent is one transaction and one undo record. Validation runs before commit. Side effects are staged or compensated; failed commands do not leave half-mutated ProjectState.

## 9. Async/jobs
UI thread never performs long I/O, probing, rendering, AI requests or scans. JobManager owns lifecycle, cancellation, progress and stale-result protection. Worker completion must revalidate session/revision before apply.

## 10. Error taxonomy
ValidationError, ImportError, MediaProbeError, PersistenceError, ToolExecutionError, ProviderError, RenderError, ConfigurationError, SecurityError. User-facing errors include action/remediation; logs include diagnostic context without secrets.

## 11. Config/defaults
Immutable application defaults are versioned in code/resources. User settings go through SettingsRepository. Project-specific settings belong in .aavcproj. Machine-local paths/credentials never enter portable project files unless explicitly represented as relinkable references.

## 12. Portable paths/resources
No absolute developer paths. PathService resolves application root, bundled tools/resources, user config/cache/logs/recovery. Runtime writes never modify bundled resource directories.

## 13. Secrets
Raw API keys only in CredentialStore/Windows Credential Manager. Logs, exceptions, diagnostics bundle, ProjectState, settings JSON, screenshots/tests must redact secrets.

## 14. Logging/diagnostics
Structured logger only. Include subsystem/action/project-id correlation where useful. Never log full subtitle/narration/provider prompt unless explicitly enabled in a diagnostic mode designed for privacy.

## 15. Dependencies
Every new runtime dependency needs owner, reason, license, exact pin, provenance, size/runtime impact, test and removal plan. One library per responsibility unless ADR approves overlap.

## 16. UI separation
Qt widgets emit intents and render state; they do not own domain rules, filesystem or provider calls. Presenter/view-model translates application results into UI state.

## 17. Providers
Provider SDK/HTTP lives only under providers/adapters. AI produces plans/actions; application validators decide whether they are legal. AI never receives raw API key and never mutates ProjectState directly.

## 18. FFmpeg/tools
No subprocess.run/Popen outside platform/process_runner. FFmpeg/ffprobe commands are built by rendering/import media adapters, executed by ProcessRunner, capability-checked by ToolRegistry.

## 19. Persistence/migrations
.aavcproj is versioned JSON. Save = validate -> serialize -> temp file -> fsync/close where supported -> atomic replace. Autosave/recovery separate from source project. Migrations are one-way versioned transformations with fixtures and backup-aware behavior.

## 20. Security/input validation
Treat DOCX, SRT, PNG/media, project JSON and AI text as untrusted input. Validate size/type/schema/path; never execute content; quote/process arguments as arrays; block path traversal where destination paths are user-influenced.

## 21. Performance/observability
No full-frame Python composition for final render. Cache/proxy work is invalidated by explicit keys. Measure before optimization. Long jobs report progress/cancel capability when underlying operation supports it.

## 22. Definition of evidence
A task is not DONE because code exists. It needs acceptance results, canonical test output, relevant screenshots/artifacts, and a reviewable diff/commit.
