bl_info = {
    'name': 'Smash Ultimate Blender',
    'author': 'Carlos Aguilar, ScanMountGoat (SMG)',
    'category': 'All',
    'location': 'View 3D > Tool Shelf > Ultimate',
    'description': 'A collection of tools for importing models and animations to smash ultimate.',
    'version': (0, 9, 0),
    'blender': (2, 93, 0),
    'warning': 'TO REMOVE: First "Disable" the plugin, then restart blender, then you can hit "Remove" to uninstall',
    'doc_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/wiki',
    'tracker_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/issues',
    'special thanks': 'SMG for making SSBH_DATA_PY, which none of this would be possible without. and also the rokoko plugin for being the reference used to make this UI'
}

import bpy, sys

from . import modules
from . import operators
from . import properties
from . import shaders
from . import properties

def check_unsupported_blender_versions():
    if bpy.app.version < (2, 93):
        unregister()
        sys.tracebacklimit = 0 # TODO: research what this does
        raise ImportError('Cant use a Blender version older than 2.93, please use 2.93 or later')
         
classes = [
    modules.import_model.SUB_PT_import_model,
    modules.import_model.SUB_OP_select_model_import_folder,
    modules.import_model.SUB_OP_import_model,
    modules.export_model.SUB_PT_export_model,
    modules.export_model.SUB_OP_model_exporter,
    modules.export_model.SUB_OP_vanilla_nusktb_selector,
    modules.exo_skel.SUB_OP_build_bone_list,
    modules.exo_skel.SUB_OP_populate_bone_list,
    modules.exo_skel.SUB_OP_update_bone_list,
    modules.exo_skel.SUB_OP_rename_other_bones,
    modules.exo_skel.SUB_PT_ultimate_exo_skel,
    modules.exo_skel.BoneListItem,
    modules.exo_skel.PairableBoneListItem,
    modules.exo_skel.SUB_UL_BoneList,
    modules.exo_skel.SUB_OP_make_combined_skeleton,
    modules.import_anim.SUB_PT_import_anim,
    modules.import_anim.SUB_OP_import_model_anim,
    modules.import_anim.SUB_OP_import_camera_anim,
    modules.export_anim.SUB_PT_export_anim,
    modules.export_anim.SUB_OP_export_model_anim,
    modules.export_anim.SUB_OP_export_camera_anim,
    modules.anim_data.SUB_PT_sub_smush_anim_data_master,
    modules.anim_data.SUB_PT_sub_smush_anim_data_vis_tracks,
    modules.anim_data.SUB_PT_sub_smush_anim_data_mat_tracks,
    modules.anim_data.SUB_UL_vis_track_entries,
    modules.anim_data.SUB_UL_mat_tracks,
    modules.anim_data.SUB_UL_mat_properties,
    modules.anim_data.SUB_OP_mat_track_add,
    modules.anim_data.SUB_OP_mat_track_remove,
    modules.anim_data.SUB_OP_mat_property_add,
    modules.anim_data.SUB_OP_mat_property_remove,
    modules.anim_data.SUB_OP_mat_drivers_refresh,
    modules.anim_data.SUB_OP_mat_drivers_remove,
    modules.anim_data.SUB_OP_vis_entry_add,
    modules.anim_data.SUB_OP_vis_entry_remove,
    modules.anim_data.SUB_OP_vis_drivers_refresh,
    modules.anim_data.SUB_OP_vis_drivers_remove,
    modules.anim_data.SUB_MT_vis_entry_context_menu,
    modules.anim_data.SUB_MT_mat_entry_context_menu,
    modules.anim_data.VisTrackEntry,
    modules.anim_data.MatTrackProperty,
    modules.anim_data.MatTrack,
    modules.anim_data.SubAnimProperties,
    modules.helper_bone_data.SUB_PT_helper_bone_data_master,
    modules.helper_bone_data.SUB_PT_helper_bone_data_aim_entries,
    modules.helper_bone_data.SUB_PT_helper_bone_data_interpolation_entries,
    modules.helper_bone_data.SUB_PT_helper_bone_data_version_info,
    modules.helper_bone_data.SUB_UL_aim_entries,
    modules.helper_bone_data.SUB_UL_interpolation_entries,
    modules.helper_bone_data.SUB_OP_add_interpolation_entry,
    modules.helper_bone_data.SUB_OP_remove_interpolation_entry,
    modules.helper_bone_data.SUB_OP_add_aim_entry,
    modules.helper_bone_data.SUB_OP_remove_aim_entry,
    modules.helper_bone_data.SUP_OP_helper_bone_constraints_remove,
    modules.helper_bone_data.SUP_OP_helper_bone_constraints_refresh,
    modules.helper_bone_data.SUB_MT_interpolation_entry_context_menu,
    modules.helper_bone_data.AimEntry,
    modules.helper_bone_data.InterpolationEntry,
    modules.helper_bone_data.SubHelperBoneData,
    modules.reimport_materials.SUB_PT_reimport_materials,
    modules.reimport_materials.SUB_OP_mat_reimport_directory_selector,
    modules.reimport_materials.SUB_OP_mat_reimport_numatb_selector,
    modules.reimport_materials.SUB_OP_reimport_materials,
    properties.SubSceneProperties,
]

def register():
    print('Loading Smash Ultimate Blender Tools...')

    check_unsupported_blender_versions()

    for cls in classes:
        bpy.utils.register_class(cls)

    properties.register()
    shaders.custom_sampler_node.register()
    print('Loaded Smash Ultimate Blender Tools!')

def unregister():
    print('Unloading Smash Ultimate Blender Tools')

    shaders.custom_sampler_node.unregister()
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            print('So this runtime error happened when unregistering ')
            

if __name__ == '__main__':
    register()