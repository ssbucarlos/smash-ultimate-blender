import bpy
import ssbh_data_py

from bpy.types import PropertyGroup, ShaderNodeTexImage, ShaderNodeUVMap, ShaderNodeValue, ShaderNodeOutputMaterial
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
    param_id_name: StringProperty(

    )
class SUB_PG_matl_float(PropertyGroup):
    #socket_name: StringProperty()
    ui_name: StringProperty(
    )
    value: FloatProperty(
        soft_min=0.0,
        soft_max=1.0,
        update=update_active_material,
    )
    param_id_name: StringProperty(

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
    param_id_name: StringProperty(

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
    wrap_r: EnumProperty(
        name="R",
        description="Wrap R",
        items=wrap_types,
        default='Repeat',
        update=update_active_material,
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

    param_id_name: StringProperty(

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
    param_id_name: StringProperty(

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
    param_id_name: StringProperty(

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
            new_bool.param_id_name = bool_param.param_id.name
            
    def add_floats(self, float_params: list[ssbh_data_py.matl_data.FloatParam]):
        for float_param in float_params:
            new_float: SUB_PG_matl_float = self.floats.add()
            new_float.value = float_param.data
            new_float.ui_name = param_id_to_ui_name[float_param.param_id.value]
            new_float.param_id_name = float_param.param_id.name
            
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
            new_texture.param_id_name = texture_param.param_id.name

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
            new_sampler.param_id_name = sampler_param.param_id.name

    def add_blend_states(self, blend_states: list[ssbh_data_py.matl_data.BlendStateParam]):
        for blend_state in blend_states:
            new_blend_state: SUB_PG_matl_blend_state = self.blend_states.add()
            new_blend_state.ui_name = param_id_to_ui_name[blend_state.param_id.value]
            new_blend_state.alpha_sample_to_coverage = blend_state.data.alpha_sample_to_coverage
            new_blend_state.source_color = blend_state.data.source_color.name
            new_blend_state.destination_color = blend_state.data.destination_color.name
            new_blend_state.param_id_name = blend_state.param_id.name

    def add_rasterizer_states(self, rasterizer_states: list[ssbh_data_py.matl_data.RasterizerStateParam]):
        for rasterizer_state in rasterizer_states:
            new_rasterizer_state: SUB_PG_matl_rasterizer_state = self.rasterizer_states.add()
            new_rasterizer_state.ui_name = param_id_to_ui_name[rasterizer_state.param_id.value]
            new_rasterizer_state.depth_bias = rasterizer_state.data.depth_bias
            new_rasterizer_state.cull_mode = rasterizer_state.data.cull_mode.name
            new_rasterizer_state.fill_mode = rasterizer_state.data.fill_mode.name
            new_rasterizer_state.param_id_name = rasterizer_state.param_id.name

    def set_shader_label(self, shader_label):
        self.shader_label = shader_label

