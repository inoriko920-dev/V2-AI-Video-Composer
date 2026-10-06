# FFmpeg tool slot — Final Release 0.1.0

AAVC 0.1.0 does **not** redistribute an FFmpeg/ffprobe binary inside the repository or release ZIP.

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
