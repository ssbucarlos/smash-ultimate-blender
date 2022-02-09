import os
import time
from .import_model import get_ssbh_lib_json_exe_path
import bpy
import os.path
import numpy as np
import numpy.linalg as la

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, Panel
import re
from .. import ssbh_data_py
import bmesh
import sys
import json
import subprocess
from mathutils import Vector, Matrix
import math

class ExportModelPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Model Exporter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        row = layout.row(align=True)
        row.label(text='Select an armature. The armature + its meshes will be exported')

        row = layout.row(align=True)
        row.prop(context.scene, 'sub_model_export_armature', icon='ARMATURE_DATA')

        if not context.scene.sub_model_export_armature:
            return
        
        if '' == context.scene.sub_vanilla_nusktb:
            row = layout.row(align=True)
            row.label(text='Please select the vanilla .nusktb for the exporter to reference!')
            row = layout.row(align=True)
            row.label(text='Impossible to accurately replace an existing ultimate fighter skeleton without it...')
            row = layout.row(align=True)
            row.label(text='If you know you really dont need to link it, then go ahead and skip this step and export...')
            row = layout.row(align=True)
            row.operator('sub.vanilla_nusktb_selector', icon='FILE', text='Select Vanilla Nusktb')
        else:
            row = layout.row(align=True)
            row.label(text='Selected reference .nusktb: ' + context.scene.sub_vanilla_nusktb)
            row = layout.row(align=True)
            row.operator('sub.vanilla_nusktb_selector', icon='FILE', text='Re-Select Vanilla Nusktb')

        row = layout.row(align=True)
        row.operator('sub.model_exporter', icon='EXPORT', text='Export Model Files to a Folder')
    
class VanillaNusktbSelector(Operator, ImportHelper):
    bl_idname = 'sub.vanilla_nusktb_selector'
    bl_label = 'Vanilla Nusktb Selector'

    filter_glob: StringProperty(
        default='*.nusktb',
        options={'HIDDEN'}
    )
    def execute(self, context):
        context.scene.sub_vanilla_nusktb = self.filepath
        return {'FINISHED'}   

class ModelExporterOperator(Operator, ImportHelper):
    bl_idname = 'sub.model_exporter'
    bl_label = 'Export To This Folder'

    filter_glob: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped. Also blender has this in the example but tbh idk what it does yet
    )

    include_numdlb: BoolProperty(
        name="Export .NUMDLB",
        description="Export .NUMDLB",
        default=True,
    )
    include_numshb: BoolProperty(
        name="Export .NUMSHB",
        description="Export .NUMSHB",
        default=True,
    )
    include_numshexb: BoolProperty(
        name="Export .NUMSHEXB",
        description="Export .NUMSHEXB",
        default=True,
    )
    include_nusktb: BoolProperty(
        name="Export .NUSKTB",
        description="Export .NUSKTB",
        default=True,
    )
    include_numatb: BoolProperty(
        name="Export .NUMATB",
        description="Export .NUMATB",
        default=True,
    )
    include_nuhlpb: BoolProperty(
        name="Export .NUHLPB",
        description="Export .NUHLPB",
        default=True,
    )

    linked_nusktb_settings: EnumProperty(
        name="Bone Linkage",
        description="Pick 'Order & Values' unless you intentionally edited the vanilla bones.",
        items=(
            ('ORDER_AND_VALUES', "Order & Values", "Pick this one unless u know not too"),
            ('ORDER_ONLY', "Order Only", "Pick this if you edited the vanilla bones"),
            ('NO_LINK', "No Link", "Pick this if you really know what ur doing"),
        ),
        default='ORDER_AND_VALUES',
    )
    
    def execute(self, context):
        export_model(context, self.filepath, self.include_numdlb, self.include_numshb, self.include_numshexb,
                     self.include_nusktb, self.include_numatb, self.include_nuhlpb, self.linked_nusktb_settings)
        return {'FINISHED'}

def export_model(context, filepath, include_numdlb, include_numshb, include_numshexb, include_nusktb, include_numatb, include_nuhlpb, linked_nusktb_settings):
    '''
    numdlb and numshb are inherently linked, must export both if exporting one
    if include_numdlb:
        export_numdlb(context, filepath)
    '''
    # The skel needs to be made first to determine the mesh's bone influences.
    ssbh_skel_data = None
    if '' == context.scene.sub_vanilla_nusktb or 'NO_LINK' == linked_nusktb_settings:
        ssbh_skel_data = make_skel_no_link(context)
    else:
        ssbh_skel_data = make_skel(context, linked_nusktb_settings)
    
    # Prepare the scene for export and find the meshes to export.
    arma = context.scene.sub_model_export_armature
    export_meshes = [child for child in arma.children if child.type == 'MESH']
    export_meshes = [m for m in export_meshes if len(m.data.vertices) > 0] # Skip Empty Objects
    export_meshes.sort(key=lambda mesh: mesh.get("numshb order", 10000))
    '''
    TODO: Investigate why export fails if meshes are selected before hitting export.
    '''
    for selected_object in context.selected_objects:
        selected_object.select_set(False)
    context.view_layer.objects.active = arma

    start = time.time()

    ssbh_modl_data, ssbh_mesh_data = make_modl_mesh_data(context, export_meshes, ssbh_skel_data)
    
    end = time.time()
    print(f'Created export files in {end - start} seconds')

    start = time.time()

    # TODO: Avoid creating files we don't plan on saving in this step.
    if include_numdlb:
        ssbh_modl_data.save(filepath + 'model.numdlb')
    if include_numshb:
        ssbh_mesh_data.save(filepath + 'model.numshb')
    if include_nusktb:
        ssbh_skel_data.save(filepath + 'model.nusktb')
    if include_numatb:
        create_and_save_matl(filepath, export_meshes)
    if include_numshexb:
        create_and_save_meshex(filepath, ssbh_mesh_data)
    if include_nuhlpb:
        create_and_save_nuhlpb(filepath, arma)

    end = time.time()
    print(f'Saved files in {end - start} seconds')


def create_and_save_meshex(filepath, ssbh_mesh_data):
    meshex = ssbh_data_py.meshex_data.MeshExData.from_mesh_objects(ssbh_mesh_data.objects)
    meshex.save(filepath + 'model.numshexb')


def create_and_save_matl(filepath, export_meshes):
    #  Gather Material Info
    materials = {mesh.data.materials[0] for mesh in export_meshes}
    ssbh_matl = make_matl(materials)

    ssbh_matl.save(filepath + 'model.numatb')


'''
def export_numdlb(context, filepath):
    arma = context.scene.sub_model_export_armature
    ssbh_model = ssbh_data_py.modl_data.ModlData()
    ssbh_model.model_name = 'model'
    ssbh_model.skeleton_file_name = 'model.nusktb'
    ssbh_model.material_file_names = ['model.numatb']
    ssbh_model.animation_file_name = None
'''
def get_material_label_from_mesh(mesh):
    material = mesh.material_slots[0].material
    nodes = material.node_tree.nodes
    node_group_node = nodes['smash_ultimate_shader']
    mat_label = node_group_node.inputs['Material Name'].default_value

    return mat_label

def find_bone_index(skel, name):
    for i, bone in enumerate(skel.bones):
        if bone.name == name:
            return i

    return None

def make_matl(materials):
    matl = ssbh_data_py.matl_data.MatlData()

    for material in materials:
        node = material.node_tree.nodes.get('smash_ultimate_shader', None)
        if node is None:
            raise RuntimeError(f'The material {material.name} does not have the smash ultimate shader, cannot export materials!')
        entry = ssbh_data_py.matl_data.MatlEntryData(node.inputs['Material Name'].default_value, node.inputs['Shader Label'].default_value)

        inputs = [input for input in node.inputs if input.hide == False]
        skip = ['Material Name', 'Shader Label']

        for input in inputs:
            name = input.name
            if name in skip:
                continue

            elif 'BlendState0 Field1 (Source Color)' == name:
                data = ssbh_data_py.matl_data.BlendStateData()                          
                data.source_color = ssbh_data_py.matl_data.BlendFactor.from_str(node.inputs['BlendState0 Field1 (Source Color)'].default_value)
                data.destination_color = ssbh_data_py.matl_data.BlendFactor.from_str(node.inputs['BlendState0 Field3 (Destination Color)'].default_value)
                data.alpha_sample_to_coverage = node.inputs['BlendState0 Field7 (Alpha to Coverage)'].default_value

                attribute = ssbh_data_py.matl_data.BlendStateParam(ssbh_data_py.matl_data.ParamId.BlendState0, data)
                entry.blend_states.append(attribute)
            elif 'RasterizerState0 Field1 (Polygon Fill)' == name:
                data = ssbh_data_py.matl_data.RasterizerStateData()
                data.fill_mode = ssbh_data_py.matl_data.FillMode.from_str(node.inputs['RasterizerState0 Field1 (Polygon Fill)'].default_value)
                data.cull_mode = ssbh_data_py.matl_data.CullMode.from_str(node.inputs['RasterizerState0 Field2 (Cull Mode)'].default_value)
                data.depth_bias = node.inputs['RasterizerState0 Field3 (Depth Bias)'].default_value

                attribute = ssbh_data_py.matl_data.RasterizerStateParam(ssbh_data_py.matl_data.ParamId.RasterizerState0, data)
                entry.rasterizer_states.append(attribute)
            elif 'Texture' in name.split(' ')[0] and 'RGB' in name.split(' ')[1]:
                texture_node = input.links[0].from_node

                texture_attribute = ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.from_str(name.split(' ')[0]), texture_node.label)
                entry.textures.append(texture_attribute)

                sampler_number = name.split(' ')[0].split('Texture')[1]
                sampler_param_id_text = f'Sampler{sampler_number}'

                # Sampler Data
                sampler_data = ssbh_data_py.matl_data.SamplerData()

                sampler_node = texture_node.inputs[0].links[0].from_node
                # TODO: These conversions may return None on error.
                sampler_data.wraps = ssbh_data_py.matl_data.WrapMode.from_str(sampler_node.wrap_s)
                sampler_data.wrapt = ssbh_data_py.matl_data.WrapMode.from_str(sampler_node.wrap_t)
                sampler_data.wrapr = ssbh_data_py.matl_data.WrapMode.from_str(sampler_node.wrap_r)
                sampler_data.min_filter = ssbh_data_py.matl_data.MinFilter.from_str(sampler_node.min_filter)
                sampler_data.mag_filter = ssbh_data_py.matl_data.MagFilter.from_str(sampler_node.mag_filter)
                sampler_data.border_color = sampler_node.border_color
                sampler_data.lod_bias = sampler_node.lod_bias
                print(sampler_node.anisotropic_filtering, sampler_node.max_anisotropy)
                sampler_data.max_anisotropy = ssbh_data_py.matl_data.MaxAnisotropy.from_str(sampler_node.max_anisotropy) if sampler_node.anisotropic_filtering else None
         
                sampler_attribute = ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.from_str(sampler_param_id_text), sampler_data)
                entry.samplers.append(sampler_attribute)
            elif 'Sampler' in name.split(' ')[0]:
                # Samplers are not thier own input in the master node, rather they are a seperate node entirely
                pass
            elif 'Boolean' in name.split(' ')[0]:
                attribute = ssbh_data_py.matl_data.BooleanParam(ssbh_data_py.matl_data.ParamId.from_str(name.split(' ')[0]), input.default_value)
                entry.booleans.append(attribute)
            elif 'Float' in name.split(' ')[0]:
                attribute = ssbh_data_py.matl_data.FloatParam(ssbh_data_py.matl_data.ParamId.from_str(name.split(' ')[0]), input.default_value)
                entry.floats.append(attribute)
            elif 'Vector' in name.split(' ')[0]:
                attribute = ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.from_str(name.split(' ')[0]), [0.0, 0.0, 0.0, 0.0])
                
                # TODO: Is there a simpler way to do this?
                # Im sorry
                # print(f'Name = {name}') # DEBUG
                if name == 'CustomVector0 X (Min Texture Alpha)':
                    attribute.data[0] = node.inputs['CustomVector0 X (Min Texture Alpha)'].default_value
                    attribute.data[1] = node.inputs['CustomVector0 Y (???)'].default_value
                    attribute.data[2] = node.inputs['CustomVector0 Z (???)'].default_value
                    attribute.data[3] = node.inputs['CustomVector0 W (???)'].default_value
                elif name == 'CustomVector1':
                    attribute.data[0] = node.inputs['CustomVector1'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector1'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector1'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector1'].default_value[3]
                elif name == 'CustomVector2':
                    attribute.data[0] = node.inputs['CustomVector2'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector2'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector2'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector2'].default_value[3]
                elif name == 'CustomVector3 (Emission Color Multiplier)':
                    attribute.data[0] = node.inputs['CustomVector3 (Emission Color Multiplier)'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector3 (Emission Color Multiplier)'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector3 (Emission Color Multiplier)'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector3 (Emission Color Multiplier)'].default_value[3]
                elif name == 'CustomVector4':
                    attribute.data[0] = node.inputs['CustomVector4'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector4'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector4'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector4'].default_value[3]
                elif name == 'CustomVector5':
                    attribute.data[0] = node.inputs['CustomVector5'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector5'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector5'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector5'].default_value[3]
                elif name == 'CustomVector6 X (UV Transform Layer 1)':
                    attribute.data[0] = node.inputs['CustomVector6 X (UV Transform Layer 1)'].default_value
                    attribute.data[1] = node.inputs['CustomVector6 Y (UV Transform Layer 1)'].default_value
                    attribute.data[2] = node.inputs['CustomVector6 Z (UV Transform Layer 1)'].default_value
                    attribute.data[3] = node.inputs['CustomVector6 W (UV Transform Layer 1)'].default_value
                elif name == 'CustomVector7':
                    attribute.data[0] = node.inputs['CustomVector7'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector7'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector7'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector7'].default_value[3]
                elif name == 'CustomVector8 (Final Color Multiplier)':
                    attribute.data[0] = node.inputs['CustomVector8 (Final Color Multiplier)'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector8 (Final Color Multiplier)'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector8 (Final Color Multiplier)'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector8 (Final Color Multiplier)'].default_value[3]
                elif name == 'CustomVector9':
                    attribute.data[0] = node.inputs['CustomVector9'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector9'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector9'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector9'].default_value[3]
                elif name == 'CustomVector10':
                    attribute.data[0] = node.inputs['CustomVector10'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector10'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector10'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector10'].default_value[3]
                elif name == 'CustomVector11 (Fake SSS Color)':
                    attribute.data[0] = node.inputs['CustomVector11 (Fake SSS Color)'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector11 (Fake SSS Color)'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector11 (Fake SSS Color)'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector11 (Fake SSS Color)'].default_value[3]
                elif name == 'CustomVector12':
                    attribute.data[0] = node.inputs['CustomVector12'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector12'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector12'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector12'].default_value[3]
                elif name == 'CustomVector13 (Diffuse Color Multiplier)':
                    attribute.data[0] = node.inputs['CustomVector13 (Diffuse Color Multiplier)'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector13 (Diffuse Color Multiplier)'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector13 (Diffuse Color Multiplier)'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector13 (Diffuse Color Multiplier)'].default_value[3]
                elif name == 'CustomVector14 RGB (Rim Lighting Color)':
                    attribute.data[0] = node.inputs['CustomVector14 RGB (Rim Lighting Color)'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector14 RGB (Rim Lighting Color)'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector14 RGB (Rim Lighting Color)'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector14 Alpha (Rim Lighting Blend Factor)'].default_value
                elif name == 'CustomVector15 RGB':
                    attribute.data[0] = node.inputs['CustomVector15 RGB'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector15 RGB'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector15 RGB'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector15 Alpha'].default_value
                elif name == 'CustomVector16':
                    attribute.data[0] = node.inputs['CustomVector16'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector16'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector16'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector16'].default_value[3]
                elif name == 'CustomVector17':
                    attribute.data[0] = node.inputs['CustomVector17'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector17'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector17'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector17'].default_value[3]
                elif name == 'CustomVector18 X (Sprite Sheet Column Count)':
                    attribute.data[0] = node.inputs['CustomVector18 X (Sprite Sheet Column Count)'].default_value
                    attribute.data[1] = node.inputs['CustomVector18 Y (Sprite Sheet Row Count)'].default_value
                    attribute.data[2] = node.inputs['CustomVector18 Z (Sprite Sheet Frames Per Sprite)'].default_value
                    attribute.data[3] = node.inputs['CustomVector18 W (Sprite Sheet Sprite Count)'].default_value
                elif name == 'CustomVector19':
                    attribute.data[0] = node.inputs['CustomVector19'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector19'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector19'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector19'].default_value[3]
                elif name == 'CustomVector20':
                    attribute.data[0] = node.inputs['CustomVector20'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector20'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector20'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector20'].default_value[3]
                elif name == 'CustomVector21':
                    attribute.data[0] = node.inputs['CustomVector21'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector21'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector21'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector21'].default_value[3]
                elif name == 'CustomVector22':
                    attribute.data[0] = node.inputs['CustomVector22'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector22'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector22'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector22'].default_value[3]
                elif name == 'CustomVector23':
                    attribute.data[0] = node.inputs['CustomVector23'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector23'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector23'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector23'].default_value[3]
                elif name == 'CustomVector24':
                    attribute.data[0] = node.inputs['CustomVector24'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector24'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector24'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector24'].default_value[3]
                elif name == 'CustomVector25':
                    attribute.data[0] = node.inputs['CustomVector25'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector25'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector25'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector25'].default_value[3]
                elif name == 'CustomVector26':
                    attribute.data[0] = node.inputs['CustomVector26'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector26'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector26'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector26'].default_value[3]
                elif name == 'CustomVector27 (Controls Distant Fog, X = Intensity)':
                    attribute.data[0] = node.inputs['CustomVector27 (Controls Distant Fog, X = Intensity)'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector27 (Controls Distant Fog, X = Intensity)'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector27 (Controls Distant Fog, X = Intensity)'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector27 (Controls Distant Fog, X = Intensity)'].default_value[3]
                elif name == 'CustomVector28':
                    attribute.data[0] = node.inputs['CustomVector28'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector28'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector28'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector28'].default_value[3]
                elif name == 'CustomVector29':
                    attribute.data[0] = node.inputs['CustomVector29'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector29'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector29'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector29'].default_value[3]
                elif name == 'CustomVector30 X (SSS Blend Factor)':
                    attribute.data[0] = node.inputs['CustomVector30 X (SSS Blend Factor)'].default_value
                    attribute.data[1] = node.inputs['CustomVector30 Y (SSS Diffuse Shading Smooth Factor)'].default_value
                    attribute.data[2] = node.inputs['CustomVector30 Z (Unused)'].default_value
                    attribute.data[3] = node.inputs['CustomVector30 W (Unused)'].default_value
                elif name == 'CustomVector31 X (UV Transform Layer 2)':
                    attribute.data[0] = node.inputs['CustomVector31 X (UV Transform Layer 2)'].default_value
                    attribute.data[1] = node.inputs['CustomVector31 Y (UV Transform Layer 2)'].default_value
                    attribute.data[2] = node.inputs['CustomVector31 Z (UV Transform Layer 2)'].default_value
                    attribute.data[3] = node.inputs['CustomVector31 W (UV Transform Layer 2)'].default_value
                elif name == 'CustomVector32 X (UV Transform Layer 3)':
                    attribute.data[0] = node.inputs['CustomVector32 X (UV Transform Layer 3)'].default_value
                    attribute.data[1] = node.inputs['CustomVector32 Y (UV Transform Layer 3)'].default_value
                    attribute.data[2] = node.inputs['CustomVector32 Z (UV Transform Layer 3)'].default_value
                    attribute.data[3] = node.inputs['CustomVector32 W (UV Transform Layer 3)'].default_value
                elif name == 'CustomVector33 X (UV Transform ?)':
                    attribute.data[0] = node.inputs['CustomVector33 X (UV Transform ?)'].default_value
                    attribute.data[1] = node.inputs['CustomVector33 Y (UV Transform ?)'].default_value
                    attribute.data[2] = node.inputs['CustomVector33 Z (UV Transform ?)'].default_value
                    attribute.data[3] = node.inputs['CustomVector33 W (UV Transform ?)'].default_value
                elif name == 'CustomVector34 X (UV Transform ?)':
                    attribute.data[0] = node.inputs['CustomVector34 X (UV Transform ?)'].default_value
                    attribute.data[1] = node.inputs['CustomVector34 Y (UV Transform ?)'].default_value
                    attribute.data[2] = node.inputs['CustomVector34 Z (UV Transform ?)'].default_value
                    attribute.data[3] = node.inputs['CustomVector34 W (UV Transform ?)'].default_value
                elif name == 'CustomVector35':
                    attribute.data[0] = node.inputs['CustomVector35'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector35'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector35'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector35'].default_value[3]
                elif name == 'CustomVector36':
                    attribute.data[0] = node.inputs['CustomVector36'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector36'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector36'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector36'].default_value[3]
                elif name == 'CustomVector37':
                    attribute.data[0] = node.inputs['CustomVector37'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector37'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector37'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector37'].default_value[3]
                elif name == 'CustomVector38':
                    attribute.data[0] = node.inputs['CustomVector38'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector38'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector38'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector38'].default_value[3]
                elif name == 'CustomVector39':
                    attribute.data[0] = node.inputs['CustomVector39'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector39'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector39'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector39'].default_value[3]
                elif name == 'CustomVector40':
                    attribute.data[0] = node.inputs['CustomVector40'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector40'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector40'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector40'].default_value[3]
                elif name == 'CustomVector41':
                    attribute.data[0] = node.inputs['CustomVector41'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector41'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector41'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector41'].default_value[3]
                elif name == 'CustomVector42':
                    attribute.data[0] = node.inputs['CustomVector42'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector42'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector42'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector42'].default_value[3]
                elif name == 'CustomVector43':
                    attribute.data[0] = node.inputs['CustomVector43'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector43'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector43'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector43'].default_value[3]
                elif name == 'CustomVector44':
                    attribute.data[0] = node.inputs['CustomVector44'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector44'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector44'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector44'].default_value[3]
                elif name == 'CustomVector45':
                    attribute.data[0] = node.inputs['CustomVector45'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector45'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector45'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector45'].default_value[3]
                elif name == 'CustomVector46':
                    attribute.data[0] = node.inputs['CustomVector46'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector46'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector46'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector46'].default_value[3]
                elif name == 'CustomVector47 RGB':
                    attribute.data[0] = node.inputs['CustomVector47 RGB'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector47 RGB'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector47 RGB'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector47 Alpha'].default_value
                elif name == 'CustomVector48':
                    attribute.data[0] = node.inputs['CustomVector48'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector48'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector48'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector48'].default_value[3]
                elif name == 'CustomVector49':
                    attribute.data[0] = node.inputs['CustomVector49'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector49'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector49'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector49'].default_value[3]
                elif name == 'CustomVector50':
                    attribute.data[0] = node.inputs['CustomVector50'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector50'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector50'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector50'].default_value[3]
                elif name == 'CustomVector51':
                    attribute.data[0] = node.inputs['CustomVector51'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector51'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector51'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector51'].default_value[3]
                elif name == 'CustomVector52':
                    attribute.data[0] = node.inputs['CustomVector52'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector52'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector52'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector52'].default_value[3]
                elif name == 'CustomVector53':
                    attribute.data[0] = node.inputs['CustomVector53'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector53'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector53'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector53'].default_value[3]
                elif name == 'CustomVector54':
                    attribute.data[0] = node.inputs['CustomVector54'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector54'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector54'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector54'].default_value[3]
                elif name == 'CustomVector55':
                    attribute.data[0] = node.inputs['CustomVector55'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector55'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector55'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector55'].default_value[3]
                elif name == 'CustomVector56':
                    attribute.data[0] = node.inputs['CustomVector56'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector56'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector56'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector56'].default_value[3]
                elif name == 'CustomVector57':
                    attribute.data[0] = node.inputs['CustomVector57'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector57'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector57'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector57'].default_value[3]
                elif name == 'CustomVector58':
                    attribute.data[0] = node.inputs['CustomVector58'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector58'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector58'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector58'].default_value[3]
                elif name == 'CustomVector59':
                    attribute.data[0] = node.inputs['CustomVector59'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector59'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector59'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector59'].default_value[3]
                elif name == 'CustomVector60':
                    attribute.data[0] = node.inputs['CustomVector60'].default_value[0]
                    attribute.data[1] = node.inputs['CustomVector60'].default_value[1]
                    attribute.data[2] = node.inputs['CustomVector60'].default_value[2]
                    attribute.data[3] = node.inputs['CustomVector60'].default_value[3]
                else:
                    continue
                entry.vectors.append(attribute)
            else:
                continue
        
        matl.entries.append(entry)

    return matl


def per_loop_to_per_vertex(per_loop, vertex_indices, dim):
    # Consider the following per loop data.
    # index, value
    # 0, 1
    # 1, 3
    # 0, 1
    
    # This generates the following per vertex data.
    # vertex, value
    # 0, 1
    # 1, 3

    # Convert from 1D per loop to 2D per vertex using numpy indexing magic.
    _, cols = dim
    per_vertex = np.zeros(dim, dtype=np.float32)
    per_vertex[vertex_indices] = per_loop.reshape((-1, cols))
    return per_vertex


def make_modl_mesh_data(context, export_meshes, ssbh_skel_data):

    ssbh_mesh_data = ssbh_data_py.mesh_data.MeshData()
    ssbh_modl_data = ssbh_data_py.modl_data.ModlData()

    ssbh_modl_data.model_name = 'model'
    ssbh_modl_data.skeleton_file_name = 'model.nusktb'
    ssbh_modl_data.material_file_names = ['model.numatb']
    ssbh_modl_data.animation_file_name = None
    ssbh_modl_data.mesh_file_name = 'model.numshb'


    '''
    # TODO split meshes
    Potential uv_layer clean_up code?
    remove = [uv_layer for uv_layer in mesh.data.uv_layers if all([uv == 0.0 for data in uv_layer.data for uv in data.uv])]
    for l in remove:
        mesh.data.uv_layers.remove(l)
    '''

    # Gather true names for NUMSHEXB
    true_names = {re.split('Shape|_VIS_|_O_', mesh.name)[0] for mesh in export_meshes}
    true_name_to_meshes = {true_name : [mesh for mesh in export_meshes if true_name == re.split('Shape|_VIS_|_O_', mesh.name)[0]] for true_name in true_names}
    true_name_to_meshes = {k:v for k,v in sorted(true_name_to_meshes.items(), key = lambda item: item[1][0].get("numshb order", 10000))}

    pruned_mesh_name_list = []
    for mesh in [mesh for mesh_list in true_name_to_meshes.values() for mesh in mesh_list]:
        '''
        Need to Make a copy of the mesh, split by material, apply transforms, and validate for potential errors.

        list of potential issues that need to validate
        1.) Shape Keys 2.) Negative Scaling 3.) Invalid Materials 4.) Degenerate Geometry
        '''
        mesh_object_copy = mesh.copy() # Copy the Mesh Object
        mesh_object_copy.data = mesh.data.copy() # Make a copy of the mesh DATA, so that the original remains unmodified
        mesh_data_copy = mesh_object_copy.data 
        # Undo the Matrix axis correction that was done on import
        # TODO: Is there a way to apply transforms that works as expected without using bpy.ops
        context.collection.objects.link(mesh_object_copy)
        context.view_layer.update()
        context.view_layer.objects.active = mesh_object_copy
        mesh_object_copy.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        axis_correction = Matrix.Rotation(math.radians(-90), 4, 'X')  
        mesh_object_copy.matrix_world = mesh_object_copy.matrix_world @ axis_correction
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        pruned_mesh_name = re.split(r'.\d\d\d', mesh.name)[0] # Un-uniquify the names

        # Quick Detour to file out MODL stuff
        ssbh_mesh_object_sub_index = pruned_mesh_name_list.count(pruned_mesh_name)
        pruned_mesh_name_list.append(pruned_mesh_name)
        mat_label = get_material_label_from_mesh(mesh)
        ssbh_modl_entry = ssbh_data_py.modl_data.ModlEntryData(pruned_mesh_name, ssbh_mesh_object_sub_index, mat_label)
        ssbh_modl_data.entries.append(ssbh_modl_entry)

        # Back to MESH stuff
        # ssbh_data_py accepts lists, tuples, or numpy arrays for AttributeData.data.
        # foreach_get and foreach_set provide substantially faster access to property collections in Blender.
        # https://devtalk.blender.org/t/alternative-in-2-80-to-create-meshes-from-python-using-the-tessfaces-api/7445/3
        ssbh_mesh_object = ssbh_data_py.mesh_data.MeshObjectData(pruned_mesh_name, ssbh_mesh_object_sub_index)
        position0 = ssbh_data_py.mesh_data.AttributeData('Position0')
        # For example, vertices is a bpy_prop_collection of MeshVertex, which has a "co" attribute for position.
        positions = np.zeros(len(mesh_data_copy.vertices) * 3, dtype=np.float32)
        mesh_data_copy.vertices.foreach_get("co", positions)
        # The output data is flattened, so we need to reshape it into the appropriate number of rows and columns.
        position0.data = positions.reshape((-1, 3))
        ssbh_mesh_object.positions = [position0]

        # Store vertex indices as a numpy array for faster indexing later.
        vertex_indices = np.zeros(len(mesh_data_copy.loops), dtype=np.uint32)
        mesh_data_copy.loops.foreach_get("vertex_index", vertex_indices)
        ssbh_mesh_object.vertex_indices = vertex_indices

        # We use the loop normals rather than vertex normals to allow exporting custom normals.
        mesh_object_copy.data.calc_normals_split()

        # Export Normals
        normal0 = ssbh_data_py.mesh_data.AttributeData('Normal0')
        loop_normals = np.zeros(len(mesh_object_copy.data.loops) * 3, dtype=np.float32)
        mesh_object_copy.data.loops.foreach_get("normal", loop_normals)
        normals = per_loop_to_per_vertex(loop_normals, vertex_indices, (len(mesh_object_copy.data.vertices), 3))

        # Pad normals to 4 components instead of 3 components.
        # This actually results in smaller file sizes since HalFloat4 is smaller than Float3.
        normals = np.append(normals, np.zeros((normals.shape[0],1)), axis=1)
        
        normal0.data = normals
        ssbh_mesh_object.normals = [normal0]

        # Export Weights
        # TODO: Research weight layers       
        # Reversing a vertex -> group lookup to a group -> vertex lookup is expensive.
        # TODO: Does Blender not expose this directly?
        group_to_weights = { vg.index : (vg.name, []) for vg in mesh_object_copy.vertex_groups }
        for vertex in mesh_data_copy.vertices:
            for group in vertex.groups:
                ssbh_vertex_weight = ssbh_data_py.mesh_data.VertexWeight(vertex.index, group.weight)
                group_to_weights[group.group][1].append(ssbh_vertex_weight)
        
        # Keep track of the skel's bone names to avoid adding influences for nonexistant bones.
        skel_bone_names = set([bone.name for bone in ssbh_skel_data.bones])
        BoneInfluence = ssbh_data_py.mesh_data.BoneInfluence
        if len([wieghts for index, (name, wieghts) in group_to_weights.items() if len(wieghts) > 0]) == 0:
            print(f'Found Mesh with no wieghts {mesh.name}, not assigning bone_influences')
        else:
            ssbh_mesh_object.bone_influences = [BoneInfluence(name, weights) for name, weights in group_to_weights.values() if name in skel_bone_names]

        '''
        The uv layer data is actually empty for the active object in edit mode
        '''
        #bpy.ops.object.mode_set(mode='EDIT')

        for uv_layer in mesh_object_copy.data.uv_layers:
            ssbh_uv_layer = ssbh_data_py.mesh_data.AttributeData(uv_layer.name)
            loop_uvs = np.zeros(len(mesh_object_copy.data.loops) * 2, dtype=np.float32)
            uv_layer.data.foreach_get("uv", loop_uvs)
            
            uvs = per_loop_to_per_vertex(loop_uvs, vertex_indices, (len(mesh_object_copy.data.vertices), 2))
            # Flip vertical.
            uvs[:,1] = 1.0 - uvs[:,1]
            ssbh_uv_layer.data = uvs

            ssbh_mesh_object.texture_coordinates.append(ssbh_uv_layer)

        # Export Color Set 
        for color_layer in mesh_object_copy.data.vertex_colors:
            ssbh_color_layer = ssbh_data_py.mesh_data.AttributeData(color_layer.name)

            loop_colors = np.zeros(len(mesh_object_copy.data.loops) * 4, dtype=np.float32)
            color_layer.data.foreach_get("color", loop_colors)
            ssbh_color_layer.data = per_loop_to_per_vertex(loop_colors, vertex_indices, (len(mesh_object_copy.data.vertices), 4))

            ssbh_mesh_object.color_sets.append(ssbh_color_layer)


        # Calculate tangents now that the necessary attributes are initialized.
        # TODO: It's possible to generate tangents for other UV maps by passing in the appropriate UV data.
        tangent0 = ssbh_data_py.mesh_data.AttributeData('Tangent0')
        tangent0.data = ssbh_data_py.mesh_data.calculate_tangents_vec4(ssbh_mesh_object.positions[0].data, 
            ssbh_mesh_object.normals[0].data, 
            ssbh_mesh_object.texture_coordinates[0].data,
            ssbh_mesh_object.vertex_indices)
        ssbh_mesh_object.tangents = [tangent0]
        
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.data.meshes.remove(mesh_data_copy)
        ssbh_mesh_data.objects.append(ssbh_mesh_object)

    return ssbh_modl_data, ssbh_mesh_data

def unreorient_matrix(reoriented_matrix) -> Matrix:
    c00,c01,c02,c03 = reoriented_matrix[0]
    c10,c11,c12,c13 = reoriented_matrix[1]
    c20,c21,c22,c23 = reoriented_matrix[2]
    c30,c31,c32,c33 = reoriented_matrix[3]
    matrix_unreordered = Matrix([
        [c11, -c10, c12, c13],
        [ -c01, c00, -c02, -c03],
        [ c21, -c20, c22, c23],
        [ c30, c31, c32, c33]
    ])
    matrix_unreoriented = matrix_unreordered.transposed()
    return matrix_unreoriented

def unreorient_root(reoriented_matrix) -> Matrix:
    m = Matrix([
        [ 1.0, 0.0, 0.0, 0.0],
        [ 0.0, 1.0, 0.0, 0.0],
        [ 0.0, 0.0, 1.0, 0.0],
        [ 0.0, 0.0, 0.0, 1.0]
    ])
    return m


def make_skel_no_link(context):
    arma = context.scene.sub_model_export_armature
    bpy.context.view_layer.objects.active = arma
    arma.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    ssbh_skel = ssbh_data_py.skel_data.SkelData()
    edit_bones = arma.data.edit_bones
    edit_bones_list = list(edit_bones)
    for edit_bone in edit_bones_list:
        #if edit_bone.use_deform == False: # Need a way to not export user created control bones
            #continue
        ssbh_bone = None
        if edit_bone.parent is not None:
            unreoriented_matrix = unreorient_matrix(edit_bone.parent.matrix.inverted() @ edit_bone.matrix)
            ssbh_bone = ssbh_data_py.skel_data.BoneData(edit_bone.name, unreoriented_matrix, edit_bones_list.index(edit_bone.parent))
        else:
            ssbh_bone = ssbh_data_py.skel_data.BoneData(edit_bone.name, unreorient_root(edit_bone.matrix), None)
        ssbh_skel.bones.append(ssbh_bone) 

    #ssbh_skel.save(filepath + 'model.nusktb')

    bpy.ops.object.mode_set(mode='OBJECT')
    arma.select_set(False)
    bpy.context.view_layer.objects.active = None
    return ssbh_skel

def make_skel(context, linked_nusktb_settings):
    '''
    Wow i wrote this terribly lol, #TODO ReWrite this
    '''
    arma = context.scene.sub_model_export_armature
    bpy.context.view_layer.objects.active = arma
    arma.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    
    normal_bones = []
    swing_bones = []
    misc_bones = []
    null_bones = []
    helper_bones = []

    output_bones = {}
    eb = arma.data.edit_bones
    keys = eb.keys()
    for key in keys:
        if 'S_' in key:
            swing_bones.append(eb[key])
        elif any(ss in key for ss in ['_eff', '_offset'] ):
            null_bones.append(eb[key])
        elif 'H_' in key:
            helper_bones.append(eb[key])
        elif any(ss in key for ss in ['Mouth', 'Finger', 'Face']) or key == 'Have':
            misc_bones.append(eb[key])
            for child in eb[key].children_recursive:
                if any(ss in child.name for ss in ['_eff', '_offset']):
                    continue
                misc_bones.append(child)
                keys.remove(child.name)
        else:
            normal_bones.append(eb[key])
            
    for boneList in [normal_bones, swing_bones, misc_bones, null_bones, helper_bones]:
        for bone in boneList:
            #if bone.use_deform == False:
                #continue
            output_bones[bone.name] = bone
    
    ssbh_skel = ssbh_data_py.skel_data.SkelData()
 
    if '' != context.scene.sub_vanilla_nusktb:
        reordered_bones = []
        vanilla_ssbh_skel = ssbh_data_py.skel_data.read_skel(context.scene.sub_vanilla_nusktb)
        for vanilla_ssbh_bone in vanilla_ssbh_skel.bones:
            linked_bone = output_bones.get(vanilla_ssbh_bone.name)
            if linked_bone is None:
                continue
            reordered_bones.append(linked_bone)
            del output_bones[linked_bone.name]
        
        for remaining_bone in output_bones.values():
            reordered_bones.append(remaining_bone)
        
        ssbh_bone_name_to_bone_dict = {}
        for ssbh_bone in vanilla_ssbh_skel.bones:
            ssbh_bone_name_to_bone_dict[ssbh_bone.name] = ssbh_bone
        
        index = 0 # Debug
        print(f'Reordered Bones = {reordered_bones} \n')
        for blender_bone in reordered_bones:
            ssbh_bone = None
            if 'ORDER_AND_VALUES' == linked_nusktb_settings:
                vanilla_ssbh_bone = ssbh_bone_name_to_bone_dict.get(blender_bone.name)
                if vanilla_ssbh_bone is not None:
                    #print('O&V Link Found: index %s, transform= %s' % (index, vanilla_ssbh_bone.transform))
                    index = index + 1
                    ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, vanilla_ssbh_bone.transform, reordered_bones.index(blender_bone.parent) if blender_bone.parent else None)
                else:
                    if blender_bone.parent:
                        unreoriented_matrix = unreorient_matrix(blender_bone.parent.matrix.inverted() @ blender_bone.matrix)
                        ssbh_bone = ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, unreoriented_matrix, reordered_bones.index(blender_bone.parent))
                        #print(f'O&V No Link Found: index {index}, name {blender_bone.name}, rel_mat.transposed()= {rel_mat.transposed()}')
                        index = index + 1
                    else:
                        ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, unreorient_root(blender_bone.matrix), None)
            else:
                if blender_bone.parent:
                    '''
                    blender_bone_matrix_as_list = [list(row) for row in blender_bone.matrix.transposed()]
                    blender_bone_parent_matrix_as_list = [list(row) for row in blender_bone.parent.matrix.transposed()]
                    rel_transform = ssbh_data_py.skel_data.calculate_relative_transform(blender_bone_matrix_as_list, blender_bone_parent_matrix_as_list)
                    ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, rel_transform, reordered_bones.index(blender_bone.parent))
                    '''
                    unreoriented_matrix = unreorient_matrix(blender_bone.parent.matrix.inverted() @ blender_bone.matrix)
                    ssbh_bone = ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, unreoriented_matrix, reordered_bones.index(blender_bone.parent))
                    #print('OO: index %s, name %s, rel_mat.transposed()= %s' % (index, blender_bone.name, rel_mat.transposed()))
                    index = index + 1
                else:
                    ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, unreorient_root(blender_bone.matrix), None)
            ssbh_skel.bones.append(ssbh_bone)    

    #ssbh_skel.save(filepath + 'model.nusktb')

    bpy.ops.object.mode_set(mode='OBJECT')
    arma.select_set(False)
    bpy.context.view_layer.objects.active = None
    return ssbh_skel



# TODO: This will eventually be replaced by ssbh_data_py.
def bounding_sphere(objects):
    # A fast to compute bounding sphere that will contain all points.
    # We don't need an optimal solution for visibility tests and depth sorting.
    # Create a single numpy array for better performance.
    vertex_count = sum([len(obj.data.vertices) for obj in objects])
    positions_world_all = np.ones((vertex_count, 4))

    offset = 0
    for obj in objects:
        count = len(obj.data.vertices)

        positions = np.zeros(count * 3, dtype=np.float32)
        obj.data.vertices.foreach_get("co", positions)
        # TODO: Find a more elegant way to account for world position.
        positions_world_all[offset:offset+count,:3] = positions.reshape((-1,3)) 
        positions_world_all[offset:offset+count,:] = positions_world_all[offset:offset+count,:] @ obj.matrix_world

        offset += count

    center = positions_world_all[:,:3].mean(axis=0)
    radius = np.max(la.norm(positions_world_all[:,:3] - center, 2, axis=1))
    return center, radius

def save_ssbh_json(ssbh_json, output_file_path):
    ssbh_lib_json_exe_path = get_ssbh_lib_json_exe_path()
    dumped_json_file_path = output_file_path + '.tmp.json'
    with open(dumped_json_file_path, 'w') as f:
        json.dump(ssbh_json, f, indent=2)
    subprocess.run([ssbh_lib_json_exe_path, dumped_json_file_path, output_file_path])
    #os.remove(dumped_json_file_path)
    return

def create_and_save_nuhlpb(filepath, armature:bpy.types.Object):
    root_empty = None
    for child in armature.children:
        if child.name.startswith('_NUHLPB') and child.type == 'EMPTY':
            root_empty = child
            break
    
    if root_empty is None:
        return
    
    aim_entries_empty, interpolation_entries_empty = None, None
    for child in root_empty.children:
        if child.name.startswith('aim_entries'):
            aim_entries_empty = child
        elif child.name.startswith('interpolation_entries'):
            interpolation_entries_empty = child
    
    if aim_entries_empty is None or interpolation_entries_empty is None:
        print(f'Selected armature had the _NUHLPB empty but not the aim_entries_empty or interpolation_entries_empty!')
        return
    
    nuhlpb_json = {}
    nuhlpb_json['data'] = {}
    nuhlpb_json['data']['Hlpb'] = {}
    nuhlpb_json['data']['Hlpb']['major_version'] = root_empty['major_version']
    nuhlpb_json['data']['Hlpb']['minor_version'] = root_empty['minor_version']
    
    nuhlpb_json['data']['Hlpb']['aim_entries'] = []
    nuhlpb_json['data']['Hlpb']['interpolation_entries'] = []
    nuhlpb_json['data']['Hlpb']['list1'] = []
    nuhlpb_json['data']['Hlpb']['list2'] = []

    for index, aim_entry_empty in enumerate(aim_entries_empty.children):
        aim_entry = {}
        aim_entry['name'] = aim_entry_empty.name
        aim_entry['aim_bone_name1'] = aim_entry_empty['aim_bone_name1']
        aim_entry['aim_bone_name2'] = aim_entry_empty['aim_bone_name2']
        aim_entry['aim_type1'] = aim_entry_empty['aim_type1']
        aim_entry['aim_type2'] = aim_entry_empty['aim_type2']
        aim_entry['target_bone_name1'] = aim_entry_empty['target_bone_name1']
        aim_entry['target_bone_name2'] = aim_entry_empty['target_bone_name2']
        for unk_index in range(1, 22+1):
            aim_entry[f'unk{unk_index}'] = aim_entry_empty[f'unk{unk_index}']
        nuhlpb_json['data']['Hlpb']['aim_entries'].append(aim_entry)
        nuhlpb_json['data']['Hlpb']['list1'].append(index)
        nuhlpb_json['data']['Hlpb']['list2'].append(0)

    for index, interpolation_entry_empty in enumerate(interpolation_entries_empty.children):
        interpolation_entry = {}
        interpolation_entry['name'] = interpolation_entry_empty.name
        interpolation_entry['bone_name'] = interpolation_entry_empty['bone_name']
        interpolation_entry['root_bone_name'] = interpolation_entry_empty['root_bone_name']
        interpolation_entry['parent_bone_name'] = interpolation_entry_empty['parent_bone_name']
        interpolation_entry['driver_bone_name'] = interpolation_entry_empty['driver_bone_name']
        interpolation_entry['unk_type'] = interpolation_entry_empty['unk_type']
        interpolation_entry['aoi'] = {}
        interpolation_entry['aoi']['x'] = interpolation_entry_empty['aoi'][0]
        interpolation_entry['aoi']['y'] = interpolation_entry_empty['aoi'][1]
        interpolation_entry['aoi']['z'] = interpolation_entry_empty['aoi'][2]
        interpolation_entry['quat1'] = {}
        interpolation_entry['quat1']['x'] = interpolation_entry_empty['quat1'][0]
        interpolation_entry['quat1']['y'] = interpolation_entry_empty['quat1'][1]
        interpolation_entry['quat1']['z'] = interpolation_entry_empty['quat1'][2]
        interpolation_entry['quat1']['w'] = interpolation_entry_empty['quat1'][3]
        interpolation_entry['quat2'] = {}
        interpolation_entry['quat2']['x'] = interpolation_entry_empty['quat1'][0]
        interpolation_entry['quat2']['y'] = interpolation_entry_empty['quat1'][1]
        interpolation_entry['quat2']['z'] = interpolation_entry_empty['quat1'][2]
        interpolation_entry['quat2']['w'] = interpolation_entry_empty['quat1'][3]
        interpolation_entry['range_min'] = {}
        interpolation_entry['range_min']['x'] = interpolation_entry_empty['range_min'][0]
        interpolation_entry['range_min']['y'] = interpolation_entry_empty['range_min'][1] 
        interpolation_entry['range_min']['z'] = interpolation_entry_empty['range_min'][2]
        interpolation_entry['range_max'] = {}
        interpolation_entry['range_max']['x'] = interpolation_entry_empty['range_max'][0]
        interpolation_entry['range_max']['y'] = interpolation_entry_empty['range_max'][1] 
        interpolation_entry['range_max']['z'] = interpolation_entry_empty['range_max'][2]
        nuhlpb_json['data']['Hlpb']['interpolation_entries'].append(interpolation_entry)
        nuhlpb_json['data']['Hlpb']['list1'].append(index)
        nuhlpb_json['data']['Hlpb']['list2'].append(1)

    save_ssbh_json(nuhlpb_json, filepath + 'model.nuhlpb')


    



