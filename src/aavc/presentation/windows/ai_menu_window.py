from __future__ import annotations

import sys
from typing import Any

from aavc.bootstrap.composition_root import FoundationServices
from aavc.platform.credentials import CredentialStore, WindowsCredentialManagerStore
from aavc.presentation.windows.animation_menu_window import AnimationMenuMainWindow

GEMINI_CREDENTIAL_SLOT_MIN = 1
GEMINI_CREDENTIAL_SLOT_MAX = 100


def gemini_credentials_supported(platform: str) -> bool:
    """Return whether the secure production credential store is available."""

    return platform == "win32"


def gemini_credential_reference(slot: int) -> str:
    """Return a deterministic, secret-free credential reference for one Gemini slot."""

    if slot < GEMINI_CREDENTIAL_SLOT_MIN or slot > GEMINI_CREDENTIAL_SLOT_MAX:
        raise ValueError(
            f"Gemini credential slot must be {GEMINI_CREDENTIAL_SLOT_MIN}–"
            f"{GEMINI_CREDENTIAL_SLOT_MAX}"
        )
    return f"gemini-slot-{slot:03d}"


def configured_gemini_slots(credentials: CredentialStore) -> tuple[int, ...]:
    """Return configured slot numbers without exposing stored secret values."""

    configured: list[int] = []
    first_read_error: OSError | None = None
    for slot in range(GEMINI_CREDENTIAL_SLOT_MIN, GEMINI_CREDENTIAL_SLOT_MAX + 1):
        try:
            secret = credentials.get_secret(gemini_credential_reference(slot))
        except OSError as error:
            if first_read_error is None:
                first_read_error = error
            continue
        if secret:
            configured.append(slot)
    if configured:
        return tuple(configured)
    if first_read_error is not None:
        raise first_read_error
    return ()


def gemini_status_text(slots: tuple[int, ...]) -> str:
    """Build a secret-free status message for the Gemini credential pool."""

    if not slots:
        return (
            "Belum ada API key Gemini yang tersimpan.\n\n"
            "Gunakan 'Simpan / Ganti API Key Gemini…' untuk mengisi salah satu dari 100 slot."
        )
    slot_list = ", ".join(str(slot) for slot in slots)
    return (
        f"Gemini: {len(slots)}/{GEMINI_CREDENTIAL_SLOT_MAX} slot terkonfigurasi.\n"
        f"Slot aktif: {slot_list}\n\n"
        "API key disimpan di Windows Credential Manager dan tidak ditampilkan kembali."
    )


class AiMenuMainWindow(AnimationMenuMainWindow):
    """Expose secure Gemini credential management through the runtime AI menu."""

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        ai_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "AI":
                ai_menu = menu_action.menu()
                break
        if ai_menu is None:
            return

        ai_menu.clear()

        status_action = action_type("Status Gemini…", self.window)
        status_action.setObjectName("GeminiStatusAction")
        status_action.triggered.connect(
            lambda _checked=False: self.show_gemini_status()
        )
        ai_menu.addAction(status_action)
        ai_menu.addSeparator()

        save_action = action_type("Simpan / Ganti API Key Gemini…", self.window)
        save_action.setObjectName("GeminiSaveCredentialAction")
        save_action.triggered.connect(
            lambda _checked=False: self.save_gemini_credential()
        )
        ai_menu.addAction(save_action)

        delete_action = action_type("Hapus API Key Gemini…", self.window)
        delete_action.setObjectName("GeminiDeleteCredentialAction")
        delete_action.triggered.connect(
            lambda _checked=False: self.delete_gemini_credential()
        )
        ai_menu.addAction(delete_action)

    def _windows_credential_store(self) -> CredentialStore | None:
        if not gemini_credentials_supported(sys.platform):
            self._show_project_notice(
                "Credential Gemini tidak tersedia",
                "Penyimpanan aman API key pada build ini menggunakan Windows Credential Manager. "
                "Tidak ada fallback plaintext pada platform selain Windows.",
            )
            return None
        try:
            return WindowsCredentialManagerStore()
        except (OSError, RuntimeError, ValueError) as error:
            self._show_project_error("Windows Credential Manager tidak tersedia", error)
            return None

    def _choose_gemini_slot(self, title: str) -> int | None:
        from PySide6.QtWidgets import QInputDialog

        slot, accepted = QInputDialog.getInt(
            self.window,
            title,
            "Slot API key Gemini (1–100):",
            value=1,
            minValue=GEMINI_CREDENTIAL_SLOT_MIN,
            maxValue=GEMINI_CREDENTIAL_SLOT_MAX,
            step=1,
        )
        return int(slot) if accepted else None

    def show_gemini_status(self) -> None:
        credentials = self._windows_credential_store()
        if credentials is None:
            return
        try:
            slots = configured_gemini_slots(credentials)
        except OSError as error:
            self._show_project_error("Gagal membaca credential Gemini", error)
            return
        self._show_project_notice("Status Gemini", gemini_status_text(slots))

    def save_gemini_credential(self) -> None:
        from PySide6.QtWidgets import QInputDialog, QLineEdit

        credentials = self._windows_credential_store()
        if credentials is None:
            return
        slot = self._choose_gemini_slot("Simpan API Key Gemini")
        if slot is None:
            return

        secret, accepted = QInputDialog.getText(
            self.window,
            "Simpan API Key Gemini",
            (
                f"Masukkan API key untuk slot {slot}.\n"
                "Key akan disimpan di Windows Credential Manager dan tidak akan ditampilkan kembali:"
            ),
            QLineEdit.EchoMode.Password,
        )
        if not accepted:
            return
        normalized = secret.strip()
        if not normalized:
            self._show_project_notice(
                "API key kosong",
                "API key Gemini tidak disimpan karena input kosong.",
            )
            return

        reference = gemini_credential_reference(slot)
        try:
            credentials.set_secret(reference, normalized)
        except (OSError, RuntimeError, ValueError) as error:
            self._show_project_error("Gagal menyimpan API key Gemini", error)
            return

        self.window.statusBar().showMessage(
            f"API key Gemini slot {slot} disimpan aman di Windows Credential Manager.",
            7000,
        )
        self._show_project_notice(
            "API key Gemini tersimpan",
            f"Slot {slot} berhasil diperbarui. Nilai API key tidak akan ditampilkan kembali.",
        )

    def delete_gemini_credential(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        credentials = self._windows_credential_store()
        if credentials is None:
            return
        slot = self._choose_gemini_slot("Hapus API Key Gemini")
        if slot is None:
            return

        reference = gemini_credential_reference(slot)
        try:
            configured = bool(credentials.get_secret(reference))
        except OSError as error:
            self._show_project_error("Gagal membaca API key Gemini", error)
            return
        if not configured:
            self._show_project_notice(
                "Slot Gemini kosong",
                f"Slot {slot} tidak memiliki API key tersimpan.",
            )
            return

        answer = QMessageBox.question(
            self.window,
            "Hapus API Key Gemini",
            f"Hapus credential Gemini pada slot {slot}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            credentials.delete_secret(reference)
        except (OSError, RuntimeError, ValueError) as error:
            self._show_project_error("Gagal menghapus API key Gemini", error)
            return

        self.window.statusBar().showMessage(
            f"API key Gemini slot {slot} dihapus dari Windows Credential Manager.",
            7000,
        )


def create_ai_menu_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> AiMenuMainWindow:
    return AiMenuMainWindow(services, initial_state=initial_state)
