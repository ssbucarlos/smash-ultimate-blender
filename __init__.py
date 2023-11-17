bl_info = {
    'name': 'Smash Ultimate Blender',
    'author': 'Carlos Aguilar, ScanMountGoat (SMG)',
    'category': 'All',
    'location': 'View 3D > Tool Shelf > Ultimate',
    'description': 'A collection of tools for importing models and animations to smash ultimate.',
    'version': (0, 10, 0),
    'blender': (3, 3, 0),
    'warning': 'TO REMOVE: First "Disable" the plugin, then restart blender, then you can hit "Remove" to uninstall',
    'doc_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/wiki',
    'tracker_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/issues',
    'special thanks': 'SMG for making SSBH_DATA_PY, which none of this would be possible without. and also the rokoko plugin for being the reference used to make this UI'
}

import bpy
import sys
import traceback
import nodeitems_utils

def check_unsupported_blender_versions():
    if bpy.app.version < (3, 3):
        #sys.tracebacklimit = 0 # TODO: research what this does
        raise ImportError('Cant use a Blender version older than 3.3, please use 3.3 or later')

def register():
    print('Loading Smash Ultimate Blender Tools...')

    check_unsupported_blender_versions()
    
    from . import modules
    from . import operators
    from . import properties
    from . import shader_nodes
    from . import properties
    
    from .bpy_classes import classes
    for cls in classes:
        bpy.utils.register_class(cls)

    properties.register()
    
    nodeitems_utils.register_node_categories('CUSTOM_ULTIMATE_NODES', shader_nodes.node_categories.node_categories)

    print('Loaded Smash Ultimate Blender Tools!')

def unregister():
    print('Unloading Smash Ultimate Blender Tools')

    from . import modules
    from . import operators
    from . import properties
    from . import shader_nodes
    from . import properties

    nodeitems_utils.unregister_node_categories('CUSTOM_ULTIMATE_NODES')

    from .bpy_classes import classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f'Failed to unregister smash_ultimate_blender; Error="{e}" ; Traceback=\n{traceback.format_exc()}')
            
if __name__ == '__main__':
    register()