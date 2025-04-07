bl_info = {
    'name': 'Smash Ultimate Blender Tools',
    'author': 'Carlos Aguilar, ScanMountGoat (SMG)',
    'category': 'Object',
    'location': 'View 3D > Tool Shelf > Ultimate',
    'description': 'A collection of tools for importing models and animations to smash ultimate.',
    'version': (3, 0, 3),
    'blender': (2, 80, 0),
    'warning': 'TO REMOVE: First "Disable" the plugin, then restart blender, then you can hit "Remove" to uninstall',
    'doc_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/wiki',
    'tracker_url': 'https://github.com/ssbucarlos/smash-ultimate-blender/issues',
    'special thanks': 'SMG for making SSBH_DATA_PY, which none of this would be possible without. and also the rokoko plugin for being the reference used to make the exo_skel UI'
}

def check_unsupported_blender_versions():
    import bpy
    if bpy.app.version < (2, 80):
        raise ImportError('Cant use a Blender version older than 2.80, please use 2.80 or newer')
    
def register():
    import bpy
    import nodeitems_utils
    print('Loading Smash Ultimate Blender Tools...')

    check_unsupported_blender_versions()

    from .source import blender_property_extensions, new_classes_to_register
    from .source.extras import set_linear_vertex_color
    from .source.model.material import shader_nodes
    from .source.blender_property_extensions import SubSceneProperties

    new_classes_to_register.register()

    blender_property_extensions.register()
    
    bpy.types.VIEW3D_MT_paint_vertex.append(set_linear_vertex_color.menu_func)

    nodeitems_utils.register_node_categories('CUSTOM_ULTIMATE_NODES', shader_nodes.node_categories.node_categories)
    
    # Register texture conversion tools
    from .source.model.material import texture
    texture.register()

    from .source.updater.version_check import check_for_newer_version
    check_for_newer_version()

    # Add sub_scene_properties to the Scene object
    if not hasattr(bpy.types.Scene, "sub_scene_properties"):
        bpy.types.Scene.sub_scene_properties = bpy.props.PointerProperty(type=SubSceneProperties)

    print('Loaded Smash Ultimate Blender Tools!')

def unregister():
    import bpy
    import nodeitems_utils
    print('Unloading Smash Ultimate Blender Tools...')

    from .source.extras import set_linear_vertex_color
    from .source import new_classes_to_register
    from .source.model.material import texture

    nodeitems_utils.unregister_node_categories('CUSTOM_ULTIMATE_NODES')
    
    # Unregister texture conversion tools
    texture.unregister()

    bpy.types.VIEW3D_MT_paint_vertex.remove(set_linear_vertex_color.menu_func)

    # Remove sub_scene_properties from the Scene object
    if hasattr(bpy.types.Scene, "sub_scene_properties"):
        del bpy.types.Scene.sub_scene_properties

    new_classes_to_register.unregister()

    print('Unloaded Smash Ultimate Blender Tools!')
            
if __name__ == '__main__':
    register()