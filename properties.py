import bpy
import re
from bpy.types import Scene, Object, Armature, PropertyGroup, Camera, Material, Bone, Mesh, Collection
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty
from bpy.props import FloatVectorProperty
from .modules.swing import sub_swing_data
from .modules.material import sub_matl_data
from .modules import exo_skel, import_anim, helper_bone_data, anim_data, export_model
def register():
    Armature.sub_anim_properties = PointerProperty(
        type=anim_data.SUB_PG_sub_anim_data
    )
    Scene.sub_scene_properties = PointerProperty(
        type=SubSceneProperties
    )
    Armature.sub_helper_bone_data = PointerProperty(
        type=helper_bone_data.SubHelperBoneData
    )
    Material.sub_matl_data = PointerProperty(
        type=sub_matl_data.SUB_PG_sub_matl_data
    )
    Armature.sub_swing_data = PointerProperty(
        type=sub_swing_data.SUB_PG_sub_swing_data
    )
    Bone.sub_swing_blender_bone_data = PointerProperty(
        type=sub_swing_data.SUB_PG_blender_bone_data
    )
    Mesh.sub_swing_data_linked_mesh = PointerProperty(
        type=sub_swing_data.SUB_PG_sub_swing_data_linked_mesh
    )
    Collection.sub_swing_collection_props = PointerProperty(
        type=sub_swing_data.SUB_PG_sub_swing_master_collection_props
    )

class SubSceneProperties(PropertyGroup):
    model_export_arma: PointerProperty(
        name='Armature',
        description='Select the Armature',
        type=Object,
        poll=exo_skel.poll_armatures,
        update=export_model.model_export_arma_update,
    )
    model_export_show_all_new_bones: BoolProperty(
        name='Show All',
        description='True if more than the first 5 bones should be displayed',
        default=False,
    )
    model_export_show_all_missing_bones: BoolProperty(
        name='Show All',
        description='True if more than the first 5 bones should be displayed',
        default=False,
    )
    vanilla_nusktb: StringProperty(
        name='Vanilla .NUSKTB file path',
        description='The path to the vanilla nusktb file',
        default='',
    )
    vanilla_update_prc: StringProperty(
        name='Vanilla update.prc file path',
        description='The path to the vanilla update.prc file',
        default='',
    )
    model_import_numatb_file_name: StringProperty(
        name='.numatb file name',
        description='The name of the .numatb file',
        default='',
    )
    model_import_numshb_file_name: StringProperty(
        name='.numshb file name',
        description='The name of the .numshb file',
        default='',
    )
    model_import_nusktb_file_name: StringProperty(
        name='.nusktb file name',
        description='The name of the .nusktb file',
        default='',
    )
    model_import_numdlb_file_name: StringProperty(
        name='.numdlb file name',
        description='The name of the .numdlb file',
        default='',
    )
    model_import_nuhlpb_file_name: StringProperty(
        name='.nuhlpb file name',
        description='The name the .nuhlpb file',
        default='',
    )
    model_import_folder_path: StringProperty(
        name='Model folder path',
        description='The path to the model folder',
        default='',
    )
    smash_armature: PointerProperty(
        name='Smash Armature',
        description='Select the Smash armature',
        type=Object,
        poll=exo_skel.poll_armatures,
    )
    other_armature: PointerProperty(
        name='Other Armature',
        description='Select the Other armature',
        type=Object,
        poll=exo_skel.poll_other_armatures,
    )
    bone_list: CollectionProperty(
        type=exo_skel.BoneListItem
    )
    saved_bone_list: CollectionProperty(
        type=exo_skel.BoneListItem
    )
    bone_list_index: IntProperty(
        name="Index for the exo bone list",
        default=0
    )
    pairable_bone_list: CollectionProperty(
        type=exo_skel.PairableBoneListItem
    )
    armature_prefix: StringProperty(
        name="Prefix",
        description="The Prefix that will be added to the bones in the 'Other' armature. Must begin with H_ or else it wont work!",
        default="H_Exo_"
    )
    material_reimport_arma: PointerProperty(
        name='Armature',
        description='Select the Armature',
        type=Object,
        poll=exo_skel.poll_armatures,  
    )
    material_reimport_folder: StringProperty(
        name='Material Reimport folder',
        description='The folder w/ .numatb & textures',
        default='',
    )
    material_reimport_numatb_path: StringProperty(
        name='Material Reimport .numatb',
        description='The selected .numatb',
        default='',
    )
    cv31_modal_last_mode: StringProperty(
        name='Last Eye Material CV31 Modal Operator Mode',
        description='the last used mode for this operator',
        default='LEFT',
    )
    cv31_modal_use_auto_keyframe: BoolProperty(
        name='Use Auto Keyframe',
        description='True if a keyframe should be automatically inserted on confirm',
        default=True,
    )
    cv31_modal_reset_on_mode_switch: BoolProperty(
        name='Reset on Mode Switch',
        description='If true, switching modes will "undo" the changes made while in that mode',
        default=False,
    )
    last_anim_import_dir: StringProperty(
        subtype="DIR_PATH",
        default=""
    )

    last_anim_export_dir: StringProperty(
        subtype="DIR_PATH",
        default=""
    )




