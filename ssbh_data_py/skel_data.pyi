from typing import List, Tuple, Any, Optional


def read_skel(path: str) -> SkelData: ...


def calculate_relative_transform(
    world_transform: list[list[float]],
    parent_world_transform: list[list[float]]) -> list[list[float]]: ...


class SkelData:
    major_version: int
    minor_version: int
    bones: list[BoneData]

    def __init__(
        self,
        major_version: int = ...,
        minor_version: int = ...,
    ) -> None: ...

    def save(self, path: str) -> None: ...

    def calculate_world_transform(
        self, bone: BoneData) -> list[list[float]]: ...


class BoneData:
    name: str
    transform: list[list[float]]
    parent_index: Optional[int]

    def __init__(
        self,
        name: str,
        transform: list[list[float]],
        parent_index: Optional[int]
    ) -> None: ...
