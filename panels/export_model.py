import os
from .import_model import get_color_scale, get_ssbh_lib_json_exe_path
import bpy
import os.path

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, Panel
import re
from ..ssbh_data_py import ssbh_data_py
import bmesh
import sys
import json
import subprocess
from mathutils import Vector

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
                     self.include_nusktb, self.include_numatb, self.linked_nusktb_settings)
        return {'FINISHED'}

def export_model(context, filepath, include_numdlb, include_numshb, include_numshexb, include_nusktb, include_numatb, linked_nusktb_settings):
    '''
    numdlb and numshb are inherently linked, must export both if exporting one
    if include_numdlb:
        export_numdlb(context, filepath)
    '''
    ssbh_skel_data = None
    if '' == context.scene.sub_vanilla_nusktb or 'NO_LINK' == linked_nusktb_settings:
        ssbh_skel_data = make_skel_no_link(context)
    else:
        ssbh_skel_data = make_skel(context, linked_nusktb_settings)
    
    ssbh_modl_data = None
    ssbh_mesh_data = None
    ssbh_matl_json = None
    ssbh_modl_data, ssbh_mesh_data, ssbh_matl_json, ssbh_numshexb_json = make_modl_mesh_matl_data(context, ssbh_skel_data, filepath)

    if include_numdlb:
        ssbh_modl_data.save(filepath + 'model.numdlb')
    if include_numshb:
        ssbh_mesh_data.save(filepath + 'model.numshb')
    if include_nusktb:
        ssbh_skel_data.save(filepath + 'model.nusktb')
    if include_numatb:
        save_ssbh_json(ssbh_matl_json, filepath + 'model.numatb')
    if include_numshexb:
        save_ssbh_json(ssbh_numshexb_json, filepath + 'model.numshexb')

def save_ssbh_json(ssbh_json, output_file_path):
    ssbh_lib_json_exe_path = get_ssbh_lib_json_exe_path()
    dumped_json_file_path = output_file_path + '.tmp.json'
    with open(dumped_json_file_path, 'w') as f:
        json.dump(ssbh_json, f, indent=2)
    subprocess.run([ssbh_lib_json_exe_path, dumped_json_file_path, output_file_path])
    os.remove(dumped_json_file_path)
    return

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

def make_matl_json(materials):
    matl_json = {}
    matl_json['data'] = {}
    matl_json['data']['Matl'] = {}
    matl_json['data']['Matl']['major_version'] = 1
    matl_json['data']['Matl']['minor_version'] = 6
    matl_json['data']['Matl']['entries'] = []
    entries = matl_json['data']['Matl']['entries']

    for material in materials:
        node = material.node_tree.nodes.get('smash_ultimate_shader', None)
        if node is None:
            raise RuntimeError(f'The material {material.name} does not have the smash ultimate shader, cannot export materials!')
        entry = {}
        entry['material_label'] = node.inputs['Material Name'].default_value
        entry['attributes'] = {}
        entry['attributes']['Attributes16'] = []
        attributes16 = entry['attributes']['Attributes16']
        inputs = [input for input in node.inputs if input.hide == False]
        skip = ['Material Name', 'Shader Label']

        for input in inputs:
            attribute = {}
            name = input.name
            if name in skip:
                continue
            elif 'BlendState0 Field1 (Source Color)' == name:
                attribute['param_id'] = 'BlendState0'
                attribute['param'] = {}
                attribute['param']['data'] = {}
                attribute['param']['data']['BlendState'] = {}
                attribute['param']['data']['BlendState']['source_color'] = node.inputs['BlendState0 Field1 (Source Color)'].default_value
                attribute['param']['data']['BlendState']['unk2'] = node.inputs['BlendState0 Field2 (Unk2)'].default_value
                attribute['param']['data']['BlendState']['destination_color'] = node.inputs['BlendState0 Field3 (Destination Color)'].default_value
                attribute['param']['data']['BlendState']['unk4'] = node.inputs['BlendState0 Field4 (Unk4)'].default_value
                attribute['param']['data']['BlendState']['unk5'] = node.inputs['BlendState0 Field5 (Unk5)'].default_value
                attribute['param']['data']['BlendState']['unk6'] = node.inputs['BlendState0 Field6 (Unk6)'].default_value
                attribute['param']['data']['BlendState']['unk7'] = node.inputs['BlendState0 Field7 (Alpha to Coverage)'].default_value
                attribute['param']['data']['BlendState']['unk8'] = node.inputs['BlendState0 Field8 (Unk8)'].default_value
                attribute['param']['data']['BlendState']['unk9'] = node.inputs['BlendState0 Field9 (Unk9)'].default_value
                attribute['param']['data']['BlendState']['unk10'] = node.inputs['BlendState0 Field10 (Unk10)'].default_value
                attribute['param']['data_type'] = 17
                
            elif 'RasterizerState0 Field1 (Polygon Fill)' == name:
                attribute['param_id'] = 'RasterizerState0'
                attribute['param'] = {}
                attribute['param']['data'] = {}
                attribute['param']['data']['RasterizerState'] = {}
                attribute['param']['data']['RasterizerState']['fill_mode'] = 'Line' if node.inputs['RasterizerState0 Field1 (Polygon Fill)'].default_value == 0 else 'Solid'
                attribute['param']['data']['RasterizerState']['cull_mode'] = 'Back' if node.inputs['RasterizerState0 Field2 (Cull Mode)'].default_value == 0 else\
                                                                             'Front' if node.inputs['RasterizerState0 Field2 (Cull Mode)'].default_value == 1 else\
                                                                             'FrontAndBack'  
                attribute['param']['data']['RasterizerState']['depth_bias'] = node.inputs['RasterizerState0 Field3 (Depth Bias)'].default_value
                attribute['param']['data']['RasterizerState']['unk4'] = node.inputs['RasterizerState0 Field4 (Unk4)'].default_value
                attribute['param']['data']['RasterizerState']['unk5'] = node.inputs['RasterizerState0 Field5 (Unk5)'].default_value
                attribute['param']['data']['RasterizerState']['unk6'] = node.inputs['RasterizerState0 Field6 (Unk6)'].default_value
                attribute['param']['data_type'] = 18

            elif 'Texture' in name.split(' ')[0] and 'RGB' in name.split(' ')[1]:
                sampler_number = name.split(' ')[0].split('Texture')[1]
                texture_and_number = name.split(' ')[0]
                attribute['param_id'] = texture_and_number
                attribute['param'] = {}
                attribute['param']['data'] = {}
                texture_node = input.links[0].from_node
                texture_name = texture_node.label
                attribute['param']['data']['MatlString'] = texture_name
                attribute['param']['data_type'] = 11
                # Sampler Data
                sampler_node = texture_node.inputs[0].links[0].from_node
                sampler_attribute = {}
                sampler_attribute['param_id'] = f'Sampler{sampler_number}'
                sampler_attribute['param'] = {}
                sampler_attribute['param']['data'] = {}
                sampler_attribute['param']['data']['Sampler'] = {}
                sampler_attribute['param']['data']['Sampler']['wraps'] = 'Repeat' if sampler_node.wrap_s == 'REPEAT' else\
                                                                         'ClampToBorder' if sampler_node.wrap_s == 'CLAMP_TO_BORDER' else\
                                                                         'ClampToEdge' if sampler_node.wrap_s == 'CLAMP_TO_EDGE' else\
                                                                         'MirroredRepeat'
                sampler_attribute['param']['data']['Sampler']['wrapt'] = 'Repeat' if sampler_node.wrap_t == 'REPEAT' else\
                                                                         'ClampToBorder' if sampler_node.wrap_t == 'CLAMP_TO_BORDER' else\
                                                                         'ClampToEdge' if sampler_node.wrap_t == 'CLAMP_TO_EDGE' else\
                                                                         'MirroredRepeat'
                sampler_attribute['param']['data']['Sampler']['wrapr'] = 'Repeat' if sampler_node.wrap_r == 'REPEAT' else\
                                                                         'ClampToBorder' if sampler_node.wrap_r == 'CLAMP_TO_BORDER' else\
                                                                         'ClampToEdge' if sampler_node.wrap_r == 'CLAMP_TO_EDGE' else\
                                                                         'MirroredRepeat'
                sampler_attribute['param']['data']['Sampler']['min_filter'] = 'Nearest' if sampler_node.min_filter == 'NEAREST' else\
                                                                              'LinearMipmapLinear' if sampler_node.min_filter == 'LINEAR_MIPMAP_LINEAR' else\
                                                                              'LinearMipmapLinear2'
                sampler_attribute['param']['data']['Sampler']['mag_filter'] = 'Nearest' if sampler_node.mag_filter == 'NEAREST' else\
                                                                              'Linear' if sampler_node.mag_filter == 'LINEAR' else\
                                                                              'Linear2'
                sampler_attribute['param']['data']['Sampler']['texture_filtering_type'] = 'AnisotropicFiltering' if sampler_node.texture_filter == 'ANISOTROPIC_FILTERING' else\
                                                                                          'Default' if sampler_node.texture_filter == 'DEFAULT' else\
                                                                                          'Default2'
                sampler_attribute['param']['data']['Sampler']['border_color'] = {}
                sampler_attribute['param']['data']['Sampler']['border_color']['r'] = sampler_node.border_color[0]
                sampler_attribute['param']['data']['Sampler']['border_color']['g'] = sampler_node.border_color[1]
                sampler_attribute['param']['data']['Sampler']['border_color']['b'] = sampler_node.border_color[2]
                sampler_attribute['param']['data']['Sampler']['border_color']['a'] = sampler_node.border_color[3]
                sampler_attribute['param']['data']['Sampler']['unk11'] = sampler_node.unk11
                sampler_attribute['param']['data']['Sampler']['unk12'] = sampler_node.unk12
                sampler_attribute['param']['data']['Sampler']['lod_bias'] = sampler_node.lod_bias
                sampler_attribute['param']['data']['Sampler']['max_anisotropy'] = 0 if sampler_node.max_anisotropy == '1X' else\
                                                                                  2 if sampler_node.max_anisotropy == '2X' else\
                                                                                  4 if sampler_node.max_anisotropy == '4X' else\
                                                                                  8 if sampler_node.max_anisotropy == '16X' else\
                                                                                  16
                                                                               
                sampler_attribute['param']['data_type'] = 14
                attributes16.append(sampler_attribute)

            elif 'Sampler' in name.split(' ')[0]:
                # Samplers are not thier own input in the master node, rather they are a seperate node entirely
                pass
            elif 'Boolean' in name.split(' ')[0]:
                attribute['param_id'] = name.split(' ')[0]
                attribute['param'] = {}
                attribute['param']['data'] = {}
                attribute['param']['data']['Boolean'] = 1 if input.default_value == True else 0
                attribute['param']['data_type'] = 2
                
            elif 'Float' in name.split(' ')[0]:
                attribute['param_id'] = name.split(' ')[0]
                attribute['param'] = {}
                attribute['param']['data'] = {}
                attribute['param']['data']['Float'] = input.default_value
                attribute['param']['data_type'] = 1

            elif 'Vector' in name.split(' ')[0]:
                attribute['param_id'] = name.split(' ')[0]
                attribute['param'] = {}
                attribute['param']['data'] = {}
                attribute['param']['data']['Vector4'] = {}
                attribute['param']['data_type'] = 5
                # Im sorry
                print(f'Name = {name}') # DEBUG
                if name == 'CustomVector0 X (Min Texture Alpha)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector0 X (Min Texture Alpha)'].default_value
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector0 Y (???)'].default_value
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector0 Z (???)'].default_value
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector0 W (???)'].default_value
                elif name == 'CustomVector1':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector1'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector1'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector1'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector1'].default_value[3]
                elif name == 'CustomVector2':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector2'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector2'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector2'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector2'].default_value[3]
                elif name == 'CustomVector3 (Emission Color Multiplier)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector3 (Emission Color Multiplier)'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector3 (Emission Color Multiplier)'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector3 (Emission Color Multiplier)'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector3 (Emission Color Multiplier)'].default_value[3]
                elif name == 'CustomVector4':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector4'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector4'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector4'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector4'].default_value[3]
                elif name == 'CustomVector5':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector5'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector5'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector5'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector5'].default_value[3]
                elif name == 'CustomVector6 X (UV Transform Layer 1)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector6 X (UV Transform Layer 1)'].default_value
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector6 Y (UV Transform Layer 1)'].default_value
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector6 Z (UV Transform Layer 1)'].default_value
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector6 W (UV Transform Layer 1)'].default_value
                elif name == 'CustomVector7':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector7'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector7'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector7'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector7'].default_value[3]
                elif name == 'CustomVector8 (Final Color Multiplier)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector8 (Final Color Multiplier)'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector8 (Final Color Multiplier)'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector8 (Final Color Multiplier)'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector8 (Final Color Multiplier)'].default_value[3]
                elif name == 'CustomVector9':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector9'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector9'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector9'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector9'].default_value[3]
                elif name == 'CustomVector10':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector10'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector10'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector10'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector10'].default_value[3]
                elif name == 'CustomVector11 (Fake SSS Color)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector11 (Fake SSS Color)'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector11 (Fake SSS Color)'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector11 (Fake SSS Color)'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector11 (Fake SSS Color)'].default_value[3]
                elif name == 'CustomVector12':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector12'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector12'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector12'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector12'].default_value[3]
                elif name == 'CustomVector13 (Diffuse Color Multiplier)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector13 (Diffuse Color Multiplier)'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector13 (Diffuse Color Multiplier)'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector13 (Diffuse Color Multiplier)'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector13 (Diffuse Color Multiplier)'].default_value[3]
                elif name == 'CustomVector14 RGB (Rim Lighting Color)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector14 RGB (Rim Lighting Color)'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector14 RGB (Rim Lighting Color)'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector14 RGB (Rim Lighting Color)'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector14 Alpha (Rim Lighting Blend Factor)'].default_value
                elif name == 'CustomVector15 RGB':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector15 RGB'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector15 RGB'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector15 RGB'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector15 Alpha'].default_value
                elif name == 'CustomVector16':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector16'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector16'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector16'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector16'].default_value[3]
                elif name == 'CustomVector17':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector17'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector17'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector17'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector17'].default_value[3]
                elif name == 'CustomVector18 X (Sprite Sheet Column Count)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector18 X (Sprite Sheet Column Count)'].default_value
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector18 Y (Sprite Sheet Row Count)'].default_value
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector18 Z (Sprite Sheet Frames Per Sprite)'].default_value
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector18 W (Sprite Sheet Sprite Count)'].default_value
                elif name == 'CustomVector19':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector19'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector19'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector19'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector19'].default_value[3]
                elif name == 'CustomVector20':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector20'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector20'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector20'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector20'].default_value[3]
                elif name == 'CustomVector21':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector21'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector21'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector21'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector21'].default_value[3]
                elif name == 'CustomVector22':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector22'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector22'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector22'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector22'].default_value[3]
                elif name == 'CustomVector23':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector23'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector23'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector23'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector23'].default_value[3]
                elif name == 'CustomVector24':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector24'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector24'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector24'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector24'].default_value[3]
                elif name == 'CustomVector25':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector25'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector25'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector25'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector25'].default_value[3]
                elif name == 'CustomVector26':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector26'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector26'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector26'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector26'].default_value[3]
                elif name == 'CustomVector27 (Controls Distant Fog, X = Intensity)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector27 (Controls Distant Fog, X = Intensity)'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector27 (Controls Distant Fog, X = Intensity)'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector27 (Controls Distant Fog, X = Intensity)'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector27 (Controls Distant Fog, X = Intensity)'].default_value[3]
                elif name == 'CustomVector28':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector28'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector28'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector28'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector28'].default_value[3]
                elif name == 'CustomVector29':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector29'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector29'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector29'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector29'].default_value[3]
                elif name == 'CustomVector30 X (SSS Blend Factor)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector30 X (SSS Blend Factor)'].default_value
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector30 Y (SSS Diffuse Shading Smooth Factor)'].default_value
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector30 Z (Unused)'].default_value
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector30 W (Unused)'].default_value
                elif name == 'CustomVector31 X (UV Transform Layer 2)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector31 X (UV Transform Layer 2)'].default_value
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector31 Y (UV Transform Layer 2)'].default_value
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector31 Z (UV Transform Layer 2)'].default_value
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector31 W (UV Transform Layer 2)'].default_value
                elif name == 'CustomVector32 X (UV Transform Layer 3)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector32 X (UV Transform Layer 3)'].default_value
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector32 Y (UV Transform Layer 3)'].default_value
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector32 Z (UV Transform Layer 3)'].default_value
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector32 W (UV Transform Layer 3)'].default_value
                elif name == 'CustomVector33 X (UV Transform ?)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector33 X (UV Transform ?)'].default_value
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector33 Y (UV Transform ?)'].default_value
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector33 Z (UV Transform ?)'].default_value
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector33 W (UV Transform ?)'].default_value
                elif name == 'CustomVector34 X (UV Transform ?)':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector34 X (UV Transform ?)'].default_value
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector34 Y (UV Transform ?)'].default_value
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector34 Z (UV Transform ?)'].default_value
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector34 W (UV Transform ?)'].default_value
                elif name == 'CustomVector35':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector35'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector35'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector35'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector35'].default_value[3]
                elif name == 'CustomVector36':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector36'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector36'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector36'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector36'].default_value[3]
                elif name == 'CustomVector37':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector37'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector37'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector37'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector37'].default_value[3]
                elif name == 'CustomVector38':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector38'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector38'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector38'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector38'].default_value[3]
                elif name == 'CustomVector39':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector39'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector39'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector39'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector39'].default_value[3]
                elif name == 'CustomVector40':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector40'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector40'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector40'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector40'].default_value[3]
                elif name == 'CustomVector41':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector41'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector41'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector41'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector41'].default_value[3]
                elif name == 'CustomVector42':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector42'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector42'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector42'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector42'].default_value[3]
                elif name == 'CustomVector43':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector43'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector43'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector43'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector43'].default_value[3]
                elif name == 'CustomVector44':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector44'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector44'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector44'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector44'].default_value[3]
                elif name == 'CustomVector45':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector45'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector45'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector45'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector45'].default_value[3]
                elif name == 'CustomVector46':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector46'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector46'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector46'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector46'].default_value[3]
                elif name == 'CustomVector47 RGB':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector47 RGB'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector47 RGB'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector47 RGB'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector47 Alpha'].default_value
                elif name == 'CustomVector48':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector48'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector48'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector48'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector48'].default_value[3]
                elif name == 'CustomVector49':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector49'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector49'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector49'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector49'].default_value[3]
                elif name == 'CustomVector50':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector50'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector50'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector50'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector50'].default_value[3]
                elif name == 'CustomVector51':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector51'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector51'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector51'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector51'].default_value[3]
                elif name == 'CustomVector52':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector52'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector52'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector52'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector52'].default_value[3]
                elif name == 'CustomVector53':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector53'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector53'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector53'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector53'].default_value[3]
                elif name == 'CustomVector54':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector54'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector54'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector54'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector54'].default_value[3]
                elif name == 'CustomVector55':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector55'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector55'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector55'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector55'].default_value[3]
                elif name == 'CustomVector56':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector56'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector56'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector56'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector56'].default_value[3]
                elif name == 'CustomVector57':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector57'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector57'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector57'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector57'].default_value[3]
                elif name == 'CustomVector58':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector58'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector58'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector58'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector58'].default_value[3]
                elif name == 'CustomVector59':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector59'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector59'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector59'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector59'].default_value[3]
                elif name == 'CustomVector60':
                    attribute['param']['data']['Vector4']['x'] = node.inputs['CustomVector60'].default_value[0]
                    attribute['param']['data']['Vector4']['y'] = node.inputs['CustomVector60'].default_value[1]
                    attribute['param']['data']['Vector4']['z'] = node.inputs['CustomVector60'].default_value[2]
                    attribute['param']['data']['Vector4']['w'] = node.inputs['CustomVector60'].default_value[3]
                else:
                    continue
            else:
                continue
            attributes16.append(attribute)
        
        entry['shader_label'] = node.inputs['Shader Label'].default_value
        entries.append(entry)
    return matl_json

def make_numshexb_json(true_name_to_meshes, temp_file_path):
    numshexb_json = {}
    numshexb_json['file_length'] = 0 # Will fill this in later
    numshexb_json['entry_count'] = len([mesh for mesh_list in true_name_to_meshes.values() for mesh in mesh_list])
    numshexb_json['mesh_object_group_count'] = len(true_name_to_meshes.keys())
    numshexb_json['all_data'] = []
    
    all_data = numshexb_json['all_data']
    all_data_entry = {}
    all_data_entry['bounding_sphere'] = {}
    all_sphere_vector, all_sphere_radius = bounding_sphere([mesh for mesh_list in true_name_to_meshes.values() for mesh in mesh_list], mode='GEOMETRY')
    all_data_entry['bounding_sphere']['x'] = all_sphere_vector[0]
    all_data_entry['bounding_sphere']['y'] = all_sphere_vector[1]
    all_data_entry['bounding_sphere']['z'] = all_sphere_vector[2]
    all_data_entry['bounding_sphere']['w'] = all_sphere_radius
    all_data_entry['name'] = []
    all_data_entry['name'].append('All')
    all_data_entry['name'].append(None)
    all_data.append(all_data_entry)
    all_data.append(None)
    
    numshexb_json['mesh_object_group'] = []
    mesh_object_group = numshexb_json['mesh_object_group']
    mesh_object_group_entry = [] 
    for true_name in true_name_to_meshes.keys():
        true_name_entry = {}
        full_name = re.split(r'.\d\d\d',true_name_to_meshes[true_name][0].name)[0]
        group_sphere_vector, group_sphere_radius = bounding_sphere(true_name_to_meshes[true_name], mode='GEOMETRY')
        true_name_entry['bounding_sphere'] = {}
        true_name_entry['bounding_sphere']['x'] = group_sphere_vector[0]
        true_name_entry['bounding_sphere']['y'] = group_sphere_vector[1]
        true_name_entry['bounding_sphere']['z'] = group_sphere_vector[2]
        true_name_entry['bounding_sphere']['w'] = group_sphere_radius
        true_name_entry['mesh_object_full_name'] = []
        true_name_entry['mesh_object_full_name'].append(full_name)
        true_name_entry['mesh_object_full_name'].append(None)
        true_name_entry['mesh_object_name'] = []
        true_name_entry['mesh_object_name'].append(true_name)
        true_name_entry['mesh_object_name'].append(None)
        mesh_object_group_entry.append(true_name_entry)
    mesh_object_group.append(mesh_object_group_entry)
    mesh_object_group.append(None)
    
    numshexb_json['entries'] = []
    entries = numshexb_json['entries']
    entries_array = []
    numshexb_json['entry_flags'] = []
    entry_flags = numshexb_json['entry_flags']
    entry_flags_array = []
    for index, (true_name, mesh_list) in enumerate(true_name_to_meshes.items()):
        for mesh in mesh_list:
            entries_array_entry = {}
            entries_array_entry['mesh_object_index'] = index
            entries_array_entry['unk1'] = {}
            entries_array_entry['unk1']['x'] = 0.0
            entries_array_entry['unk1']['y'] = 1.0
            entries_array_entry['unk1']['z'] = 0.0
            entries_array.append(entries_array_entry)
            entry_flags_array_entry = {}
            entry_flags_array_entry['bytes'] = []
            entry_flags_array_entry['bytes'].append(3) # if mesh[numshexb_flags] == 3 or something
            entry_flags_array_entry['bytes'].append(0)
            entry_flags_array.append(entry_flags_array_entry)

    entries.append(entries_array)
    entries.append(None)

    entry_flags.append(entry_flags_array)
    entry_flags.append(None)
    
    # Calculate filesize by first saving the JSON and then getting its filesize and then resending out the JSON
    temp_file_name = temp_file_path + 'tempfile.numshexb'
    save_ssbh_json(numshexb_json, temp_file_name)
    numshexb_json['file_length'] = os.path.getsize(temp_file_name)
    os.remove(temp_file_name)
    return numshexb_json

def make_modl_mesh_matl_data(context, ssbh_skel_data, temp_file_path):

    ssbh_mesh_data = ssbh_data_py.mesh_data.MeshData()
    ssbh_modl_data = ssbh_data_py.modl_data.ModlData()
    ssbh_matl_json = None
    ssbh_numshexb_json = None

    ssbh_modl_data.model_name = 'model'
    ssbh_modl_data.skeleton_file_name = 'model.nusktb'
    ssbh_modl_data.material_file_names = ['model.numatb']
    ssbh_modl_data.animation_file_name = None
    ssbh_modl_data.mesh_file_name = 'model.numshb'

    arma = context.scene.sub_model_export_armature
    export_meshes = [child for child in arma.children if child.type == 'MESH']
    export_meshes = [m for m in export_meshes if len(m.data.vertices) > 0] # Skip Empty Objects

    '''
    # TODO split meshes
    Potential uv_layer clean_up code?
    remove = [uv_layer for uv_layer in mesh.data.uv_layers if all([uv == 0.0 for data in uv_layer.data for uv in data.uv])]
    for l in remove:
        mesh.data.uv_layers.remove(l)
    '''
    #  Gather Material Info
    materials = {mesh.data.materials[0] for mesh in export_meshes}
    ssbh_matl_json = make_matl_json(materials)

    # Gather true names for NUMSHEXB
    true_names = {re.split('Shape|_VIS_|_O_', mesh.name)[0] for mesh in export_meshes}
    true_name_to_meshes = {true_name : [mesh for mesh in export_meshes if true_name == re.split('Shape|_VIS_|_O_', mesh.name)[0]] for true_name in true_names}
    
    # Make NUMMSHEXB
    ssbh_numshexb_json = make_numshexb_json(true_name_to_meshes, temp_file_path)

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
        #mesh_data_copy = mesh.data.copy()
        #mesh_object_copy = bpy.data.objects.new(mesh.name, mesh_data_copy)
        pruned_mesh_name = re.split(r'.\d\d\d', mesh.name)[0] # Un-uniquify the names

        # Quick Detour to file out MODL stuff
        ssbh_mesh_object_sub_index = pruned_mesh_name_list.count(pruned_mesh_name)
        pruned_mesh_name_list.append(pruned_mesh_name)
        mat_label = get_material_label_from_mesh(mesh)
        ssbh_modl_entry = ssbh_data_py.modl_data.ModlEntryData(pruned_mesh_name, ssbh_mesh_object_sub_index, mat_label)
        ssbh_modl_data.entries.append(ssbh_modl_entry)

        # Back to MESH stuff
        ssbh_mesh_object = ssbh_data_py.mesh_data.MeshObjectData(pruned_mesh_name, ssbh_mesh_object_sub_index)
        position0 = ssbh_data_py.mesh_data.AttributeData('Position0')
        position0.data = [list(vertex.co[:]) for vertex in mesh_data_copy.vertices] # Thanks SMG for these one-liners 
        ssbh_mesh_object.positions = [position0]

        normal0 = ssbh_data_py.mesh_data.AttributeData('Normal0')
        #normal0.data = [list(vertex.normal[:]) for vertex in mesh.data.vertices] <-- omg why cant this just contain custom normal data
        # So we gotta go through loop by loop
        # mesh.data.loops[index].normal contains the actual custom normal data
        index_to_normals_dict = {} # Dont judge the internet told me list insertion was bugged plus dictionaries are goated
        mesh_data_copy.calc_normals_split() # Needed apparently or the vertex normal data wont be filled 
        for loop in mesh_data_copy.loops:
            index_to_normals_dict[loop.vertex_index] = loop.normal[:]
        normal0.data = [list(index_to_normals_dict[key]) for key in sorted(index_to_normals_dict.keys())]
        ssbh_mesh_object.normals = [normal0]
        

        # Calculate Tangents
        # it is so hard to find examples of this online pls if you know how to better calculate tangents
        # please let me know
        tangent0 = ssbh_data_py.mesh_data.AttributeData('Tangent0')
        try:
            mesh_data_copy.calc_tangents()
        except RuntimeError as err:
            print(f'Could Not Calculate Tangents for mesh {mesh.name}, skipping for now, err = {err}')
            print(f'For reference, this is the meshs uvmaps{mesh.data.uv_layers.items()}')
            print(f'and now the copies {mesh_data_copy.uv_layers.items()}')
        else:
            index_to_tangents_dict = {l.vertex_index : [l.tangent[0], l.tangent[1], l.tangent[2], -1.0 * l.bitangent_sign] for l in mesh_data_copy.loops}
            sorted_dict = sorted(index_to_tangents_dict.items())
            tangent0.data = [val for index, val in sorted_dict]
            ssbh_mesh_object.tangents = [tangent0]

            mesh_data_copy.free_normals_split()
            mesh_data_copy.free_tangents()

        # Python magic to flatten the faces into a single list of vertex indices.
        #ssbh_mesh_object.vertex_indices = [index for face in mesh_data_copy.polygons for index in face.vertices]
        ssbh_mesh_object.vertex_indices = [loop.vertex_index for loop in mesh_data_copy.loops]



        # Export Weights
        blender_weight_layer = 0 # TODO: Research weight layers
        
        index_to_name_dict = {vg.index: vg.name for vg in mesh_object_copy.vertex_groups}
       
        bone_name_to_vertex_weights = {bone.name : [] for bone in ssbh_skel_data.bones}

        for vertex in mesh_data_copy.vertices:
            for group in vertex.groups:
                group_index = group.group
                weight = group.weight
                group_name = index_to_name_dict[group_index]
                bone_index = find_bone_index(ssbh_skel_data, group_name)
                if bone_index is None:
                    continue
                ssbh_vertex_weight = ssbh_data_py.mesh_data.VertexWeight(vertex.index, weight)
                bone_name_to_vertex_weights[group_name].append(ssbh_vertex_weight)
        
        BoneInfluence = ssbh_data_py.mesh_data.BoneInfluence
        ssbh_mesh_object.bone_influences = [BoneInfluence(name, weights) for name, weights in bone_name_to_vertex_weights.items()]

        '''
        # Export color sets
        for vertex_color_layer in mesh_data_copy.vertex_colors:
            ssbh_color_set = ssbh_data_py.mesh_data.AttributeData(vertex_color_layer.name)
            scale = get_color_scale(vertex_color_layer.name)
            ssbh_color_set.data = [list(val / scale for val in vc.color[:]) for vc in vertex_color_layer.data.values()]
            if real_mesh_name == 'TopN_1_Shape1' and ssbh_mesh_object_sub_index == 0:
                print('%s %s' % (ssbh_color_set.name, len(ssbh_color_set.data)))
                print('%s %s' % (ssbh_color_set.name, ssbh_color_set.data))

            
            ssbh_mesh_object.color_sets.append(ssbh_color_set)       
        '''
        '''
        for vertex_color_layer in mesh_data_copy.vertex_colors:
            ssbh_color_set = ssbh_data_py.mesh_data.AttributeData(vertex_color_layer.name)
            vertex_index_to_vertex_color = {loop.vertex_index : vertex_color_layer.data[loop.index].color[:] for loop in mesh_data_copy.loops}
            scale = get_color_scale(vertex_color_layer.name)       
            ssbh_color_set.data = [[index / scale for index in val] for val in vertex_index_to_vertex_color.values()]
            ssbh_mesh_object.color_sets.append(ssbh_color_set) 
        
        # Export UV maps
        for uv_layer in mesh_data_copy.uv_layers:
            ssbh_uv_layer = ssbh_data_py.mesh_data.AttributeData(uv_layer.name)
            vertex_index_to_vertex_uv = {loop.vertex_index : uv_layer.data[loop.index].uv for loop in mesh_data_copy.loops}
            ssbh_uv_layer.data = [[val[0], 1 - val[1]] for val in vertex_index_to_vertex_uv.values()]            
            if real_mesh_name == 'TopN_1_Shape1' and ssbh_mesh_object_sub_index == 0:
                print('%s %s' % (ssbh_uv_layer.name, len(ssbh_uv_layer.data)))
                #print('%s %s' % (ssbh_uv_layer.name, ssbh_uv_layer.data))
                for index, val in enumerate(ssbh_uv_layer.data):
                    print('%s  %s' % (index, val))
            ssbh_mesh_object.texture_coordinates.append(ssbh_uv_layer)
        '''
        '''
        So it seems like the issue is that i can't produce a reliable mapping between vertex_index to vertex,
        but with bmesh i can avoid the issue
        '''
        context.collection.objects.link(mesh_object_copy)
        context.view_layer.update()
        context.view_layer.objects.active = mesh_object_copy
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(mesh_object_copy.data)
        # Export UV Maps
        for uv_layer in bm.loops.layers.uv.values():
            ssbh_uv_layer = ssbh_data_py.mesh_data.AttributeData(uv_layer.name)
            v_to_uvs = {}
            for v in bm.verts:
                for l in v.link_loops:
                    uv_data = l[uv_layer]
                    v_to_uvs[v] = uv_data.uv
            fixed = [[uv[0], 1 - uv[1]] for uv in v_to_uvs.values()]
            ssbh_uv_layer.data = fixed
            ssbh_mesh_object.texture_coordinates.append(ssbh_uv_layer)
        # Export Color Set 
        for color_set_layer in bm.loops.layers.color.values():
            ssbh_color_set = ssbh_data_py.mesh_data.AttributeData(color_set_layer.name)
            v_to_color_set = {v : l[color_set_layer] for v in bm.verts for l in v.link_loops}
            #scale = get_color_scale(color_set_layer.name)
            #fixed = [[i / scale for i in col] for col in v_to_color_set.values()]
            color_set_values = [[i for i in col] for col in v_to_color_set.values()]
            ssbh_color_set.data = color_set_values
            ssbh_mesh_object.color_sets.append(ssbh_color_set)


        bm.free()
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.data.meshes.remove(mesh_data_copy)
        #bpy.data.objects.remove(mesh_object_copy)
        ssbh_mesh_data.objects.append(ssbh_mesh_object)




    #ssbh_mesh_data.save(filepath + 'model.numshb')
    #ssbh_model_data.save(filepath + 'model.numdlb')
    return ssbh_modl_data, ssbh_mesh_data, ssbh_matl_json, ssbh_numshexb_json

def make_skel_no_link(context):
    arma = context.scene.sub_model_export_armature
    bpy.context.view_layer.objects.active = arma
    arma.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    ssbh_skel = ssbh_data_py.skel_data.SkelData()
    edit_bones = arma.data.edit_bones
    edit_bones_list = list(edit_bones)
    for edit_bone in edit_bones_list:
        if edit_bone.use_deform == False:
            continue
        ssbh_bone = None
        if edit_bone.parent is not None:
            rel_mat = edit_bone.parent.matrix.inverted() @ edit_bone.matrix
            ssbh_bone = ssbh_data_py.skel_data.BoneData(edit_bone.name, rel_mat.transposed(), edit_bones_list.index(edit_bone.parent))
        else:
            ssbh_bone = ssbh_data_py.skel_data.BoneData(edit_bone.name, edit_bone.matrix.transposed(), None)
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
            if bone.use_deform == False:
                continue
            output_bones[bone.name] = bone
    
    ssbh_skel = ssbh_data_py.skel_data.SkelData()
 
    if '' != context.scene.sub_vanilla_nusktb:
        reordered_bones = []
        vanilla_ssbh_skel = ssbh_data_py.skel_data.read_skel(context.scene.sub_vanilla_nusktb)
        for vanilla_ssbh_bone in vanilla_ssbh_skel.bones:
            linked_bone = output_bones.get(vanilla_ssbh_bone.name)
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
                    print('O&V Link Found: index %s, transform= %s' % (index, vanilla_ssbh_bone.transform))
                    index = index + 1
                    ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, vanilla_ssbh_bone.transform, reordered_bones.index(blender_bone.parent) if blender_bone.parent else None)
                else:
                    if blender_bone.parent:
                        rel_mat = blender_bone.parent.matrix.inverted() @ blender_bone.matrix
                        ssbh_bone = ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, rel_mat.transposed(), reordered_bones.index(blender_bone.parent))
                        print(f'O&V No Link Found: index {index}, name {blender_bone.name}, rel_mat.transposed()= {rel_mat.transposed()}')
                        index = index + 1
                    else:
                        ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, blender_bone.matrix.transposed(), None)
            else:
                if blender_bone.parent:
                    '''
                    blender_bone_matrix_as_list = [list(row) for row in blender_bone.matrix.transposed()]
                    blender_bone_parent_matrix_as_list = [list(row) for row in blender_bone.parent.matrix.transposed()]
                    rel_transform = ssbh_data_py.skel_data.calculate_relative_transform(blender_bone_matrix_as_list, blender_bone_parent_matrix_as_list)
                    ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, rel_transform, reordered_bones.index(blender_bone.parent))
                    '''
                    rel_mat = blender_bone.parent.matrix.inverted() @ blender_bone.matrix
                    ssbh_bone = ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, rel_mat.transposed(), reordered_bones.index(blender_bone.parent))
                    print('OO: index %s, name %s, rel_mat.transposed()= %s' % (index, blender_bone.name, rel_mat.transposed()))
                    index = index + 1
                else:
                    ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, blender_bone.matrix.transposed(), None)
            ssbh_skel.bones.append(ssbh_bone)    

    #ssbh_skel.save(filepath + 'model.nusktb')

    bpy.ops.object.mode_set(mode='OBJECT')
    arma.select_set(False)
    bpy.context.view_layer.objects.active = None
    return ssbh_skel


'''
Bounding sphere calculation from https://b3d.interplanety.org/en/how-to-calculate-the-bounding-sphere-for-selected-objects/
'''
def bounding_sphere(objects, mode='GEOMETRY'):
    # return the bounding sphere center and radius for objects (in global coordinates)
    points_co_global = []
    if mode == 'GEOMETRY':
        # GEOMETRY - by all vertices/points - more precise, more slow
        for obj in objects:
            points_co_global.extend([obj.matrix_world @ vertex.co for vertex in obj.data.vertices])
    elif mode == 'BBOX':
        # BBOX - by object bounding boxes - less precise, quick
        for obj in objects:
            points_co_global.extend([obj.matrix_world @ Vector(bbox) for bbox in obj.bound_box])
    def get_center(l):
        return (max(l) + min(l)) / 2 if l else 0.0
    x, y, z = [[point_co[i] for point_co in points_co_global] for i in range(3)]
    b_sphere_center = Vector([get_center(axis) for axis in [x, y, z]]) if (x and y and z) else None
    b_sphere_radius = max(((point - b_sphere_center) for point in points_co_global)) if b_sphere_center else None
    return b_sphere_center, b_sphere_radius.length
