# STEP 03 — Data Contract, Activation & Migration Plan

Status: **PASS**

Detailed planning artifact:
`03_V2_0.2.1_DATA_CONTRACT_ACTIVATION_AND_MIGRATION_PLAN.docx`.

## Core data decision: dual schema capability model
STEP 03 refines the earlier marker-only concept.

- `schema_version=3` remains the legacy-compatible project state.
- `schema_version=4` means the project has explicitly entered advanced keyframe semantics.
- Schema v4 requires:
  `metadata["animation_keyframe_contract"] = "advanced-v1"`.
- Schema v3 must not carry the advanced-v1 marker.
- v4 with a missing/unknown marker and v3 with the advanced-v1 marker are invalid states.
- Future schema >=5 is rejected.

Recommended constants:
- `MAX_SUPPORTED_SCHEMA_VERSION = 4`
- `LEGACY_COMPAT_SCHEMA_VERSION = 3`
- `ADVANCED_SCHEMA_VERSION = 4`
- `ADVANCED_KEYFRAME_CONTRACT = "advanced-v1"`

## Why schema v4 is required
v0.2.0 already parses the declared advanced property names and bezier/velocity/overshoot fields.
If an advanced project stayed schema v3, v0.2.0 could open it and silently ignore advanced semantics during render.
Schema v4 converts this into the already-existing future-schema hard rejection in v0.2.0.

## No automatic v3 -> v4 migration
Automatic persistence migrations remain:
`v1 -> v2 -> v3`.

There is intentionally no generic persistence migration from v3 to v4.

- New v0.2.1 projects start schema v3 with no advanced marker.
- Opening, previewing, rendering, ordinary saving, Random presets, AI preset assignment or Copy Scene Animations never promote a project.
- The first successfully committed advanced edit promotes the project transactionally to schema v4 + advanced-v1.
- Once promoted, normal editing never auto-demotes the project even if all advanced tracks are later removed.

## Dormant advanced tracks
Schema v3 may contain advanced property names or bezier/velocity/overshoot because v0.2.0 already serialized them.

Without advanced-v1:
- preserve the tracks;
- ignore their advanced semantics;
- report `ADVANCED_TRACK_DORMANT` WARNING;
- do not mutate schema/metadata.

Before promotion, scan all dormant advanced tracks project-wide.
If unrelated dormant advanced tracks would become active, the UI must obtain a one-time explicit activation acknowledgement.
Invalid/corrupt dormant data blocks promotion.

## First advanced edit must be atomic
Recommended command semantics:
- resolve target;
- reject locked assignment;
- validate requested track and all dormant advanced tracks;
- require dormant-activation acknowledgement when applicable;
- only then create a local candidate with schema 4 + advanced-v1 marker;
- insert/replace/remove the requested track;
- return one immutable ProjectState.

The entire promotion + edit is one HistoryEntry.
There should be no standalone public metadata-only promotion command.

Failed target/lock/validation/acknowledgement operations:
- create no history entry;
- do not dirty the project;
- do not alter schema or metadata.

## Serializer contract
`dumps_project()` must stop blindly forcing the maximum supported schema.
It must serialize the validated `project.schema_version`.

`loads_project()` must separate:
- maximum readable schema;
- automatic migration target.

Load rules:
- v1/v2 auto-migrate to v3;
- v3 remains v3;
- v4 loads directly after schema/contract consistency validation;
- v3 is never auto-promoted on load.

Opening alone never writes to disk.

## Save rules
- Saving a v3 project without advanced activation remains v3 and marker-free.
- Saving a v4 project remains v4 and preserves advanced-v1.
- First manual overwrite from an existing v3 file to a v4 candidate creates:
  `<project>.pre-schema-v4.bak`.
- The first promotion backup is never clobbered.
- Save As to a new path creates no source backup.
- Normal Save must reject overwriting a v4 disk project with an in-memory v3 state:
  `SCHEMA_DOWNGRADE_BLOCKED`.

This downgrade guard is required because Undo may return to the pre-promotion v3 state after the v4 project has already been saved.

Save As of a valid v3 in-memory state to a new file is allowed.

## Recovery
Autosave preserves exact schema/marker but should not create schema-promotion backups beside the autosave file.

Restore:
- validate snapshot before touching project/backup;
- create `<project>.pre-recovery.bak`;
- atomically replace the project.

Unlike normal Save, explicit Recovery may restore:
- v3 snapshot over v4 project; or
- v4 snapshot over v3 project.

A v4 -> v3 recovery requires a downgrade warning before execution because recovery is an explicit rollback path.
The pre-recovery backup protects the current file.

Corrupt/future/inconsistent snapshots fail before any replacement.

## Copy/Paste and lock propagation
Current Copy Scene Animations remains same-project and copies the entire AnimationAssignment.

For schema v3:
- dormant advanced tracks copy as data;
- Copy does not promote.

For schema v4:
- advanced tracks copy as active data.

Preserve existing semantics:
- target locked assignment conflict aborts the whole paste atomically;
- source lock flag copies with the assignment;
- no partial paste;
- AI/Random/preset changes never implicitly promote;
- AI cannot unlock an assignment.

If cross-project animation paste is ever added later, advanced paste into v3 must use the same explicit activation transaction.

## Undo/Redo
- First promotion + advanced edit is one HistoryEntry.
- Undo before that edit restores exact v3/no-marker state.
- Redo restores exact v4/advanced-v1 state.
- Failed operations create no history entry.
- Removing the final advanced track after promotion does not demote the project.
- If promotion has been saved and Undo returns to v3, normal Save to the same v4 path is blocked; Redo or explicit Save As are the safe paths.

## Validation codes / severities
- v3 dormant advanced data:
  `ADVANCED_TRACK_DORMANT` / WARNING.
- v3 + advanced-v1 marker:
  `ADVANCED_CONTRACT_SCHEMA_MISMATCH` / ERROR on load.
- v4 missing/unknown marker:
  `ADVANCED_CONTRACT_INVALID` / ERROR on load.
- v4 missing required backend feature:
  `ADVANCED_BACKEND_UNAVAILABLE` / ERROR at render preflight.
- velocity/overshoot on hold/linear:
  `ADVANCED_PARAMETER_MISMATCH` / WARNING.
- finite value requiring runtime clamp:
  `ADVANCED_VALUE_CLAMPED` / WARNING.
- unsafe crop sum normalized by STEP 01:
  `ADVANCED_CROP_NORMALIZED` / WARNING.
- NaN/Inf/corrupt keyframe:
  project-data ERROR.
- schema >=5:
  future-schema ERROR.

Warnings may continue only when semantics remain deterministic.
Any condition that could silently change advanced-v1 meaning is an ERROR.

## Compatibility guarantees
- v0.2.0 project opened in v0.2.1: zero disk write, zero activation.
- v0.2.0 project explicitly saved in v0.2.1 without advanced edit: stays schema v3 and marker-free.
- First successful advanced edit: schema v4 + advanced-v1.
- Advanced-v1 file opened in v0.2.0: rejected by future-schema guard.
- Foundational keyframes and 21 preset animations do not require promotion and must not regress.
- Exact byte identity after an explicit Save is not promised because JSON is canonicalized.
- Semantic identity for legacy saves is mandatory.

## Required implementation tests
- preserve v1->v3 and v2->v3 migration tests;
- v3 load/save remains v3;
- dormant advanced tracks round-trip but remain inactive;
- first advanced edit promotes exactly once;
- invalid schema/marker combinations reject;
- v0.2.0 rejects a v4 fixture;
- first v3->v4 overwrite creates a non-clobbering backup;
- v3 overwrite of existing v4 is blocked;
- Save As v3 to new path works;
- recovery v3<->v4 paths remain atomic and backed up;
- promotion+edit Undo/Redo restores exact schema/metadata/track state;
- dormant-track acknowledgement is required;
- Copy Scene Animations preserves tracks/velocity/overshoot/lock without promotion;
- locked targets reject with no history entry;
- validation codes match this contract.

## STEP 03 gate
- Backward silent-degradation risk eliminated: **PASS**
- Open/save activation behavior frozen: **PASS**
- Promotion transaction frozen: **PASS**
- Migration policy frozen: **PASS**
- Backup/recovery policy frozen: **PASS**
- Undo/Redo downgrade edge case frozen: **PASS**
- Copy/Paste + lock behavior frozen: **PASS**
- Validation matrix frozen: **PASS**
- Production coding authorized: **NO — BLOCKED**

## Next exact action
**STEP 04 — UI / Editing Interaction Contract**

STEP 04 must define how advanced tracks are exposed in the existing frozen UI, including:
- property grouping and editor controls;
- one-time dormant-track activation acknowledgement;
- keyframe controls and Bezier/velocity/overshoot editing;
- truth-preview state and heavy-preview feedback;
- locked-assignment behavior;
- validation presentation;
- no redesign of the established UI.

**CODING GATE: BLOCKED**
