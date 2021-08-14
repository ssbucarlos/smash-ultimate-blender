from bpy.types import Scene, Object
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty

from .panels import exo_skel

def register():
    Scene.smash_armature = PointerProperty(
        name='Smash Armature',
        description='Select the Smash armature',
        type=Object,
        poll=exo_skel.poll_armatures,
        #update=?
    )

    Scene.other_armature = PointerProperty(
        name='Other Armature',
        description='Select the Other armature',
        type=Object,
        poll=exo_skel.poll_other_armatures,
        #update=?
    )

    Scene.bone_list = CollectionProperty(
        type=exo_skel.BoneListItem
    )

    Scene.bone_list_index = IntProperty(
        name="Index for the exo bone list",
        default=0
    )

    Scene.armature_prefix = StringProperty(
        name="Prefix",
        description="The Prefix that will be added to the bones in the 'Other' armature. Must begin with H_ or else it wont work!",
        default="H_Exo_"
    )