# FFmpeg tool slot — V2 0.2.2

AAVC v0.2.2 does **not** redistribute an FFmpeg/ffprobe binary inside the repository or release ZIP.

Reason: the exact FFmpeg build determines codec availability and license obligations. The application keeps that decision explicit instead of silently shipping an unknown third-party binary.

Supported runtime setup:
1. place an approved `ffmpeg.exe` and `ffprobe.exe` in this `tools/ffmpeg/` directory next to the portable application; or
2. install an approved FFmpeg build and make both executables available on the Windows `PATH`.

Resolution order:
- app-local `tools/ffmpeg/`
- system `PATH`

Before using a build for redistribution, record:
- exact build/version and download source;
- SHA-256 checksums;
- enabled codecs/filters required by AAVC;
- license profile and corresponding NOTICE/source obligations.

Minimum functional capability expected by the current render pipeline includes H.264 video encoding, AAC audio, scale/overlay/concat/unsharp filters, and ASS/libass subtitle rendering.

For v0.2.2 automated Windows acceptance, the reference is **FFmpeg/ffprobe 9.0.2** (gyan.dev essentials build, as verified by v0.2.1 evidence). Both executables must report 9.0.2 in the first `-version` line; record their SHA-256 fingerprints with the acceptance evidence. The approved binary remains external to the public ZIP. An absent/mismatched version fails acceptance; do not auto-upgrade to another version.
