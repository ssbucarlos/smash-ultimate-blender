from bpy.types import Scene, Object
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty

from .panels import exo_skel, io_matl, import_anim

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

    Scene.ssbh_lib_json_path = StringProperty(
        name='ssbh_lib_json path',
        description='The Path to the ssbh_lib_json.exe file',
        default='',
    )
    

    Scene.numatb_file_path = StringProperty(
        name='.numatb file path',
        description='The Path to the model.numatb file',
        default='',
    )

    Scene.sub_model_numshb_file_name = StringProperty(
        name='.numshb file path',
        description='The Path to the model.numshb file',
        default='',
    )

    Scene.sub_model_nusktb_file_name = StringProperty(
        name='.nusktb file path',
        description='The Path to the model.nusktb file',
        default='',
    )

    Scene.sub_model_numdlb_file_name = StringProperty(
        name='.numdlb file path',
        description='The Path to the model.numdlb file',
        default='',
    )

    Scene.sub_model_numatb_file_name = StringProperty(
        name='.numatb file path',
        description='The Path to the model.numatb file',
        default='',
    )

    Scene.sub_model_folder_path = StringProperty(
        name='Model folder path',
        description='The path to the model folder',
        default='',
    )

    Scene.io_matl_armature = PointerProperty(
        name='Armature',
        description='Select the Armature',
        type=Object,
        poll=exo_skel.poll_armatures,
    )

    Scene.sub_model_export_armature = PointerProperty(
        name='Armature',
        description='Select the Armature',
        type=Object,
        poll=exo_skel.poll_armatures,
    )

    Scene.sub_vanilla_nusktb = StringProperty(
        name='Vanilla .NUSKTB file path',
        description='The path to the vanilla nusktb file',
        default='',
    )

    Scene.sub_merge_same_name_meshes = BoolProperty(
        name='merge_same_name_meshes',
        description='Wether to merge same name meshes',
        default=True,
    )

    Scene.sub_anim_armature = PointerProperty(
        name='Armature',
        description='Select the Armature',
        type=Object,
        poll=exo_skel.poll_armatures,
    )
    
    Scene.sub_anim_camera = PointerProperty(
        name='Camera',
        description='Select the Camera',
        type=Object,
        poll=import_anim.poll_cameras,
    )


