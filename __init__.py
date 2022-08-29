bl_info = {
    'name': 'Smash Ultimate Blender',
    'author': 'Carlos Aguilar',
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

from . import panels
from . import operators
from . import properties
from . import shaders

def check_unsupported_blender_versions():
    if bpy.app.version < (2, 93):
        unregister()
        sys.tracebacklimit = 0 # TODO: research what this does
        raise ImportError('Cant use a Blender version older than 2.93, please use 2.93 or later')
         
classes = [
    panels.import_model.ImportModelPanel,
    panels.import_model.ModelFolderSelector,
    panels.import_model.ModelImporter,
    panels.export_model.ExportModelPanel,
    panels.export_model.ModelExporterOperator,
    panels.export_model.VanillaNusktbSelector,
    panels.io_matl.MaterialPanel,
    panels.io_matl.SsbhLibJsonFileSelector,
    panels.io_matl.NumatbFileSelector,
    panels.io_matl.MatlReimporter,
    panels.exo_skel.BuildBoneList,
    panels.exo_skel.PopulateBoneList,
    panels.exo_skel.UpdateBoneList,
    panels.exo_skel.RenameOtherBones,
    panels.exo_skel.VIEW3D_PT_ultimate_exo_skel,
    panels.exo_skel.BoneListItem,
    panels.exo_skel.PairableBoneListItem,
    panels.exo_skel.SUB_UL_BoneList,
    panels.exo_skel.MakeCombinedSkeleton,
    panels.import_anim.ImportAnimPanel,
    panels.import_anim.AnimArmatureClearOperator,
    panels.import_anim.AnimCameraClearOperator,
    panels.import_anim.AnimModelImporterOperator,
    panels.import_anim.AnimCameraImporterOperator,
    panels.export_anim.ExportAnimPanel,
    panels.export_anim.AnimModelExporterOperator,
    panels.anim_properties.DATA_PT_sub_smush_anim_data_master,
    panels.anim_properties.DATA_PT_sub_smush_anim_data_vis_tracks,
    panels.anim_properties.DATA_PT_sub_smush_anim_data_mat_tracks,
    panels.anim_properties.SUB_UL_vis_track_entries,
    panels.anim_properties.VisTrackEntry,
    panels.anim_properties.MatTrackEntry,
    panels.anim_properties.MatTrack,
    panels.anim_properties.SubAnimProperties,
    panels.anim_properties.SUB_OP_vis_entry_add,
    panels.anim_properties.SUB_OP_vis_entry_remove,
    panels.anim_properties.SUB_OP_vis_drivers_refresh,
    panels.anim_properties.SUB_OP_vis_drivers_remove,
    panels.anim_properties.SUB_MT_vis_entry_context_menu
]

def register():
    print('Loading Smash Ultimate Blender Tools...')

    check_unsupported_blender_versions()

    for cls in classes:
        bpy.utils.register_class(cls)

    properties.register()
    shaders.custom_sampler_node.register()
    bpy.types.Armature.sub_anim_properties = bpy.props.PointerProperty(type=panels.anim_properties.SubAnimProperties)
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