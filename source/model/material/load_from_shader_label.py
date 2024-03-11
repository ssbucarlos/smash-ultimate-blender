import bpy
import sqlite3

from pathlib import Path
from typing import Any

from ....dependencies import ssbh_data_py
from .sub_matl_data import *
from .matl_params import vector_param_id_values, param_id_to_ui_name, vector_param_id_value_to_default_value
from ..export_model import default_texture
from .matl_params import *
from .create_blender_materials_from_matl import setup_blender_material_settings, setup_blender_material_node_tree, get_shader_db_file_path, get_vertex_attributes

"""
def get_shader_db_file_path():
    # This file was generated with duplicates removed to optimize space.
    # https://github.com/ScanMountGoat/Smush-Material-Research#shader-database
    this_file_path = Path(__file__)
    return this_file_path.parent.parent.parent.joinpath('shader_file').joinpath('Nufx.db').resolve()
"""

def is_valid_shader_label(operator: bpy.types.Operator, shader_label: str) -> bool:
    if len(shader_label) > len("SFX_PBS_0100000008008269_opaque"):
        operator.report({'ERROR'}, f'Shader Label "{shader_label}" was too long!')
        return False
    if len(shader_label) < len("SFX_PBS_0100000008008269"):
        operator.report({'ERROR'}, f'Shader Label "{shader_label}" was too short!')
        return False
    if len(shader_label) != len("SFX_PBS_0100000008008269"):
        suffixes = ["_opaque", "_far", "_sort", "_near"]
        if not any(shader_label.endswith(suffix) for suffix in suffixes):
            operator.report({'ERROR'}, f'Shader Label "{shader_label}" has an invalid suffix!')
            return False
    with sqlite3.connect(get_shader_db_file_path()) as con:
        sql = """
            SELECT *
            FROM ShaderProgram s 
            WHERE s.Name = ?
            """
        ret = [row[0] for row in con.execute(sql, (shader_label[:len('SFX_PBS_0000000000000080')],)).fetchall()]
        if len(ret) == 0:
            operator.report({'ERROR'}, f'Shader Label "{shader_label}" was not in the database!')
            return False
    return True


def get_material_parameter_ids(shader_label: str) -> set[int]:
    # Query the shader database for attribute information.
    # Using SQLite is much faster than iterating through the JSON dump.
    with sqlite3.connect(get_shader_db_file_path()) as con:
        # Construct a query to find all the vertex attributes for this shader.
        # Invalid shaders will return an empty list.
        sql = """
            SELECT m.ParamId
            FROM MaterialParameter m 
            INNER JOIN ShaderProgram s ON m.ShaderProgramID = s.ID 
            WHERE s.Name = ?
            """
        # The database has a single entry for each program, so don't include the render pass tag.
        return {row[0] for row in con.execute(sql, (shader_label[:len('SFX_PBS_0000000000000080')],)).fetchall()}


def create_sub_matl_data_from_shader_label(material: bpy.types.Material, shader_label: str):

    sub_matl_data: SUB_PG_sub_matl_data = material.sub_matl_data

    collections = (
        sub_matl_data.bools,
        sub_matl_data.floats,
        sub_matl_data.vectors,
        sub_matl_data.textures,
        sub_matl_data.samplers,
        sub_matl_data.blend_states,
        sub_matl_data.rasterizer_states,
    )
    needed_param_ids: set[int] = get_material_parameter_ids(shader_label)
    # Remove Un-Needed Attributes
    for collection in collections:
        prop_names_to_remove: set[str] = set(name for name,prop in collection.items() if prop.param_id_value not in needed_param_ids)
        for prop_name in prop_names_to_remove:
            sub_matl_prop_index = collection.find(prop_name)
            collection.remove(sub_matl_prop_index)

    # Add Missing ones
    current_param_ids: set[int] = {sub_matl_prop.param_id_value for c in collections for sub_matl_prop in c}
    missing_param_ids = needed_param_ids - current_param_ids
    for missing_param_id in missing_param_ids:
        if missing_param_id in bool_param_id_values:
            sub_matl_data.add_bool(
                ssbh_data_py.matl_data.BooleanParam(
                    param_id=ssbh_data_py.matl_data.ParamId.from_value(missing_param_id),
                    data=bool_param_id_value_to_default_value[missing_param_id]
                )
            )
        elif missing_param_id in float_param_id_values:
            sub_matl_data.add_float(
                ssbh_data_py.matl_data.FloatParam(
                    param_id=ssbh_data_py.matl_data.ParamId.from_value(missing_param_id),
                    data=float_param_id_value_to_default_value[missing_param_id]
                )
            )
        elif missing_param_id in vector_param_id_values:
            sub_matl_data.add_vector(
                ssbh_data_py.matl_data.Vector4Param(
                    param_id=ssbh_data_py.matl_data.ParamId.from_value(missing_param_id),
                    data=vector_param_id_value_to_default_value[missing_param_id],
                )
            )
        elif missing_param_id in texture_param_id_values:
            tex_param_id = ssbh_data_py.matl_data.ParamId.from_value(missing_param_id)
            default_texture_name = default_texture(tex_param_id.name)
            default_image = bpy.data.images.get(default_texture_name)
            sub_matl_data.add_texture(
                texture_param=ssbh_data_py.matl_data.TextureParam(
                    param_id=tex_param_id,
                    data=default_texture_name,
                ),
                texture_name_to_image_dict={default_texture_name:default_image},
            )

        elif missing_param_id in sampler_param_id_values:
            param_id = ssbh_data_py.matl_data.ParamId.from_value(missing_param_id)
            new_sampler: SUB_PG_matl_sampler = sub_matl_data.samplers.add()
            new_sampler.name = param_id.name
            new_sampler.param_id_name = param_id.name
            new_sampler.param_id_value = param_id.value
            new_sampler.ui_name = param_id_to_ui_name[param_id.value]
            new_sampler.node_name = param_id.name
            new_sampler.sampler_number = int(param_id.name.split('Sampler')[1])
            
        elif missing_param_id in blend_state_param_id_values:
            param_id = ssbh_data_py.matl_data.ParamId.from_value(missing_param_id)
            new_blend_state: SUB_PG_matl_blend_state = sub_matl_data.blend_states.add()
            new_blend_state.name = param_id.name
            new_blend_state.ui_name = param_id_to_ui_name[param_id.value]
            new_blend_state.param_id_name = param_id.name
            new_blend_state.param_id_value = param_id.value

        elif missing_param_id in rasterizer_state_param_id_values:
            param_id = ssbh_data_py.matl_data.ParamId.from_value(missing_param_id)
            new_rasterizer_state: SUB_PG_matl_rasterizer_state = sub_matl_data.rasterizer_states.add()
            new_rasterizer_state.name = param_id.name
            new_rasterizer_state.ui_name = param_id_to_ui_name[param_id.value]
            new_rasterizer_state.param_id_name = param_id.name
            new_rasterizer_state.param_id_value = param_id.value

    # Refresh needed vertex attributes
    sub_matl_data.vertex_attributes.clear()
    attrs = get_vertex_attributes(shader_label)
    sub_matl_data.add_vertex_attributes(attrs)
    
    # Relabel
    if len(shader_label) == len("SFX_PBS_0100000008008269"):
        shader_label = f'{shader_label}_opaque'
    sub_matl_data.set_shader_label(shader_label)

    # Reload Material
    setup_blender_material_settings(material)
    setup_blender_material_node_tree(material)
    return