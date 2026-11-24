import re
from math import degrees, radians
from pathlib import Path
from typing import TYPE_CHECKING

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Context,
    CopyLocationConstraint,
    CopyRotationConstraint,
    CopyTransformsConstraint,
    Menu,
    Operator,
    Panel,
    PropertyGroup,
    TrackToConstraint,
    UIList,
)
from mathutils import Vector

from ...dependencies import pyprc
from ..extras import create_meshes

if TYPE_CHECKING:
    from ..blender_property_extensions import SubSceneProperties
