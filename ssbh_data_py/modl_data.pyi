from typing import List, Tuple, Any, Optional


def read_modl(path: str) -> ModlData: ...


def calculate_relative_transform(
    world_transform: list[list[float]], parent_world_transform: list[list[float]]) -> list[list[float]]: ...


class ModlData:
    major_version: int
    minor_version: int
    model_name: str
    skeleton_file_name: str
    material_file_names: list[str]
    animation_file_name: Optional[str]
    mesh_file_name: str
    entries: list[ModlEntryData]
    def save(self, path: str) -> None: ...

    def __init__(
        self,
        major_version: int = ...,
        minor_version: int = ...,
    ) -> None: ...


class ModlEntryData:
    mesh_object_name: str
    mesh_object_sub_index: int
    material_label: str

    def __init__(
        self,
        mesh_object_name: str,
        mesh_object_sub_index: int,
        material_label: str
    ) -> None: ...
