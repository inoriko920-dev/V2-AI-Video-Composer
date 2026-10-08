from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from aavc.bootstrap.composition_root import build_foundation_services

FOUNDATION_SMOKE_TOKEN = "AAVC_FOUNDATION_SMOKE_OK"


def _arg_value(args: list[str], flag: str, default: str | None = None) -> str | None:
    if flag not in args:
        return default
    idx = args.index(flag)
    if idx + 1 >= len(args):
        raise ValueError(f"{flag} requires a value")
    return args[idx + 1]


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    services = build_foundation_services()
    if "--foundation-smoke" in args:
        marker_path = _arg_value(args, "--foundation-smoke-file")
        if marker_path:
            marker = Path(marker_path)
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(FOUNDATION_SMOKE_TOKEN, encoding="utf-8")
        print(FOUNDATION_SMOKE_TOKEN)
        services.jobs.shutdown(wait=False)
        return 0

    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QFont, QFontDatabase
        from PySide6.QtWidgets import QApplication

        from aavc.presentation.windows.recovery_main_window import (
            create_recovery_main_window as create_main_window,
        )
    except ModuleNotFoundError as exc:
        services.jobs.shutdown(wait=False)
        print(f"Qt runtime belum terpasang: {exc}", file=sys.stderr)
        return 2

    state = _arg_value(args, "--ui-state", "UI-002") or "UI-002"
    capture_path = _arg_value(args, "--capture-path")
    app = QApplication([services.app_name])

    if sys.platform == "win32":
        windows_fonts = Path(r"C:\Windows\Fonts")
        for font_name in ("segoeui.ttf", "arial.ttf"):
            font_path = windows_fonts / font_name
            if font_path.exists():
                QFontDatabase.addApplicationFont(str(font_path))
                break
    app.setFont(QFont("Segoe UI", 10))

    window = create_main_window(services, initial_state=state)
    if capture_path:
        window.resize(1920, 1080)
    window.show()

    if capture_path:
        target = Path(capture_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        def capture() -> None:
            pixmap = window.grab()
            if not pixmap.save(str(target), "PNG"):
                print(f"Gagal menyimpan screenshot: {target}", file=sys.stderr)
                app.exit(3)
                return
            print(target)
            app.quit()

        QTimer.singleShot(500, capture)
    try:
        return int(app.exec())
    finally:
        services.jobs.shutdown(wait=False)
