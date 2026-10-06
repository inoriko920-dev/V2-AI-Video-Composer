from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from aavc.presentation.subtitle_view import build_subtitle_views
from aavc.presentation.widgets.common import make_primary_button, muted_label, section_title
from aavc.subtitles import (
    SubtitleCue,
    SubtitleWorkingCopyHistory,
    SubtitleWorkingCopySnapshot,
    delete_subtitle_cue,
    duplicate_subtitle_cue,
    format_srt_timestamp,
    insert_subtitle_cue,
    merge_subtitle_cues,
    normalize_subtitle_cue_indexes,
    parse_srt,
    parse_srt_timestamp,
    resolve_subtitle_cue_overlap,
    shift_subtitle_cues,
    shift_subtitle_cues_from_row,
    sort_subtitle_cues_by_start_time,
    split_subtitle_cue,
    stretch_subtitle_cues_from_row,
)
from aavc.subtitles.dirty import subtitle_working_copy_is_dirty
from aavc.subtitles.selection import commit_pending_subtitle_edit


def create_subtitle_cue_edit_page(
    source: str | Path,
    *,
    on_save_copy: Callable[[tuple[SubtitleCue, ...]], None] | None = None,
    on_dirty_changed: Callable[[bool], None] | None = None,
) -> Any:
    from PySide6.QtWidgets import (
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    source_path = Path(source).resolve()
    source_cues = parse_srt(source_path)
    working_cues = source_cues
    history = SubtitleWorkingCopyHistory()
    loaded_row = -1

    page = QWidget()
    layout = QVBoxLayout(page)
    title = section_title(f"Edit Cue Subtitle ({len(working_cues)} cue) — Simpan sebagai Salinan")
    layout.addWidget(title)
    layout.addWidget(
        muted_label(
            "Edit teks/timing, tambah, duplikasi, pisah, gabungkan, hapus, perbaiki overlap, "
            "geser/stretch timing, urutkan waktu, normalisasi nomor cue, serta Undo/Redo pada "
            "working copy. Source asli tidak ditimpa; Simpan Salinan SRT menulis file baru lalu "
            "project diarahkan ke salinan."
        )
    )

    cue_list = QListWidget()
    layout.addWidget(cue_list, 1)

    text = QTextEdit()
    text.setMaximumHeight(92)
    start = QLineEdit()
    start.setPlaceholderText("00:00:00,000")
    end = QLineEdit()
    end.setPlaceholderText("00:00:01,000")
    form = QFormLayout()
    form.addRow("Teks", text)
    form.addRow("Waktu Mulai (IN)", start)
    form.addRow("Waktu Selesai (OUT)", end)
    layout.addLayout(form)

    shift_row = QHBoxLayout()
    shift_row.addWidget(QLabel("Offset Timing"))
    shift_offset_ms = QSpinBox()
    shift_offset_ms.setRange(-86_400_000, 86_400_000)
    shift_offset_ms.setSingleStep(100)
    shift_offset_ms.setSuffix(" ms")
    shift_offset_ms.setToolTip(
        "Nilai positif memajukan timing; nilai negatif memundurkan timing."
    )
    shift_all = QPushButton("⏱ Geser Semua Cue")
    shift_all.setEnabled(False)
    shift_all.setToolTip("Masukkan offset selain 0 ms untuk menggeser seluruh working copy.")
    shift_from_selected = QPushButton("⤵ Geser Cue Ini + Setelahnya")
    shift_from_selected.setEnabled(False)
    shift_from_selected.setToolTip(
        "Pilih cue dan masukkan offset selain 0 ms untuk menggeser cue itu serta semua cue sesudahnya."
    )
    shift_row.addWidget(shift_offset_ms)
    shift_row.addWidget(shift_all)
    shift_row.addWidget(shift_from_selected)
    shift_row.addStretch(1)
    layout.addLayout(shift_row)

    stretch_row = QHBoxLayout()
    stretch_row.addWidget(QLabel("Stretch dari Cue Ini"))
    stretch_percent = QDoubleSpinBox()
    stretch_percent.setRange(10.0, 400.0)
    stretch_percent.setDecimals(3)
    stretch_percent.setSingleStep(0.1)
    stretch_percent.setValue(100.0)
    stretch_percent.setSuffix(" %")
    stretch_percent.setToolTip(
        "100% mempertahankan timing. Nilai di atas 100% memperlebar dan di bawah 100% memampatkan "
        "timing relatif terhadap waktu mulai cue terpilih."
    )
    stretch_from_selected = QPushButton("↔ Stretch dari Cue Ini")
    stretch_from_selected.setEnabled(False)
    stretch_row.addWidget(stretch_percent)
    stretch_row.addWidget(stretch_from_selected)
    stretch_row.addStretch(1)
    layout.addLayout(stretch_row)

    warning = QLabel("")
    warning.setStyleSheet("color:#B45309; background:#FEF3C7; padding:4px 8px;")
    warning.setVisible(False)
    layout.addWidget(warning)

    action_row = QHBoxLayout()
    undo_edit = QPushButton("↶ Undo Edit")
    redo_edit = QPushButton("↷ Redo Edit")
    add_cue = QPushButton("＋ Tambah Cue Setelah Ini")
    duplicate_cue = QPushButton("⧉ Duplikasi Cue")
    split_cue = QPushButton("✂ Pisah Cue di Kursor")
    merge_cue = QPushButton("⇄ Gabung dengan Cue Berikutnya")
    delete_cue = QPushButton("🗑 Hapus Cue")
    resolve_overlap = QPushButton("↦ Perbaiki Overlap")
    sort_by_start = QPushButton("↕ Urutkan Waktu Mulai")
    normalize_indexes = QPushButton("123 Normalisasi Nomor Cue")
    save_copy = make_primary_button("Simpan Salinan SRT…")
    if on_save_copy is None:
        save_copy.setEnabled(False)
        save_copy.setToolTip("Penyimpanan salinan SRT belum terhubung ke sesi project.")
    action_row.addWidget(undo_edit)
    action_row.addWidget(redo_edit)
    action_row.addWidget(add_cue)
    action_row.addWidget(duplicate_cue)
    action_row.addWidget(split_cue)
    action_row.addWidget(merge_cue)
    action_row.addWidget(delete_cue)
    action_row.addWidget(resolve_overlap)
    action_row.addWidget(sort_by_start)
    action_row.addWidget(normalize_indexes)
    action_row.addStretch(1)
    action_row.addWidget(save_copy)
    layout.addLayout(action_row)

    def views() -> tuple[Any, ...]:
        return build_subtitle_views(working_cues)

    def snapshot(selected_row: int | None = None) -> SubtitleWorkingCopySnapshot:
        row = loaded_row if selected_row is None else selected_row
        return SubtitleWorkingCopySnapshot(working_cues, row)

    def notify_dirty() -> None:
        if on_dirty_changed is None:
            return
        on_dirty_changed(
            subtitle_working_copy_is_dirty(
                source_cues,
                working_cues,
                loaded_row=loaded_row,
                pending_text=text.toPlainText(),
                pending_start=start.text(),
                pending_end=end.text(),
            )
        )

    def refresh_history_actions() -> None:
        undo_edit.setEnabled(history.can_undo)
        redo_edit.setEnabled(history.can_redo)
        undo_edit.setToolTip(
            "Batalkan aksi terakhir pada working copy subtitle."
            if history.can_undo
            else "Belum ada edit working copy yang dapat dibatalkan."
        )
        redo_edit.setToolTip(
            "Ulangi aksi working copy yang terakhir dibatalkan."
            if history.can_redo
            else "Belum ada edit working copy yang dapat diulang."
        )

    def record_change(
        previous: SubtitleWorkingCopySnapshot,
        selected_row: int,
    ) -> None:
        history.record(previous, snapshot(selected_row))
        refresh_history_actions()
        notify_dirty()

    def indexes_are_canonical() -> bool:
        return all(cue.index == expected for expected, cue in enumerate(working_cues, start=1))

    def pending_start_values() -> list[float] | None:
        values = [cue.start_seconds for cue in working_cues]
        if 0 <= loaded_row < len(values):
            try:
                values[loaded_row] = parse_srt_timestamp(start.text())
            except ValueError:
                return None
        return values

    def refresh_sort_action() -> None:
        values = pending_start_values()
        needs_sort = len(working_cues) > 1 and (
            values is None
            or any(
                previous > current
                for previous, current in zip(values, values[1:], strict=False)
            )
        )
        sort_by_start.setEnabled(needs_sort)
        sort_by_start.setToolTip(
            "Urutkan working copy secara stabil berdasarkan waktu mulai tanpa mengubah isi cue."
            if needs_sort
            else "Cue sudah berurutan berdasarkan waktu mulai."
        )

    def refresh_shift_action() -> None:
        has_offset = shift_offset_ms.value() != 0
        can_shift_all = bool(working_cues) and has_offset
        can_shift_from_selected = 0 <= loaded_row < len(working_cues) and has_offset
        shift_all.setEnabled(can_shift_all)
        shift_all.setToolTip(
            "Geser seluruh cue dengan offset ini sebagai satu langkah Undo."
            if can_shift_all
            else "Masukkan offset selain 0 ms untuk menggeser seluruh working copy."
        )
        shift_from_selected.setEnabled(can_shift_from_selected)
        shift_from_selected.setToolTip(
            "Geser cue terpilih dan seluruh cue sesudahnya dengan offset ini sebagai satu langkah Undo."
            if can_shift_from_selected
            else "Pilih cue dan masukkan offset selain 0 ms."
        )

    def refresh_stretch_action() -> None:
        can_stretch = (
            0 <= loaded_row < len(working_cues)
            and abs(stretch_percent.value() - 100.0) > 0.000_001
        )
        stretch_from_selected.setEnabled(can_stretch)
        stretch_from_selected.setToolTip(
            "Skalakan durasi dan jarak timing mulai dari cue terpilih sebagai satu langkah Undo."
            if can_stretch
            else "Pilih cue dan gunakan nilai selain 100%."
        )

    def show_selected(row: int) -> None:
        nonlocal loaded_row
        current_views = views()
        available = 0 <= row < len(working_cues)
        loaded_row = row if available else -1
        duplicate_cue.setEnabled(available)
        duplicate_cue.setToolTip(
            "Duplikasi cue terpilih dengan teks dan timing yang sama serta nomor baru unik."
            if available
            else "Pilih cue yang akan diduplikasi."
        )
        split_cue.setEnabled(available)
        merge_cue.setEnabled(0 <= row < len(working_cues) - 1)
        can_delete = available and len(working_cues) > 1
        delete_cue.setEnabled(can_delete)
        delete_cue.setToolTip(
            "Hapus cue terpilih dari working copy."
            if can_delete
            else "Cue terakhir tidak dapat dihapus dari working copy."
        )
        has_overlap = available and current_views[row].overlaps_previous
        resolve_overlap.setEnabled(has_overlap)
        resolve_overlap.setToolTip(
            "Geser cue terpilih agar mulai tepat setelah cue sebelumnya tanpa mengubah durasi."
            if has_overlap
            else "Cue terpilih tidak overlap dengan cue sebelumnya."
        )
        needs_normalization = bool(working_cues) and not indexes_are_canonical()
        normalize_indexes.setEnabled(needs_normalization)
        normalize_indexes.setToolTip(
            "Ubah nomor cue menjadi 1..N sesuai urutan saat ini tanpa mengubah teks/timing."
            if needs_normalization
            else "Nomor cue sudah canonical 1..N."
        )
        refresh_shift_action()
        refresh_stretch_action()
        if not available:
            text.clear()
            start.clear()
            end.clear()
            save_copy.setEnabled(False)
            warning.setVisible(False)
            refresh_sort_action()
            notify_dirty()
            return
        cue = working_cues[row]
        view = current_views[row]
        text.setPlainText(cue.text.replace("\\N", "\n"))
        start.setText(format_srt_timestamp(cue.start_seconds))
        end.setText(format_srt_timestamp(cue.end_seconds))
        warning.setText("⚠ Cue ini tumpang tindih dengan cue sebelumnya pada working copy.")
        warning.setVisible(view.overlaps_previous)
        save_copy.setEnabled(on_save_copy is not None)
        refresh_sort_action()
        notify_dirty()

    def refresh_list(selected_row: int | None = None) -> None:
        current_views = views()
        target = -1
        cue_list.blockSignals(True)
        try:
            cue_list.clear()
            for view in current_views:
                cue_list.addItem(QListWidgetItem(view.list_label))
            if working_cues:
                requested = selected_row if selected_row is not None else 0
                target = max(0, min(requested, len(working_cues) - 1))
                cue_list.setCurrentRow(target)
            else:
                cue_list.setCurrentRow(-1)
        finally:
            cue_list.blockSignals(False)
        title.setText(
            f"Edit Cue Subtitle ({len(working_cues)} cue) — Simpan sebagai Salinan"
        )
        show_selected(target)

    def apply_loaded_form() -> bool:
        nonlocal working_cues
        if loaded_row < 0 or loaded_row >= len(working_cues):
            return True
        try:
            working_cues = commit_pending_subtitle_edit(
                working_cues,
                loaded_row,
                text=text.toPlainText(),
                start_timestamp=start.text(),
                end_timestamp=end.text(),
            )
        except ValueError as error:
            QMessageBox.warning(page, "Cue subtitle tidak valid", str(error))
            return False
        return True

    def commit_loaded_form_as_history_step(selected_row: int | None = None) -> bool:
        if loaded_row < 0 or loaded_row >= len(working_cues):
            return True
        previous = snapshot(loaded_row)
        if not apply_loaded_form():
            return False
        target = loaded_row if selected_row is None else selected_row
        record_change(previous, target)
        return True

    def handle_selection_change(row: int) -> None:
        if row == loaded_row:
            return
        previous_row = loaded_row
        if 0 <= previous_row < len(working_cues) and not commit_loaded_form_as_history_step(row):
            cue_list.blockSignals(True)
            try:
                cue_list.setCurrentRow(previous_row)
            finally:
                cue_list.blockSignals(False)
            return
        show_selected(row)

    def add_new_cue() -> None:
        nonlocal working_cues
        row = loaded_row
        previous = snapshot(row)
        if 0 <= row < len(working_cues) and not apply_loaded_form():
            return
        after_row = row if 0 <= row < len(working_cues) else len(working_cues) - 1
        start_seconds = working_cues[after_row].end_seconds if after_row >= 0 else 0.0
        working_cues = insert_subtitle_cue(
            working_cues,
            after_row,
            text="Teks subtitle baru",
            start_seconds=start_seconds,
            end_seconds=start_seconds + 1.0,
        )
        selected_row = after_row + 1
        record_change(previous, selected_row)
        refresh_list(selected_row)
        text.setFocus()
        text.selectAll()

    def duplicate_current_cue() -> None:
        nonlocal working_cues
        row = loaded_row
        previous = snapshot(row)
        if not apply_loaded_form():
            return
        try:
            working_cues = duplicate_subtitle_cue(working_cues, row)
        except ValueError as error:
            QMessageBox.warning(page, "Cue tidak dapat diduplikasi", str(error))
            return
        selected_row = row + 1
        record_change(previous, selected_row)
        refresh_list(selected_row)

    def split_current_cue() -> None:
        nonlocal working_cues
        row = loaded_row
        previous = snapshot(row)
        cursor_position = text.textCursor().position()
        if not apply_loaded_form():
            return
        try:
            working_cues = split_subtitle_cue(
                working_cues,
                row,
                text_offset=cursor_position,
            )
        except ValueError as error:
            QMessageBox.warning(page, "Cue tidak dapat dipisah", str(error))
            return
        selected_row = row + 1
        record_change(previous, selected_row)
        refresh_list(selected_row)

    def merge_with_next_cue() -> None:
        nonlocal working_cues
        row = loaded_row
        previous = snapshot(row)
        if not apply_loaded_form():
            return
        try:
            working_cues = merge_subtitle_cues(working_cues, row)
        except ValueError as error:
            QMessageBox.warning(page, "Cue tidak dapat digabung", str(error))
            return
        record_change(previous, row)
        refresh_list(row)

    def delete_current_cue() -> None:
        nonlocal working_cues
        row = loaded_row
        if row < 0 or row >= len(working_cues):
            return
        previous = snapshot(row)
        cue = working_cues[row]
        answer = QMessageBox.question(
            page,
            "Hapus Cue",
            f"Hapus cue {cue.index} dari working copy?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            working_cues = delete_subtitle_cue(working_cues, row)
        except ValueError as error:
            QMessageBox.warning(page, "Cue tidak dapat dihapus", str(error))
            return
        selected_row = min(row, len(working_cues) - 1)
        record_change(previous, selected_row)
        refresh_list(selected_row)

    def resolve_current_overlap() -> None:
        nonlocal working_cues
        row = loaded_row
        previous = snapshot(row)
        if not apply_loaded_form():
            return
        try:
            working_cues = resolve_subtitle_cue_overlap(working_cues, row)
        except ValueError as error:
            QMessageBox.warning(page, "Overlap tidak dapat diperbaiki", str(error))
            return
        record_change(previous, row)
        refresh_list(row)

    def sort_cues_by_start_now() -> None:
        nonlocal working_cues
        row = loaded_row
        previous = snapshot(row)
        selected_cue: SubtitleCue | None = None
        if 0 <= row < len(working_cues):
            if not apply_loaded_form():
                return
            selected_cue = working_cues[row]
        working_cues = sort_subtitle_cues_by_start_time(working_cues)
        selected_row = 0
        if selected_cue is not None:
            selected_row = next(
                index for index, cue in enumerate(working_cues) if cue is selected_cue
            )
        record_change(previous, selected_row)
        refresh_list(selected_row if working_cues else None)

    def normalize_indexes_now() -> None:
        nonlocal working_cues
        row = loaded_row
        previous = snapshot(row)
        if 0 <= row < len(working_cues) and not apply_loaded_form():
            return
        working_cues = normalize_subtitle_cue_indexes(working_cues)
        selected_row = row if row >= 0 else -1
        record_change(previous, selected_row)
        refresh_list(row if row >= 0 else None)

    def shift_all_cues_now() -> None:
        nonlocal working_cues
        row = loaded_row
        previous = snapshot(row)
        if 0 <= row < len(working_cues) and not apply_loaded_form():
            return
        try:
            shifted = shift_subtitle_cues(
                working_cues,
                shift_offset_ms.value() / 1000.0,
            )
        except ValueError as error:
            QMessageBox.warning(page, "Timing subtitle tidak dapat digeser", str(error))
            return
        if shifted == working_cues:
            refresh_shift_action()
            return
        working_cues = shifted
        selected_row = row if row >= 0 else (0 if working_cues else -1)
        record_change(previous, selected_row)
        refresh_list(selected_row if selected_row >= 0 else None)

    def shift_from_selected_now() -> None:
        nonlocal working_cues
        row = loaded_row
        if row < 0 or row >= len(working_cues):
            return
        previous = snapshot(row)
        if not apply_loaded_form():
            return
        try:
            shifted = shift_subtitle_cues_from_row(
                working_cues,
                row,
                shift_offset_ms.value() / 1000.0,
            )
        except ValueError as error:
            QMessageBox.warning(page, "Timing subtitle tidak dapat digeser", str(error))
            return
        if shifted == working_cues:
            refresh_shift_action()
            return
        working_cues = shifted
        record_change(previous, row)
        refresh_list(row)

    def stretch_from_selected_now() -> None:
        nonlocal working_cues
        row = loaded_row
        if row < 0 or row >= len(working_cues):
            return
        previous = snapshot(row)
        if not apply_loaded_form():
            return
        try:
            stretched = stretch_subtitle_cues_from_row(
                working_cues,
                row,
                stretch_percent.value() / 100.0,
            )
        except ValueError as error:
            QMessageBox.warning(page, "Timing subtitle tidak dapat di-stretch", str(error))
            return
        if stretched == working_cues:
            refresh_stretch_action()
            return
        working_cues = stretched
        record_change(previous, row)
        refresh_list(row)

    def undo_working_copy() -> None:
        nonlocal working_cues
        if not commit_loaded_form_as_history_step():
            return
        current = snapshot()
        restored = history.undo(current)
        if restored == current:
            refresh_history_actions()
            notify_dirty()
            return
        working_cues = restored.cues
        refresh_list(restored.selected_row if working_cues else None)
        refresh_history_actions()
        notify_dirty()

    def redo_working_copy() -> None:
        nonlocal working_cues
        if not commit_loaded_form_as_history_step():
            return
        current = snapshot()
        restored = history.redo(current)
        if restored == current:
            refresh_history_actions()
            notify_dirty()
            return
        working_cues = restored.cues
        refresh_list(restored.selected_row if working_cues else None)
        refresh_history_actions()
        notify_dirty()

    def save_selected_copy() -> None:
        if not commit_loaded_form_as_history_step():
            return
        row = loaded_row
        refresh_list(row if row >= 0 else None)
        if on_save_copy is not None:
            on_save_copy(working_cues)

    cue_list.currentRowChanged.connect(handle_selection_change)
    text.textChanged.connect(notify_dirty)
    start.textChanged.connect(refresh_sort_action)
    start.textChanged.connect(notify_dirty)
    end.textChanged.connect(notify_dirty)
    shift_offset_ms.valueChanged.connect(lambda _value: refresh_shift_action())
    shift_all.clicked.connect(shift_all_cues_now)
    shift_from_selected.clicked.connect(shift_from_selected_now)
    stretch_percent.valueChanged.connect(lambda _value: refresh_stretch_action())
    stretch_from_selected.clicked.connect(stretch_from_selected_now)
    undo_edit.clicked.connect(undo_working_copy)
    redo_edit.clicked.connect(redo_working_copy)
    add_cue.clicked.connect(add_new_cue)
    duplicate_cue.clicked.connect(duplicate_current_cue)
    split_cue.clicked.connect(split_current_cue)
    merge_cue.clicked.connect(merge_with_next_cue)
    delete_cue.clicked.connect(delete_current_cue)
    resolve_overlap.clicked.connect(resolve_current_overlap)
    sort_by_start.clicked.connect(sort_cues_by_start_now)
    normalize_indexes.clicked.connect(normalize_indexes_now)
    if on_save_copy is not None:
        save_copy.clicked.connect(save_selected_copy)
    refresh_history_actions()
    refresh_list(0 if working_cues else None)
    notify_dirty()
    if not working_cues:
        layout.addWidget(
            muted_label(
                "Source SRT kosong. Gunakan Tambah Cue untuk membuat cue pertama pada working copy."
            )
        )
    return page
