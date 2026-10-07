# STEP 01 — Mathematical & Property Contract

Status: **PASS**

This text mirror is the handoff companion for the detailed planning DOCX:
`01_V2_0.2.1_MATHEMATICAL_AND_PROPERTY_CONTRACT.docx`.

## Frozen baseline
- Stable release `v0.2.0` remains immutable.
- Planning baseline: `bf805011373d339e1290c1b645daaabdad12b750`.
- Existing foundational keyframes remain production contract:
  `position_x`, `position_y`, `scale`, `rotation_degrees`.
- No production coding is authorized by STEP 01.

## Time model
- Stored keyframe time is normalized Scene time in [0,1].
- Segment local time: `u = clamp((t-t0)/(t1-t0), 0, 1)`.
- Before first point use first value; after last point use last value.
- Start keyframe owns outgoing interpolation/easing/overshoot. End keyframe contributes value and incoming Bezier velocity.

## Property limits
| Property | Unit | Hard range | Neutral |
|---|---|---:|---:|
| position_x | normalized canvas width | -0.10..+0.10 | 0 |
| position_y | normalized canvas height | -0.10..+0.10 | 0 |
| scale | multiplier | 0.75..1.50 | 1 |
| rotation_degrees | degrees | -30..+30 | 0 |
| opacity | unit alpha | 0..1 | 1 |
| crop_left/top/right/bottom | source fraction | 0..0.45 each | 0 |
| blur | normalized intensity | 0..1 | 0 |
| shadow | normalized intensity | 0..1 | 0 |
| glow | normalized intensity | 0..1 | 0 |
| mask_progress | normalized reveal | 0..1 | 1 |

## Crop joint safety
After individual clamping:
- if `L+R > 0.90`, scale L/R proportionally so their sum is 0.90;
- if `T+B > 0.90`, scale T/B proportionally so their sum is 0.90.
At least 10% source width and height must remain visible.

## Resolution-aware effect mapping
- `sigma_blur = blur * clamp(0.022222*min(canvas_w,canvas_h), 8, 48)`.
- `shadow_alpha = 0.55*shadow`.
- `shadow_offset = 0.012*min(canvas_w,canvas_h)*shadow`.
- `shadow_sigma = 0.014*min(canvas_w,canvas_h)*shadow`.
- `glow_alpha = 0.65*glow`.
- `glow_sigma = 0.018*min(canvas_w,canvas_h)*glow`.
- mask_progress is a hard-edge left-to-right reveal in v0.2.1.

## Locked composition order
1. Decode / RGBA normalize.
2. Crop.
3. Blur.
4. Scale.
5. Rotation.
6. Mask progress.
7. Shadow + glow.
8. Opacity.
9. Position / overlay.

Legacy preset transforms remain additive inside their matching stage.

## Easing
- linear: `u`
- ease_in: `u^2`
- ease_out: `1-(1-u)^2`
- ease_in_out: existing v0.2.0 quadratic piecewise formula
- hold switches exactly at the next keyframe boundary.

## Bezier / velocity
The current scalar schema is retained; no new control-point schema.

For segment delta `D=v1-v0`:
- `m0 = clamp(velocity0 or 1, 0, 4) * D`
- `m1 = clamp(velocity1 or 1, 0, 4) * D`
- `P0=v0`
- `P1=v0+m0/3`
- `P2=v1-m1/3`
- `P3=v1`

Evaluate the cubic scalar Bezier at eased segment time.

Velocity semantics:
- dimensionless tangent multiplier;
- default 1.0;
- hard range 0..4;
- start velocity = outgoing tangent;
- end velocity = incoming tangent;
- if delta is zero, tangent is zero.

## Overshoot
For Bezier only:
- `o = clamp(start.overshoot or 0, 0, 0.50)`
- `value_preclamp = B(u_eased) + D*o*sin(pi*u_eased)*u_eased`
- contribution is exactly zero at both endpoints;
- final value is then property-clamped.
Velocity/overshoot on hold/linear is configuration mismatch and must warn, not silently reinterpret.

## Backward compatibility
Do not silently activate advanced tracks that may already exist in a v0.2.0 project.

Advanced semantics require project metadata:
`animation_keyframe_contract = "advanced-v1"`.

Rules:
- foundational tracks are always active as before;
- old projects without marker keep advanced tracks fail-soft with `KEYFRAME_TRACK_FALLBACK`;
- new v0.2.1 projects may default to advanced-v1;
- existing projects are promoted only by an explicit advanced-keyframe edit, transactionally, with recovery/backup;
- open/preview/render alone must never promote a project.

## Preview/render parity tolerances
- scalar evaluator: <=1e-4 absolute;
- foundational regression: <=1e-9;
- position: <=1 px at 1080p, <=2 px at 4K;
- scale bounds: <=1 px per axis at 1080p;
- rotation: <=0.10 degree;
- opacity: <=1/255 alpha;
- crop edge: <=1 px at 1080p;
- mask edge: <=1 px;
- blur sigma mapping: <=0.25 px equivalent sigma;
- shadow offset: <=1 px;
- glow/shadow alpha: <=2/255;
- endpoints: exact within evaluator float tolerance.

Reference resolutions: 1280x720, 1920x1080, 3840x2160.

## Fail-soft / fail-closed
- known advanced track without marker: ignore + warning;
- advanced-v1 project with unavailable backend: render preflight FAIL;
- unsupported Bezier/velocity/overshoot backend in advanced-v1: render preflight FAIL, no linear fallback;
- unsafe crop sum: proportional normalization + warning;
- NaN/Inf/corrupt keyframe: fail closed before FFmpeg.

## Implementation waves after planning
K1 opacity; K2 crop; K3 blur; K4 shadow/glow; K5 mask_progress; K6 Bezier/velocity/overshoot; K7 UI/transaction integration; K8 Windows acceptance + 0.2.1 RC.

## Next step
**STEP 02 — Backend Feasibility & Render Architecture**

Map each locked property to truthful Qt-preview and FFmpeg implementation mechanisms, including dynamic-filter constraints, performance, real-render proofs, and rollback/fallback policy.

**CODING GATE: BLOCKED**
