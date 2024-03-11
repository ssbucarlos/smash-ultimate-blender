bl_info = {
    'name': 'Smash Ultimate Blender',
    'author': 'Carlos Aguilar, ScanMountGoat (SMG)',
    'category': 'All',
    'location': 'View 3D > Tool Shelf > Ultimate',
    'description': 'A collection of tools for importing models and animations to smash ultimate.',
    'version': (1, 3, 2),
    'blender': (4, 0, 0),
    'warning': 'TO REMOVE: First "Disable" the plugin, then restart blender, then you can hit "Remove" to uninstall',
    'doc_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/wiki',
    'tracker_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/issues',
    'special thanks': 'SMG for making SSBH_DATA_PY, which none of this would be possible without. and also the rokoko plugin for being the reference used to make this UI'
}

import inspect
import sys
import traceback

import bpy
import nodeitems_utils

from .source import blender_property_extensions, new_classes_to_register
from .source.extras import set_linear_vertex_color
from .source.model.material import shader_nodes

def check_unsupported_blender_versions():
    if bpy.app.version < (4, 0):
        raise ImportError('Cant use a Blender version older than 4.0, please use 4.0 or newer')

def get_bpy_derived_classes():
    bpy_derived_classes = set()
    for _name, obj in inspect.getmembers(sys.modules[__name__]):
        if not inspect.isclass(obj):
            continue
        if not obj.__module__ == __name__:
            continue
        if not issubclass(obj, bpy.types.bpy_struct):
            continue
        bpy_derived_classes.add(obj)
    return bpy_derived_classes

def register():
    print('Loading Smash Ultimate Blender Tools...')

    check_unsupported_blender_versions()

    new_classes_to_register.register()

    blender_property_extensions.register()
    
    bpy.types.VIEW3D_MT_paint_vertex.append(set_linear_vertex_color.menu_func)

    nodeitems_utils.register_node_categories('CUSTOM_ULTIMATE_NODES', shader_nodes.node_categories.node_categories)

    from .source.updater.version_check import check_for_newer_version
    check_for_newer_version()

    print('Loaded Smash Ultimate Blender Tools!')

def unregister():
    print('Unloading Smash Ultimate Blender Tools')

    nodeitems_utils.unregister_node_categories('CUSTOM_ULTIMATE_NODES')

    bpy.types.VIEW3D_MT_paint_vertex.remove(set_linear_vertex_color.menu_func)

    from .source.new_classes_to_register import classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f'Failed to unregister smash_ultimate_blender; Error="{e}" ; Traceback=\n{traceback.format_exc()}')
            
if __name__ == '__main__':
    register()