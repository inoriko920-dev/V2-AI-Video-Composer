from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aavc.animation.contract import (
    AUTOMATIC_MIGRATION_SCHEMA_VERSION,
    MAX_SUPPORTED_SCHEMA_VERSION,
    validate_project_animation_contract,
)
from aavc.domain.animation import (
    KEYFRAME_EASINGS,
    KEYFRAME_INTERPOLATIONS,
    TRANSFORM_PROPERTIES,
    AnimationKeyframe,
    AnimationKeyframeTrack,
    KeyframeEasing,
    KeyframeInterpolation,
    TransformProperty,
)
from aavc.domain.project.models import (
    AnimationAssignment,
    AssetBinding,
    AssetStatus,
    ProjectState,
    RenderQualitySettings,
    Scene,
    SubtitleAnimationSettings,
    SubtitleStyle,
)
from aavc.persistence.migrations import migrate_project_payload

CURRENT_SCHEMA_VERSION = AUTOMATIC_MIGRATION_SCHEMA_VERSION
_ASSET_STATUSES = {"READY", "MISSING", "CORRUPT", "DUPLICATE"}


def dumps_project(project: ProjectState) -> str:
    validate_project_animation_contract(project)
    payload = project.to_dict()
    payload["schema_version"] = project.schema_version
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} harus berupa object JSON")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} harus berupa array JSON")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} harus berupa string")
    return value


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _integer(value: Any, field: str, *, positive: bool = False) -> int:
    if type(value) is not int:
        raise ValueError(f"{field} harus berupa integer")
    if positive and value <= 0:
        raise ValueError(f"{field} harus lebih besar dari 0")
    return value


def _finite_number(
    value: Any,
    field: str,
    *,
    positive: bool = False,
    non_negative: bool = False,
) -> float:
    if type(value) not in {int, float}:
        raise ValueError(f"{field} harus berupa angka")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} harus finite")
    if positive and number <= 0:
        raise ValueError(f"{field} harus lebih besar dari 0")
    if non_negative and number < 0:
        raise ValueError(f"{field} tidak boleh negatif")
    return number


def _optional_finite_number(
    value: Any,
    field: str,
    *,
    non_negative: bool = False,
) -> float | None:
    if value is None:
        return None
    return _finite_number(value, field, non_negative=non_negative)


def _deserialize_scene(raw: Any, index: int) -> Scene:
    data = _mapping(raw, f"scenes[{index}]")
    scene_number = _integer(data.get("scene_number"), f"scenes[{index}].scene_number")
    asset_ids_raw = _list(data.get("asset_ids"), f"scenes[{index}].asset_ids")
    quotes_raw = _list(data.get("source_quotes"), f"scenes[{index}].source_quotes")
    asset_ids = tuple(
        _string(value, f"scenes[{index}].asset_ids[{asset_index}]")
        for asset_index, value in enumerate(asset_ids_raw)
    )
    source_quotes = tuple(
        _string(value, f"scenes[{index}].source_quotes[{quote_index}]")
        for quote_index, value in enumerate(quotes_raw)
    )
    if len(asset_ids) not in {1, 2}:
        raise ValueError(
            f"scenes[{index}].asset_ids harus berisi tepat 1 atau 2 aset"
        )
    if len(source_quotes) != len(asset_ids):
        raise ValueError(
            f"scenes[{index}].source_quotes harus cocok dengan jumlah asset_ids"
        )
    duration = _finite_number(
        data.get("duration_seconds", 3.0),
        f"scenes[{index}].duration_seconds",
        positive=True,
    )
    return Scene(
        scene_number=scene_number,
        asset_ids=asset_ids,
        source_quotes=source_quotes,
        duration_seconds=duration,
    )


def _deserialize_binding(raw: Any, index: int) -> AssetBinding:
    data = _mapping(raw, f"bindings[{index}]")
    asset_id = _string(data.get("asset_id"), f"bindings[{index}].asset_id")
    source_quote = _string(
        data.get("source_quote"), f"bindings[{index}].source_quote"
    )
    path = _optional_string(data.get("path"), f"bindings[{index}].path")
    status = _string(data.get("status"), f"bindings[{index}].status")
    if status not in _ASSET_STATUSES:
        raise ValueError(f"bindings[{index}].status tidak didukung: {status}")
    return AssetBinding(
        asset_id=asset_id,
        source_quote=source_quote,
        path=path,
        status=cast(AssetStatus, status),
    )


def _deserialize_keyframe(
    raw: Any,
    *,
    animation_index: int,
    track_index: int,
    keyframe_index: int,
) -> AnimationKeyframe:
    prefix = (
        f"animations[{animation_index}].keyframe_tracks[{track_index}]"
        f".keyframes[{keyframe_index}]"
    )
    data = _mapping(raw, prefix)
    time = _finite_number(data.get("time"), f"{prefix}.time", non_negative=True)
    if time > 1.0:
        raise ValueError(f"{prefix}.time harus pada rentang 0–1")
    interpolation = _string(
        data.get("interpolation", "linear"),
        f"{prefix}.interpolation",
    )
    if interpolation not in KEYFRAME_INTERPOLATIONS:
        raise ValueError(f"{prefix}.interpolation tidak didukung: {interpolation}")
    easing = _string(data.get("easing", "linear"), f"{prefix}.easing")
    if easing not in KEYFRAME_EASINGS:
        raise ValueError(f"{prefix}.easing tidak didukung: {easing}")
    return AnimationKeyframe(
        time=time,
        value=_finite_number(data.get("value"), f"{prefix}.value"),
        interpolation=cast(KeyframeInterpolation, interpolation),
        easing=cast(KeyframeEasing, easing),
        velocity=_optional_finite_number(
            data.get("velocity"),
            f"{prefix}.velocity",
        ),
        overshoot=_optional_finite_number(
            data.get("overshoot"),
            f"{prefix}.overshoot",
            non_negative=True,
        ),
    )


def _deserialize_keyframe_track(
    raw: Any,
    *,
    animation_index: int,
    track_index: int,
) -> AnimationKeyframeTrack:
    prefix = f"animations[{animation_index}].keyframe_tracks[{track_index}]"
    data = _mapping(raw, prefix)
    property_name = _string(data.get("property_name"), f"{prefix}.property_name")
    if property_name not in TRANSFORM_PROPERTIES:
        raise ValueError(f"{prefix}.property_name tidak didukung: {property_name}")
    keyframes = tuple(
        _deserialize_keyframe(
            value,
            animation_index=animation_index,
            track_index=track_index,
            keyframe_index=keyframe_index,
        )
        for keyframe_index, value in enumerate(
            _list(data.get("keyframes"), f"{prefix}.keyframes")
        )
    )
    return AnimationKeyframeTrack(
        property_name=cast(TransformProperty, property_name),
        keyframes=keyframes,
    )


def _deserialize_animation(raw: Any, index: int) -> AnimationAssignment:
    data = _mapping(raw, f"animations[{index}]")
    intensity = _finite_number(
        data.get("intensity", 1.0),
        f"animations[{index}].intensity",
        non_negative=True,
    )
    locked = data.get("locked", False)
    if type(locked) is not bool:
        raise ValueError(f"animations[{index}].locked harus berupa boolean")
    keyframe_tracks = tuple(
        _deserialize_keyframe_track(
            value,
            animation_index=index,
            track_index=track_index,
        )
        for track_index, value in enumerate(
            _list(
                data.get("keyframe_tracks", []),
                f"animations[{index}].keyframe_tracks",
            )
        )
    )
    return AnimationAssignment(
        scene_number=_integer(
            data.get("scene_number"), f"animations[{index}].scene_number"
        ),
        asset_id=_string(data.get("asset_id"), f"animations[{index}].asset_id"),
        enter_effect=_string(
            data.get("enter_effect", "Fade"), f"animations[{index}].enter_effect"
        ),
        exit_effect=_string(
            data.get("exit_effect", "Fade"), f"animations[{index}].exit_effect"
        ),
        intensity=intensity,
        locked=locked,
        keyframe_tracks=keyframe_tracks,
    )


def _validated_settings(
    cls: type[Any],
    raw: Any,
    field: str,
) -> Any:
    data = _mapping(raw, field)
    try:
        return cls(**data)
    except TypeError as error:
        raise ValueError(f"{field} tidak valid: {error}") from error


def _validate_project_invariants(project: ProjectState) -> None:
    scene_numbers = [scene.scene_number for scene in project.scenes]
    if len(scene_numbers) != len(set(scene_numbers)):
        raise ValueError("scene_number harus unik")

    bindings_by_id: dict[str, AssetBinding] = {}
    for binding in project.bindings:
        if binding.asset_id in bindings_by_id:
            raise ValueError(f"binding asset_id duplikat: {binding.asset_id}")
        bindings_by_id[binding.asset_id] = binding

    scenes_by_number = {scene.scene_number: scene for scene in project.scenes}
    for scene in project.scenes:
        for asset_id in scene.asset_ids:
            if asset_id not in bindings_by_id:
                raise ValueError(
                    f"Scene {scene.scene_number} merujuk asset tanpa binding: {asset_id}"
                )

    seen_assignments: set[tuple[int, str]] = set()
    for assignment in project.animations:
        target_scene = scenes_by_number.get(assignment.scene_number)
        if target_scene is None:
            raise ValueError(
                f"Animasi merujuk scene yang tidak ada: {assignment.scene_number}"
            )
        if assignment.asset_id not in target_scene.asset_ids:
            raise ValueError(
                "Animasi merujuk asset yang tidak ada pada scene "
                f"{assignment.scene_number}: {assignment.asset_id}"
            )
        key = (assignment.scene_number, assignment.asset_id)
        if key in seen_assignments:
            raise ValueError(
                "Assignment animasi duplikat untuk scene/asset "
                f"{assignment.scene_number}/{assignment.asset_id}"
            )
        seen_assignments.add(key)


def loads_project(text: str) -> ProjectState:
    data = _mapping(json.loads(text), "root")
    raw_schema_version = data.get("schema_version", 1)
    source_schema_version = _integer(raw_schema_version, "schema_version", positive=True)
    if source_schema_version > MAX_SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            "Versi project tidak didukung: "
            f"schema {source_schema_version} lebih baru dari schema "
            f"{MAX_SUPPORTED_SCHEMA_VERSION} yang didukung aplikasi ini"
        )
    if source_schema_version < CURRENT_SCHEMA_VERSION:
        data = migrate_project_payload(
            data,
            source_version=source_schema_version,
            target_version=CURRENT_SCHEMA_VERSION,
        )
        effective_schema_version = CURRENT_SCHEMA_VERSION
    else:
        effective_schema_version = source_schema_version

    scenes = tuple(
        _deserialize_scene(raw, index)
        for index, raw in enumerate(_list(data.get("scenes"), "scenes"))
    )
    bindings = tuple(
        _deserialize_binding(raw, index)
        for index, raw in enumerate(_list(data.get("bindings"), "bindings"))
    )
    animations = tuple(
        _deserialize_animation(raw, index)
        for index, raw in enumerate(_list(data.get("animations", []), "animations"))
    )

    metadata_raw = _mapping(data.get("metadata", {}), "metadata")
    metadata: dict[str, str] = {}
    for key, value in metadata_raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("metadata harus berupa object string ke string")
        metadata[key] = value

    project = ProjectState(
        schema_version=effective_schema_version,
        title=_string(data.get("title"), "title"),
        source_docx=_string(data.get("source_docx"), "source_docx"),
        asset_directory=_string(data.get("asset_directory"), "asset_directory"),
        scenes=scenes,
        bindings=bindings,
        narration_audio=_optional_string(
            data.get("narration_audio"), "narration_audio"
        ),
        subtitle_source=_optional_string(
            data.get("subtitle_source"), "subtitle_source"
        ),
        background_source=_optional_string(
            data.get("background_source"), "background_source"
        ),
        fps=_integer(data.get("fps", 30), "fps", positive=True),
        width=_integer(data.get("width", 1920), "width", positive=True),
        height=_integer(data.get("height", 1080), "height", positive=True),
        animations=animations,
        subtitle_style=_validated_settings(
            SubtitleStyle, data.get("subtitle_style", {}), "subtitle_style"
        ),
        subtitle_animation=_validated_settings(
            SubtitleAnimationSettings,
            data.get("subtitle_animation", {}),
            "subtitle_animation",
        ),
        render_quality=_validated_settings(
            RenderQualitySettings, data.get("render_quality", {}), "render_quality"
        ),
        metadata=metadata,
    )

    _finite_number(
        project.subtitle_style.outline_width,
        "subtitle_style.outline_width",
        non_negative=True,
    )
    _finite_number(
        project.subtitle_style.shadow,
        "subtitle_style.shadow",
        non_negative=True,
    )
    _finite_number(
        project.subtitle_animation.intensity,
        "subtitle_animation.intensity",
        non_negative=True,
    )
    _finite_number(
        project.render_quality.sharpen_amount,
        "render_quality.sharpen_amount",
        non_negative=True,
    )
    _validate_project_invariants(project)
    validate_project_animation_contract(project)
    return project


def temporary_sibling_path(path: str | Path, *, label: str) -> Path:
    destination = Path(path)
    return destination.with_name(
        f".{destination.name}.aavc-{label}-{uuid4().hex}.tmp"
    )


def _existing_schema_version(path: Path) -> int | None:
    """Read and validate an existing destination before allowing a normal Save.

    A corrupt existing project must never be treated like a fresh destination.
    Future-schema files retain the separate downgrade-protection error.
    """
    if not path.exists() and not path.is_symlink():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("root JSON bukan object")
        version = payload.get("schema_version", 1)
        if type(version) is not int or version < 1:
            raise ValueError("schema_version tidak valid")
        if version <= MAX_SUPPORTED_SCHEMA_VERSION:
            # Even syntactically valid JSON (e.g. {}) may be a broken project.
            loads_project(raw)
        return version
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(
            f"PROJECT_DESTINATION_UNREADABLE: project sudah ada tetapi "
            f"tidak dapat dibaca dengan aman: {path}"
        ) from error


def migration_backup_path(
    path: str | Path,
    *,
    target_version: int = CURRENT_SCHEMA_VERSION,
) -> Path:
    destination = Path(path)
    return destination.with_suffix(
        destination.suffix + f".pre-schema-v{target_version}.bak"
    )


def save_project(
    project: ProjectState,
    path: str | Path,
    *,
    create_schema_backup: bool = True,
    allow_schema_downgrade: bool = False,
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = temporary_sibling_path(destination, label="save")
    try:
        temporary.write_text(dumps_project(project), encoding="utf-8")
        # Autosave is an explicitly replaceable snapshot, unlike user project files.
        existing_version = (
            None
            if allow_schema_downgrade and not create_schema_backup
            else _existing_schema_version(destination)
        )
        if (
            existing_version is not None
            and existing_version > project.schema_version
            and not allow_schema_downgrade
        ):
            raise ValueError(
                "SCHEMA_DOWNGRADE_BLOCKED: tidak boleh menimpa project "
                f"schema v{existing_version} dengan schema v{project.schema_version}"
            )
        if (
            create_schema_backup
            and existing_version is not None
            and existing_version < project.schema_version
        ):
            backup = migration_backup_path(
                destination,
                target_version=project.schema_version,
            )
            if not backup.exists():
                shutil.copy2(destination, backup)
        temporary.replace(destination)
        return destination
    finally:
        temporary.unlink(missing_ok=True)


def load_project(path: str | Path) -> ProjectState:
    return loads_project(Path(path).read_text(encoding="utf-8"))
