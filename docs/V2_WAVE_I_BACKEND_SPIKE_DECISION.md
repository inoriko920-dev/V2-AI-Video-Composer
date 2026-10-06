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
| PyAV | 19.0.1 | BSD-3-Clause | CPython 3.12 ABI3 Windows x64 wheel published | ISOLATED SPIKE |
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
