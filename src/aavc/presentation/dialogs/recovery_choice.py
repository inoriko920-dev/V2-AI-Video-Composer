"""Approved STEP03-R recovery modal variants: three dialogs, no editor redesign.

The existing 42-screen shell is unchanged. DLG-01 and DLG-02 share a single
Qt modal component, with conflict confirmation as a second state in DLG-02;
DLG-03 reuses the native QMessageBox visual idiom. Cancel/Esc is always safe.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from aavc.persistence.snapshot_provenance import CandidateStatus

RecoveryChoice = Literal["restore", "saved", "cancel"]


class RecoveryChoiceDialog(QDialog):
    """The two approved interactive recoverable-candidate dialog variations."""

    def __init__(self, status: CandidateStatus, filename: str, parent: QWidget | None = None) -> None:
        if status not in ("VERIFIED", "UNCERTAIN"):
            raise ValueError("RECOVERY_CHOICE_REQUIRES_VALID_CANDIDATE")
        super().__init__(parent)
        self.setObjectName("AAVCRecoveryChoiceDialog")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(610)
        self.setMaximumWidth(675)
        self.setModal(True)
        self.result_action: RecoveryChoice = "cancel"
        self.conflict_confirmation_visible = False
        self._conflicted = status == "UNCERTAIN"
        self.setWindowTitle(
            "Cadangan Perlu Diperiksa" if self._conflicted else "Cadangan Proyek Ditemukan"
        )
        self.setStyleSheet(
            "QDialog { background-color: #FFFFFF; color: #273347; }"
            "QLabel { color: #273347; }"
            "QPushButton { padding: 8px 12px; border: 1px solid #C7D5E6;"
            " border-radius: 5px; background: white; color: #273347; }"
            "QPushButton#RecoveryRestoreButton { background: #1767B3;"
            " color: white; border-color: #1767B3; }"
            "QFrame#RecoveryInfoFrame { background: #EDF5FF;"
            " border: 1px solid #C7DCF4; border-radius: 5px; }"
        )

        base = QVBoxLayout(self)
        base.setContentsMargins(24, 23, 24, 20)
        base.setSpacing(15)
        self.description = QLabel(
            "Versi proyek tersimpan mungkin berbeda dari versi saat cadangan dibuat."
            if self._conflicted
            else "Ada perubahan proyek yang ditemukan dalam cadangan otomatis."
        )
        self.description.setWordWrap(True)
        self.description.setObjectName("RecoveryDescription")
        base.addWidget(self.description)

        label = QLabel(Path(filename).name)
        label.setObjectName("RecoveryProjectFilename")
        label.setWordWrap(True)
        base.addWidget(label)

        if not self._conflicted:
            comparison = QFrame()
            comp_layout = QVBoxLayout(comparison)
            comp_layout.setContentsMargins(12, 12, 12, 12)
            line_saved = QLabel(
                "Proyek tersimpan — versi terakhir yang Anda simpan secara manual"
            )
            line_saved.setWordWrap(True)
            line_recovery = QLabel(
                "Cadangan otomatis — perubahan yang belum disimpan manual"
            )
            line_recovery.setWordWrap(True)
            comp_layout.addWidget(line_saved)
            comp_layout.addWidget(line_recovery)
            base.addWidget(comparison)

        self.info = QFrame()
        self.info.setObjectName("RecoveryInfoFrame")
        info_layout = QVBoxLayout(self.info)
        info_layout.setContentsMargins(12, 12, 12, 12)
        self.information = QLabel(
            "Pemulihan hanya dilakukan setelah Anda menyetujuinya. "
            "Proyek tersimpan akan dicadangkan terlebih dahulu."
            if self._conflicted
            else "Jika dipulihkan, salinan proyek tersimpan dibuat terlebih dahulu."
        )
        self.information.setWordWrap(True)
        info_layout.addWidget(self.information)
        base.addWidget(self.info)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        self.restore_button = QPushButton(
            "Periksa dan Pulihkan" if self._conflicted else "Pulihkan Cadangan"
        )
        self.restore_button.setObjectName("RecoveryRestoreButton")
        self.saved_button = QPushButton("Gunakan Proyek Tersimpan")
        self.saved_button.setObjectName("RecoveryUseSavedButton")
        self.cancel_button = QPushButton("Batal")
        self.cancel_button.setObjectName("RecoveryCancelButton")
        self.cancel_button.setDefault(True)
        self.cancel_button.setAutoDefault(True)
        self.restore_button.setAutoDefault(False)
        self.saved_button.setAutoDefault(False)
        self.restore_button.clicked.connect(self._choose_restore)
        self.saved_button.clicked.connect(self._choose_saved)
        self.cancel_button.clicked.connect(self.reject)
        button_row.addWidget(self.restore_button)
        button_row.addWidget(self.saved_button)
        button_row.addWidget(self.cancel_button)
        base.addLayout(button_row)
        self.cancel_button.setFocus()

    def _choose_restore(self) -> None:
        if self._conflicted and not self.conflict_confirmation_visible:
            self.conflict_confirmation_visible = True
            self.description.setText(
                "Yakin ingin memulihkan cadangan meskipun data proyek berbeda?"
            )
            self.restore_button.setText("Ya, Pulihkan Cadangan")
            self.saved_button.hide()
            self.cancel_button.setDefault(True)
            self.cancel_button.setFocus()
            return
        self.result_action = "restore"
        self.accept()

    def _choose_saved(self) -> None:
        self.result_action = "saved"
        self.accept()

    def reject(self) -> None:
        self.result_action = "cancel"
        super().reject()


def choose_recovery(
    parent: QWidget | None,
    status: CandidateStatus,
    filename: str,
) -> RecoveryChoice:
    """Display only approved designs and return an explicit choice."""
    if status == "ABSENT":
        return "saved"
    if status == "INVALID":
        message = QMessageBox(parent)
        message.setIcon(QMessageBox.Icon.Warning)
        message.setWindowTitle("Cadangan Tidak Dapat Dibaca")
        message.setText(
            "Cadangan otomatis tidak dapat dibuka dengan aman. "
            "File proyek tersimpan tidak diubah."
        )
        message.setInformativeText("File cadangan tetap disimpan untuk pemeriksaan.")
        saved_button = message.addButton(
            "Buka Proyek Tersimpan", QMessageBox.ButtonRole.AcceptRole
        )
        cancel_button = message.addButton("Batal", QMessageBox.ButtonRole.RejectRole)
        message.setDefaultButton(cancel_button)
        message.setEscapeButton(cancel_button)
        message.exec()
        return "saved" if message.clickedButton() is saved_button else "cancel"

    dialog = RecoveryChoiceDialog(status, filename, parent)
    dialog.exec()
    return dialog.result_action
