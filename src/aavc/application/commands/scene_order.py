from __future__ import annotations

from dataclasses import dataclass, replace

from aavc.domain.project.models import ProjectState

MIN_SCENE_SEGMENT_SECONDS = 0.001


@dataclass(frozen=True, slots=True)
class MoveScene:
    """Move one stable scene number by one position in project order."""

    scene_number: int
    offset: int

    def apply(self, project: ProjectState) -> ProjectState:
        if self.offset not in {-1, 1}:
            raise ValueError("Offset perpindahan Scene harus -1 atau 1")

        index = next(
            (
                current_index
                for current_index, scene in enumerate(project.scenes)
                if scene.scene_number == self.scene_number
            ),
            None,
        )
        if index is None:
            raise ValueError(f"Scene {self.scene_number} tidak ditemukan")

        target = index + self.offset
        if target < 0:
            raise ValueError("Scene sudah berada di posisi paling atas")
        if target >= len(project.scenes):
            raise ValueError("Scene sudah berada di posisi paling bawah")

        scenes = list(project.scenes)
        scenes[index], scenes[target] = scenes[target], scenes[index]
        return replace(project, scenes=tuple(scenes))

    def describe(self) -> str:
        direction = "atas" if self.offset < 0 else "bawah"
        return f"Pindah Scene {self.scene_number} ke {direction}"


@dataclass(frozen=True, slots=True)
class MoveSceneToIndex:
    """Move one stable scene number directly to a final project-order index."""

    scene_number: int
    target_index: int

    def apply(self, project: ProjectState) -> ProjectState:
        scene_count = len(project.scenes)
        if self.target_index < 0 or self.target_index >= scene_count:
            raise ValueError(
                f"Posisi target Scene harus antara 0 dan {max(0, scene_count - 1)}"
            )

        source_index = next(
            (
                current_index
                for current_index, scene in enumerate(project.scenes)
                if scene.scene_number == self.scene_number
            ),
            None,
        )
        if source_index is None:
            raise ValueError(f"Scene {self.scene_number} tidak ditemukan")
        if source_index == self.target_index:
            raise ValueError("Scene sudah berada di posisi target")

        scenes = list(project.scenes)
        scene = scenes.pop(source_index)
        scenes.insert(self.target_index, scene)
        return replace(project, scenes=tuple(scenes))

    def describe(self) -> str:
        return f"Pindah Scene {self.scene_number} ke posisi {self.target_index + 1}"


@dataclass(frozen=True, slots=True)
class SplitScene:
    """Split one Scene at scene-local time and preserve all visual assignments."""

    scene_number: int
    split_seconds: float

    def apply(self, project: ProjectState) -> ProjectState:
        source_index = next(
            (
                index
                for index, scene in enumerate(project.scenes)
                if scene.scene_number == self.scene_number
            ),
            None,
        )
        if source_index is None:
            raise ValueError(f"Scene {self.scene_number} tidak ditemukan")

        source = project.scenes[source_index]
        split_seconds = round(float(self.split_seconds), 3)
        remaining_seconds = source.duration_seconds - split_seconds
        if split_seconds < MIN_SCENE_SEGMENT_SECONDS:
            raise ValueError("Playhead terlalu dekat dengan awal Scene untuk Split")
        if remaining_seconds < MIN_SCENE_SEGMENT_SECONDS:
            raise ValueError("Playhead terlalu dekat dengan akhir Scene untuk Split")

        new_scene_number = max(scene.scene_number for scene in project.scenes) + 1
        first = replace(source, duration_seconds=split_seconds)
        second = replace(
            source,
            scene_number=new_scene_number,
            duration_seconds=remaining_seconds,
        )

        scenes = list(project.scenes)
        scenes[source_index : source_index + 1] = [first, second]
        cloned_animations = tuple(
            replace(assignment, scene_number=new_scene_number)
            for assignment in project.animations
            if assignment.scene_number == self.scene_number
        )
        return replace(
            project,
            scenes=tuple(scenes),
            animations=(*project.animations, *cloned_animations),
        )

    def describe(self) -> str:
        return f"Split Scene {self.scene_number} pada {self.split_seconds:.3f}s"


@dataclass(frozen=True, slots=True)
class DeleteScene:
    """Delete one scene while preserving a renderable project."""

    scene_number: int

    def apply(self, project: ProjectState) -> ProjectState:
        if len(project.scenes) <= 1:
            raise ValueError("Scene terakhir tidak boleh dihapus")

        if not any(scene.scene_number == self.scene_number for scene in project.scenes):
            raise ValueError(f"Scene {self.scene_number} tidak ditemukan")

        scenes = tuple(
            scene for scene in project.scenes if scene.scene_number != self.scene_number
        )
        used_asset_ids = {
            asset_id
            for scene in scenes
            for asset_id in scene.asset_ids
        }
        bindings = tuple(
            binding for binding in project.bindings if binding.asset_id in used_asset_ids
        )
        animations = tuple(
            assignment
            for assignment in project.animations
            if assignment.scene_number != self.scene_number
        )
        return replace(
            project,
            scenes=scenes,
            bindings=bindings,
            animations=animations,
        )

    def describe(self) -> str:
        return f"Hapus Scene {self.scene_number}"


@dataclass(frozen=True, slots=True)
class DuplicateScene:
    """Duplicate one scene immediately after its source with a new stable number."""

    scene_number: int

    def apply(self, project: ProjectState) -> ProjectState:
        source_index = next(
            (
                index
                for index, scene in enumerate(project.scenes)
                if scene.scene_number == self.scene_number
            ),
            None,
        )
        if source_index is None:
            raise ValueError(f"Scene {self.scene_number} tidak ditemukan")

        new_scene_number = max(scene.scene_number for scene in project.scenes) + 1
        source_scene = project.scenes[source_index]
        duplicate = replace(source_scene, scene_number=new_scene_number)

        scenes = list(project.scenes)
        scenes.insert(source_index + 1, duplicate)

        cloned_animations = tuple(
            replace(assignment, scene_number=new_scene_number)
            for assignment in project.animations
            if assignment.scene_number == self.scene_number
        )
        return replace(
            project,
            scenes=tuple(scenes),
            animations=(*project.animations, *cloned_animations),
        )

    def describe(self) -> str:
        return f"Duplikasi Scene {self.scene_number}"
