from typing import List, Tuple, Any, Optional

from ssbh_data_py.mesh_data import MeshObjectData


def read_adj(path: str) -> AdjData: ...


class AdjData:
    entries: list[AdjEntryData]

    def save(self, path: str) -> None: ...

    def __init__(
        self,
    ) -> None: ...


class AdjEntryData:
    mesh_object_index: int
    vertex_adjacency: list[int]

    def __init__(
        self,
        mesh_object_index: int,
    ) -> None: ...

    @classmethod
    def from_mesh_object(cls, mesh_object_index: int,
                         mesh_object: MeshObjectData) -> AdjEntryData: ...
