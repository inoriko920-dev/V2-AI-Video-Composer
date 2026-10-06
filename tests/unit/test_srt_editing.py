from pathlib import Path

import pytest

from aavc.application.commands import SetSubtitleSource
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.subtitles import (
    SubtitleCue,
    delete_subtitle_cue,
    duplicate_subtitle_cue,
    format_srt_timestamp,
    insert_subtitle_cue,
    merge_subtitle_cues,
    parse_srt,
    parse_srt_timestamp,
    replace_subtitle_cue,
    serialize_srt,
    split_subtitle_cue,
    write_srt_atomic,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _sample_cues() -> tuple[SubtitleCue, ...]:
    return (
        SubtitleCue(1, 0.125, 1.5, "Baris satu\\NBaris dua"),
        SubtitleCue(2, 2.0, 3.875, "Cue kedua"),
    )


def test_timestamp_round_trip_and_validation() -> None:
    assert format_srt_timestamp(3661.007) == "01:01:01,007"
    assert parse_srt_timestamp("01:01:01,007") == pytest.approx(3661.007)
    assert parse_srt_timestamp("00:00:01.250") == pytest.approx(1.25)

    with pytest.raises(ValueError, match="Timestamp SRT tidak valid"):
        parse_srt_timestamp("00:61:00,000")
    with pytest.raises(ValueError, match="tidak boleh negatif"):
        format_srt_timestamp(-0.001)


def test_replace_cue_preserves_index_and_other_cues() -> None:
    cues = _sample_cues()
    edited = replace_subtitle_cue(
        cues,
        0,
        text="Teks baru\nbaris kedua",
        start_seconds=0.25,
        end_seconds=1.75,
    )

    assert edited[0] == SubtitleCue(1, 0.25, 1.75, "Teks baru\\Nbaris kedua")
    assert edited[1] is cues[1]

    with pytest.raises(ValueError, match="Teks cue tidak boleh kosong"):
        replace_subtitle_cue(cues, 0, text="  ", start_seconds=0.0, end_seconds=1.0)
    with pytest.raises(ValueError, match="lebih besar"):
        replace_subtitle_cue(cues, 0, text="Valid", start_seconds=1.0, end_seconds=1.0)
    with pytest.raises(ValueError, match="dipilih tidak valid"):
        replace_subtitle_cue(cues, 99, text="Valid", start_seconds=0.0, end_seconds=1.0)


def test_insert_cue_after_selected_preserves_existing_indexes() -> None:
    cues = _sample_cues()
    inserted = insert_subtitle_cue(
        cues,
        0,
        text="Cue tambahan",
        start_seconds=1.5,
        end_seconds=2.0,
    )

    assert [cue.index for cue in inserted] == [1, 3, 2]
    assert inserted[1] == SubtitleCue(3, 1.5, 2.0, "Cue tambahan")
    assert inserted[0] is cues[0]
    assert inserted[2] is cues[1]


def test_insert_first_cue_into_empty_source() -> None:
    inserted = insert_subtitle_cue(
        (),
        -1,
        text="Cue pertama",
        start_seconds=0.0,
        end_seconds=1.0,
    )
    assert inserted == (SubtitleCue(1, 0.0, 1.0, "Cue pertama"),)


def test_insert_cue_rejects_invalid_position_and_content() -> None:
    cues = _sample_cues()
    with pytest.raises(ValueError, match="Posisi cue baru tidak valid"):
        insert_subtitle_cue(cues, 2, text="Valid", start_seconds=4.0, end_seconds=5.0)
    with pytest.raises(ValueError, match="Teks cue tidak boleh kosong"):
        insert_subtitle_cue(cues, 1, text=" ", start_seconds=4.0, end_seconds=5.0)


def test_duplicate_cue_after_selected_uses_unique_index_and_preserves_source() -> None:
    cues = _sample_cues()
    duplicated = duplicate_subtitle_cue(cues, 0)

    assert [cue.index for cue in duplicated] == [1, 3, 2]
    assert duplicated[1] == SubtitleCue(3, 0.125, 1.5, "Baris satu\\NBaris dua")
    assert duplicated[0] is cues[0]
    assert duplicated[2] is cues[1]
    assert duplicated[1] is not cues[0]


def test_duplicate_cue_rejects_invalid_row() -> None:
    cues = _sample_cues()
    with pytest.raises(ValueError, match="dipilih tidak valid"):
        duplicate_subtitle_cue(cues, -1)
    with pytest.raises(ValueError, match="dipilih tidak valid"):
        duplicate_subtitle_cue(cues, len(cues))


def test_split_cue_at_cursor_uses_midpoint_and_unique_index() -> None:
    cues = (
        SubtitleCue(7, 1.0, 5.0, "Halo dunia"),
        SubtitleCue(9, 6.0, 7.0, "Lanjut"),
    )
    split = split_subtitle_cue(cues, 0, text_offset=5)

    assert [cue.index for cue in split] == [7, 10, 9]
    assert split[0] == SubtitleCue(7, 1.0, 3.0, "Halo")
    assert split[1] == SubtitleCue(10, 3.0, 5.0, "dunia")
    assert split[2] is cues[1]


def test_split_cue_supports_multiline_and_explicit_time() -> None:
    cues = (SubtitleCue(4, 0.0, 4.0, "Baris satu\\NBaris dua"),)
    split = split_subtitle_cue(
        cues,
        0,
        text_offset=len("Baris satu\n"),
        split_seconds=1.25,
    )
    assert split == (
        SubtitleCue(4, 0.0, 1.25, "Baris satu"),
        SubtitleCue(5, 1.25, 4.0, "Baris dua"),
    )


def test_split_cue_rejects_invalid_cursor_and_time() -> None:
    cues = (SubtitleCue(1, 0.0, 2.0, "Halo dunia"),)
    with pytest.raises(ValueError, match="Posisi kursor"):
        split_subtitle_cue(cues, 0, text_offset=0)
    with pytest.raises(ValueError, match="Posisi kursor"):
        split_subtitle_cue(cues, 0, text_offset=len("Halo dunia"))
    with pytest.raises(ValueError, match="Waktu pisah"):
        split_subtitle_cue(cues, 0, text_offset=5, split_seconds=2.0)


def test_merge_adjacent_cues_preserves_first_index_and_full_span() -> None:
    cues = (
        SubtitleCue(7, 1.0, 2.0, "Baris pertama"),
        SubtitleCue(10, 2.5, 4.0, "Baris kedua"),
        SubtitleCue(12, 5.0, 6.0, "Tetap"),
    )
    merged = merge_subtitle_cues(cues, 0)

    assert merged == (
        SubtitleCue(7, 1.0, 4.0, "Baris pertama\\NBaris kedua"),
        cues[2],
    )


def test_merge_adjacent_cues_handles_overlap_and_multiline() -> None:
    cues = (
        SubtitleCue(2, 1.0, 4.0, "A\\NB"),
        SubtitleCue(3, 3.0, 5.0, "C\\ND"),
    )
    merged = merge_subtitle_cues(cues, 0)
    assert merged == (SubtitleCue(2, 1.0, 5.0, "A\\NB\\NC\\ND"),)


def test_merge_cue_rejects_invalid_or_last_row() -> None:
    cues = _sample_cues()
    with pytest.raises(ValueError, match="dipilih tidak valid"):
        merge_subtitle_cues(cues, -1)
    with pytest.raises(ValueError, match="tidak memiliki cue berikutnya"):
        merge_subtitle_cues(cues, len(cues) - 1)


def test_delete_cue_preserves_remaining_indexes_and_objects() -> None:
    cues = (
        SubtitleCue(4, 0.0, 1.0, "Pertama"),
        SubtitleCue(9, 1.5, 2.5, "Hapus"),
        SubtitleCue(12, 3.0, 4.0, "Ketiga"),
    )
    deleted = delete_subtitle_cue(cues, 1)

    assert deleted == (cues[0], cues[2])
    assert [cue.index for cue in deleted] == [4, 12]
    assert deleted[0] is cues[0]
    assert deleted[1] is cues[2]


def test_delete_cue_rejects_invalid_or_last_remaining_cue() -> None:
    with pytest.raises(ValueError, match="dipilih tidak valid"):
        delete_subtitle_cue(_sample_cues(), 99)
    with pytest.raises(ValueError, match="Cue terakhir tidak dapat dihapus"):
        delete_subtitle_cue((SubtitleCue(1, 0.0, 1.0, "Satu"),), 0)


def test_serialize_and_atomic_write_round_trip(tmp_path: Path) -> None:
    cues = _sample_cues()
    serialized = serialize_srt(cues)
    assert "00:00:00,125 --> 00:00:01,500" in serialized
    assert "Baris satu\nBaris dua" in serialized

    destination = tmp_path / "edited.srt"
    resolved = write_srt_atomic(destination, cues)

    assert resolved == destination.resolve()
    assert parse_srt(destination) == cues
    assert not list(tmp_path.glob("*.tmp"))


def test_added_cue_round_trips_through_copy(tmp_path: Path) -> None:
    added = insert_subtitle_cue(
        _sample_cues(),
        1,
        text="Cue ketiga",
        start_seconds=4.0,
        end_seconds=5.25,
    )
    destination = tmp_path / "with-added-cue.srt"
    write_srt_atomic(destination, added)
    assert parse_srt(destination) == added


def test_duplicated_cue_round_trips_through_copy(tmp_path: Path) -> None:
    duplicated = duplicate_subtitle_cue(_sample_cues(), 0)
    destination = tmp_path / "with-duplicated-cue.srt"
    write_srt_atomic(destination, duplicated)
    assert parse_srt(destination) == duplicated


def test_split_cue_round_trips_through_copy(tmp_path: Path) -> None:
    split = split_subtitle_cue(
        (SubtitleCue(1, 0.0, 3.0, "Bagian pertama bagian kedua"),),
        0,
        text_offset=len("Bagian pertama"),
    )
    destination = tmp_path / "with-split-cue.srt"
    write_srt_atomic(destination, split)
    assert parse_srt(destination) == split


def test_merged_cue_round_trips_through_copy(tmp_path: Path) -> None:
    merged = merge_subtitle_cues(_sample_cues(), 0)
    destination = tmp_path / "with-merged-cue.srt"
    write_srt_atomic(destination, merged)
    assert parse_srt(destination) == merged


def test_deleted_cue_round_trips_through_copy(tmp_path: Path) -> None:
    deleted = delete_subtitle_cue(_sample_cues(), 0)
    destination = tmp_path / "with-deleted-cue.srt"
    write_srt_atomic(destination, deleted)
    assert parse_srt(destination) == deleted


def test_writing_copy_does_not_touch_original(tmp_path: Path) -> None:
    original = tmp_path / "original.srt"
    original.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nAsli\n",
        encoding="utf-8",
    )
    before = original.read_bytes()
    cues = parse_srt(original)
    edited = replace_subtitle_cue(
        cues,
        0,
        text="Hasil edit",
        start_seconds=0.1,
        end_seconds=1.2,
    )

    copy = tmp_path / "original.edited.srt"
    write_srt_atomic(copy, edited)

    assert original.read_bytes() == before
    assert parse_srt(copy)[0].text == "Hasil edit"


def test_atomic_writer_requires_srt_extension(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="berekstensi .srt"):
        write_srt_atomic(tmp_path / "edited.txt", _sample_cues())


def test_copied_subtitle_source_participates_in_undo_redo(tmp_path: Path) -> None:
    original = tmp_path / "original.srt"
    original.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nAsli\n",
        encoding="utf-8",
    )
    edited_path = tmp_path / "original.edited.srt"
    edited = replace_subtitle_cue(
        parse_srt(original),
        0,
        text="Versi edit",
        start_seconds=0.1,
        end_seconds=1.25,
    )
    write_srt_atomic(edited_path, edited)

    project = create_project_state(
        title="subtitle-edit",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )
    session = ProjectSession()
    session.start(project)
    session.execute(SetSubtitleSource(str(original)))
    session.execute(SetSubtitleSource(str(edited_path)))

    assert session.current is not None
    assert session.current.subtitle_source == str(edited_path.resolve())
    session.undo()
    assert session.current.subtitle_source == str(original.resolve())
    session.redo()
    assert session.current.subtitle_source == str(edited_path.resolve())



def test_parse_srt_rejects_empty_file(tmp_path: Path) -> None:
    source = tmp_path / "empty.srt"
    source.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="tidak memiliki cue"):
        parse_srt(source)


def test_parse_srt_rejects_incomplete_block(tmp_path: Path) -> None:
    source = tmp_path / "broken.srt"
    source.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="tidak lengkap"):
        parse_srt(source)


def test_parse_srt_rejects_invalid_cue_timing(tmp_path: Path) -> None:
    source = tmp_path / "invalid-timing.srt"
    source.write_text(
        "1\n00:00:02,000 --> 00:00:01,000\nTeks\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="lebih besar"):
        parse_srt(source)
