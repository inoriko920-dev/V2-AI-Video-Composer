from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any
from uuid import uuid4

from aavc.application.commands import SetNarrationAudio
from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.project_action_state_window import (
    ProjectActionStateMainWindow,
)


def narration_recording_enabled(*, has_project: bool) -> bool:
    """Return whether microphone recording may start for the current session."""

    return has_project


def ensure_wav_suffix(path: str | Path) -> Path:
    """Normalize a narration recording destination to a .wav file."""

    candidate = Path(path).expanduser()
    if candidate.suffix != ".wav":
        candidate = candidate.with_suffix(".wav")
    return candidate.resolve()


def narration_staging_path(destination: str | Path) -> Path:
    """Return a same-directory temporary WAV path for one recording attempt."""

    final_path = ensure_wav_suffix(destination)
    return final_path.with_name(
        f".{final_path.stem}.aavc-recording-{uuid4().hex}{final_path.suffix}"
    )


def finalize_narration_recording(
    recorded_path: str | Path,
    destination: str | Path,
) -> Path:
    """Atomically replace the final narration only after a valid recording exists."""

    recorded = Path(recorded_path).expanduser().resolve()
    final_path = ensure_wav_suffix(destination)
    if not recorded.is_file() or recorded.stat().st_size <= 0:
        raise ValueError("Rekaman audio sementara tidak valid")
    recorded.replace(final_path)
    return final_path


def default_narration_recording_path(
    *,
    project_path: str | Path | None,
    source_docx: str | Path,
    project_title: str,
) -> Path:
    """Build a safe project-adjacent default recording path."""

    if project_path is not None:
        directory = Path(project_path).expanduser().resolve().parent
    else:
        directory = Path(source_docx).expanduser().resolve().parent
    safe_title = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in project_title.strip()
    ).strip("_")
    if not safe_title:
        safe_title = "project"
    return directory / f"{safe_title}_narration.wav"


def record_narration_dialog(parent: Any, output_path: str | Path) -> str | None:
    """Record one microphone take and return its finalized WAV path."""

    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtMultimedia import (
        QAudioInput,
        QMediaCaptureSession,
        QMediaDevices,
        QMediaFormat,
        QMediaRecorder,
    )
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
    )

    destination = ensure_wav_suffix(output_path)
    devices = tuple(QMediaDevices.audioInputs())
    if not devices:
        QMessageBox.warning(
            parent,
            "Mikrofon tidak tersedia",
            "Windows/Qt tidak menemukan perangkat input audio. Sambungkan atau aktifkan mikrofon lalu coba lagi.",
        )
        return None

    media_format = QMediaFormat(QMediaFormat.FileFormat.Wave)
    media_format.setAudioCodec(QMediaFormat.AudioCodec.Wave)
    if not media_format.isSupported(QMediaFormat.ConversionMode.Encode):
        QMessageBox.warning(
            parent,
            "Rekaman WAV tidak tersedia",
            "Backend Qt Multimedia pada komputer ini tidak dapat merekam WAV.",
        )
        return None

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = narration_staging_path(destination)

    dialog = QDialog(parent)
    dialog.setWindowTitle("Rekam Narasi")
    dialog.setModal(True)
    dialog.setMinimumWidth(440)
    dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

    layout = QVBoxLayout(dialog)
    intro = QLabel(
        "Pilih mikrofon, lalu klik Mulai. File baru akan dipasang sebagai narasi project hanya setelah rekaman selesai dengan benar."
    )
    intro.setWordWrap(True)
    layout.addWidget(intro)

    device_combo = QComboBox(dialog)
    for device in devices:
        description = device.description().strip() or "Perangkat audio"
        device_combo.addItem(description)
    layout.addWidget(device_combo)

    destination_label = QLabel(f"Tujuan: {destination}", dialog)
    destination_label.setWordWrap(True)
    layout.addWidget(destination_label)

    status_label = QLabel("Siap merekam.", dialog)
    duration_label = QLabel("00:00.0", dialog)
    layout.addWidget(status_label)
    layout.addWidget(duration_label)

    buttons = QHBoxLayout()
    start_button = QPushButton("Mulai", dialog)
    stop_button = QPushButton("Stop & Gunakan", dialog)
    cancel_button = QPushButton("Batal", dialog)
    stop_button.setEnabled(False)
    buttons.addWidget(start_button)
    buttons.addWidget(stop_button)
    buttons.addStretch(1)
    buttons.addWidget(cancel_button)
    layout.addLayout(buttons)

    capture_session = QMediaCaptureSession(dialog)
    audio_input = QAudioInput(dialog)
    recorder = QMediaRecorder(dialog)
    capture_session.setAudioInput(audio_input)
    capture_session.setRecorder(recorder)
    recorder.setMediaFormat(media_format)
    recorder.setQuality(QMediaRecorder.Quality.HighQuality)
    recorder.setOutputLocation(QUrl.fromLocalFile(str(staging)))

    result: dict[str, Any] = {
        "path": None,
        "stop_requested": False,
        "cancelled": False,
        "error": None,
    }

    def cleanup_partial() -> None:
        with suppress(OSError):
            staging.unlink(missing_ok=True)
        actual = recorder.actualLocation().toLocalFile()
        if actual:
            actual_path = Path(actual).expanduser().resolve()
            if actual_path != destination:
                with suppress(OSError):
                    actual_path.unlink(missing_ok=True)

    def finish_cancel() -> None:
        cleanup_partial()
        QDialog.reject(dialog)

    def on_duration_changed(milliseconds: int) -> None:
        total_seconds = max(0.0, float(milliseconds) / 1000.0)
        minutes = int(total_seconds // 60)
        seconds = total_seconds - minutes * 60
        duration_label.setText(f"{minutes:02d}:{seconds:04.1f}")

    def on_error(_error: Any, error_string: str) -> None:
        result["error"] = error_string or "Rekaman audio gagal."
        status_label.setText(f"Gagal: {result['error']}")
        start_button.setEnabled(False)
        stop_button.setEnabled(False)
        if recorder.recorderState() != QMediaRecorder.RecorderState.StoppedState:
            recorder.stop()
        else:
            cleanup_partial()

    def finalize_stopped() -> None:
        if result["cancelled"]:
            finish_cancel()
            return
        if result["error"] is not None:
            cleanup_partial()
            QMessageBox.critical(dialog, "Rekaman gagal", str(result["error"]))
            QDialog.reject(dialog)
            return
        if not result["stop_requested"]:
            return

        actual = recorder.actualLocation().toLocalFile()
        recorded_candidate = Path(actual).expanduser().resolve() if actual else staging
        if recorded_candidate == destination:
            recorded_candidate = staging
        try:
            finalized = finalize_narration_recording(recorded_candidate, destination)
        except (OSError, ValueError) as error:
            cleanup_partial()
            QMessageBox.critical(
                dialog,
                "Rekaman gagal",
                f"File rekaman tidak dapat diselesaikan dengan aman: {error}",
            )
            QDialog.reject(dialog)
            return
        result["path"] = str(finalized)
        QDialog.accept(dialog)

    def on_state_changed(state: Any) -> None:
        if state == QMediaRecorder.RecorderState.RecordingState:
            status_label.setText("Merekam…")
            start_button.setEnabled(False)
            stop_button.setEnabled(True)
            device_combo.setEnabled(False)
        elif state == QMediaRecorder.RecorderState.StoppedState:
            stop_button.setEnabled(False)
            finalize_stopped()

    def start_recording() -> None:
        index = device_combo.currentIndex()
        if index < 0 or index >= len(devices):
            return
        result["cancelled"] = False
        result["stop_requested"] = False
        result["error"] = None
        cleanup_partial()
        audio_input.setDevice(devices[index])
        recorder.setOutputLocation(QUrl.fromLocalFile(str(staging)))
        recorder.record()

    def stop_recording() -> None:
        result["stop_requested"] = True
        status_label.setText("Menyelesaikan file rekaman…")
        stop_button.setEnabled(False)
        recorder.stop()

    def cancel_recording() -> None:
        result["cancelled"] = True
        result["stop_requested"] = False
        if recorder.recorderState() == QMediaRecorder.RecorderState.StoppedState:
            finish_cancel()
        else:
            status_label.setText("Membatalkan rekaman…")
            start_button.setEnabled(False)
            stop_button.setEnabled(False)
            recorder.stop()

    recorder.durationChanged.connect(on_duration_changed)
    recorder.errorOccurred.connect(on_error)
    recorder.recorderStateChanged.connect(on_state_changed)
    start_button.clicked.connect(start_recording)
    stop_button.clicked.connect(stop_recording)
    cancel_button.clicked.connect(cancel_recording)

    dialog.exec()
    recorded_path = result["path"]
    return str(recorded_path) if recorded_path else None


class NarrationRecordingMainWindow(ProjectActionStateMainWindow):
    """Turn the visible narration toolbar control into a real microphone workflow."""

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        self._narration_record_action: Any | None = None
        super().__init__(services, initial_state=initial_state)

    def _build_toolbar(self, toolbar_type: Any, action_type: Any) -> None:
        super()._build_toolbar(toolbar_type, action_type)
        toolbar = self._toolbar
        if toolbar is None:
            return
        for action in toolbar.actions():
            if action.text() != "Rekam Narasi":
                continue
            self._narration_record_action = action
            action.setObjectName("RecordNarrationAction")
            action.setToolTip("Rekam narasi dari mikrofon dan pasang hasilnya ke project aktif.")
            with suppress(TypeError, RuntimeError):
                action.triggered.disconnect()
            action.triggered.connect(
                lambda _checked=False: self.open_narration_recorder()
            )
            break
        self._refresh_narration_recording_state()

    def _refresh_narration_recording_state(self) -> None:
        action = self._narration_record_action
        if action is None:
            return
        action.setEnabled(
            narration_recording_enabled(
                has_project=self.services.project_session.current is not None
            )
        )

    def open_narration_recorder(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Rekam Narasi tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        project_path = self.services.project_session.path
        default_path = default_narration_recording_path(
            project_path=project_path,
            source_docx=project.source_docx,
            project_title=project.title,
        )
        chosen, _ = QFileDialog.getSaveFileName(
            self.window,
            "Simpan Rekaman Narasi",
            str(default_path),
            "WAV Audio (*.wav)",
        )
        if not chosen:
            return
        destination = ensure_wav_suffix(chosen)

        recorded = record_narration_dialog(self.window, destination)
        if recorded is None:
            self.window.statusBar().showMessage("Rekam Narasi dibatalkan.", 5000)
            return

        try:
            self.services.project_session.execute(SetNarrationAudio(recorded))
        except (OSError, ValueError) as error:
            self._show_project_error("Gagal memasang narasi", error)
            return

        self._refresh_window_title()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"Narasi direkam: {Path(recorded).name}. Klik Simpan untuk menyimpan perubahan project.",
            8000,
        )

    def refresh_editor_overview(self) -> None:
        super().refresh_editor_overview()
        self._refresh_narration_recording_state()

    def show_route(self, route: UiRoute) -> None:
        super().show_route(route)
        self._refresh_narration_recording_state()


def create_narration_recording_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> NarrationRecordingMainWindow:
    return NarrationRecordingMainWindow(services, initial_state=initial_state)
