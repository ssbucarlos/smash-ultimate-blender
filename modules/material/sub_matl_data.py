import bpy
import ssbh_data_py

from bpy.types import PropertyGroup, ShaderNodeTexImage, ShaderNodeUVMap, ShaderNodeValue
from bpy.props import (
    PointerProperty, BoolProperty, StringProperty, FloatVectorProperty,
    FloatProperty, CollectionProperty, EnumProperty, IntProperty
)
from bpy_extras import image_utils
from enum import Enum
from pathlib import Path
from .matl_params import param_id_to_ui_name, texture_param_name_to_socket_params, vec4_param_name_to_socket_params
from . import matl_enums, matl_params

def update_active_material(self, context):
    '''
    Manually setting the PointerProperties, such as during model import, will call
    this update method, so the None check is necesary.
    '''
    active_mat:bpy.types.Material = bpy.context.object.active_material
    if active_mat is None:
        return
    sub_matl_data: SUB_PG_sub_matl_data = active_mat.sub_matl_data
    
    for texture in sub_matl_data.textures:
        texture_node = active_mat.node_tree.nodes.get(texture.node_name)
        if texture_node is not None:
            texture_node.image = texture.image

class SUB_PG_matl_bool(PropertyGroup):
    socket_name: StringProperty(

    )
    ui_name: StringProperty(

    )
    value: BoolProperty(

    )
class SUB_PG_matl_float(PropertyGroup):
    socket_name: StringProperty(
    )
    ui_name: StringProperty(
    )
    value: FloatProperty(
        soft_min=0.0,
        soft_max=1.0,
        update=update_active_material,
    )

class SUB_PG_matl_vector(PropertyGroup):
    param_id_name: StringProperty(
        
    )
    ui_name: StringProperty(
        description="The user-friendlier name of this custom vector",
    )
    value: FloatVectorProperty(
        default=(0,0,0,0),
        size=4,
        subtype='COLOR_GAMMA',
        update=update_active_material,
        soft_max=1.0,
        soft_min=0.0,
    )

class SUB_PG_matl_texture(PropertyGroup):
    node_name: StringProperty(
        default="",
        description="The name the shader node of this texture",
    )
    ui_name: StringProperty(
        default="",
        description="The user-friendlier name of this texture",
    )
    image: PointerProperty(
        description="Select the Image",
        type=bpy.types.Image,
        update=update_active_material,
    )
    texture_number: IntProperty(
        default = 0,
        description="0 thru 19"
    )
from ...shader_nodes.custom_sampler_node import wrap_types, min_filter_types, mag_filter_types, max_anisotropy_levels
class SUB_PG_matl_sampler(PropertyGroup):
    node_name: StringProperty(
        default="",
        description="The name the shader node of this sampler",
    )
    ui_name: StringProperty(
        default="",
        description="The user-friendlier name of this sampler",
    )
    sampler_number: IntProperty(
        default = 0,
        description="0 thru 19"
    )
    wrap_s: EnumProperty(
        name="S",
        description="Wrap S",
        items=wrap_types,
        default='Repeat',
        update=update_active_material,
    )
    wrap_t: EnumProperty(
        name="T",
        description="Wrap T",
        items=wrap_types,
        default='Repeat',
        update=update_active_material,
    )
    wrap_r: EnumProperty(
        name="R",
        description="Wrap R",
        items=wrap_types,
        default='Repeat',
        update=update_active_material,
    )
    
    min_filter: EnumProperty(
        name='Min',
        description='Min Filter',
        items=min_filter_types,
        default='Nearest',
        update=update_active_material,
    )
    
    mag_filter: EnumProperty(
        name='Mag',
        description='Mag Filter',
        items=mag_filter_types,
        default='Nearest',
        update=update_active_material,
    )
    
    anisotropic_filtering: BoolProperty(
        name='Anisotropic Filtering',
        description='Anisotropic Filtering',
        default=False,
        update=update_active_material,
    )
    
    border_color: FloatVectorProperty(
        name='Border Color',
        description='Border Color',
        subtype='COLOR',
        size=4,
        default=(1.0,1.0,1.0,1.0),
        soft_max=1.0,
        soft_min=0.0,
        update=update_active_material,
    )

    lod_bias: FloatProperty(
        name='LOD Bias',
        description='LOD Bias',
        default=0.0,
        update=update_active_material,
    )
    
    max_anisotropy: EnumProperty(
        name='Max Anisotropy',
        description='Max Anisotropy',
        items=max_anisotropy_levels,
        default='One',
        update=update_active_material,
    )



class SUB_PG_matl_blend_state(PropertyGroup):
    ui_name: StringProperty(
        default="",
        description="The user-friendlier name of this blend state",
    )
    source_color: EnumProperty(
        items=matl_enums.blend_factor_enum,
    )
    destination_color: EnumProperty(
        items=matl_enums.blend_factor_enum,
    )
    alpha_sample_to_coverage: BoolProperty(
    )

    

class SUB_PG_matl_rasterizer_state(PropertyGroup):
    ui_name: StringProperty(

    )
    cull_mode: EnumProperty(
        items=matl_enums.cull_mode_enum,
    )
    depth_bias: FloatProperty(
        default=0.0
    )
    fill_mode: EnumProperty(
        items=matl_enums.fill_mode_enum,
    )


class SUB_PG_sub_matl_data(PropertyGroup):
    bools: CollectionProperty(
        type=SUB_PG_matl_bool
    ) 
    floats: CollectionProperty(
        type=SUB_PG_matl_float
    )
    vectors: CollectionProperty(
        type=SUB_PG_matl_vector
    )
    textures: CollectionProperty(
        type=SUB_PG_matl_texture
    )
    samplers: CollectionProperty(
        type=SUB_PG_matl_sampler
    )
    blend_states: CollectionProperty(
        type=SUB_PG_matl_blend_state
    )
    rasterizer_states: CollectionProperty(
        type=SUB_PG_matl_rasterizer_state
    )
    shader_label: StringProperty(
        name="Shader Label",
        default="",
    )

    def add_bools(self, bool_params: list[ssbh_data_py.matl_data.BooleanParam]):
        for bool_param in bool_params:
            new_bool: SUB_PG_matl_bool = self.bools.add()
            new_bool.value = bool_param.data
            new_bool.ui_name = param_id_to_ui_name[bool_param.param_id.value]
            
    def add_floats(self, float_params: list[ssbh_data_py.matl_data.FloatParam]):
        for float_param in float_params:
            new_float: SUB_PG_matl_float = self.floats.add()
            new_float.value = float_param.data
            new_float.ui_name = param_id_to_ui_name[float_param.param_id.value]
    def add_vectors(self, vector_params: list[ssbh_data_py.matl_data.Vector4Param]):
        for vector_param in vector_params:
            new_vector: SUB_PG_matl_vector = self.vectors.add()
            new_vector.value = vector_param.data
            new_vector.ui_name = param_id_to_ui_name[vector_param.param_id.value]
            new_vector.param_id_name = vector_param.param_id.name
                
    def add_textures(self, texture_params:list[ssbh_data_py.matl_data.TextureParam], texture_name_to_image_dict):
        for texture_param in texture_params:
            new_texture: SUB_PG_matl_texture = self.textures.add()
            new_texture.image = texture_name_to_image_dict[texture_param.data]
            new_texture.image.preview_ensure() # Previews aren't generated till needed / forced.
            new_texture.ui_name = param_id_to_ui_name[texture_param.param_id.value]
            new_texture.node_name = texture_param.param_id.name
            new_texture.texture_number = int(texture_param.param_id.name.split('Texture')[1])

    def add_samplers(self, sampler_params: list[ssbh_data_py.matl_data.SamplerParam]):
        for sampler_param in sampler_params:
            new_sampler: SUB_PG_matl_sampler = self.samplers.add()
            new_sampler.ui_name = param_id_to_ui_name[sampler_param.param_id.value]
            new_sampler.node_name = sampler_param.param_id.name
            new_sampler.sampler_number = int(sampler_param.param_id.name.split('Sampler')[1])
            sampler_data = sampler_param.data
            new_sampler.wrap_s = sampler_data.wraps.name
            new_sampler.wrap_t = sampler_data.wrapt.name
            new_sampler.wrap_r = sampler_data.wrapr.name
            new_sampler.min_filter = sampler_data.min_filter.name
            new_sampler.mag_filter = sampler_data.mag_filter.name
            new_sampler.anisotropic_filtering = sampler_data.max_anisotropy is not None
            new_sampler.max_anisotropy = sampler_data.max_anisotropy.name if sampler_data.max_anisotropy else 'One'
            new_sampler.border_color = tuple(sampler_data.border_color)
            new_sampler.lod_bias = sampler_data.lod_bias

    def add_blend_states(self, blend_states: list[ssbh_data_py.matl_data.BlendStateParam]):
        for blend_state in blend_states:
            new_blend_state: SUB_PG_matl_blend_state = self.blend_states.add()
            new_blend_state.ui_name = param_id_to_ui_name[blend_state.param_id.value]
            new_blend_state.alpha_sample_to_coverage = blend_state.data.alpha_sample_to_coverage
            new_blend_state.source_color = blend_state.data.source_color.name
            new_blend_state.destination_color = blend_state.data.destination_color.name

    def add_rasterizer_states(self, rasterizer_states: list[ssbh_data_py.matl_data.RasterizerStateParam]):
        for rasterizer_state in rasterizer_states:
            new_rasterizer_state: SUB_PG_matl_rasterizer_state = self.rasterizer_states.add()
            new_rasterizer_state.ui_name = param_id_to_ui_name[rasterizer_state.param_id.value]
            new_rasterizer_state.depth_bias = rasterizer_state.data.depth_bias
            new_rasterizer_state.cull_mode = rasterizer_state.data.cull_mode.name
            new_rasterizer_state.fill_mode = rasterizer_state.data.fill_mode.name

    def set_shader_label(self, shader_label):
        self.shader_label = shader_label

def import_material_images(ssbh_matl, dir) -> dict[str, bpy.types.Image]:
    texture_name_to_image_dict = {}
    texture_name_set = set()

    for ssbh_mat_entry in ssbh_matl.entries:
        for attribute in ssbh_mat_entry.textures:
            texture_name_set.add(attribute.data)

    for texture_name in texture_name_set:
        image = image_utils.load_image(texture_name + '.png', dir, place_holder=True, check_existing=False)  
        texture_name_to_image_dict[texture_name] = image

    return texture_name_to_image_dict

def get_discard_shaders():
    global discard_shaders
    try:
        discard_shaders
    except NameError:
        this_file_path = Path(__file__)
        discard_shaders_file = this_file_path.parent.parent.parent.joinpath('shader_file').joinpath('shaders_discard_v13.0.1.txt').resolve()
        with open(discard_shaders_file, 'r') as f:
            discard_shaders = {line.strip() for line in f.readlines()}
    return discard_shaders

def get_blend_method(shader_label: str, blend_states: list[SUB_PG_matl_blend_state]):
    # TODO: Access blenders internal enum instead? Or use a cleaner enum method
    BlendMethod = Enum('BlendMethod', 'OPAQUE HASHED CLIP BLEND')
    if len(blend_states) != 1: # no vanilla ultimate shader has more than one blend state
        return BlendMethod.OPAQUE.name
    
    discard_shaders = get_discard_shaders()
    # Trims the trailing '_OPAQUE', '_SORT', etc.
    if shader_label[:len('SFX_PBS_0000000000000080')] in discard_shaders:
        return BlendMethod.CLIP.name
    
    blend_state_0 = blend_states[0]
    if blend_state_0.alpha_sample_to_coverage is True:
        return BlendMethod.HASHED.name
    
    if blend_state_0.destination_color == ssbh_data_py.matl_data.BlendFactor.OneMinusSourceAlpha.name:
        # In theory, its supposed to be 'BLEND', but this more often than not looks wrong.
        # I don't understand shaders well enough to really know why it doesn't work in EEVEE.
        # So return 'HASHED' instead for now. The user can manually adjust to 'BLEND' after import.
        return BlendMethod.HASHED.name
    
    return BlendMethod.OPAQUE.name

def setup_blender_material_settings(material: bpy.types.Material):
    sub_matl_data: SUB_PG_sub_matl_data = material.sub_matl_data
    # Blend Method
    material.blend_method = get_blend_method(sub_matl_data.shader_label, sub_matl_data.blend_states)
    # Back Face Culling
    if len(sub_matl_data.rasterizer_states) == 1:
        if sub_matl_data.rasterizer_states[0].cull_mode == ssbh_data_py.matl_data.CullMode.Back.name:
            material.use_backface_culling = True

def get_matched_sampler(sub_matl_data: SUB_PG_sub_matl_data, texture: SUB_PG_matl_texture):
    sampler: SUB_PG_matl_sampler
    for sampler in sub_matl_data.samplers:
        if texture.texture_number == sampler.sampler_number:
            return sampler

def setup_blender_material_node_tree(material: bpy.types.Material):
    from ...operators.master_shader import create_master_shader, get_master_shader_name
    sub_matl_data: SUB_PG_sub_matl_data = material.sub_matl_data
    
    # Make Master Shader if its not already made
    create_master_shader()
    
    # Clone Master Shader
    master_shader_name = get_master_shader_name()
    master_node_group = bpy.data.node_groups.get(master_shader_name)
    clone_group = master_node_group.copy()

    # Setup Clone
    clone_group.name = sub_matl_data.shader_label

    # Prep the node_tree for the new nodes
    material.use_nodes = True
    material.node_tree.nodes.clear()

    # Add the new Nodes
    nodes = material.node_tree.nodes
    
    material_output_node = nodes.new('ShaderNodeOutputMaterial')
    material_output_node.location = (900,0)

    node_group_node = nodes.new('ShaderNodeGroup')
    node_group_node.name = 'smash_ultimate_shader'
    node_group_node.width = 600
    node_group_node.location = (-300, 300)
    node_group_node.node_tree = clone_group

    links = material.node_tree.links
    links.new(material_output_node.inputs[0], node_group_node.outputs[0])

    texture: SUB_PG_matl_texture
    ParamId = ssbh_data_py.matl_data.ParamId
    created_node_rows = 0
    texture_node_row_width = 500
    for texture in sub_matl_data.textures:
        # Create Texture Node
        texture_node: ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
        texture_node.location = (-800, 1000 - (texture_node_row_width * created_node_rows))
        texture_node.name = texture.node_name
        texture_node.label = texture.ui_name
        texture_node.image = texture.image

        # For now, manually set the colorspace types....
        linear_textures_names = {ParamId.Texture4.name, ParamId.Texture6.name}
        if texture.node_name in linear_textures_names:
            texture_node.image.colorspace_settings.name = 'Linear'
            texture_node.image.alpha_mode = 'CHANNEL_PACKED'
        
        # Create UV Map Node
        uv_map_node: ShaderNodeUVMap = nodes.new("ShaderNodeUVMap")
        uv_map_node.name = f'{texture.node_name}_uv_map'
        uv_map_node.location = (texture_node.location[0] - 1200, texture_node.location[1])
        uv_map_node.label = f'{texture.node_name} UV Map'
        
        # For now, manually set the UV maps
        if texture.node_name == ParamId.Texture9.name:
            uv_map_node.uv_map = 'bake1'
        elif texture.node_name == ParamId.Texture1.name:
            uv_map_node.uv_map = 'uvSet'
        else:
            uv_map_node.uv_map = 'map1'
        
        # Create UV Transform Node
        # Also set the default_values here. I know it makes more sense to have the default_values
        # be in the init func of the node itself, but it just doesn't work there lol
        from ...shader_nodes import custom_uv_transform_node
        uv_transform_node = nodes.new(custom_uv_transform_node.SUB_CSN_ultimate_uv_transform.bl_idname)
        uv_transform_node.name = 'uv_transform_node'
        uv_transform_node.label = 'UV Transform' + texture.node_name.split('Texture')[1]
        uv_transform_node.location = (texture_node.location[0] - 900, texture_node.location[1])
        uv_transform_node.inputs[0].default_value = 1.0 # Scale X
        uv_transform_node.inputs[1].default_value = 1.0 # Scale Y

        # Create Sampler Node
        from ...shader_nodes import custom_sampler_node
        
        matched_sampler: SUB_PG_matl_sampler = get_matched_sampler(sub_matl_data, texture)
        sampler_node:custom_sampler_node.SUB_CSN_ultimate_sampler = nodes.new(custom_sampler_node.SUB_CSN_ultimate_sampler.bl_idname)
        sampler_node.name = 'sampler_node'
        sampler_node.label = 'Sampler' + texture.node_name.split('Texture')[1]
        sampler_node.location = (texture_node.location[0] - 600, texture_node.location[1])
        sampler_node.width = 500

        sampler_node.wrap_s = matched_sampler.wrap_s
        sampler_node.wrap_t = matched_sampler.wrap_t
        sampler_node.wrap_r = matched_sampler.wrap_r
        sampler_node.min_filter = matched_sampler.min_filter
        sampler_node.mag_filter = matched_sampler.mag_filter
        sampler_node.anisotropic_filtering = matched_sampler.max_anisotropy is not None
        sampler_node.max_anisotropy = matched_sampler.max_anisotropy if matched_sampler.max_anisotropy else 'One'
        sampler_node.border_color = matched_sampler.border_color
        sampler_node.lod_bias = matched_sampler.lod_bias 

        # Link these nodes together
        links.new(uv_transform_node.inputs[4], uv_map_node.outputs[0])
        links.new(sampler_node.inputs['UV Input'], uv_transform_node.outputs[0])
        links.new(texture_node.inputs[0], sampler_node.outputs[0])
        links.new(node_group_node.inputs[texture_param_name_to_socket_params[texture.node_name].rgb_socket_name], texture_node.outputs['Color'])
        links.new(node_group_node.inputs[texture_param_name_to_socket_params[texture.node_name].alpha_socket_name], texture_node.outputs['Alpha'])

        created_node_rows = created_node_rows + 1

    created_vector_rows = 0
    vector: SUB_PG_matl_vector
    for vector_index, vector in enumerate(sub_matl_data.vectors):
        for axis_index, axis in enumerate(['X', 'Y', 'Z', 'W']):
            # Create the value node
            value_node: ShaderNodeValue = nodes.new('ShaderNodeValue')
            value_node.name = f"{vector.param_id_name}_{axis}"
            value_node.label = f"{vector.ui_name} {axis}"
            value_node.location = (-1500 + (200 * axis_index), 1000 - (texture_node_row_width * (created_node_rows-1)) - 300 - (100 * created_vector_rows))
            
            socket_params = vec4_param_name_to_socket_params[vector.param_id_name]
            if axis is 'X':
                socket_name = socket_params.x_socket_name
            elif axis is 'Y':
                socket_name = socket_params.y_socket_name
            elif axis is 'Z':
                socket_name = socket_params.z_socket_name
            elif axis is 'W':
                socket_name = socket_params.w_socket_name

            links.new(node_group_node.inputs[socket_name], value_node.outputs[0])

            # Setup Driver
            driver_fcurve: bpy.types.FCurve = value_node.outputs[0].driver_add('default_value')
            var = driver_fcurve.driver.variables.new()
            var.name = 'var'
            target = var.targets[0]
            target.id_type = 'MATERIAL'
            target.id = material
            target.data_path = f'sub_matl_data.vectors[{vector_index}].value[{axis_index}]'
            driver_fcurve.driver.expression = f'{var.name}'
        created_vector_rows = created_vector_rows + 1


def create_blender_materials_from_matl(ssbh_matl: ssbh_data_py.matl_data.MatlData) -> dict[str, bpy.types.Material]:
    '''
    Creates a blender material with the sub_matl_data filled out for every entry in the ssbh_matl.
    Returns a dictionary mapping the material_label to the created blender material to handle multiple models 
    having the same material name.
    '''
    # Make new Blender Materials
    material_label_to_material: dict[str, bpy.types.Material] = \
        {entry.material_label: bpy.data.materials.new(entry.material_label) for entry in ssbh_matl.entries}
    # Import the texture PNGs
    texture_name_to_image_dict = import_material_images(ssbh_matl, bpy.context.scene.sub_scene_properties.model_import_folder_path)
    # Fill out the sub_matl_data of each material
    for entry in ssbh_matl.entries:
        sub_matl_data: SUB_PG_sub_matl_data = material_label_to_material[entry.material_label].sub_matl_data
        sub_matl_data.set_shader_label(entry.shader_label)
        sub_matl_data.add_bools(entry.booleans)
        sub_matl_data.add_floats(entry.floats)
        sub_matl_data.add_vectors(entry.vectors)
        sub_matl_data.add_textures(entry.textures, texture_name_to_image_dict)
        sub_matl_data.add_samplers(entry.samplers)
        sub_matl_data.add_blend_states(entry.blend_states)
        sub_matl_data.add_rasterizer_states(entry.rasterizer_states)
 
    # Make the blender material settings
    for material_label, material in material_label_to_material.items():
        setup_blender_material_settings(material)
        setup_blender_material_node_tree(material)

    return material_label_to_material
