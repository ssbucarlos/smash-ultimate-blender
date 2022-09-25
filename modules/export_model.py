import os
import time
import bpy
import os.path
import numpy as np
import math
import bmesh
import json
import subprocess
import re

from pathlib import Path
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, Panel
from .. import ssbh_data_py
from mathutils import Vector, Matrix
from ..operators import material_inputs
from .import_model import get_ssbh_lib_json_exe_path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bpy.types import EditBone, Mesh, MeshVertex
    from .helper_bone_data import SubHelperBoneData, AimEntry, InterpolationEntry
    from ..properties import SubSceneProperties

class SUB_PT_export_model(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Ultimate'
    bl_label = 'Model Exporter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ssp = context.scene.sub_scene_properties
        layout = self.layout
        layout.use_property_split = False
        row = layout.row(align=True)
        row.label(text='Select an armature. The armature + its meshes will be exported')
        row = layout.row(align=True)
        row.prop(ssp, 'model_export_arma', icon='ARMATURE_DATA')
        if not ssp.model_export_arma:
            return
        if '' == ssp.vanilla_nusktb:
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
            row.label(text='Selected reference .nusktb: ' + ssp.vanilla_nusktb)
            row = layout.row(align=True)
            row.operator('sub.vanilla_nusktb_selector', icon='FILE', text='Re-Select Vanilla Nusktb')

        row = layout.row(align=True)
        row.operator('sub.model_exporter', icon='EXPORT', text='Export Model Files to a Folder')
    
class SUB_OP_vanilla_nusktb_selector(Operator, ImportHelper):
    bl_idname = 'sub.vanilla_nusktb_selector'
    bl_label = 'Vanilla Nusktb Selector'

    filter_glob: StringProperty(
        default='*.nusktb',
        options={'HIDDEN'}
    )
    def execute(self, context):
        context.scene.sub_scene_properties.vanilla_nusktb = self.filepath
        return {'FINISHED'}   

class SUB_OP_model_exporter(Operator):
    bl_idname = 'sub.model_exporter'
    bl_label = 'Export To This Folder'

    filter_glob: StringProperty(
        default='*.numdlb;*.nusktb;*.numshb;*.numatb;*.nuhlpb',
        options={'HIDDEN'},
        #maxlen=255,  # Max internal buffer length, longer would be clamped. Also blender has this in the example but tbh idk what it does yet
    )
    directory: bpy.props.StringProperty(subtype="DIR_PATH")

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
            ('ORDER_AND_VALUES', "Order & Values", "Preserve the order and transforms of vanilla bones (recommended)"),
            ('ORDER_ONLY', "Order Only", "Preserve the order of vanilla bones but use bone transforms from Blender."),
            ('NO_LINK', "No Link", "Recreate the bone order and transforms from Blender (not recommended)."),
        ),
        default='ORDER_AND_VALUES',
    )

    # Initially set the filename field to be nothing
    def invoke(self, context, _event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        export_model(self, context, self.directory, self.include_numdlb, self.include_numshb, self.include_numshexb,
                     self.include_nusktb, self.include_numatb, self.include_nuhlpb, self.linked_nusktb_settings)
        return {'FINISHED'}


def export_model(operator, context, directory, include_numdlb, include_numshb, include_numshexb, include_nusktb, include_numatb, include_nuhlpb, linked_nusktb_settings):
    # Prepare the scene for export and find the meshes to export.
    arma = context.scene.sub_scene_properties.model_export_arma
    try:
        context.view_layer.objects.active = arma
    except:
        operator.report({'ERROR'}, f'{arma.name} is not a valid armature name. Please select a valid armature.')
        return
    # Temporarily remove mesh vis drivers and un-hide them for export
    if arma.animation_data is not None:
        bpy.ops.sub.vis_drivers_remove()
    for child in arma.children:
        child.hide_viewport = False
        child.hide_render = False

    # TODO: Investigate why export fails if meshes are selected before hitting export.
    for selected_object in context.selected_objects:
        selected_object.select_set(False)

    export_meshes = [child for child in arma.children if child.type == 'MESH']
    export_meshes = [m for m in export_meshes if len(m.data.vertices) > 0] # Skip Empty Objects
    # TODO: Is it possible to keep the correct order for non imported meshes?
    export_meshes.sort(key=lambda mesh: mesh.get("numshb order", 10000))

    if len(export_meshes) == 0:
        message = f'No meshes are parented to the armature {arma.name}. Exported .NUMDLB, .NUMSHB, .NUMATB, and .NUMSHEXB files will have no entries.'
        operator.report({'WARNING'}, message)

    # Smash Ultimate groups mesh objects with the same name like 'c00BodyShape'.
    # Blender appends numbers like '.001' to prevent duplicates, so we need to remove those before grouping.
    # Use a dictionary since we can't assume meshes with the same name are contiguous.
    export_mesh_groups = {}
    for mesh in export_meshes:
        name = re.split(r'\.\d\d\d', mesh.name)[0]
        if name in export_mesh_groups:
            export_mesh_groups[name].append(mesh)
        else:
            export_mesh_groups[name] = [mesh]

    export_mesh_groups = export_mesh_groups.items()

    start = time.time()

    try:
        # TODO: The mesh is only needed for include_numshb or include_numshexb.
        ssbh_mesh_data = make_mesh_data(operator, context, export_mesh_groups)
    except RuntimeError as e:
        operator.report({'ERROR'}, str(e))
        return

    # Make sure this is a folder instead of a file.
    # TODO: This doesn't work if the file path isn't actually a file on disk?
    '''
    folder = Path(filepath)
    if folder.is_file():
        folder = folder.parent
    '''
    folder = Path(directory)
    # Create and save files individually to make this step more robust.
    # Users can avoid errors in generating a file by disabling export for that file.
    if include_numdlb:
        # TODO: Do we want to use exceptions instead of None for stopping export early?
        ssbh_modl_data = make_modl_data(operator, context, export_mesh_groups)
        if ssbh_modl_data is not None:
            path = str(folder.joinpath('model.numdlb'))
            try:
                ssbh_modl_data.save(path)
            except Exception as e:
                operator.report({'ERROR'}, f'Failed to save {path}: {e}')

    if include_numshb:
        path = str(folder.joinpath('model.numshb'))
        try:
            ssbh_mesh_data.save(path)
        except Exception as e:
            operator.report({'ERROR'}, f'Failed to save {path}: {e}')

    if include_nusktb:
        create_and_save_skel(operator, context, linked_nusktb_settings, folder)

    if include_numatb:
        create_and_save_matl(operator, folder, export_meshes)

    if include_numshexb:
        create_and_save_meshex(operator, folder, ssbh_mesh_data)

    if include_nuhlpb:
        create_and_save_nuhlpb(folder, arma)

    end = time.time()
    print(f'Create and save export files in {end - start} seconds')

    if arma.animation_data is not None:
        from .import_anim import setup_visibility_drivers
        setup_visibility_drivers(arma)

def create_and_save_skel(operator, context, linked_nusktb_settings, folder):
    try:
        ssbh_skel_data = make_skel(operator, context, linked_nusktb_settings)
    except RuntimeError as e:
        operator.report({'ERROR'}, str(e))
        return

    # The uniform buffer for bone transformations in the skinning shader has a fixed size.
    # Limit exports to 511 bones to prevent rendering issues and crashes in game.
    if len(ssbh_skel_data.bones) > 511:
        operator.report({'ERROR'}, f'{len(ssbh_skel_data.bones)} bones exceeds the maximum supported count of 511.')
        return

    path = str(folder.joinpath('model.nusktb'))
    try:
        ssbh_skel_data.save(path)
    except Exception as e:
        operator.report({'ERROR'}, f'Failed to save {path}: {e}')


def create_and_save_meshex(operator, folder, ssbh_mesh_data):
    meshex = ssbh_data_py.meshex_data.MeshExData.from_mesh_objects(ssbh_mesh_data.objects)

    path = str(folder.joinpath('model.numshexb'))
    try:
        meshex.save(path)
    except Exception as e:
        operator.report({'ERROR'}, f'Failed to save {path}: {e}')


def get_mesh_materials(operator, export_meshes):
    #  Gather Material Info
    materials = set()
    for mesh in export_meshes:
        if len(mesh.data.materials) > 0:
            if mesh.data.materials[0] is not None:
                if len(mesh.data.materials) > 1:
                    message = f'The mesh {mesh.name} has more than one material slot. Only the first material will be exported.'
                    operator.report({'WARNING'}, message)

                materials.add(mesh.data.materials[0])
            else:
                message = f'The mesh {mesh.name} has no material created for the first material slot.' 
                message += ' Cannot create model.numatb. Create a material or disable .NUMATB export.'
                raise RuntimeError(message)

    return materials


def create_and_save_matl(operator, folder, export_meshes):
    try:
        materials = get_mesh_materials(operator, export_meshes)
        ssbh_matl = make_matl(operator, materials)
    except RuntimeError as e:
        operator.report({'ERROR'}, str(e))
        return

    path = str(folder.joinpath('model.numatb'))
    try:
        ssbh_matl.save(path)
    except Exception as e:
        operator.report({'ERROR'}, f'Failed to save {path}: {e}')

        
def get_material_label_from_mesh(operator, mesh):
    if len(mesh.material_slots) == 0:
        message = f'No material assigned for {mesh.name}. Cannot create model.numdlb. Assign a material or disable .NUMDLB export.'
        raise RuntimeError(message)

    material = mesh.material_slots[0].material

    if material is None:
        message = f'The mesh {mesh.name} has no material created for the first material slot.' 
        message += ' Cannot create model.numdlb. Create a material or disable .NUMDLB export.'
        raise RuntimeError(message)

    mat_label = None
    try:
        ultimate_node = find_ultimate_node(material)
        mat_label = ultimate_node.inputs['Material Name'].default_value
    except:
        # Use the Blender material name as a fallback.
        mat_label = material.name
        message = f'Missing Smash Ultimate node group for the mesh {mesh.name}. Assigning {mat_label} by material name.'
        operator.report({'WARNING'}, message)

    return mat_label


def find_bone_index(bones, name):
    for i, bone in enumerate(bones):
        if bone.name == name:
            return i

    return None


def default_ssbh_material(material_label):
    # Mario's phong0_sfx_0x9a011063_____VTC___TANGENT___BINORMAL_101 material.
    # This is a good default for fighters since the user can just assign textures in another application.
    entry = ssbh_data_py.matl_data.MatlEntryData(material_label, 'SFX_PBS_0100000008008269_opaque')
    entry.blend_states = [ssbh_data_py.matl_data.BlendStateParam(
        ssbh_data_py.matl_data.ParamId.BlendState0,
        ssbh_data_py.matl_data.BlendStateData()
    )]
    entry.floats = [ssbh_data_py.matl_data.FloatParam(ssbh_data_py.matl_data.ParamId.CustomFloat0, 0.8)]
    entry.booleans = [
        ssbh_data_py.matl_data.BooleanParam(ssbh_data_py.matl_data.ParamId.CustomBoolean1, True),
        ssbh_data_py.matl_data.BooleanParam(ssbh_data_py.matl_data.ParamId.CustomBoolean3, True),
        ssbh_data_py.matl_data.BooleanParam(ssbh_data_py.matl_data.ParamId.CustomBoolean4, True),
    ]
    entry.vectors = [
        ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.CustomVector0, [1.0, 0.0, 0.0, 0.0]),
        ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.CustomVector13, [1.0, 1.0, 1.0, 1.0]),
        ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.CustomVector14, [1.0, 1.0, 1.0, 1.0]),
        ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.CustomVector8, [1.0, 1.0, 1.0, 1.0]),
    ]
    entry.rasterizer_states = [ssbh_data_py.matl_data.RasterizerStateParam(
        ssbh_data_py.matl_data.ParamId.RasterizerState0,
        ssbh_data_py.matl_data.RasterizerStateData()
    )]
    entry.samplers = [
        ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.Sampler0, ssbh_data_py.matl_data.SamplerData()),
        ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.Sampler4, ssbh_data_py.matl_data.SamplerData()),
        ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.Sampler6, ssbh_data_py.matl_data.SamplerData()),
        ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.Sampler7, ssbh_data_py.matl_data.SamplerData()),
    ]
    # Use magenta for the albedo/base color to avoid confusion with existing error colors like white, yellow, or red.
    # Magenta is commonly used to indicate missing/invalid textures in applications and game engines.
    entry.textures = [
        ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.Texture0, '/common/shader/sfxpbs/default_params_r100_g025_b100'),
        ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.Texture4, '/common/shader/sfxpbs/fighter/default_normal'),
        ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.Texture6, '/common/shader/sfxpbs/fighter/default_params'),
        ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.Texture7, '#replace_cubemap'),
    ]
    return entry


def default_texture(param_name):
    # Select defaults that have as close to no effect as possible.
    # This is white (1,1,1) for multiplication and black (0,0,0) for addition.
    defaults = {
        'Texture0': '/common/shader/sfxpbs/default_white',
        'Texture1': '/common/shader/sfxpbs/default_white',
        'Texture2': '#replace_cubemap',
        'Texture3': '/common/shader/sfxpbs/default_white',
        'Texture4': '/common/shader/sfxpbs/fighter/default_normal',
        'Texture5': '/common/shader/sfxpbs/default_black',
        'Texture6': '/common/shader/sfxpbs/fighter/default_params',
        'Texture7': '#replace_cubemap',
        'Texture8': '#replace_cubemap',
        'Texture9': '/common/shader/sfxpbs/default_black',
        'Texture10': '/common/shader/sfxpbs/default_white',
        'Texture11': '/common/shader/sfxpbs/default_white',
        'Texture12': '/common/shader/sfxpbs/default_white',
        'Texture13': '/common/shader/sfxpbs/default_white',
        'Texture14': '/common/shader/sfxpbs/default_black',
        'Texture15': '/common/shader/sfxpbs/default_white',
        'Texture16': '/common/shader/sfxpbs/default_white',
        'Texture17': '/common/shader/sfxpbs/default_white',
        'Texture18': '/common/shader/sfxpbs/default_white',
        'Texture19': '/common/shader/sfxpbs/default_white',
    }

    if param_name in defaults:
        return defaults[param_name]
    else:
        return '/common/shader/sfxpbs/default_white'


def find_output_node(material):
    for node in material.node_tree.nodes:
        if node.bl_idname == 'ShaderNodeOutputMaterial':
            return node

    return None


def find_ultimate_node(material):
    output_node = find_output_node(material)
    if output_node is None:
        return None

    # We can't differentiate the ultimate node group from other node groups.
    # Just assume all node groups are correct and handle errors on export.
    node = output_node.inputs['Surface'].links[0].from_node
    if node is not None and node.bl_idname == 'ShaderNodeGroup':
        return node
    else:
        return None


def find_principled_node(material):
    output_node = find_output_node(material)
    if output_node is None:
        return None

    # We can't differentiate the ultimate node group from other node groups.
    # Just assume all node groups are correct and handle errors on export.
    node = output_node.inputs['Surface'].links[0].from_node
    if node is not None and node.bl_idname == 'ShaderNodeBsdfPrincipled':
        return node
    else:
        return None


def make_matl(operator, materials):
    matl = ssbh_data_py.matl_data.MatlData()

    for material in materials:
        ultimate_node = find_ultimate_node(material)
    
        if ultimate_node is not None:
            entry = create_material_entry_from_node_group(operator, ultimate_node)
        else:
            # Materials are often edited in external applications.
            # Use a default for missing node groups to allow exporting to proceed.    
            entry = default_ssbh_material(material.name)
            principled_node = find_principled_node(material)
            if principled_node is not None:
                operator.report({'WARNING'}, f'Missing Smash Ultimate node group for {material.name}. Creating material from Principled BSDF.')
                texture, sampler = create_texture_sampler(operator, principled_node.inputs['Base Color'], material.name, 'Texture0')
                entry.textures[0] = texture
                entry.samplers[0] = sampler
            else:
                operator.report({'WARNING'}, f'Missing Smash Ultimate node group for {material.name}. Creating default material.')
        

        matl.entries.append(entry)

    return matl


def create_material_entry_from_node_group(operator, node):
    material_label = node.inputs['Material Name'].default_value
    entry = ssbh_data_py.matl_data.MatlEntryData(material_label, node.inputs['Shader Label'].default_value)

    # The ultimate node group has inputs for each material parameter.
    # Hidden inputs aren't used by the in game shader and should be skipped.
    inputs = [input for input in node.inputs if input.hide == False]

    # Multiple inputs may correspond to a single parameter.
    # Avoid exporting the same parameter more than once.
    exported_params = set()

    for input in inputs:
        name = input.name
        param_name = name.split(' ')[0]

        if param_name in exported_params:
            continue

        elif name == 'BlendState0 Field1 (Source Color)':
            attribute = create_blend_state(node)
            entry.blend_states.append(attribute)
        elif name == 'RasterizerState0 Field1 (Polygon Fill)':
            attribute = create_rasterizer_state(node)
            entry.rasterizer_states.append(attribute)
        elif 'Texture' in param_name and 'RGB' in name.split(' ')[1]:
            # Samplers are connected to their corresponding texture nodes instead of the ultimate node group.
            texture_attribute, sampler_attribute = create_texture_sampler(operator, input, material_label, param_name)
            entry.textures.append(texture_attribute)
            entry.samplers.append(sampler_attribute)
        elif 'Boolean' in param_name:
            attribute = ssbh_data_py.matl_data.BooleanParam(ssbh_data_py.matl_data.ParamId.from_str(param_name), input.default_value)
            entry.booleans.append(attribute)
        elif 'Float' in param_name:
            attribute = ssbh_data_py.matl_data.FloatParam(ssbh_data_py.matl_data.ParamId.from_str(param_name), input.default_value)
            entry.floats.append(attribute)
        elif 'Vector' in param_name:
            if param_name in material_inputs.vec4_param_to_inputs:
                attribute = ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.from_str(param_name), [0.0, 0.0, 0.0, 0.0])        

                inputs = [node.inputs.get(name) for _, name, _ in material_inputs.vec4_param_to_inputs[param_name]]
                    
                # Assume inputs are RGBA, RGB/A, or X/Y/Z/W.
                if len(inputs) == 1:
                    attribute.data = inputs[0].default_value
                elif len(inputs) == 2:
                    # Discard the 4th RGB component and use the explicit alpha instead.
                    attribute.data[:3] = list(inputs[0].default_value)[:3]
                    attribute.data[3] = inputs[1].default_value
                elif len(inputs) == 4:
                    attribute.data[0] = inputs[0].default_value
                    attribute.data[1] = inputs[1].default_value
                    attribute.data[2] = inputs[2].default_value
                    attribute.data[3] = inputs[3].default_value

                entry.vectors.append(attribute)
        else:
            continue

        exported_params.add(param_name)
    return entry


def create_blend_state(node):
    data = ssbh_data_py.matl_data.BlendStateData()

    try:
        data.source_color = ssbh_data_py.matl_data.BlendFactor.from_str(node.inputs['BlendState0 Field1 (Source Color)'].default_value)
        data.destination_color = ssbh_data_py.matl_data.BlendFactor.from_str(node.inputs['BlendState0 Field3 (Destination Color)'].default_value)
        data.alpha_sample_to_coverage = node.inputs['BlendState0 Field7 (Alpha to Coverage)'].default_value
    except:
        # TODO: Report errors?
        data = ssbh_data_py.matl_data.BlendStateData()

    attribute = ssbh_data_py.matl_data.BlendStateParam(ssbh_data_py.matl_data.ParamId.BlendState0, data)
    return attribute


def create_rasterizer_state(node):
    data = ssbh_data_py.matl_data.RasterizerStateData()

    try:
        data.fill_mode = ssbh_data_py.matl_data.FillMode.from_str(node.inputs['RasterizerState0 Field1 (Polygon Fill)'].default_value)
        data.cull_mode = ssbh_data_py.matl_data.CullMode.from_str(node.inputs['RasterizerState0 Field2 (Cull Mode)'].default_value)
        data.depth_bias = node.inputs['RasterizerState0 Field3 (Depth Bias)'].default_value
    except:
        # TODO: Report errors?
        data = ssbh_data_py.matl_data.RasterizerStateData()

    attribute = ssbh_data_py.matl_data.RasterizerStateParam(ssbh_data_py.matl_data.ParamId.RasterizerState0, data)
    return attribute


def create_texture_sampler(operator, input, material_label, param_name):
    # Texture Data
    try:
        texture_node = input.links[0].from_node
        texture_name = texture_node.label
    except:
        operator.report({'WARNING'}, f'Missing texture {param_name} for material {material_label}. Applying defaults.')
        texture_name = default_texture(param_name)

    texture_attribute = ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.from_str(param_name), texture_name)

    # Sampler Data
    sampler_number = param_name.split('Texture')[1]
    sampler_param_id_text = f'Sampler{sampler_number}'

    sampler_data = ssbh_data_py.matl_data.SamplerData()

    try:
        sampler_node = texture_node.inputs[0].links[0].from_node
        # TODO: These conversions may return None on error.
        sampler_data.wraps = ssbh_data_py.matl_data.WrapMode.from_str(sampler_node.wrap_s)
        sampler_data.wrapt = ssbh_data_py.matl_data.WrapMode.from_str(sampler_node.wrap_t)
        sampler_data.wrapr = ssbh_data_py.matl_data.WrapMode.from_str(sampler_node.wrap_r)
        sampler_data.min_filter = ssbh_data_py.matl_data.MinFilter.from_str(sampler_node.min_filter)
        sampler_data.mag_filter = ssbh_data_py.matl_data.MagFilter.from_str(sampler_node.mag_filter)
        sampler_data.border_color = sampler_node.border_color
        sampler_data.lod_bias = sampler_node.lod_bias
        sampler_data.max_anisotropy = ssbh_data_py.matl_data.MaxAnisotropy.from_str(sampler_node.max_anisotropy) if sampler_node.anisotropic_filtering else None
    except:
        operator.report({'WARNING'}, f'Missing sampler {sampler_param_id_text} for material {material_label}. Applying defaults.')
        sampler_data = ssbh_data_py.matl_data.SamplerData()

    sampler_attribute = ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.from_str(sampler_param_id_text), sampler_data)

    return texture_attribute, sampler_attribute


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


def make_mesh_data(operator, context, export_mesh_groups):
    ssbh_mesh_data = ssbh_data_py.mesh_data.MeshData()

    for group_name, meshes in export_mesh_groups:
        for i, mesh in enumerate(meshes):
            '''
            Need to Make a copy of the mesh, split by material, apply transforms, and validate for potential errors.
            list of potential issues that need to validate
            1.) Shape Keys 2.) Negative Scaling 3.) Invalid Materials 4.) Degenerate Geometry
            '''   
            # Make a copy of the mesh so that the original remains unmodified.
            mesh_object_copy = mesh.copy()
            mesh_object_copy.data = mesh.data.copy()

            # Apply any transforms before exporting to preserve vertex positions.
            # Assume the meshes have no children that would inherit their transforms.
            mesh_object_copy.data.transform(mesh_object_copy.matrix_basis)
            mesh_object_copy.matrix_basis.identity()

            # Check if any of the faces are not tris, and converts them into tris
            if any(len(f.vertices) != 3 for f in mesh_object_copy.data.polygons):
                operator.report({'WARNING'}, f'Mesh {mesh.name} has non triangular faces. Triangulating a temporary mesh for export.')

                # https://blender.stackexchange.com/questions/45698
                me = mesh_object_copy.data
                # Get a BMesh representation
                bm = bmesh.new()
                bm.from_mesh(me)

                bmesh.ops.triangulate(bm, faces=bm.faces[:])

                # Finish up, write the bmesh back to the mesh
                bm.to_mesh(me)
                bm.free()

            context.collection.objects.link(mesh_object_copy)
            context.view_layer.update()

            if split_duplicate_uvs(mesh_object_copy, mesh):
                message = f'Mesh {mesh.name} has more than one UV coord per vertex.'
                message += ' Splitting duplicate UV edges on temporary mesh for export.'
                operator.report({'WARNING'}, message)

            try:
                # Use the original mesh name since the copy will have strings like ".001" appended.
                ssbh_mesh_object = make_mesh_object(operator, context, mesh_object_copy, group_name, i, mesh.name)
            finally:
                bpy.data.meshes.remove(mesh_object_copy.data)

            ssbh_mesh_data.objects.append(ssbh_mesh_object)

    return ssbh_mesh_data


def make_mesh_object(operator, context, mesh: bpy.types.Object, group_name, i, mesh_name):
    # ssbh_data_py accepts lists, tuples, or numpy arrays for AttributeData.data.
    # foreach_get and foreach_set provide substantially faster access to property collections in Blender.
    # https://devtalk.blender.org/t/alternative-in-2-80-to-create-meshes-from-python-using-the-tessfaces-api/7445/3
    mesh_data: bpy.types.Mesh = mesh.data
    ssbh_mesh_object = ssbh_data_py.mesh_data.MeshObjectData(group_name, i)
    position0 = ssbh_data_py.mesh_data.AttributeData('Position0')

    # TODO: Is there a better way to account for the change of coordinates?
    axis_correction = np.array(Matrix.Rotation(math.radians(90), 3, 'X'))

    # For example, vertices is a bpy_prop_collection of MeshVertex, which has a "co" attribute for position.
    positions = np.zeros(len(mesh_data.vertices) * 3, dtype=np.float32)
    mesh_data.vertices.foreach_get("co", positions)
    # The output data is flattened, so we need to reshape it into the appropriate number of rows and columns.
    position0.data = positions.reshape((-1, 3)) @ axis_correction
    ssbh_mesh_object.positions = [position0]

    # Store vertex indices as a numpy array for faster indexing later.
    vertex_indices = np.zeros(len(mesh_data.loops), dtype=np.uint32)
    mesh_data.loops.foreach_get("vertex_index", vertex_indices)
    ssbh_mesh_object.vertex_indices = vertex_indices

    # We use the loop normals rather than vertex normals to allow exporting custom normals.
    mesh_data.calc_normals_split()

    # Export Normals
    normal0 = ssbh_data_py.mesh_data.AttributeData('Normal0')
    loop_normals = np.zeros(len(mesh_data.loops) * 3, dtype=np.float32)
    mesh_data.loops.foreach_get("normal", loop_normals)
    normals = per_loop_to_per_vertex(loop_normals, vertex_indices, (len(mesh_data.vertices), 3))
    normals = normals @ axis_correction

    # Pad normals to 4 components instead of 3 components.
    # This actually results in smaller file sizes since HalFloat4 is smaller than Float3.
    normals = np.append(normals, np.zeros((normals.shape[0],1)), axis=1)
            
    normal0.data = normals
    ssbh_mesh_object.normals = [normal0]

    # Export Weights
    # TODO: Reversing a vertex -> group lookup to a group -> vertex lookup is expensive.
    # TODO: Does Blender not expose this directly?
    group_to_weights = { vg.index : (vg.name, []) for vg in mesh.vertex_groups }
    has_unweighted_vertices = False
    # TODO: Skip this for performance reasons if there are no vertex groups?
    '''
    Vertex groups can either be 'Deform' groups used for actual mesh deformation, or 'Other'
    Only want the 'Deform' groups exported.
    '''
    ssp: SubSceneProperties = context.scene.sub_scene_properties
    arma = ssp.model_export_arma
    deform_vertex_group_indices = {vg.index for vg in mesh.vertex_groups if vg.name in arma.data.bones}
    for vertex in mesh_data.vertices:
        vertex: MeshVertex 
        deform_groups = [g for g in vertex.groups if g.group in deform_vertex_group_indices]
        if len(deform_groups) > 4:
            # We won't fix this automatically since removing influences may break animations.
            message = f'Vertex with more than 4 weights detected for mesh {mesh_name}.'
            message += ' Select all in Edit Mode and click Mesh > Weights > Limit Total with the limit set to 4.'
            message += ' Weights may need to be reassigned after limiting totals.'
            raise RuntimeError(message)

        # Only report this warning once.
        if len(deform_groups) == 0 or all([g.weight == 0.0 for g in deform_groups]):
            has_unweighted_vertices = True

        # Blender doesn't enforce normalization, since it normalizes while animating.
        # Normalize on export to ensure the weights work correctly in game.
        weight_sum = sum([g.weight for g in deform_groups])
        for group in deform_groups:
            # Remove unused weights on export.
            if group.weight > 0.0:
                ssbh_weight = ssbh_data_py.mesh_data.VertexWeight(vertex.index, group.weight / weight_sum)
                group_to_weights[group.group][1].append(ssbh_weight)

    if has_unweighted_vertices:
        message = f'Mesh {mesh_name} has unweighted vertices or vertices with only 0.0 weights.'
        operator.report({'WARNING'}, message)

    # Avoid adding unused influences if there are no weights.
    # Some meshes are parented to a bone instead of using vertex skinning.
    # This requires the influence list to be empty to save properly.
    ssbh_mesh_object.bone_influences = []
    for name, weights in group_to_weights.values():
        # Assume all influence names are valid since some in game models have influences not in the skel.
        # For example, fighter/miifighter/model/b_deacon_m weights vertices to effect bones.
        if len(weights) > 0:
            ssbh_mesh_object.bone_influences.append(ssbh_data_py.mesh_data.BoneInfluence(name, weights))
    
    # Mesh version 1.10 only has 16-bit unsigned vertex indices for skin weights.
    # Meshes without vertex skinning can use the full range of 32-bit unsigned vertex indices.
    vertex_index = vertex_indices.max()
    if len(ssbh_mesh_object.bone_influences) > 0 and vertex_index > 65535:
        message = f'Vertex index {vertex_index} exceeds the limit of 65535 for mesh {mesh_name}.'
        message += ' Reduce the number of vertices or split the mesh into smaller meshes.'
        message += ' Note that splitting duplicate UVs will increase the vertex count.'
        raise RuntimeError(message)

    smash_uv_names = ['map1', 'bake1', 'uvSet', 'uvSet1', 'uvSet2']
    for uv_layer in mesh.data.uv_layers:
        if uv_layer.name not in smash_uv_names:
            # TODO: Use more specific exception classes?
            valid_attribute_list = ', '.join(smash_uv_names)
            message = f'Mesh {mesh_name} has invalid UV map name {uv_layer.name}. Valid names are {valid_attribute_list}.'
            message += ' Select the mesh and change the UV map name in Object Data Properties > UV Maps.'
            raise RuntimeError(message)

        ssbh_uv_layer = ssbh_data_py.mesh_data.AttributeData(uv_layer.name)
        loop_uvs = np.zeros(len(mesh.data.loops) * 2, dtype=np.float32)
        uv_layer.data.foreach_get("uv", loop_uvs)

        uvs = per_loop_to_per_vertex(loop_uvs, vertex_indices, (len(mesh.data.vertices), 2))
        # Flip vertical.
        uvs[:,1] = 1.0 - uvs[:,1]
        ssbh_uv_layer.data = uvs

        ssbh_mesh_object.texture_coordinates.append(ssbh_uv_layer)

    # Export Color Set
    smash_color_names = ['colorSet1', 'colorSet2', 'colorSet2_1', 'colorSet2_2', 'colorSet2_3', 'colorSet3', 'colorSet4', 'colorSet5', 'colorSet6', 'colorSet7']
    for color_layer in mesh.data.vertex_colors:
        if color_layer.name not in smash_color_names:
            # TODO: Use more specific exception classes?
            valid_attribute_list = ', '.join(smash_color_names)
            message = f'Mesh {mesh_name} has invalid vertex color name {color_layer.name}. Valid names are {valid_attribute_list}.'
            message += ' Select the mesh and change the vertex color name in Object Data Properties > Vertex Colors.'
            raise RuntimeError(message)

        ssbh_color_layer = ssbh_data_py.mesh_data.AttributeData(color_layer.name)

        loop_colors = np.zeros(len(mesh.data.loops) * 4, dtype=np.float32)
        color_layer.data.foreach_get("color", loop_colors)
        ssbh_color_layer.data = per_loop_to_per_vertex(loop_colors, vertex_indices, (len(mesh.data.vertices), 4))

        ssbh_mesh_object.color_sets.append(ssbh_color_layer)

    # Calculate tangents now that the necessary attributes are initialized.
    tangent0 = ssbh_data_py.mesh_data.AttributeData('Tangent0')

    # Assume tangents always use the first UV map since normal maps always use map1 in game.
    if len(ssbh_mesh_object.texture_coordinates) == 0:
        message = f'Mesh {mesh_name} has no UV maps. Cannot calculate tangents.'
        message += ' Add a UV map named "map1" in Object Data Properties > UV Maps.'
        raise RuntimeError(message)

    try:
        # No axis correction is needed here since we're using the transformed positions and normals.
        tangent0.data = ssbh_data_py.mesh_data.calculate_tangents_vec4(ssbh_mesh_object.positions[0].data, 
                    ssbh_mesh_object.normals[0].data, 
                    ssbh_mesh_object.texture_coordinates[0].data,
                    ssbh_mesh_object.vertex_indices)
    except Exception as e:
        # TODO (SMG): Only catch ssbh_data_py.MeshDataError once ssbh_data_py is updated.
        message = f'Failed to calculate tangents for mesh {mesh_name}: {e}.'
        raise RuntimeError(message)
    
    ssbh_mesh_object.tangents = [tangent0]
            
    return ssbh_mesh_object


def get_duplicate_uv_edges(bm, uv_layer):
    edges_to_split = []

    # Blender stores uvs per loop rather than per vertex.
    # Find edges connected to vertices with more than one uv coord.
    # This allows converting to per vertex later by splitting edges.
    index_to_uv = {}
    for face in bm.faces:
        for loop in face.loops:
            vertex_index = loop.vert.index
            uv = loop[uv_layer].uv
            if vertex_index not in index_to_uv:
                index_to_uv[vertex_index] = uv
            elif uv != index_to_uv[vertex_index]:
                # Get any edges containing this vertex.
                edges_to_split.extend(loop.vert.link_edges)

    # TODO: Do duplicates matter?
    edges_to_split = list(set(edges_to_split))
    return edges_to_split


def split_duplicate_uvs(mesh, original_mesh):
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.mode_set(mode = 'EDIT')

    me = mesh.data
    bm = bmesh.from_edit_mesh(me)

    edges_to_split = []

    for layer_name in bm.loops.layers.uv.keys():
        uv_layer = bm.loops.layers.uv.get(layer_name)
        edges_to_split.extend(get_duplicate_uv_edges(bm, uv_layer))

    # Don't modify the mesh if no edges need to be split.
    # This check also seems to prevent a potential crash.
    if len(edges_to_split) > 0:
        # Remove duplicates to avoid exceptions when splitting.
        edges_to_split = list(set(edges_to_split))
        bmesh.ops.split_edges(bm, edges=edges_to_split)
        bmesh.update_edit_mesh(me)

    bm.free()

    bpy.ops.object.mode_set(mode='OBJECT')

    if len(edges_to_split) > 0:
        # Copy the original normals to preserve smooth shading.
        # TODO: Investigate preserving smooth tangents as well.
        bpy.context.view_layer.objects.active = mesh
        modifier = mesh.modifiers.new(name='Transfer Normals', type='DATA_TRANSFER')
        modifier.object = original_mesh
        modifier.data_types_loops = {'CUSTOM_NORMAL'}
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.context.view_layer.objects.active = None

    # Check if any edges were split.
    return len(edges_to_split) > 0


def make_modl_data(operator, context, export_mesh_groups):
    ssbh_modl_data = ssbh_data_py.modl_data.ModlData()

    ssbh_modl_data.model_name = 'model'
    ssbh_modl_data.skeleton_file_name = 'model.nusktb'
    ssbh_modl_data.material_file_names = ['model.numatb']
    ssbh_modl_data.animation_file_name = None
    ssbh_modl_data.mesh_file_name = 'model.numshb'

    for group_name, meshes in export_mesh_groups:
        for i, mesh in enumerate(meshes):
            try:
                mat_label = get_material_label_from_mesh(operator, mesh)
                ssbh_modl_entry = ssbh_data_py.modl_data.ModlEntryData(group_name, i, mat_label)
                ssbh_modl_data.entries.append(ssbh_modl_entry)
            except RuntimeError as e:
                # TODO: Should this stop exporting entirely?
                operator.report({'ERROR'}, str(e))
                return None

    return ssbh_modl_data

def get_smash_transform(m) -> Matrix:
    # This is the inverse of the get_blender_transform permutation matrix.
    # https://en.wikipedia.org/wiki/Matrix_similarity
    p = Matrix([
        [0, 1, 0, 0],
        [-1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])
    # Perform the transformation m in Blender's basis and convert back to Ultimate.
    # TODO(SMG): Transposing won't be necessary in the next ssbh_data_py update.
    return (p @ m @ p.inverted()).transposed()


def get_smash_root_transform(bone: bpy.types.EditBone) -> Matrix:
    bone.transform(Matrix.Rotation(math.radians(-90), 4, 'X'))
    bone.transform(Matrix.Rotation(math.radians(90), 4, 'Z'))
    unreoriented_matrix = get_smash_transform(bone.matrix)
    bone.transform(Matrix.Rotation(math.radians(-90), 4, 'Z'))
    bone.transform(Matrix.Rotation(math.radians(90), 4, 'X'))
    return unreoriented_matrix

def read_vanilla_nusktb(path, mode):
    if not path:
        raise RuntimeError(f'Link mode {mode} requires a vanilla .NUSKTB file to be selected.')

    try:
        skel = ssbh_data_py.skel_data.read_skel(path)
        return skel
    except Exception as e:
        message = 'Failed to read vanilla .NUSKTB. Ensure the file exists and is a valid .NUSKTB file.'
        message += f' Error reading {path}: {e}'
        raise RuntimeError(message)


def get_ssbh_bone(blender_bone: bpy.types.EditBone, parent_index):
    if blender_bone.parent:
        unreoriented_matrix = get_smash_transform(blender_bone.parent.matrix.inverted() @ blender_bone.matrix)
        return ssbh_data_py.skel_data.BoneData(blender_bone.name, unreoriented_matrix, parent_index)
    else:
        return ssbh_data_py.skel_data.BoneData(blender_bone.name, get_smash_root_transform(blender_bone), None)


def bone_order(bones, name):
    # Preserve the existing bone index if possible.
    # Set the bone index to a large value for added bones.
    # Sort added bones by the bone group based on prefix.
    i = find_bone_index(bones, name)
    group = 0
    if 'S_' in name:
        group = 0
    elif '_eff' in name or '_offset' in name:
        group = 1
    elif 'H_' in name:
        group = 2

    return (10000, group) if i is None else (i, group)
    

def make_skel(operator, context, mode):
    ssp = context.scene.sub_scene_properties
    arma = ssp.model_export_arma
    bpy.context.view_layer.objects.active = arma
    # The object should be selected and visible before entering edit mode.
    arma.select_set(True)
    arma.hide_set(False)
    bpy.ops.object.mode_set(mode='EDIT')

    skel = ssbh_data_py.skel_data.SkelData()

    preserve_values = mode == 'ORDER_AND_VALUES'
    preserve_order = mode == 'ORDER_AND_VALUES' or mode == 'ORDER_ONLY'

    vanilla_skel = read_vanilla_nusktb(ssp.vanilla_nusktb, mode) if preserve_values or preserve_order else None

    if vanilla_skel is None:
        message = 'Creating .NUSKTB without a vanilla .NUSKTB file.'
        message += ' Bone order will not be preserved and may cause animation issues in game.'
        operator.report({'WARNING'}, message)

    edit_bones = list(arma.data.edit_bones)
    if vanilla_skel is not None and preserve_order:
        # Sort based on the original order with added bones at the end.
        edit_bones = sorted(edit_bones, key = lambda b: bone_order(vanilla_skel.bones, b.name))

    # Flatten Blender's bone heirarchy into a list of bones with parent indices.
    for blender_bone in edit_bones:
        # TODO: Handle the case where a vanilla bone was deleted?
        parent_index = edit_bones.index(blender_bone.parent) if blender_bone.parent else None
        ssbh_bone = get_ssbh_bone(blender_bone, parent_index)

        if vanilla_skel is not None and preserve_values:
            # TODO: Will this correctly set the parent index?
            vanilla_index = find_bone_index(vanilla_skel.bones, blender_bone.name)
            if vanilla_index is not None:
                ssbh_bone = vanilla_skel.bones[vanilla_index]

        skel.bones.append(ssbh_bone)

    bpy.ops.object.mode_set(mode='OBJECT')
    arma.select_set(False)
    bpy.context.view_layer.objects.active = None
    return skel


def save_ssbh_json(ssbh_json, dumped_json_path, output_file_path):
    ssbh_lib_json_exe_path = get_ssbh_lib_json_exe_path()
    with open(dumped_json_path, 'w') as f:
        json.dump(ssbh_json, f, indent=2)
    subprocess.run([ssbh_lib_json_exe_path, dumped_json_path, output_file_path])
    os.remove(dumped_json_path)
    return


def create_and_save_nuhlpb(folder, arma:bpy.types.Object):
    shbd:SubHelperBoneData = arma.data.sub_helper_bone_data

    nuhlpb_json = {}
    nuhlpb_json['data'] = {}
    nuhlpb_json['data']['Hlpb'] = {}
    nuhlpb_json['data']['Hlpb']['major_version'] = shbd.major_version
    nuhlpb_json['data']['Hlpb']['minor_version'] = shbd.minor_version
    
    nuhlpb_json['data']['Hlpb']['aim_entries'] = []
    nuhlpb_json['data']['Hlpb']['interpolation_entries'] = []
    nuhlpb_json['data']['Hlpb']['list1'] = []
    nuhlpb_json['data']['Hlpb']['list2'] = []

    for index, arma_aim_entry in enumerate(shbd.aim_entries):
        arma_aim_entry: AimEntry
        json_aim_entry = {}
        json_aim_entry['name'] = arma_aim_entry.name
        json_aim_entry['aim_bone_name1'] = arma_aim_entry.aim_bone_name1
        json_aim_entry['aim_bone_name2'] = arma_aim_entry.aim_bone_name2
        json_aim_entry['aim_type1'] = arma_aim_entry.aim_type1
        json_aim_entry['aim_type2'] = arma_aim_entry.aim_type2
        json_aim_entry['target_bone_name1'] = arma_aim_entry.target_bone_name1
        json_aim_entry['target_bone_name2'] = arma_aim_entry.target_bone_name2
        json_aim_entry['unk1'] = arma_aim_entry.unk1
        json_aim_entry['unk2'] = arma_aim_entry.unk2
        json_aim_entry['unk3'] = arma_aim_entry.aim.x
        json_aim_entry['unk4'] = arma_aim_entry.aim.y
        json_aim_entry['unk5'] = arma_aim_entry.aim.z
        json_aim_entry['unk6'] = arma_aim_entry.up.x
        json_aim_entry['unk7'] = arma_aim_entry.up.y
        json_aim_entry['unk8'] = arma_aim_entry.up.z
        json_aim_entry['unk9'] = arma_aim_entry.quat1.x
        json_aim_entry['unk10'] = arma_aim_entry.quat1.y
        json_aim_entry['unk11'] = arma_aim_entry.quat1.z
        json_aim_entry['unk12'] = arma_aim_entry.quat1.w
        json_aim_entry['unk13'] = arma_aim_entry.quat2.x
        json_aim_entry['unk14'] = arma_aim_entry.quat2.y
        json_aim_entry['unk15'] = arma_aim_entry.quat2.z
        json_aim_entry['unk16'] = arma_aim_entry.quat2.w
        json_aim_entry['unk17'] = arma_aim_entry.unk17
        json_aim_entry['unk18'] = arma_aim_entry.unk18
        json_aim_entry['unk19'] = arma_aim_entry.unk19
        json_aim_entry['unk20'] = arma_aim_entry.unk20
        json_aim_entry['unk21'] = arma_aim_entry.unk21
        json_aim_entry['unk22'] = arma_aim_entry.unk22
        nuhlpb_json['data']['Hlpb']['aim_entries'].append(json_aim_entry)
        nuhlpb_json['data']['Hlpb']['list1'].append(index)
        nuhlpb_json['data']['Hlpb']['list2'].append(0)

    for index, arma_interpolation_entry in enumerate(shbd.interpolation_entries):
        arma_interpolation_entry: InterpolationEntry
        arma_interpolation_entry_aoi: Vector = arma_interpolation_entry.constraint_axes
        arma_interpolation_entry_quat1: Vector = arma_interpolation_entry.quat1
        arma_interpolation_entry_quat2: Vector = arma_interpolation_entry.quat2
        arma_interpolation_entry_range_min: Vector = arma_interpolation_entry.range_min
        arma_interpolation_entry_range_max: Vector = arma_interpolation_entry.range_max
        json_interpolation_entry = {}
        json_interpolation_entry['name'] = arma_interpolation_entry.name
        json_interpolation_entry['bone_name'] = arma_interpolation_entry.parent_bone_name1
        json_interpolation_entry['root_bone_name'] = arma_interpolation_entry.parent_bone_name2
        json_interpolation_entry['parent_bone_name'] = arma_interpolation_entry.source_bone_name
        json_interpolation_entry['driver_bone_name'] = arma_interpolation_entry.target_bone_name
        json_interpolation_entry['unk_type'] = arma_interpolation_entry.unk_type
        json_interpolation_entry['aoi'] = {}
        json_interpolation_entry['aoi']['x'] = arma_interpolation_entry_aoi.x
        json_interpolation_entry['aoi']['y'] = arma_interpolation_entry_aoi.y
        json_interpolation_entry['aoi']['z'] = arma_interpolation_entry_aoi.z
        json_interpolation_entry['quat1'] = {}
        json_interpolation_entry['quat1']['x'] = arma_interpolation_entry_quat1.x
        json_interpolation_entry['quat1']['y'] = arma_interpolation_entry_quat1.y
        json_interpolation_entry['quat1']['z'] = arma_interpolation_entry_quat1.z
        json_interpolation_entry['quat1']['w'] = arma_interpolation_entry_quat1.w
        json_interpolation_entry['quat2'] = {}
        json_interpolation_entry['quat2']['x'] = arma_interpolation_entry_quat2.x
        json_interpolation_entry['quat2']['y'] = arma_interpolation_entry_quat2.y
        json_interpolation_entry['quat2']['z'] = arma_interpolation_entry_quat2.z
        json_interpolation_entry['quat2']['w'] = arma_interpolation_entry_quat2.w
        json_interpolation_entry['range_min'] = {}
        json_interpolation_entry['range_min']['x'] = arma_interpolation_entry_range_min.x
        json_interpolation_entry['range_min']['y'] = arma_interpolation_entry_range_min.y
        json_interpolation_entry['range_min']['z'] = arma_interpolation_entry_range_min.z
        json_interpolation_entry['range_max'] = {}
        json_interpolation_entry['range_max']['x'] = arma_interpolation_entry_range_max.x
        json_interpolation_entry['range_max']['y'] = arma_interpolation_entry_range_max.y
        json_interpolation_entry['range_max']['z'] = arma_interpolation_entry_range_max.z
        nuhlpb_json['data']['Hlpb']['interpolation_entries'].append(json_interpolation_entry)
        nuhlpb_json['data']['Hlpb']['list1'].append(index)
        nuhlpb_json['data']['Hlpb']['list2'].append(1)

    save_ssbh_json(nuhlpb_json, str(folder.joinpath('model.nuhlpb.tmp.json')), str(folder.joinpath('model.nuhlpb')))

