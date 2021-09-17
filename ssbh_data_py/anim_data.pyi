from typing import List, Tuple, Any, Optional, Union


def read_anim(path: str) -> AnimData: ...


class AnimData:
    major_version: int
    minor_version: int
    groups: list[GroupData]


class GroupData:
    group_type: GroupType
    nodes: list[NodeData]


class GroupType:
    name: str
    value: int

    # TODO: Class attributes?


class NodeData:
    name: str
    tracks: list[TrackData]


class TrackData:
    name: str
    values: Union[list[UvTransform], list[Transform], list[float], list[bool], list[int], list[list[float]]]


class Transform:
    scale: list[float]
    rotation: list[float]
    translation: list[float]
    compensate_scale: float


class UvTransform:
    unk1: float
    unk2: float
    unk3: float
    unk4: float
    unk5: float
