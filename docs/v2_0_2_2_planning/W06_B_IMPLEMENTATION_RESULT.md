# W06-B Implementation Result — Advanced Editor Lifecycle Wiring

Status: **COMPLETE / PASS**

Implementation branch: `v2/0.2.2-w06b-advanced-editor-wiring`  
Implementation PR: **#42**  
Frozen stable release preserved: `v0.2.1` @ `eb94efebf142ba8203dfc3ae3c5fa861222a0926`

## Scope completed

W06-B fixed only the already-authorized advanced editor controller wiring defects.

Implemented:
- pass the real `project.schema_version` into `show_asset_motion_dialog(...)`;
- route asset Apply through `ApplyAnimationKeyframeEdit` instead of direct `SetAnimationAssignment`;
- catch typed `AdvancedAnimationActivationRequired` before mutation;
- reject activation => zero mutation;
- accept activation => one retry with `activate_advanced=True`;
- unrelated dormant advanced tracks are listed in the confirmation and retried with `acknowledge_dormant=True`;
- already-v4 projects use the canonical command without a repeat activation prompt;
- existing Remove path, preset behavior, lock semantics, modal layout and main-window layout are preserved.

No dialog visual redesign was required.

## Failing-before evidence

First W06-B test commit:
`6639c5677ce963dbd16b96552102b8c9da321d02`

CI run:
`37677626046` — **EXPECTED FAILURE**

Result:
- **5 failed**
- **719 passed**
- **45 deselected**

Failures exactly matched the authorized defects:
1. `project_schema_version` missing from the modal call;
2. v3 reject path received `SetAnimationAssignment` instead of `ApplyAnimationKeyframeEdit`;
3. v3 accept path received `SetAnimationAssignment`;
4. dormant acknowledgement path received `SetAnimationAssignment`;
5. v4 path received `SetAnimationAssignment`.

No unrelated failure was present.

## Implementation commit

Controller fix commit:
`4a61b979ca04754afa9afddf3b376d4240cfa8c9`

Application runtime file changed:
- `src/aavc/presentation/windows/animation_menu_window.py`

New permanent regression file:
- `tests/unit/test_v2_0_2_2_animation_menu_advanced_wiring.py`

No change was required in:
- `src/aavc/presentation/dialogs/asset_motion.py`;
- schema/serializer/persistence;
- rendering;
- provider/credentials;
- packaging/dependencies.

## Controller behavior after fix

### Schema context
The modal is opened with:
`project_schema_version=project.schema_version`.

Therefore a schema-v4 advanced-v1 project no longer enters the dialog through the default Legacy-v3 presentation path.

### Advanced activation
For Apply:
1. controller submits `ApplyAnimationKeyframeEdit(assignment)`;
2. if no activation is required, the command commits normally;
3. if `AdvancedAnimationActivationRequired` is raised, the project remains unchanged;
4. controller shows `Aktifkan Advanced Animation?`;
5. reject returns immediately with zero mutation;
6. accept retries the same assignment with `activate_advanced=True`;
7. when unrelated dormant advanced tracks exist, the confirmation names them and the retry sets `acknowledge_dormant=True`;
8. successful activation remains one ProjectSession history mutation because the first command raised before commit;
9. an already-v4 project does not raise the activation signal and is not re-prompted.

## Final verification before result-document update

CI run:
`37677943203` — **PASS**

Result:
- **724 passed**
- **45 deselected**
- compile PASS
- Ruff PASS
- strict mypy PASS
- STEP09 screenshot capture/verification PASS

Additional gates:
- CodeQL `37677943401` — **PASS**
- Optional Backend Spike `37677943249` — **PASS**
- V2 Automated User Acceptance `37677943275` — **PASS**
  - real FFmpeg/ffprobe PASS
  - full technical acceptance PASS
  - Windows portable build PASS
  - portable verification PASS
  - packaged EXE launch/capture PASS

## Regression authority preserved

Existing v0.2.1 K7 command tests remain authoritative for:
- foundational edits remain schema v3;
- preset edits preserve dormant tracks without promotion;
- activation is required before advanced mutation;
- unrelated dormant tracks require acknowledgement;
- accepted activation promotes schema+marker+edit atomically;
- Undo restores exact pre-edit project;
- already-v4 project does not require activation again.

W06-B adds the previously missing controller/UI routing proof on top of those command-level invariants.

## Explicit non-changes

W06-B did not:
- add schema v5;
- redesign the Asset Motion dialog or main window;
- add a panel/dock;
- alter the 21 native effect registry;
- change FFmpeg renderer behavior;
- change Gemini provider/credentials;
- change persistence/recovery behavior;
- change package version/dependencies;
- publish or retarget any release tag.

## Gate

**W06-B: PASS / COMPLETE**

Exact next wave:
**STEP 06 / W06-C — Persistence / Recovery File Safety**

Do not begin W06-D in the same turn.
