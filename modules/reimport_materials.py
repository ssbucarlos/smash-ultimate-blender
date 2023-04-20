import bpy
import re
import os
from pathlib import Path
from bpy.types import Panel, Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty
from .. import ssbh_data_py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..properties import SubSceneProperties

class SUB_PT_reimport_materials(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Ultimate'
    bl_label = 'Material Re-Importer'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        layout = self.layout
        layout.use_property_split = False

        row = layout.row(align=True)
        row.label(text='Select an Armature')
        row = layout.row(align=True)
        row.prop(ssp, 'material_reimport_arma', icon='ARMATURE_DATA')
        if not ssp.material_reimport_arma:
            return
        if '' == ssp.material_reimport_folder:
            row = layout.row(align=True)
            row.operator('sub.mat_reimport_dir_selector', icon='ZOOM_ALL', text='Select folder w/ .NUMATB & textures')
        else:
            row = layout.row(align=True)
            row.label(text=f'Textures Folder= "{ssp.material_reimport_folder}"')
            if '' == ssp.material_reimport_numatb_path:
                row = layout.row(align=True)
                row.alert = True
                row.label(text='No .numatb file found!', icon='ERROR')
            else:
                row = layout.row(align=True)
                row.label(text=f'.numatb file: "{Path(ssp.material_reimport_numatb_path).name}"', icon='FILE')
                row = layout.row(align=True)
                row.operator('sub.mat_reimport_numatb_selector', icon='ZOOM_ALL', text='Re-select .numatb')
                row = layout.row(align=True)
            row = layout.row(align=True)
            row.operator('sub.mat_reimport_dir_selector', icon='ZOOM_ALL', text='Re-Select folder')
            row = layout.row(align=True)
            row.operator('sub.reimport_materials', icon='IMPORT', text='Re-Import materials')

class SUB_OP_mat_reimport_directory_selector(Operator):
    bl_idname = 'sub.mat_reimport_dir_selector'
    bl_label = 'Confirm folder'

    filter_glob: StringProperty(
        default='*.numatb; *.png',
        options={'HIDDEN'}
    )
    directory: StringProperty(
        subtype="DIR_PATH"
    )

    def invoke(self, context, _event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        ssp.material_reimport_folder = self.directory
        numatb_files = {f for f in os.listdir(ssp.material_reimport_folder) if f.endswith('.numatb')}
        if len(numatb_files) == 0:
            ssp.material_reimport_numatb_path = ''
        elif len(numatb_files) == 1:
            ssp.material_reimport_numatb_path = os.path.join(ssp.material_reimport_folder, numatb_files.pop())
        else:
            if {'model.numatb'} & numatb_files:
                ssp.material_reimport_numatb_path = os.path.join(ssp.material_reimport_folder, 'model.numatb')
            else:
                ssp.material_reimport_numatb_path = os.path.join(ssp.material_reimport_folder, numatb_files.pop())
        return {'FINISHED'}   

class SUB_OP_mat_reimport_numatb_selector(Operator):
    bl_idname = 'sub.mat_reimport_numatb_selector'
    bl_label = 'Confirm .numatb'

    filter_glob: StringProperty(
        default='*.numatb;',
        options={'HIDDEN'}
    )
    filepath: StringProperty(
        subtype="FILE_PATH"
    )
    def invoke(self, context, _event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        context.scene.sub_scene_properties.material_reimport_numatb_path = self.filepath
        return {'FINISHED'}   

class SUB_OP_reimport_materials(Operator):
    bl_idname = 'sub.reimport_materials'
    bl_label = 'Reimport Materials'

    @classmethod
    def poll(cls, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        return ssp.material_reimport_numatb_path != '' and ssp.material_reimport_folder != ''

    def execute(self, context):
        reimport_materials(self, context)
        return {'FINISHED'}

def reimport_materials(operator: Operator, context):
    from .material.create_blender_materials_from_matl import create_blender_materials_from_matl
    from .export_model import would_trimmed_names_be_unique, trim_name, get_problematic_names

    ssp: SubSceneProperties = context.scene.sub_scene_properties
    arma: bpy.types.Object = ssp.material_reimport_arma 
    mesh_objects: set[bpy.types.Object] = {child for child in arma.children if child.type == 'MESH'}
    materials: set[bpy.types.Material] = {material_slot.material for mesh_object in mesh_objects for material_slot in mesh_object.material_slots}
    material_names: set[str] = {material.name for material in materials}
    if not would_trimmed_names_be_unique(material_names):
        problematic_names = get_problematic_names(material_names)
        for problematic_name in problematic_names:
            message = f'The material name of "{problematic_name}" is not a unique name after trimming! Cannot reimport Materials! (Trimmed name is "{trim_name(problematic_name)}")'
            operator.report({'WARNING'}, message)
        return
    
    ssbh_matl = ssbh_data_py.matl_data.read_matl(str(ssp.material_reimport_numatb_path))
    material_label_to_material = create_blender_materials_from_matl(operator, ssbh_matl)
    for mesh_object in mesh_objects:
        for material_slot in mesh_object.material_slots:
            new_material = material_label_to_material.get(trim_name(material_slot.material.name))
            if new_material is not None:
                material_slot.material = new_material

    
