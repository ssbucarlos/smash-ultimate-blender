from typing import List, Tuple, Any, Optional, Union


def read_anim(path: str) -> AnimData: ...


class AnimData:
    major_version: int
    minor_version: int
    groups: list[GroupData]
    final_frame_index: float

    def __init__(
        self,
        major_version: int = ...,
        minor_version: int = ...,
    ) -> None: ...

    def save(self, path: str) -> None: ...


class GroupData:
    group_type: GroupType
    nodes: list[NodeData]

    def __init__(
        self,
        group_type: GroupType,
    ) -> None: ...


class GroupType:
    name: str
    value: int

    Transform: GroupType = ...
    Visibility: GroupType = ...
    Material: GroupType = ...
    Camera: GroupType = ...


class NodeData:
    name: str
    tracks: list[TrackData]

    def __init__(
        self,
        name: str,
    ) -> None: ...


class TrackData:
    name: str
    values: Union[list[UvTransform], list[Transform],
                  list[float], list[bool], list[int], list[list[float]]]
    scale_options: ScaleOptions
    
    def __init__(
        self,
        name: str,
    ) -> None: ...


class ScaleOptions:
    inherit_scale: bool
    compensate_scale: bool

    def __init__(self) -> None: ...


class Transform:
    scale: list[float]
    rotation: list[float]
    translation: list[float]

    def __init__(
        self,
        scale: list[float],
        rotation: list[float],
        translation: list[float],
    ) -> None: ...


class UvTransform:
    scale_u: float
    scale_v: float
    rotation: float
    translate_u: float
    translate_v: float

    def __init__(
        self,
        scale_u: float,
        scale_v: float,
        rotation: float,
        translate_u: float,
        translate_v: float
    ) -> None: ...
