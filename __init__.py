bl_info = {
    'name': 'Smash Ultimate Blender',
    'author': 'Carlos Aguilar, ScanMountGoat (SMG)',
    'category': 'All',
    'location': 'View 3D > Tool Shelf > Ultimate',
    'description': 'A collection of tools for importing models and animations to smash ultimate.',
    'version': (3, 0, 0),
    'blender': (4, 2, 0),
    'warning': 'TO REMOVE: First "Disable" the plugin, then restart blender, then you can hit "Remove" to uninstall',
    'doc_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/wiki',
    'tracker_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/issues',
    'special thanks': 'SMG for making SSBH_DATA_PY, which none of this would be possible without. and also the rokoko plugin for being the reference used to make the exo_skel UI'
}

def check_unsupported_blender_versions():
    import bpy
    if bpy.app.version < (4, 2):
        raise ImportError('Cant use a Blender version older than 4.2, please use 4.1 or newer')
    
def register():
    import bpy
    import nodeitems_utils
    print('Loading Smash Ultimate Blender Tools...')

    check_unsupported_blender_versions()

    from .source import blender_property_extensions, new_classes_to_register
    from .source.extras import set_linear_vertex_color
    from .source.model.material import shader_nodes

    new_classes_to_register.register()

    blender_property_extensions.register()
    
    bpy.types.VIEW3D_MT_paint_vertex.append(set_linear_vertex_color.menu_func)

    nodeitems_utils.register_node_categories('CUSTOM_ULTIMATE_NODES', shader_nodes.node_categories.node_categories)

    from .source.updater.version_check import check_for_newer_version
    check_for_newer_version()

    print('Loaded Smash Ultimate Blender Tools!')

def unregister():
    import bpy
    import nodeitems_utils
    print('Unloading Smash Ultimate Blender Tools...')

    from .source.extras import set_linear_vertex_color
    from .source import new_classes_to_register

    nodeitems_utils.unregister_node_categories('CUSTOM_ULTIMATE_NODES')

    bpy.types.VIEW3D_MT_paint_vertex.remove(set_linear_vertex_color.menu_func)

    new_classes_to_register.unregister()

    print('Unloaded Smash Ultimate Blender Tools!')
            
if __name__ == '__main__':
    register()