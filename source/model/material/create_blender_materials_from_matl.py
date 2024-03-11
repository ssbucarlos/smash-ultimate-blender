import bpy
import sqlite3
import re 

from bpy.types import ShaderNodeTexImage, ShaderNodeUVMap, ShaderNodeValue, ShaderNodeOutputMaterial, ShaderNodeVertexColor, Operator
from bpy_extras import image_utils

from enum import Enum
from pathlib import Path
from subprocess import CalledProcessError

from ....dependencies import ssbh_data_py
from .matl_params import texture_param_name_to_socket_params, vec4_param_name_to_socket_params
from .sub_matl_data import *
from .texture.convert_nutexb_to_png import convert_nutexb_to_png
from .texture.default_textures import generated_default_texture_name_value

"""generated_default_texture_name_value: dict[str, tuple[float, float, float, float]] = {
     "/common/shader/sfxpbs/default_black": (0, 0, 0, 0),
     "/common/shader/sfxpbs/default_color": (1,1,1,1),
     "/common/shader/sfxpbs/default_color2": (1,1,1,1),
     "/common/shader/sfxpbs/default_color3": (1,1,1,1),
     "/common/shader/sfxpbs/default_color4": (1,1,1,1),
     "/common/shader/sfxpbs/default_diffuse2": (1,1,0,1), # This is supposed to be a yellow and white checkerboad texture, but i can't imagine any user actually using it tbh tbh
     "/common/shader/sfxpbs/default_gray": (.5, .5, .5, 1),
     "/common/shader/sfxpbs/default_metallicbg": (0, 1, 1, .25),
     "/common/shader/sfxpbs/default_normal": (0.5, 0.5, 1, 1),
     "/common/shader/sfxpbs/default_params": (0, 1, 1, .25),
     "/common/shader/sfxpbs/default_params_r000_g025_b100": (0, 0.25, 1, 1),
     "/common/shader/sfxpbs/default_params_r100_g025_b100": (1, 0.25, 1, 1),
     "/common/shader/sfxpbs/default_params2": (1,1,1,1),
     "/common/shader/sfxpbs/default_params3": (0, 0.5, 1, .25),
     "/common/shader/sfxpbs/default_specular": (0.25 , 0.25, 0.25, 1.0),
     "/common/shader/sfxpbs/default_white": (1.0, 1.0, 1.0, 1.0),
     "/common/shader/sfxpbs/fighter/default_normal": (0.5, 0.5, 1.0, 1.0),
     "/common/shader/sfxpbs/fighter/default_params": (0.0, 1.0, 1.0, 0.25),
     "#replace_cubemap": (1,1,1,1), # Not correct, but it needs to be here in case the user wants to use it without importing a model first
}"""

def get_shader_db_file_path():
    # This file was generated with duplicates removed to optimize space.
    # https://github.com/ScanMountGoat/Smush-Material-Research#shader-database
    this_file_path = Path(__file__)
    return this_file_path.parent.joinpath('shader_file').joinpath('Nufx.db').resolve()

def create_default_texture(texture_name: str, value: tuple[float, float, float, float]):
    if texture_name not in bpy.data.images.keys():
        image = bpy.data.images.new(texture_name, 8, 8, alpha=True, is_data=True)
        image.generated_color = value
        image.use_fake_user = True

def create_default_textures():
    for texture_name, value in generated_default_texture_name_value.items():
        create_default_texture(texture_name, value)

def get_matching_nutexb_path(texture_name: str, model_dir: Path) -> Path | None:
    lower_case_nutexb_file_name = texture_name.lower() + ".nutexb"
    for nutexb_file_path in Path(model_dir).glob("*.nutexb"):
        if nutexb_file_path.name.lower() == lower_case_nutexb_file_name:
            return nutexb_file_path
    return None

def get_matching_png_path(texture_name: str, model_dir: Path) -> Path | None:
    lower_case_png_file_name = texture_name.lower() + ".png"
    for png_file_path in Path(model_dir).glob("*.png"):
        if png_file_path.name.lower() == lower_case_png_file_name:
            return png_file_path
    return None

def import_texture_to_blender(operator: bpy.types.Operator, texture_name: str, model_dir: Path) -> bpy.types.Image:
    '''
    In order for users to be able to export and re-load from the same folder, the priority will be .nutexb, then .png
    '''
    # Check if the image being referenced is a default image
    default_texture_names: set[str] = set(generated_default_texture_name_value.keys())
    if texture_name in default_texture_names:
        # Default textures were just generated, so they should be in the .blend already
        return bpy.data.images[texture_name]
    
    # The image wasn't a default image, so will need to create the new image
    image = bpy.data.images.new(texture_name, 8, 8) # Ignore the x/y values here, its just because the new image is of type "Generated" before we change it to "File"
    image.name = texture_name
    #image.type = 'FILE' # Its read-only
    image.source = 'FILE'

    matching_nutexb_path = get_matching_nutexb_path(texture_name, model_dir)
    matching_png_path = get_matching_png_path(texture_name, model_dir)
    match (matching_nutexb_path is not None, matching_png_path is not None):
        case (True, True):
            operator.report({"INFO"}, f"Both a .nutexb and a .png were found for texture `{texture_name}`. The import priority will be nutexb if possible, followed by the png.")
            try:
                temp_png_file_path = Path(model_dir) / (texture_name + "_temp.png")
                convert_nutexb_to_png(matching_nutexb_path, temp_png_file_path)
            except CalledProcessError as e:
                operator.report({"INFO"}, f"Failed to convert .nutexb `{matching_nutexb_path.name}` to PNG, but the .PNG was available so that will be used instead. Error=`{e.stderr}`")
                image.filepath = str(matching_png_path)
                # The image wont be packed since its an existing external file.
            else:
                image.filepath = str(temp_png_file_path)
                image.pack()
                try:
                    temp_png_file_path.unlink()
                except Exception as e:
                    operator.report({"WARNING"}, f"Failed to remove temporary png file `{temp_png_file_path.name}`, error=`{e}`")
        case (True, False):
            try:
                temp_png_file_path = Path(model_dir) / (texture_name + "_temp.png")
                convert_nutexb_to_png(matching_nutexb_path, temp_png_file_path)
            except CalledProcessError as e:
                operator.report({"WARNING"}, f"Failed to convert .nutexb `{matching_nutexb_path.name}` to PNG, please manually convert the .nutexb to a .png and place it in the folder. Error=`{e.stderr}`")
            else:
                image.filepath = str(temp_png_file_path)
                image.pack()
                try:
                    temp_png_file_path.unlink()
                except Exception as e:
                    operator.report({"WARNING"}, f"Failed to remove temporary png file `{temp_png_file_path.name}`, error=`{e}`")
        case (False, True):
            image.filepath = str(matching_png_path)
        case (False, False):
            operator.report({"WARNING"}, f"No .nutexb or .png was found for texture `{texture_name}`! Please include the .nutexb or .png")
            
    return image

def import_material_images(operator: bpy.types.Operator, ssbh_matl: ssbh_data_py.matl_data.MatlData, model_dir:str ) -> dict[str, bpy.types.Image]:
    texture_name_to_image_dict: dict[str, bpy.types.Image] = {}
    texture_names_in_matl = {tex.data for mat in ssbh_matl.entries for tex in mat.textures}
    
    for texture_name in texture_names_in_matl:
        texture_name_to_image_dict[texture_name] = import_texture_to_blender(operator, texture_name, Path(model_dir))

    return texture_name_to_image_dict

def get_discard_shaders():
    global discard_shaders
    try:
        discard_shaders
    except NameError:
        this_file_path = Path(__file__)
        discard_shaders_file = this_file_path.parent.joinpath('shader_file').joinpath('shaders_discard_v13.0.1.txt').resolve()
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

def setup_sub_matl_data_node_drivers(sub_matl_data: SUB_PG_sub_matl_data):
    material: bpy.types.Material = sub_matl_data.id_data
    sub_matl_vector: SUB_PG_matl_vector
    for vector_index, sub_matl_vector in enumerate(sub_matl_data.vectors):
        for axis_index, axis in enumerate(['X', 'Y', 'Z', 'W']):
            value_node_name = f"{sub_matl_vector.param_id_name}_{axis}"
            value_node: ShaderNodeValue = material.node_tree.nodes.get(value_node_name)
            if value_node is None:
                continue
            # Setup Driver
            driver_fcurve: bpy.types.FCurve = value_node.outputs[0].driver_add('default_value')
            var = driver_fcurve.driver.variables.new()
            var.name = 'var'
            target = var.targets[0]
            target.id_type = 'MATERIAL'
            target.id = material
            target.data_path = f'sub_matl_data.vectors[{vector_index}].value[{axis_index}]'
            driver_fcurve.driver.expression = f'{var.name}'

    sub_matl_float: SUB_PG_matl_float
    for float_index, sub_matl_float in enumerate(sub_matl_data.floats):
        value_node: ShaderNodeValue = material.node_tree.nodes.get(sub_matl_float.param_id_name)
        if value_node is None:
            continue
        # Setup Driver
        driver_fcurve: bpy.types.FCurve = value_node.outputs[0].driver_add('default_value')
        var = driver_fcurve.driver.variables.new()
        var.name = 'var'
        target = var.targets[0]
        target.id_type = 'MATERIAL'
        target.id = material
        target.data_path = f'sub_matl_data.floats[{float_index}].value'
        driver_fcurve.driver.expression = f'{var.name}'


def setup_blender_material_node_tree(material: bpy.types.Material):
    from .master_shader import create_master_shader, get_master_shader_name
    sub_matl_data: SUB_PG_sub_matl_data = material.sub_matl_data
    
    # Make Master Shader if its not already made
    create_master_shader()
    
    # Clone Master Shader
    master_shader_name = get_master_shader_name()
    master_node_group = bpy.data.node_groups.get(master_shader_name)
    #clone_group = master_node_group.copy()

    # Setup Clone
    #clone_group.name = sub_matl_data.shader_label

    # Prep the node_tree for the new nodes
    material.use_nodes = True
    material.node_tree.nodes.clear()

    # Add the new Nodes
    nodes = material.node_tree.nodes
    
    cycles_output: ShaderNodeOutputMaterial = nodes.new('ShaderNodeOutputMaterial')
    cycles_output.name = 'cycles_output'
    cycles_output.label = 'Cycles Output'
    cycles_output.target = 'CYCLES'
    cycles_output.location = (400,350)

    eevee_output: ShaderNodeOutputMaterial = nodes.new('ShaderNodeOutputMaterial')
    eevee_output.name = 'eevee_output'
    eevee_output.label = 'EEVEE Output'
    eevee_output.target = 'EEVEE'
    eevee_output.location = (400,200)

    node_group_node = nodes.new('ShaderNodeGroup')
    node_group_node.name = 'smash_ultimate_shader'
    node_group_node.label = sub_matl_data.shader_label
    node_group_node.width = 600
    node_group_node.location = (-300, 300)
    #node_group_node.node_tree = clone_group
    node_group_node.node_tree = master_node_group

    links = material.node_tree.links
    links.new(node_group_node.outputs[0], cycles_output.inputs[0])
    links.new(node_group_node.outputs[1], eevee_output.inputs[0])

    texture: SUB_PG_matl_texture
    ParamId = ssbh_data_py.matl_data.ParamId
    created_node_rows = 0
    texture_node_row_width = 500
    layer_1_texture_names = {
        ParamId.Texture0.name,
        ParamId.Texture2.name,
        ParamId.Texture3.name,
        ParamId.Texture4.name,
        ParamId.Texture5.name,
        ParamId.Texture6.name,
        ParamId.Texture7.name,
        ParamId.Texture8.name,
        ParamId.Texture9.name,
        ParamId.Texture10.name,
        ParamId.Texture16.name,
    }
    layer_2_texture_names = {
        ParamId.Texture1.name,
        ParamId.Texture11.name,
        ParamId.Texture14.name,
    }
    layer_3_texture_names = {
        ParamId.Texture12.name
    }
    layer_4_texture_names = {
        ParamId.Texture13.name
    }
    layer_1_uv_transform_nodes = set()
    layer_2_uv_transform_nodes = set()
    layer_3_uv_transform_nodes = set()
    layer_4_uv_transform_nodes = set()
    sprite_sheet_nodes = set()
    for texture in sub_matl_data.textures:
        # Create Texture Node
        texture_node: ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
        texture_node.location = (-800, 1000 - (texture_node_row_width * created_node_rows))
        texture_node.name = texture.node_name
        texture_node.label = texture.ui_name
        texture_node.image = texture.image
        texture_node.show_options = False

        # For now, manually set the colorspace types....
        linear_textures_names = {ParamId.Texture4.name, ParamId.Texture6.name}
        if texture.node_name in linear_textures_names:
            texture_node.image.colorspace_settings.name = 'Non-Color'
            texture_node.image.alpha_mode = 'CHANNEL_PACKED'
        
        # Create UV Map Node
        uv_map_node: ShaderNodeUVMap = nodes.new("ShaderNodeUVMap")
        uv_map_node.name = f'{texture.node_name}_uv_map'
        uv_map_node.location = (texture_node.location[0] - 1500, texture_node.location[1])
        uv_map_node.label = f'{texture.node_name} UV Map'
        
        # For now, manually set the UV maps
        bake1_texture_names = {ParamId.Texture3.name, ParamId.Texture9.name}
        uvset_texture_names = {ParamId.Texture1.name, ParamId.Texture11.name, ParamId.Texture14.name}
        if texture.node_name in bake1_texture_names:
            uv_map_node.uv_map = 'bake1'
        elif texture.node_name in uvset_texture_names:
            uv_map_node.uv_map = 'uvSet'
        else:
            uv_map_node.uv_map = 'map1'
        
        # Create UV Transform Node
        # Also set the default_values here. I know it makes more sense to have the default_values
        # be in the init func of the node itself, but it just doesn't work there lol
        from .shader_nodes import custom_uv_transform_node
        uv_transform_node = nodes.new(custom_uv_transform_node.SUB_CSN_ultimate_uv_transform.bl_idname)
        uv_transform_node.name = 'uv_transform_node'
        uv_transform_node.label = 'UV Transform' + texture.node_name.split('Texture')[1]
        uv_transform_node.location = (texture_node.location[0] - 1200, texture_node.location[1])
        uv_transform_node.inputs[0].default_value = 1.0 # Scale X
        uv_transform_node.inputs[1].default_value = 1.0 # Scale Y
        if texture.node_name in layer_1_texture_names:
            layer_1_uv_transform_nodes.add(uv_transform_node)
        elif texture.node_name in layer_2_texture_names:
            layer_2_uv_transform_nodes.add(uv_transform_node)
        elif texture.node_name in layer_3_texture_names:
            layer_3_uv_transform_nodes.add(uv_transform_node)

        # Create Sprite Sheet Param Node
        from .shader_nodes import custom_sprite_sheet_params_node
        sprite_sheet_node = nodes.new(custom_sprite_sheet_params_node.SUB_CSN_ultimate_sprite_sheet_params.bl_idname)
        sprite_sheet_node.name = 'sprite_sheet_node'
        sprite_sheet_node.label = 'Sprite Sheet Params'
        sprite_sheet_node.location = (texture_node.location[0] - 900, texture_node.location[1])
        sprite_sheet_node.inputs[0].default_value = 1.0 # Column Count
        sprite_sheet_node.inputs[1].default_value = 1.0 # Row Count
        sprite_sheet_node.inputs[2].default_value = 1.0 # Active Sprite Count
        sprite_sheet_node.width = 250
        sprite_sheet_nodes.add(sprite_sheet_node)
        # Create Sampler Node
        from .shader_nodes import custom_sampler_node
        
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

        sampler_node.show_options = False

        # Link these nodes together
        links.new(uv_map_node.outputs[0], uv_transform_node.inputs[4])
        links.new(uv_transform_node.outputs[0], sprite_sheet_node.inputs[4])
        links.new(sprite_sheet_node.outputs[0], sampler_node.inputs[0])
        links.new(sampler_node.outputs[0], texture_node.inputs[0])
        links.new(texture_node.outputs['Color'], node_group_node.inputs[texture_param_name_to_socket_params[texture.node_name].rgb_socket_name])
        links.new(texture_node.outputs['Alpha'], node_group_node.inputs[texture_param_name_to_socket_params[texture.node_name].alpha_socket_name])

        created_node_rows = created_node_rows + 1

    created_value_rows = 0
    vector: SUB_PG_matl_vector
    for vector_index, vector in enumerate(sub_matl_data.vectors):
        if vector.param_id_name == ParamId.CustomVector47.name:
            node_group_node.inputs['use_custom_vector_47'].default_value = 1.0

        for axis_index, axis in enumerate(['X', 'Y', 'Z', 'W']):
            # Create the value node
            value_node: ShaderNodeValue = nodes.new('ShaderNodeValue')
            value_node.name = f"{vector.param_id_name}_{axis}"
            value_node.label = f"{vector.ui_name} {axis}"
            value_node.location = (-1300 + (200 * axis_index), 1000 - (texture_node_row_width * (created_node_rows-1)) - 300 - (100 * created_value_rows))
            
            socket_params = vec4_param_name_to_socket_params[vector.param_id_name]
            if axis == 'X':
                socket_name = socket_params.x_socket_name
            elif axis == 'Y':
                socket_name = socket_params.y_socket_name
            elif axis == 'Z':
                socket_name = socket_params.z_socket_name
            elif axis == 'W':
                socket_name = socket_params.w_socket_name

            links.new(node_group_node.inputs[socket_name], value_node.outputs[0])

            if vector.param_id_name == ssbh_data_py.matl_data.ParamId.CustomVector6.name:
                for node in layer_1_uv_transform_nodes:
                    links.new(value_node.outputs[0], node.inputs[axis_index])
            elif vector.param_id_name == ssbh_data_py.matl_data.ParamId.CustomVector31.name:
                for node in layer_2_uv_transform_nodes:
                    links.new(value_node.outputs[0], node.inputs[axis_index])
            elif vector.param_id_name == ssbh_data_py.matl_data.ParamId.CustomVector32.name:
                for node in layer_3_uv_transform_nodes:
                    links.new(value_node.outputs[0], node.inputs[axis_index])
            elif vector.param_id_name == ssbh_data_py.matl_data.ParamId.CustomVector18.name:
                for node in sprite_sheet_nodes:
                    links.new(value_node.outputs[0], node.inputs[axis_index])
        created_value_rows = created_value_rows + 1

    for vertex_attribute in sub_matl_data.vertex_attributes:
        if vertex_attribute.name == 'colorSet1':
            # Create Node
            vertex_color_node: ShaderNodeVertexColor = nodes.new('ShaderNodeVertexColor')
            vertex_color_node.name = vertex_attribute.name
            vertex_color_node.label = vertex_attribute.name
            vertex_color_node.location = (-1300, 1000 - (texture_node_row_width * (created_node_rows-1)) - 300 - (100 * created_value_rows))
            vertex_color_node.layer_name = 'colorSet1'
            # Link Node
            links.new(vertex_color_node.outputs[0], node_group_node.inputs['colorSet1 RGB'])
            links.new(vertex_color_node.outputs[1], node_group_node.inputs['colorSet1 Alpha'])
            # Adjust row counter (for proper placement in UI)
            created_value_rows = created_value_rows + 1
        elif vertex_attribute.name == 'colorSet5':
            # Create Node
            vertex_color_node: ShaderNodeVertexColor = nodes.new('ShaderNodeVertexColor')
            vertex_color_node.name = vertex_attribute.name
            vertex_color_node.label = vertex_attribute.name
            vertex_color_node.location = (-1300, 1000 - (texture_node_row_width * (created_node_rows-1)) - 300 - (100 * created_value_rows))
            vertex_color_node.layer_name = 'colorSet5'
            # Link Node
            links.new(vertex_color_node.outputs[0], node_group_node.inputs['colorSet5 RGB'])
            links.new(vertex_color_node.outputs[1], node_group_node.inputs['colorSet5 Alpha'])
            # Adjust row counter (for proper placement in UI)
            created_value_rows = created_value_rows + 1

    sub_matl_float: SUB_PG_matl_float
    for sub_matl_float in sub_matl_data.floats:
        # Create Node
        value_node: ShaderNodeValue = nodes.new('ShaderNodeValue')
        value_node.name = sub_matl_float.param_id_name
        value_node.label = sub_matl_float.param_id_name
        value_node.location = (-1300, 1000 - (texture_node_row_width * (created_node_rows-1)) - 300 - (100 * created_value_rows))
        # Link Node
        links.new(value_node.outputs[0], node_group_node.inputs[sub_matl_float.ui_name])
        # Adjust row counter (for proper placement in UI)
        created_value_rows = created_value_rows + 1

    setup_sub_matl_data_node_drivers(sub_matl_data)
    node_group_node.show_options = False
    for input in node_group_node.inputs:
        if input.is_linked is False:
            input.hide = True


def get_vertex_attributes(shader_name:str)->list[str]:
    # Query the shader database for attribute information.
    # Using SQLite is much faster than iterating through the JSON dump.
    with sqlite3.connect(get_shader_db_file_path()) as con:
        # Construct a query to find all the vertex attributes for this shader.
        # Invalid shaders will return an empty list.
        sql = """
            SELECT v.AttributeName 
            FROM VertexAttribute v 
            INNER JOIN ShaderProgram s ON v.ShaderProgramID = s.ID 
            WHERE s.Name = ?
            """
        # The database has a single entry for each program, so don't include the render pass tag.
        return [row[0] for row in con.execute(sql, (shader_name[:len('SFX_PBS_0000000000000080')],)).fetchall()]
    
def create_blender_materials_from_matl(operator: bpy.types.Operator, ssbh_matl: ssbh_data_py.matl_data.MatlData) -> dict[str, bpy.types.Material]:
    '''
    Creates a blender material with the sub_matl_data filled out for every entry in the ssbh_matl.
    Returns a dictionary mapping the material_label to the created blender material to handle multiple models 
    having the same material name.
    '''
    # Setup default textures if not already made
    create_default_textures()
    # Make new Blender Materials
    material_label_to_material: dict[str, bpy.types.Material] = \
        {entry.material_label : bpy.data.materials.new(entry.material_label) for entry in ssbh_matl.entries}
    # Import images 
    texture_name_to_image_dict = import_material_images(operator, ssbh_matl, bpy.context.scene.sub_scene_properties.model_import_folder_path)
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
        attrs = get_vertex_attributes(entry.shader_label)
        sub_matl_data.add_vertex_attributes(attrs)
        
    # Eye materials implicitly use extra materials despite no mesh being explicitly assigned.
    # Need to track these to preserve them on export.
    for material_label, material in material_label_to_material.items():
        sub_matl_data: SUB_PG_sub_matl_data = material.sub_matl_data
        if (match := re.match(r"(Eye[L|R])(\d?)", material_label)):
            label_no_digit, optional_digit = match.groups(default='')
            for linked_material_suffix in ('L', 'D', 'G'):
                if (linked_material := material_label_to_material.get(f'{label_no_digit}{linked_material_suffix}{optional_digit}')):
                    new_linked_material: SUB_PG_matl_linked_material = sub_matl_data.linked_materials.add()
                    new_linked_material.blender_material = linked_material

                    
    # Make the blender material settings
    for material_label, material in material_label_to_material.items():
        setup_blender_material_settings(material)
        setup_blender_material_node_tree(material)

    return material_label_to_material
