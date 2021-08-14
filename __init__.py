bl_info = {
    'name': 'Smash Ultimate Blender',
    'author': 'Carlos Aguilar',
    'category': 'All',
    'location': 'View 3D > Tool Shelf > Ultimate',
    'description': 'A collection of tools for importing models and animations to smash ultimate.',
    'version': (0, 2, 0),
    'blender': (2, 91, 0),
    'special thanks': 'The rokoko plugin for being the reference used to make this UI'
}
import bpy, sys

from . import panels
from . import operators
from . import properties

def check_unsupported_blender_versions():
    if bpy.app.version < (2, 80):
        unregister()
        sys.tracebacklimit = 0 # TODO: research what this does
        raise ImportError('Cant use a Blender version older than 2.80, please use 2.80 or later')
         
classes = [
    panels.io_matl.MaterialPanel,
    panels.exo_skel.BuildBoneList,
    panels.exo_skel.RenameOtherBones,
    panels.exo_skel.VIEW3D_PT_ultimate_exo_skel,
    panels.exo_skel.BoneListItem,
    panels.exo_skel.SUB_UL_BoneList,
    panels.exo_skel.MakeCombinedSkeleton,
    panels.exo_skel.ExportHelperBoneJson,
    panels.exo_skel.ExportSkelJson,
    #panels.exo_skel.ExoSkelProperties,
]

def register():
    print('Loading Smash Ultimate Blender Tools...')

    check_unsupported_blender_versions()

    for cls in classes:
        bpy.utils.register_class(cls)

    properties.register()
    
    print('Loaded Smash Ultimate Blender Tools!')

def unregister():
    print('Unloading Smash Ultimate Blender Tools')

    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            print('So this runtime error happened when unregistering ')
            

if __name__ == '__main__':
    register()