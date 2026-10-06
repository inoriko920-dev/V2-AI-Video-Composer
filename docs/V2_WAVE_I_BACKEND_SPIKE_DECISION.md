# V2 Wave I — Optional Mature Backend Dependency Decision

Date: 2026-10-07  
Repository: `inoriko920-dev/V2-AI-Video-Composer`

## Decision summary

The production media strategy remains **FFmpeg/ffprobe CLI as the reference and
fallback final-render path**. Wave I does not replace it and does not add a new
runtime dependency to the application.

The only candidate promoted to an isolated Windows spike is **PyAV 19.0.1**,
strictly for future probe/frame/preview helper work. Passing the spike is not
permission to make PyAV the default backend.

## Candidate matrix

| Candidate | Version checked | License | Windows/Python packaging evidence | Wave I decision |
|---|---:|---|---|---|
| FFmpeg CLI | existing V2 reference | external tool policy | already proven by V2 render/portable gates | KEEP as production reference/fallback |
| PyAV | 19.0.1 | BSD-3-Clause | CPython 3.12 ABI3 Windows x64 wheel published and CI-verified | SPIKE PASS / DEFER RUNTIME ADOPTION |
| libopenshot | 1.0.1 | LGPL-3.0 | latest GitHub release has no standalone binary assets; native dependency bundle remains non-trivial | DEFER |
| MLT | 7.42.0 | LGPL-2.1 framework | latest GitHub release publishes source tarball only; Windows native integration remains heavier than current product needs | DEFER |
| OpenTimelineIO | not a render backend | Apache-2.0 | useful for editorial interchange, not needed by current focused timeline model | DO NOT ADOPT NOW |

## PyAV acceptance gate

The Windows spike must run on Python 3.12 and:

1. install `av==19.0.1` using `--only-binary=:all:`;
2. report BSD-3-Clause package metadata;
3. expose linked FFmpeg library versions;
4. encode and decode a synthetic 64x64 MPEG-4 sample;
5. complete import under 5 seconds on CI;
6. complete the tiny encode/decode round trip under 10 seconds on CI;
7. keep installed distribution footprint below 250 MiB;
8. leave `pyproject.toml`, `requirements.lock`, final render, ProjectState,
   UI, and existing FFmpeg behavior unchanged.

## Promotion policy

Even when the spike passes, PyAV remains **not adopted** in Wave I. A future
promotion would require a concrete user-facing problem (for example materially
better frame probing or preview latency), adapter implementation behind existing
media ports, before/after benchmarks, packaging verification in the portable
build, license/notice updates, and rollback to the FFmpeg-only path.

libopenshot and MLT are not rejected as technologies; they are deferred because
their native Windows packaging and redistribution surface is larger than the
measured need in the current application. Re-evaluate only when a required
capability cannot be delivered reliably by the current architecture.

## GPL boundary

No code from `openshot-qt` is copied or linked into V2. The UI/product code
remains independent of GPL application code.


## Measured Windows spike result

Run: `37537178273` — **PASS**

- Python: 3.12.10
- PyAV: 19.0.1
- License metadata: BSD-3-Clause
- Import: ~0.727 seconds
- Synthetic encode: ~0.0092 seconds
- Synthetic decode: ~0.0020 seconds
- Total round trip: ~0.0112 seconds
- Frames decoded: 3
- Sample: 64x64 MPEG-4
- Installed distribution footprint: 71,471,760 bytes (~68.2 MiB)
- Linked FFmpeg libraries were reported successfully.

## Final Wave I decision

**DEPENDENCY GATE: PASS for a no-adoption decision.**

PyAV proved technically viable on the target Windows/Python baseline, but it is
not added to application dependencies because the current product already has a
proven FFmpeg/ffprobe path and Wave I did not identify a concrete user-facing
problem whose measured benefit justifies another ~68 MiB installed dependency.

The selected strategy is therefore:

1. production/reference/fallback final render: **FFmpeg/ffprobe CLI**;
2. optional future probe/preview candidate: **PyAV 19.0.1**, behind existing media
   ports only if a later benchmarked requirement warrants adoption;
3. libopenshot/MLT: **deferred** until a capability need justifies native Windows
   packaging and LGPL redistribution work;
4. OpenTimelineIO: **not adopted** because current timeline/interchange needs do
   not require it.
