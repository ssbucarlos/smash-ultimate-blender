import bpy
import re

from ...dependencies import pyprc
from ..extras import create_meshes
from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
    Context,
    UIList,
    CopyTransformsConstraint,
    Menu,
    CopyLocationConstraint,
    CopyRotationConstraint,
    TrackToConstraint,
    )
from bpy.props import (
    IntProperty,
    StringProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    CollectionProperty,
    PointerProperty,
    FloatVectorProperty
   )
from math import radians, degrees
from mathutils import Vector
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..blender_property_extensions import SubSceneProperties

