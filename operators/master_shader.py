import bpy

from ..modules.material import matl_params
from . import material_inputs
from .. import ssbh_data_py

from bpy.types import (
    Nodes, NodeLinks, NodeFrame, NodeGroupInput, ShaderNodeMath, ShaderNodeMixRGB,
    ShaderNodeSeparateRGB, ShaderNodeCombineRGB, ShaderNodeGamma, ShaderNodeVertexColor,
    ShaderNodeTree, NodeSocketColor, NodeSocketFloat, NodeTree, ShaderNodeInvert)

def get_master_shader_name():
    return 'Smash Ultimate Master Shader'

def add_color_input(node_group_node_tree: ShaderNodeTree, name: str, rgb_default_value: tuple[float, float, float]):
    input: NodeSocketColor = node_group_node_tree.inputs.new('NodeSocketColor', name)
    input.default_value = rgb_default_value + (1.0,) # This final alpha value is inaccessible, the true alpha value should be stored in a seperate socket

def add_float_input(node_group_node_tree: ShaderNodeTree, name: str, default_value: float):
    input: NodeSocketFloat = node_group_node_tree.inputs.new('NodeSocketFloat', name)
    input.default_value = default_value

def add_floats(node_tree: ShaderNodeTree):
    ParamId = ssbh_data_py.matl_data.ParamId
    custom_float_values = [
        ParamId.CustomFloat0.value,
        ParamId.CustomFloat1.value,
        ParamId.CustomFloat2.value,
        ParamId.CustomFloat3.value,
        ParamId.CustomFloat4.value,
        ParamId.CustomFloat5.value,
        ParamId.CustomFloat6.value,
        ParamId.CustomFloat7.value,
        ParamId.CustomFloat8.value,
        ParamId.CustomFloat9.value,
        ParamId.CustomFloat10.value,
        ParamId.CustomFloat11.value,
        ParamId.CustomFloat12.value,
        ParamId.CustomFloat13.value,
        ParamId.CustomFloat14.value,
        ParamId.CustomFloat15.value,
        ParamId.CustomFloat16.value,
        ParamId.CustomFloat17.value,
        ParamId.CustomFloat18.value,
        ParamId.CustomFloat19.value,
    ]
    for custom_float_value in custom_float_values:
        socket_name = matl_params.param_id_to_ui_name[custom_float_value] 
        input = node_tree.inputs.new("NodeSocketFloat", socket_name)
        input.default_value = 0.0

def create_inputs(node_tree, name_to_inputs):
    for _, inputs in name_to_inputs.items():
        for socket, name, default in inputs:
            input = node_tree.inputs.new(socket, name)
            input.default_value = default

def create_vec4_inputs(node_tree: NodeTree):
    for socket_params in matl_params.vec4_param_name_to_socket_params.values():
        x_input = node_tree.inputs.new('NodeSocketFloat', socket_params.x_socket_name)
        y_input = node_tree.inputs.new('NodeSocketFloat', socket_params.y_socket_name)
        z_input = node_tree.inputs.new('NodeSocketFloat', socket_params.z_socket_name)
        w_input = node_tree.inputs.new('NodeSocketFloat', socket_params.w_socket_name)
        x_input.default_value = socket_params.default_value[0]
        y_input.default_value = socket_params.default_value[1]
        z_input.default_value = socket_params.default_value[2]
        w_input.default_value = socket_params.default_value[3]

def create_texture_input_sockets(node_group_node_tree: NodeTree):
    for socket_params in matl_params.texture_param_name_to_socket_params.values():
        rgb_socket = node_group_node_tree.inputs.new('NodeSocketColor', socket_params.rgb_socket_name)
        alpha_socket = node_group_node_tree.inputs.new('NodeSocketFloat', socket_params.alpha_socket_name)
        # The alpha value of a RGB 'Color' socket is innaccessible, so the actual alpha value needs to be stored in a separate socket.
        rgb_socket.default_value = socket_params.default_rgba[0:3] + (1.0,) # The comma is for tuple concatentation, otherwise `(1.0)` evaluates to a float and causes an exception
        alpha_socket.default_value = socket_params.default_rgba[3]

def hide_unlinked_outputs(node):
    for output in node.outputs:
        if output.is_linked is False:
            output.hide = True

def create_master_shader():
    master_shader_name = get_master_shader_name()
    # Check if already exists and just skip if it does
    if bpy.data.node_groups.get(master_shader_name, None) is not None:
        return

    # Create a dummy material just for use in creation
    mat = bpy.data.materials.new(master_shader_name)
    mat.use_nodes = True
    mat_node_tree = mat.node_tree
    node_group_node = mat_node_tree.nodes.new('ShaderNodeGroup')

    # Make the Node Group, which is its own node tree and lives with other node groups
    node_group_node_tree = bpy.data.node_groups.new(master_shader_name, 'ShaderNodeTree')

    # Connect that new node_group to the node_group_node
    # (this should get rid of the 'missing data block', blender fills it out automatically)
    node_group_node.node_tree = node_group_node_tree

    node_group_node.name = 'Master'

    # Make the one output
    node_group_node_tree.outputs.new('NodeSocketShader', 'Cycles Output')
    node_group_node_tree.outputs.new('NodeSocketShader', 'EEVEE Output')

    # Now we are ready to start adding inputs
    def add_color_node(name):
        return node_group_node_tree.inputs.new('NodeSocketColor', name)

    def add_float_node(name):
        return node_group_node_tree.inputs.new('NodeSocketFloat', name)
    
    create_texture_input_sockets(node_group_node_tree)

    # TODO: It may be necessary to disable these nodes rather than use defaults in the future.
    # Set defaults for color sets that have no effect after scale is applied.
    input = add_color_node('colorSet1 RGB')
    input.default_value = (0.5, 0.5, 0.5, 0.5)
    input = add_float_node('colorSet1 Alpha')
    input.default_value = 0.5

    input = add_color_node('colorSet5 RGB')
    input.default_value = (0.0, 0.0, 0.0, 1.0 / 3.0)
    input = add_float_node('colorSet5 Alpha')
    input.default_value = 1.0 / 3.0

    #create_inputs(node_group_node_tree, material_inputs.vec4_param_to_inputs)
    create_vec4_inputs(node_group_node_tree)
    #create_inputs(node_group_node_tree, material_inputs.float_param_to_inputs)
    add_floats(node_group_node_tree)
    create_inputs(node_group_node_tree, material_inputs.bool_param_to_inputs)

    # Wont be shown to users, should always be hidden
    input = add_float_node('use_custom_vector_47')
    input.default_value = 0.0

    # Allow for wider node
    node_group_node.bl_width_max = 1000

    # Now its time to place nodes
    inner_nodes = node_group_node.node_tree.nodes
    inner_links = node_group_node.node_tree.links

    # Principled Shader Node
    cycles_shader = inner_nodes.new('ShaderNodeBsdfPrincipled')
    cycles_shader.name = 'cycles_shader'
    cycles_shader.label = 'Cycles Principled'

    # Diffuse Frame
    diffuse_main_frame: NodeFrame = inner_nodes.new('NodeFrame')
    diffuse_main_frame.name = 'diffuse_main_frame'
    diffuse_main_frame.label = 'Diffuse Color Stuff'
    diffuse_main_frame.use_custom_color = True
    diffuse_main_frame.color = (0.13, 0.13, 0.13)
    
    # Mix Col Textures Sub Frame
    mix_col_textures_frame: NodeFrame = inner_nodes.new('NodeFrame')
    mix_col_textures_frame.name = 'mix_col_textures_frame'
    mix_col_textures_frame.label = 'Mix Col Textures'

    col_textures_group_input: NodeGroupInput = inner_nodes.new('NodeGroupInput')
    col_textures_group_input.name = 'col_textures_group_input'
    col_textures_group_input.label = 'Col Textures'

    color_set_5_alpha_group_input: NodeGroupInput = inner_nodes.new('NodeGroupInput')
    color_set_5_alpha_group_input.name = 'color_set_5_alpha_group_input'
    color_set_5_alpha_group_input.label = 'colorSet5 Alpha'

    col_tex_layer_2_alpha_group_input: NodeGroupInput = inner_nodes.new('NodeGroupInput')
    col_tex_layer_2_alpha_group_input.name = 'col_tex_layer_2_alpha_group_input'
    col_tex_layer_2_alpha_group_input.label = 'Col Tex Layer 2 Alpha'

    color_set_5_scale: ShaderNodeMath = inner_nodes.new('ShaderNodeMath')
    color_set_5_scale.name = 'color_set_5_scale'
    color_set_5_scale.label = 'Color Set 5 Scale'
    color_set_5_scale.operation = 'MULTIPLY'
    color_set_5_scale.inputs[0].default_value = 3.0

    one_minus_color_set_5_alpha: ShaderNodeMath = inner_nodes.new('ShaderNodeMath')
    one_minus_color_set_5_alpha.name = 'one_minus_color_set_5_alpha'
    one_minus_color_set_5_alpha.label = '1 - colorSet5Alpha'
    one_minus_color_set_5_alpha.operation = 'SUBTRACT'
    one_minus_color_set_5_alpha.inputs[0].default_value = 1.0
    one_minus_color_set_5_alpha.use_clamp = True

    col_map_mix_factor: ShaderNodeMath = inner_nodes.new('ShaderNodeMath')
    col_map_mix_factor.name = 'col_map_mix_factor'
    col_map_mix_factor.label = 'Col Map Mix Factor'
    col_map_mix_factor.operation = 'SUBTRACT'
    col_map_mix_factor.use_clamp = True

    col_map_mix: ShaderNodeMixRGB = inner_nodes.new('ShaderNodeMixRGB')
    col_map_mix.name = 'col_map_mix'
    col_map_mix.label = 'Col Map Mix'
    col_map_mix.blend_type = 'MIX'

    # Apply Fake SSS SubFrame
    fake_sss_frame: NodeFrame = inner_nodes.new('NodeFrame')
    fake_sss_frame.name = 'fake_sss_frame'
    fake_sss_frame.label = 'Apply Fake SSS'

    fake_sss_factor_group_input: NodeGroupInput = inner_nodes.new('NodeGroupInput')
    fake_sss_factor_group_input.name = 'fake_sss_factor_group_input'
    fake_sss_factor_group_input.label = 'Fake SSS Factor Inputs'

    cv11_group_input: NodeGroupInput = inner_nodes.new('NodeGroupInput')
    cv11_group_input.name = 'cv11_group_input'
    cv11_group_input.label = 'CV 11 (Fake SSS Color)'

    separate_prm_r: ShaderNodeSeparateRGB = inner_nodes.new('ShaderNodeSeparateRGB')
    separate_prm_r.name = 'separate_prm_r'
    separate_prm_r.label = 'Separate PRM R'

    fake_sss_factor: ShaderNodeMath = inner_nodes.new('ShaderNodeMath')
    fake_sss_factor.name = 'fake_sss_factor'
    fake_sss_factor.label = 'Fake SSS Factor'
    fake_sss_factor.operation = 'MULTIPLY'

    cv11_combine: ShaderNodeCombineRGB = inner_nodes.new('ShaderNodeCombineRGB')
    cv11_combine.name = 'cv11_combine'
    cv11_combine.label = 'CV 11 RGB from X,Y,Z'

    fake_sss_color_mix: ShaderNodeMixRGB = inner_nodes.new('ShaderNodeMixRGB')
    fake_sss_color_mix.name = 'fake_sss_color_mix'
    fake_sss_color_mix.label = 'Fake SSS Color Mix'
    fake_sss_color_mix.blend_type = 'MIX'
    
    ParamId = ssbh_data_py.matl_data.ParamId
    cv11_socket_params = matl_params.vec4_param_name_to_socket_params[ParamId.CustomVector11.name]
    cv30_socket_params = matl_params.vec4_param_name_to_socket_params[ParamId.CustomVector30.name]
    texture6_socket_params =  matl_params.texture_param_name_to_socket_params[ParamId.Texture6.name]

    # Apply CV 13 SubFrame
    # Locations will be handled by the NodeToPython blender plugin
    cv13_frame: NodeFrame = inner_nodes.new('NodeFrame')
    cv13_frame.name = 'cv13_frame'
    cv13_frame.label = 'Apply CV13 (Diffuse Color Scale)'

    cv13_group_input: NodeGroupInput = inner_nodes.new('NodeGroupInput')
    cv13_group_input.name = 'cv13_group_input'
    cv13_group_input.label = 'CV 13 (Diffuse Color Scale) Input'

    cv13_combine = inner_nodes.new('ShaderNodeCombineRGB')
    cv13_combine.name = 'cv13_combine'
    cv13_combine.label = 'CV 13 Combine'

    cv13_multiply: ShaderNodeMixRGB = inner_nodes.new('ShaderNodeMixRGB')
    cv13_multiply.name = 'cv13_multiply'
    cv13_multiply.label = 'CV 13 Multiply'
    cv13_multiply.blend_type = 'MULTIPLY'
    cv13_multiply.inputs[0].default_value = 1.0

    cv13_socket_params = matl_params.vec4_param_name_to_socket_params[ParamId.CustomVector13.name]

    # Baked Lighting SubFrame
    baked_lighting_frame: NodeFrame = inner_nodes.new('NodeFrame')
    baked_lighting_frame.name = 'baked_lighting_frame'
    baked_lighting_frame.label = "Apply Baked Lighting"

    baked_lighting_group_input: NodeGroupInput = inner_nodes.new('NodeGroupInput')
    baked_lighting_group_input.name = 'baked_lighting_group_input'
    baked_lighting_group_input.label = 'Baked Lighting Inputs'

    baked_lighting_alpha_invert: ShaderNodeInvert = inner_nodes.new('ShaderNodeInvert')
    baked_lighting_alpha_invert.name = 'baked_lighting_alpha_invert'
    baked_lighting_alpha_invert.label = "Baked Lighting Alpha Invert"

    baked_lighting_texture_boost: ShaderNodeMixRGB = inner_nodes.new('ShaderNodeMixRGB')
    baked_lighting_texture_boost.name = 'baked_lighting_texture_boost'
    baked_lighting_texture_boost.label = 'Baked Lighting Texture Boost'
    baked_lighting_texture_boost.inputs[0].default_value = 1.0
    baked_lighting_texture_boost.inputs[2].default_value = (8.0, 8.0, 8.0, 8.0)
    
    baked_lighting_mix: ShaderNodeMixRGB = inner_nodes.new('ShaderNodeMixRGB')
    baked_lighting_mix.name = 'baked_lighting_mix'
    baked_lighting_mix.label = 'Baked Lighting Mix'

    texture9_socket_params = matl_params.texture_param_name_to_socket_params[ParamId.Texture9.name]

    # PRM Frame Time
    prm_frame = inner_nodes.new('NodeFrame')
    prm_frame.name = 'prm_frame'
    prm_frame.label = 'PRM Stuff'

    prm_compare_cv30_x = inner_nodes.new('ShaderNodeMath')
    prm_compare_cv30_x.name = 'prm_compare_cv30_x'
    prm_compare_cv30_x.label = 'Compare CV30 X'
    prm_compare_cv30_x.operation = 'COMPARE'
    prm_compare_cv30_x.inputs[0].default_value = 0
    prm_compare_cv30_x.inputs[2].default_value = 0.00001

    prm_metal_minimum = inner_nodes.new('ShaderNodeMath')
    prm_metal_minimum.name = 'prm_metal_minimum'
    prm_metal_minimum.label = 'PRM Metal Override'
    prm_metal_minimum.operation = 'MINIMUM'

    prm_separate_prm_rgb = inner_nodes.new('ShaderNodeSeparateRGB')
    prm_separate_prm_rgb.name = 'prm_separate_prm_rgb'
    prm_separate_prm_rgb.label = 'Separate PRM RGB'

    prm_multiply_prm_alpha = inner_nodes.new('ShaderNodeMath')
    prm_multiply_prm_alpha.name = 'prm_multiply_prm_alpha'
    prm_multiply_prm_alpha.label = 'Specular Boost'
    prm_multiply_prm_alpha.operation = 'MULTIPLY'
    prm_multiply_prm_alpha.inputs[0].default_value = 2.5

    prm_custom_vector_47_rgb_override = inner_nodes.new('ShaderNodeMixRGB')
    prm_custom_vector_47_rgb_override.name = 'prm_custom_vector_47_rgb_override'
    prm_custom_vector_47_rgb_override.label = 'Custom Vector 47 RGB Overrider'
    prm_custom_vector_47_rgb_override.blend_type = 'MIX'

    prm_custom_vector_47_alpha_override = inner_nodes.new('ShaderNodeMixRGB')
    prm_custom_vector_47_alpha_override.name = 'prm_custom_vector_47_alpha_override'
    prm_custom_vector_47_alpha_override.label = 'Custom Vector 47 Alpha Overrider'
    prm_custom_vector_47_alpha_override.blend_type = 'MIX'

    prm_frame.location = (0, 200)
    # NOR Frame Time
    nor_frame = inner_nodes.new('NodeFrame')
    nor_frame.name = 'nor_frame'
    nor_frame.label = 'NOR Map Stuff'

    nor_group_input = inner_nodes.new('NodeGroupInput')
    nor_group_input.name = 'nor_group_input'
    nor_group_input.label = 'NOR Group Input'

    nor_separate_rgb = inner_nodes.new('ShaderNodeSeparateRGB')
    nor_separate_rgb.name = 'nor_separate_rgb'
    nor_separate_rgb.label = 'Separate NOR RGB'

    nor_combine_rgb = inner_nodes.new('ShaderNodeCombineRGB')
    nor_combine_rgb.name = 'nor_combine_rgb'
    nor_combine_rgb.label = 'Combine R + G'
    nor_combine_rgb.inputs['B'].default_value = 1.0

    nor_normal_map = inner_nodes.new('ShaderNodeNormalMap')
    nor_normal_map.name = 'nor_normal_map'
    nor_normal_map.label = 'Normal Map'

    # Alpha Frame Time
    alpha_frame = inner_nodes.new('NodeFrame')
    alpha_frame.name = 'alpha_frame'
    alpha_frame.label = 'Alpha stuff'

    alpha_maximum = inner_nodes.new('ShaderNodeMath')
    alpha_maximum.name = 'alpha_maximum'
    alpha_maximum.label = 'Max Alpha'
    alpha_maximum.operation = 'MAXIMUM'

    alpha_color_set1_scale = inner_nodes.new('ShaderNodeMath')
    alpha_color_set1_scale.name = 'alpha_color_set1_scale'
    alpha_color_set1_scale.label = 'colorSet1 Alpha Scale'
    alpha_color_set1_scale.operation = 'MULTIPLY'
    alpha_color_set1_scale.inputs[1].default_value = 2.0

    # Emission Frame Time
    emission_frame = inner_nodes.new('NodeFrame')
    emission_frame.name = 'emission_frame'
    emission_frame.label = 'Emission Stuff'

    emission_multiply = inner_nodes.new('ShaderNodeMixRGB')
    emission_multiply.name = 'emission_multiply'
    emission_multiply.label = 'CV3 Emission Multiplier'
    emission_multiply.blend_type = 'MULTIPLY'
    emission_multiply.inputs[0].default_value = 1.0

    emission_mix_rgb = inner_nodes.new('ShaderNodeMixRGB')
    emission_mix_rgb.name = 'emission_mix_rgb'
    emission_mix_rgb.label = 'Emission Layer Mixer'

    ## These nodes were mostly copy pasted from NodeToPython
    colorset1_albedo_frame = inner_nodes.new("NodeFrame")
    colorset1_albedo_frame.name = 'colorset1_albedo_frame'
    colorset1_albedo_frame.label = "Apply colorSet1 Albedo"

    cv30_x_input = inner_nodes.new("NodeGroupInput")
    cv30_x_input.name = 'cv30_x_input'
    cv30_x_input.label = "CV30 X Input"

    texture6_group_input = inner_nodes.new("NodeGroupInput")
    texture6_group_input.name = 'texture6_group_input'
    texture6_group_input.label = "Texture6 (PRM)"

    use_custom_vector_47_group_input = inner_nodes.new("NodeGroupInput")
    use_custom_vector_47_group_input.name = 'use_custom_vector_47_group_input'
    use_custom_vector_47_group_input.label = "Use Custom Vector 47"

    cv47_combine = inner_nodes.new("ShaderNodeCombineXYZ")
    cv47_combine.name = "cv47_combine"
    cv47_combine.label = "Combine CV 47"
    
    cv47_group_input = inner_nodes.new("NodeGroupInput")
    cv47_group_input.name = "cv47_group_input"
    cv47_group_input.label = "CV47 (Whole Mesh PRM)"
    
    """
    diffuse_frame_fake_sss_factor_group_input = inner_nodes.new("NodeGroupInput")
    diffuse_frame_fake_sss_factor_group_input.name = "diffuse_frame_fake_sss_factor_group_input"
    diffuse_frame_fake_sss_factor_group_input.label = "Fake SSS Factor Inputs"
    """

    colorset1_albedo: ShaderNodeMixRGB = inner_nodes.new("ShaderNodeMixRGB")
    colorset1_albedo.name = "colorset1_albedo"
    colorset1_albedo.label = "Apply Color Set 1"
    colorset1_albedo.inputs[0].default_value = 1.0
    colorset1_albedo.blend_type = 'MULTIPLY'

    color_set1_scale: ShaderNodeMixRGB = inner_nodes.new("ShaderNodeMixRGB")
    color_set1_scale.name = 'color_set1_scale'
    color_set1_scale.label = "Color Set 1 Scale"
    color_set1_scale.inputs[0].default_value = 1.0
    color_set1_scale.inputs[2].default_value = (2.0, 2.0, 2.0, 2.0)
    color_set1_scale.blend_type = 'MULTIPLY'

    colorset1_group_input = inner_nodes.new("NodeGroupInput")
    colorset1_group_input.name = "colorset1_group_input"
    colorset1_group_input.label = "ColorSet1"

    emission_textures_group_input = inner_nodes.new("NodeGroupInput")
    emission_textures_group_input.name = 'emission_textures_group_input'
    emission_textures_group_input.label = "Emission Textures"

    cv3_input = inner_nodes.new("NodeGroupInput")
    cv3_input.name = "cv3_input"
    cv3_input.label = "CV 3 Input"

    cv3_combine = inner_nodes.new("ShaderNodeCombineXYZ")
    cv3_combine.name = "cv3_combine"
    cv3_combine.label = "CV 3 Combine"

    apply_color_set_1_alpha = inner_nodes.new("ShaderNodeMath")
    apply_color_set_1_alpha.name = "apply_color_set_1_alpha"
    apply_color_set_1_alpha.label = "Apply colorSet1 Alpha"
    apply_color_set_1_alpha.operation = 'MULTIPLY'
    apply_color_set_1_alpha.inputs[2].default_value = 0.5

    layer1_tex_alphas = inner_nodes.new("NodeGroupInput")
    layer1_tex_alphas.name = "layer1_tex_alphas"
    layer1_tex_alphas.label = "Layer1 Texture Alphas"

    cv0_x_input = inner_nodes.new("NodeGroupInput")
    cv0_x_input.name = "cv0_x_input"
    cv0_x_input.label = "CV 0 X Input"

    colorset1_alpha = inner_nodes.new("NodeGroupInput")
    colorset1_alpha.name = "colorset1_alpha"
    colorset1_alpha.label = "colorSet1 Alpha"

    get_lowest_tex_alpha = inner_nodes.new("ShaderNodeMath")
    get_lowest_tex_alpha.name = 'get_lowest_tex_alpha'
    get_lowest_tex_alpha.label = "Get Lowest Texture Alpha"
    get_lowest_tex_alpha.operation = 'MINIMUM'
    get_lowest_tex_alpha.inputs[2].default_value = 0.5

    cycles_frame = inner_nodes.new("NodeFrame")
    cycles_frame.name = "cycles_frame"
    cycles_frame.label = "Cycles"

    eevee_principled_shader = inner_nodes.new("ShaderNodeBsdfPrincipled")
    eevee_principled_shader.name = "eevee_principled_shader"
    eevee_principled_shader.label = "EEVEE Principled Shader"

    eevee_frame = inner_nodes.new("NodeFrame")
    eevee_frame.name = "eevee_frame"
    eevee_frame.label = "EEVEE"

    unified_output = inner_nodes.new("NodeGroupOutput")
    unified_output.name = "unified_output"
    unified_output.label = "Unified Output"

    eevee_shader_to_rgb_frame = inner_nodes.new("NodeFrame")
    eevee_shader_to_rgb_frame.name = 'eevee_shader_to_rgb_frame'
    eevee_shader_to_rgb_frame.label = "EEVEE Post-PBR Stuff"

    eevee_apply_cv8 = inner_nodes.new("ShaderNodeMixRGB")
    eevee_apply_cv8.name = "eevee_apply_cv8"
    eevee_apply_cv8.label = "Apply CV 8"
    eevee_apply_cv8.inputs[0].default_value = 1.0
    eevee_apply_cv8.blend_type = 'MULTIPLY'

    shader_to_rgb = inner_nodes.new("ShaderNodeShaderToRGB")
    shader_to_rgb.name = 'shader_to_rgb'
    
    eevee_colorset1_input = inner_nodes.new("NodeGroupInput")
    eevee_colorset1_input.name = 'eevee_colorset1_input'
    eevee_colorset1_input.label = "colorSet1 Input"

    eevee_colorset1_scale: ShaderNodeMixRGB = inner_nodes.new("ShaderNodeMixRGB")
    eevee_colorset1_scale.name = "eevee_colorset1_scale"
    eevee_colorset1_scale.label = "Scale colorSet1"
    eevee_colorset1_scale.inputs[0].default_value = 1.0
    eevee_colorset1_scale.inputs[2].default_value = (2.0, 2.0, 2.0, 2.0)
    eevee_colorset1_scale.blend_type = 'MULTIPLY'

    eevee_apply_colorset1 = inner_nodes.new("ShaderNodeMixRGB")
    eevee_apply_colorset1.name = "eevee_apply_colorset1"
    eevee_apply_colorset1.label = "Apply colorset1"
    eevee_apply_colorset1.inputs[0].default_value = 1.0
    eevee_apply_colorset1.blend_type = 'MULTIPLY'

    eevee_add_shader = inner_nodes.new("ShaderNodeAddShader")
    eevee_add_shader.name = "eevee_add_shader"

    eevee_transparent_bsdf = inner_nodes.new("ShaderNodeBsdfTransparent")
    eevee_transparent_bsdf.name = "eevee_transparent_bsdf"
    eevee_transparent_bsdf.inputs[1].default_value = 0.0

    eevee_invert_alpha = inner_nodes.new("ShaderNodeInvert")
    eevee_invert_alpha.name = "eevee_invert_alpha"
    eevee_invert_alpha.label = "Invert Alpha"
    eevee_invert_alpha.inputs[0].default_value = 1.0

    eevee_combine_cv8 = inner_nodes.new("ShaderNodeCombineColor")
    eevee_combine_cv8.name = "eevee_combine_cv8"
    eevee_combine_cv8.label = "Combine CV 8"
    eevee_combine_cv8.mode = 'RGB'

    eevee_cv8_input = inner_nodes.new("NodeGroupInput")
    eevee_cv8_input.name = "eevee_cv8_input"
    eevee_cv8_input.label = "CV 8 Input"

    reroute_1 = inner_nodes.new("NodeReroute")
    reroute_1.name = "reroute_1"

    reroute_2 = inner_nodes.new("NodeReroute")
    reroute_2.name = "reroute_2"

    reroute_3 = inner_nodes.new("NodeReroute")
    reroute_3.name = "reroute_3"

    reroute_4 = inner_nodes.new("NodeReroute")
    reroute_4.name = "reroute_4"

    # Set Parents (from NodeToPython)
    mix_col_textures_frame.parent = diffuse_main_frame
    fake_sss_frame.parent = diffuse_main_frame
    cv13_frame.parent = diffuse_main_frame
    baked_lighting_frame.parent = diffuse_main_frame
    colorset1_albedo_frame.parent = cycles_frame
    cycles_shader.parent = cycles_frame
    col_textures_group_input.parent = mix_col_textures_frame
    color_set_5_alpha_group_input.parent = mix_col_textures_frame
    col_tex_layer_2_alpha_group_input.parent = mix_col_textures_frame
    color_set_5_scale.parent = mix_col_textures_frame
    one_minus_color_set_5_alpha.parent = mix_col_textures_frame
    col_map_mix_factor.parent = mix_col_textures_frame
    col_map_mix.parent = mix_col_textures_frame
    fake_sss_factor_group_input.parent = fake_sss_frame
    cv11_group_input.parent = fake_sss_frame
    separate_prm_r.parent = fake_sss_frame
    fake_sss_factor.parent = fake_sss_frame
    cv11_combine.parent = fake_sss_frame
    fake_sss_color_mix.parent = fake_sss_frame
    cv13_group_input.parent = cv13_frame
    cv13_combine.parent = cv13_frame
    cv13_multiply.parent = cv13_frame
    baked_lighting_group_input.parent = baked_lighting_frame
    baked_lighting_alpha_invert.parent = baked_lighting_frame
    baked_lighting_texture_boost.parent = baked_lighting_frame
    baked_lighting_mix.parent = baked_lighting_frame
    prm_compare_cv30_x.parent = prm_frame
    prm_metal_minimum.parent = prm_frame
    prm_separate_prm_rgb.parent = prm_frame
    prm_multiply_prm_alpha.parent = prm_frame
    prm_custom_vector_47_rgb_override.parent = prm_frame
    prm_custom_vector_47_alpha_override.parent = prm_frame
    nor_group_input.parent = nor_frame
    nor_separate_rgb.parent = nor_frame
    nor_combine_rgb.parent = nor_frame
    nor_normal_map.parent = nor_frame
    alpha_maximum.parent = alpha_frame
    alpha_color_set1_scale.parent = alpha_frame
    emission_multiply.parent = emission_frame
    emission_mix_rgb.parent = emission_frame
    cv30_x_input.parent = prm_frame
    texture6_group_input.parent = prm_frame
    use_custom_vector_47_group_input.parent = prm_frame
    cv47_combine.parent = prm_frame
    cv47_group_input.parent = prm_frame
    colorset1_albedo.parent = colorset1_albedo_frame
    color_set1_scale.parent = colorset1_albedo_frame
    emission_textures_group_input.parent = emission_frame
    cv3_input.parent = emission_frame
    cv3_combine.parent = emission_frame
    apply_color_set_1_alpha.parent = alpha_frame
    layer1_tex_alphas.parent = alpha_frame
    cv0_x_input.parent = alpha_frame
    colorset1_alpha.parent = alpha_frame
    get_lowest_tex_alpha.parent = alpha_frame
    eevee_principled_shader.parent = eevee_frame
    colorset1_group_input.parent = colorset1_albedo_frame
    eevee_apply_cv8.parent = eevee_shader_to_rgb_frame
    shader_to_rgb.parent = eevee_shader_to_rgb_frame
    eevee_colorset1_input.parent = eevee_shader_to_rgb_frame
    eevee_colorset1_scale.parent = eevee_shader_to_rgb_frame
    eevee_apply_colorset1.parent = eevee_shader_to_rgb_frame
    eevee_add_shader.parent = eevee_shader_to_rgb_frame
    eevee_transparent_bsdf.parent = eevee_shader_to_rgb_frame
    eevee_invert_alpha.parent = eevee_shader_to_rgb_frame
    eevee_combine_cv8.parent = eevee_shader_to_rgb_frame
    eevee_cv8_input.parent = eevee_shader_to_rgb_frame
    reroute_1.parent = eevee_shader_to_rgb_frame
    reroute_2.parent = eevee_shader_to_rgb_frame
    reroute_3.parent = eevee_shader_to_rgb_frame
    reroute_4.parent = eevee_shader_to_rgb_frame

    # Set Locations (from NodeToPython)
    diffuse_main_frame.location = (-112.2184066772461, 704.4589233398438)
    mix_col_textures_frame.location = (-53.89348602294922, -695.72216796875)
    fake_sss_frame.location = (-78.49345397949219, -637.7626953125)
    cv13_frame.location = (90.51840209960938, -731.274658203125)
    baked_lighting_frame.location = (20.81695556640625, 220.4208984375)
    prm_frame.location = (257.1662902832031, 203.76144409179688)
    nor_frame.location = (458.1097717285156, -497.4741516113281)
    alpha_frame.location = (357.1073913574219, -329.7359619140625)
    emission_frame.location = (769.1549682617188, 38.64401626586914)
    cycles_frame.location = (1005.4591064453125, 725.4411010742188)
    colorset1_albedo_frame.location = (36.4132080078125, 132.049560546875)
    eevee_frame.location = (1728.2259521484375, -601.0872802734375)
    eevee_shader_to_rgb_frame.location = (-30.0, -116.88106536865234)
    cycles_shader.location = (367.297607421875, -13.69659423828125)
    col_textures_group_input.location = (-1774.048095703125, 400.0)
    color_set_5_alpha_group_input.location = (-1700.0, 560.0)
    col_tex_layer_2_alpha_group_input.location = (-1399.333251953125, 629.12158203125)
    color_set_5_scale.location = (-1517.854736328125, 560.7460327148438)
    one_minus_color_set_5_alpha.location = (-1320.4451904296875, 560.7460327148438)
    col_map_mix_factor.location = (-1130.061767578125, 560.7460327148438)
    col_map_mix.location = (-933.9639892578125, 504.34521484375)
    fake_sss_factor_group_input.location = (-1397.928955078125, 982.4134521484375)
    cv11_group_input.location = (-1395.257568359375, 835.5263671875)
    separate_prm_r.location = (-946.679931640625, 982.4134521484375)
    fake_sss_factor.location = (-768.8907470703125, 982.4134521484375)
    cv11_combine.location = (-1121.6766357421875, 835.5263671875)
    fake_sss_color_mix.location = (-552.2467651367188, 851.7605590820312)
    cv13_group_input.location = (-670.4852294921875, 468.8002624511719)
    cv13_combine.location = (-442.923095703125, 499.697021484375)
    cv13_multiply.location = (-273.11767578125, 635.7279052734375)
    baked_lighting_group_input.location = (-282.06439208984375, 32.27264404296875)
    baked_lighting_alpha_invert.location = (-27.44634246826172, 110.84942626953125)
    baked_lighting_texture_boost.location = (-22.445999145507812, -1.40313720703125)
    baked_lighting_mix.location = (230.72903442382812, -36.7052001953125)
    prm_compare_cv30_x.location = (-344.6485595703125, 28.68292236328125)
    prm_metal_minimum.location = (-88.19952392578125, 0.0)
    prm_separate_prm_rgb.location = (-344.6485595703125, -200.0)
    prm_multiply_prm_alpha.location = (-344.6485595703125, -350.0)
    prm_custom_vector_47_rgb_override.location = (-647.3397216796875, -122.52677917480469)
    prm_custom_vector_47_alpha_override.location = (-647.3397216796875, -300.0)
    nor_group_input.location = (-1294.443115234375, -600.0)
    nor_separate_rgb.location = (-900.0, -600.0)
    nor_combine_rgb.location = (-600.0, -600.0)
    nor_normal_map.location = (-300.0, -600.0)
    alpha_maximum.location = (-670.5067138671875, -400.0)
    alpha_color_set1_scale.location = (-426.2577209472656, -532.9165649414062)
    emission_multiply.location = (-674.25341796875, -481.72467041015625)
    emission_mix_rgb.location = (-943.756591796875, -407.9454650878906)
    cv30_x_input.location = (-640.99462890625, -1.10455322265625)
    texture6_group_input.location = (-1020.06884765625, 0.0)
    use_custom_vector_47_group_input.location = (-985.594970703125, -184.89730834960938)
    cv47_combine.location = (-953.4609375, -300.67572021484375)
    cv47_group_input.location = (-1217.8944091796875, -352.33709716796875)
    colorset1_albedo.location = (78.42138671875, -6.87310791015625)
    color_set1_scale.location = (-149.411865234375, -161.25177001953125)
    emission_textures_group_input.location = (-1367.0703125, -410.3283386230469)
    cv3_input.location = (-1366.397216796875, -604.44775390625)
    cv3_combine.location = (-941.1038208007812, -586.0667724609375)
    apply_color_set_1_alpha.location = (-210.05528259277344, -400.0)
    layer1_tex_alphas.location = (-1353.381591796875, -402.8682861328125)
    cv0_x_input.location = (-864.464599609375, -565.3116455078125)
    colorset1_alpha.location = (-613.5657958984375, -648.2987060546875)
    get_lowest_tex_alpha.location = (-1028.6805419921875, -400.0)
    eevee_principled_shader.location = (-336.16778564453125, 114.10406494140625)
    colorset1_group_input.location = (-323.54608154296875, -258.39532470703125)
    unified_output.location = (1900.4813232421875, 114.10406494140625)
    eevee_apply_cv8.location = (2578.93212890625, -370.62335205078125)
    shader_to_rgb.location = (1734.078369140625, -472.7522277832031)
    eevee_colorset1_input.location = (1970.90234375, -649.0486450195312)
    eevee_colorset1_scale.location = (2165.769775390625, -533.6234130859375)
    eevee_apply_colorset1.location = (2363.01953125, -374.69403076171875)
    eevee_add_shader.location = (2947.098876953125, -375.4335021972656)
    eevee_transparent_bsdf.location = (2783.951416015625, -529.043212890625)
    eevee_invert_alpha.location = (2630.9873046875, -612.8931884765625)
    eevee_combine_cv8.location = (2388.70947265625, -662.6732177734375)
    eevee_cv8_input.location = (2185.878662109375, -763.8817138671875)
    reroute_1.location = (1921.01904296875, -531.3726196289062)
    reroute_2.location = (1921.01904296875, -902.4708251953125)
    reroute_3.location = (2583.41357421875, -902.4708251953125)
    reroute_4.location = (2583.41357421875, -695.997314453125)

    # Set Dimensions (from NodeToPython)
    diffuse_main_frame.width, diffuse_main_frame.height = 2339.0, 834.0
    mix_col_textures_frame.width, mix_col_textures_frame.height = 1040.0, 363.0
    fake_sss_frame.width, fake_sss_frame.height = 1046.0, 362.0
    cv13_frame.width, cv13_frame.height = 621.4008178710938, 323.0
    baked_lighting_frame.width, baked_lighting_frame.height = 712.0, 379.0
    prm_frame.width, prm_frame.height = 1330.0, 592.0
    nor_frame.width, nor_frame.height = 1204.0, 212.0
    alpha_frame.width, alpha_frame.height = 1364.2154541015625, 360.0
    emission_frame.width, emission_frame.height = 967.2534790039062, 357.0000305175781
    cycles_frame.width, cycles_frame.height = 985.0, 889.0
    colorset1_albedo_frame.width, colorset1_albedo_frame.height = 602.0, 386.0
    eevee_frame.width, eevee_frame.height = 300.0, 720.0
    eevee_shader_to_rgb_frame.width, eevee_shader_to_rgb_frame.height = 1413.0, 599.351806640625
    cycles_shader.width, cycles_shader.height = 240.0, 100.0
    col_textures_group_input.width, col_textures_group_input.height = 197.9361572265625, 100.0
    color_set_5_alpha_group_input.width, color_set_5_alpha_group_input.height = 117.63037109375, 100.0
    col_tex_layer_2_alpha_group_input.width, col_tex_layer_2_alpha_group_input.height = 217.7059326171875, 100.0
    color_set_5_scale.width, color_set_5_scale.height = 140.0, 100.0
    one_minus_color_set_5_alpha.width, one_minus_color_set_5_alpha.height = 140.0, 100.0
    col_map_mix_factor.width, col_map_mix_factor.height = 140.0, 100.0
    col_map_mix.width, col_map_mix.height = 140.0, 100.0
    fake_sss_factor_group_input.width, fake_sss_factor_group_input.height = 223.8880615234375, 100.0
    cv11_group_input.width, cv11_group_input.height = 223.8880615234375, 100.0
    separate_prm_r.width, separate_prm_r.height = 140.0, 100.0
    fake_sss_factor.width, fake_sss_factor.height = 140.0, 100.0
    cv11_combine.width, cv11_combine.height = 132.4202880859375, 100.0
    fake_sss_color_mix.width, fake_sss_color_mix.height = 140.0, 100.0
    cv13_group_input.width, cv13_group_input.height = 200.53936767578125, 100.0
    cv13_combine.width, cv13_combine.height = 140.0, 100.0
    cv13_multiply.width, cv13_multiply.height = 164.4007568359375, 100.0
    baked_lighting_group_input.width, baked_lighting_group_input.height = 212.01339721679688, 100.0
    baked_lighting_alpha_invert.width, baked_lighting_alpha_invert.height = 187.69775390625, 100.0
    baked_lighting_texture_boost.width, baked_lighting_texture_boost.height = 178.8572998046875, 100.0
    baked_lighting_mix.width, baked_lighting_mix.height = 140.0, 100.0
    prm_compare_cv30_x.width, prm_compare_cv30_x.height = 140.0, 100.0
    prm_metal_minimum.width, prm_metal_minimum.height = 140.0, 100.0
    prm_separate_prm_rgb.width, prm_separate_prm_rgb.height = 140.0, 100.0
    prm_multiply_prm_alpha.width, prm_multiply_prm_alpha.height = 140.0, 100.0
    prm_custom_vector_47_rgb_override.width, prm_custom_vector_47_rgb_override.height = 212.19342041015625, 100.0
    prm_custom_vector_47_alpha_override.width, prm_custom_vector_47_alpha_override.height = 210.87249755859375, 100.0
    nor_group_input.width, nor_group_input.height = 234.443115234375, 100.0
    nor_separate_rgb.width, nor_separate_rgb.height = 140.0, 100.0
    nor_combine_rgb.width, nor_combine_rgb.height = 140.0, 100.0
    nor_normal_map.width, nor_normal_map.height = 150.0, 100.0
    alpha_maximum.width, alpha_maximum.height = 201.1561279296875, 100.0
    alpha_color_set1_scale.width, alpha_color_set1_scale.height = 161.55615234375, 100.0
    emission_multiply.width, emission_multiply.height = 214.25341796875, 100.0
    emission_mix_rgb.width, emission_mix_rgb.height = 206.29779052734375, 100.0
    cv30_x_input.width, cv30_x_input.height = 205.80047607421875, 100.0
    texture6_group_input.width, texture6_group_input.height = 212.7291259765625, 100.0
    use_custom_vector_47_group_input.width, use_custom_vector_47_group_input.height = 174.1201171875, 100.0
    cv47_combine.width, cv47_combine.height = 140.0, 100.0
    cv47_group_input.width, cv47_group_input.height = 212.7291259765625, 100.0
    colorset1_albedo.width, colorset1_albedo.height = 140.0, 100.0
    color_set1_scale.width, color_set1_scale.height = 140.0, 100.0
    emission_textures_group_input.width, emission_textures_group_input.height = 216.04730224609375, 100.0
    cv3_input.width, cv3_input.height = 216.04730224609375, 100.0
    cv3_combine.width, cv3_combine.height = 140.0, 100.0
    apply_color_set_1_alpha.width, apply_color_set_1_alpha.height = 161.2154541015625, 100.0
    layer1_tex_alphas.width, layer1_tex_alphas.height = 250.69598388671875, 100.0
    cv0_x_input.width, cv0_x_input.height = 178.20654296875, 100.0
    colorset1_alpha.width, colorset1_alpha.height = 143.0079345703125, 100.0
    get_lowest_tex_alpha.width, get_lowest_tex_alpha.height = 165.9859619140625, 100.0
    eevee_principled_shader.width, eevee_principled_shader.height = 240.0, 100.0
    colorset1_group_input.width, colorset1_group_input.height = 140.0, 100.0
    unified_output.width, unified_output.height = 140.0, 100.0
    eevee_apply_cv8.width, eevee_apply_cv8.height = 140.0, 100.0
    shader_to_rgb.width, shader_to_rgb.height = 140.0, 100.0
    eevee_colorset1_input.width, eevee_colorset1_input.height = 140.0, 100.0
    eevee_colorset1_scale.width, eevee_colorset1_scale.height = 140.0, 100.0
    eevee_apply_colorset1.width, eevee_apply_colorset1.height = 140.0, 100.0
    eevee_add_shader.width, eevee_add_shader.height = 140.0, 100.0
    eevee_transparent_bsdf.width, eevee_transparent_bsdf.height = 140.0, 100.0
    eevee_invert_alpha.width, eevee_invert_alpha.height = 140.0, 100.0
    eevee_combine_cv8.width, eevee_combine_cv8.height = 140.0, 100.0
    eevee_cv8_input.width, eevee_cv8_input.height = 140.0, 100.0
    reroute_1.width, reroute_1.height = 16.0, 100.0
    reroute_2.width, reroute_2.height = 16.0, 100.0
    reroute_3.width, reroute_3.height = 16.0, 100.0
    reroute_4.width, reroute_4.height = 16.0, 100.0

    # Set Links (mostly from NodeToPython)
    #cycles_shader.BSDF -> unified_output.Cycles Output
    inner_links.new(cycles_shader.outputs[0], unified_output.inputs[0])
    #color_set_5_alpha_group_input.colorSet5 Alpha -> color_set_5_scale.Value
    inner_links.new(color_set_5_alpha_group_input.outputs[43], color_set_5_scale.inputs[1])
    #color_set_5_scale.Value -> one_minus_color_set_5_alpha.Value
    inner_links.new(color_set_5_scale.outputs[0], one_minus_color_set_5_alpha.inputs[1])
    #col_tex_layer_2_alpha_group_input.Texture1 Alpha (Col Map Layer 2) -> col_map_mix_factor.Value
    inner_links.new(col_tex_layer_2_alpha_group_input.outputs[3], col_map_mix_factor.inputs[0])
    #one_minus_color_set_5_alpha.Value -> col_map_mix_factor.Value
    inner_links.new(one_minus_color_set_5_alpha.outputs[0], col_map_mix_factor.inputs[1])
    #col_map_mix_factor.Value -> col_map_mix.Fac
    inner_links.new(col_map_mix_factor.outputs[0], col_map_mix.inputs[0])
    #col_textures_group_input.Texture0 RGB (Col Map Layer 1) -> col_map_mix.Color1
    inner_links.new(col_textures_group_input.outputs[0], col_map_mix.inputs[1])
    #col_textures_group_input.Texture1 RGB (Col Map Layer 2) -> col_map_mix.Color2
    inner_links.new(col_textures_group_input.outputs[2], col_map_mix.inputs[2])
    #cv11_group_input.CV 11 X (Fake SSS Color R) -> cv11_combine.R
    inner_links.new(cv11_group_input.outputs[88], cv11_combine.inputs[0])
    #cv11_group_input.CV 11 Y (Fake SSS Color G) -> cv11_combine.G
    inner_links.new(cv11_group_input.outputs[89], cv11_combine.inputs[1])
    #cv11_group_input.CV 11 Z (Fake SSS Color B) -> cv11_combine.B
    inner_links.new(cv11_group_input.outputs[90], cv11_combine.inputs[2])
    #cv11_combine.Image -> fake_sss_color_mix.Color2
    inner_links.new(cv11_combine.outputs[0], fake_sss_color_mix.inputs[2])
    #fake_sss_factor_group_input.Texture6 RGB (PRM Map) -> separate_prm_r.Image
    inner_links.new(fake_sss_factor_group_input.outputs[12], separate_prm_r.inputs[0])
    #separate_prm_r.R -> fake_sss_factor.Value
    inner_links.new(separate_prm_r.outputs[0], fake_sss_factor.inputs[0])
    #fake_sss_factor_group_input.CV 30 X (Fake SSS Blend Factor) -> fake_sss_factor.Value
    inner_links.new(fake_sss_factor_group_input.outputs[164], fake_sss_factor.inputs[1])
    #fake_sss_factor.Value -> fake_sss_color_mix.Fac
    inner_links.new(fake_sss_factor.outputs[0], fake_sss_color_mix.inputs[0])
    #col_map_mix.Color -> fake_sss_color_mix.Color1
    inner_links.new(col_map_mix.outputs[0], fake_sss_color_mix.inputs[1])
    #cv13_group_input.CV 13 X (Diffuse Color Scale R) -> cv13_combine.R
    inner_links.new(cv13_group_input.outputs[96], cv13_combine.inputs[0])
    #cv13_group_input.CV 13 Y (Diffuse Color Scale G) -> cv13_combine.G
    inner_links.new(cv13_group_input.outputs[97], cv13_combine.inputs[1])
    #cv13_group_input.CV 13 Z (Diffuse Color Scale B) -> cv13_combine.B
    inner_links.new(cv13_group_input.outputs[98], cv13_combine.inputs[2])
    #fake_sss_color_mix.Color -> cv13_multiply.Color1
    inner_links.new(fake_sss_color_mix.outputs[0], cv13_multiply.inputs[1])
    #cv13_combine.Image -> cv13_multiply.Color2
    inner_links.new(cv13_combine.outputs[0], cv13_multiply.inputs[2])
    #baked_lighting_group_input.Texture9 Alpha (Baked Lighting Map) -> baked_lighting_alpha_invert.Color
    inner_links.new(baked_lighting_group_input.outputs[19], baked_lighting_alpha_invert.inputs[1])
    #baked_lighting_group_input.Texture9 RGB (Baked Lighting Map) -> baked_lighting_texture_boost.Color1
    inner_links.new(baked_lighting_group_input.outputs[18], baked_lighting_texture_boost.inputs[1])
    #baked_lighting_alpha_invert.Color -> baked_lighting_mix.Fac
    inner_links.new(baked_lighting_alpha_invert.outputs[0], baked_lighting_mix.inputs[0])
    #cv13_multiply.Color -> baked_lighting_mix.Color1
    inner_links.new(cv13_multiply.outputs[0], baked_lighting_mix.inputs[1])
    #baked_lighting_texture_boost.Color -> baked_lighting_mix.Color2
    inner_links.new(baked_lighting_texture_boost.outputs[0], baked_lighting_mix.inputs[2])
    #texture6_group_input.Texture6 RGB (PRM Map) -> prm_custom_vector_47_rgb_override.Color1
    inner_links.new(texture6_group_input.outputs[12], prm_custom_vector_47_rgb_override.inputs[1])
    #texture6_group_input.Texture6 Alpha (PRM Map Specular) -> prm_custom_vector_47_alpha_override.Color1
    inner_links.new(texture6_group_input.outputs[13], prm_custom_vector_47_alpha_override.inputs[1])
    #cv47_group_input.CV 47 X (PRM R Metalness) -> cv47_combine.X
    inner_links.new(cv47_group_input.outputs[232], cv47_combine.inputs[0])
    #cv47_group_input.CV 47 Y (PRM G Roughness) -> cv47_combine.Y
    inner_links.new(cv47_group_input.outputs[233], cv47_combine.inputs[1])
    #cv47_group_input.CV 47 Z (PRM B AO) -> cv47_combine.Z
    inner_links.new(cv47_group_input.outputs[234], cv47_combine.inputs[2])
    #cv47_group_input.CV 47 W (PRM A Specular Boost) -> prm_custom_vector_47_alpha_override.Color2
    inner_links.new(cv47_group_input.outputs[235], prm_custom_vector_47_alpha_override.inputs[2])
    #cv47_combine.Vector -> prm_custom_vector_47_rgb_override.Color2
    inner_links.new(cv47_combine.outputs[0], prm_custom_vector_47_rgb_override.inputs[2])
    #prm_compare_cv30_x.Value -> prm_metal_minimum.Value
    inner_links.new(prm_compare_cv30_x.outputs[0], prm_metal_minimum.inputs[0])
    #prm_separate_prm_rgb.R -> prm_metal_minimum.Value
    inner_links.new(prm_separate_prm_rgb.outputs[0], prm_metal_minimum.inputs[1])
    #prm_custom_vector_47_rgb_override.Color -> prm_separate_prm_rgb.Image
    inner_links.new(prm_custom_vector_47_rgb_override.outputs[0], prm_separate_prm_rgb.inputs[0])
    #prm_custom_vector_47_alpha_override.Color -> prm_multiply_prm_alpha.Value
    inner_links.new(prm_custom_vector_47_alpha_override.outputs[0], prm_multiply_prm_alpha.inputs[1])
    #use_custom_vector_47_group_input.use_custom_vector_47 -> prm_custom_vector_47_rgb_override.Fac
    inner_links.new(use_custom_vector_47_group_input.outputs[276], prm_custom_vector_47_rgb_override.inputs[0])
    #use_custom_vector_47_group_input.use_custom_vector_47 -> prm_custom_vector_47_alpha_override.Fac
    inner_links.new(use_custom_vector_47_group_input.outputs[276], prm_custom_vector_47_alpha_override.inputs[0])
    #colorset1_group_input.colorSet1 RGB -> color_set1_scale.Color1
    inner_links.new(colorset1_group_input.outputs[40], color_set1_scale.inputs[1])
    #color_set1_scale.Color -> colorset1_albedo.Color2
    inner_links.new(color_set1_scale.outputs[0], colorset1_albedo.inputs[2])
    #baked_lighting_mix.Color -> colorset1_albedo.Color1
    inner_links.new(baked_lighting_mix.outputs[0], colorset1_albedo.inputs[1])
    #prm_metal_minimum.Value -> cycles_shader.Metallic
    inner_links.new(prm_metal_minimum.outputs[0], cycles_shader.inputs[6])
    #colorset1_albedo.Color -> cycles_shader.Base Color
    inner_links.new(colorset1_albedo.outputs[0], cycles_shader.inputs[0])
    #cv30_x_input.CV 30 X (Fake SSS Blend Factor) -> prm_compare_cv30_x.Value
    inner_links.new(cv30_x_input.outputs[164], prm_compare_cv30_x.inputs[1])
    #prm_separate_prm_rgb.G -> cycles_shader.Roughness
    inner_links.new(prm_separate_prm_rgb.outputs[1], cycles_shader.inputs[9])
    #prm_multiply_prm_alpha.Value -> cycles_shader.Specular
    inner_links.new(prm_multiply_prm_alpha.outputs[0], cycles_shader.inputs[7])
    #emission_textures_group_input.Texture5 RGB (Emissive Map Layer 1) -> emission_mix_rgb.Color1
    inner_links.new(emission_textures_group_input.outputs[10], emission_mix_rgb.inputs[1])
    #emission_textures_group_input.Texture14 RGB (Emissive Map Layer 2) -> emission_mix_rgb.Color2
    inner_links.new(emission_textures_group_input.outputs[28], emission_mix_rgb.inputs[2])
    #emission_textures_group_input.Texture14 Alpha (Emissive Map Layer 2) -> emission_mix_rgb.Fac
    inner_links.new(emission_textures_group_input.outputs[29], emission_mix_rgb.inputs[0])
    #cv3_input.CV 3 X (Emission Scale R) -> cv3_combine.X
    inner_links.new(cv3_input.outputs[56], cv3_combine.inputs[0])
    #cv3_input.CV 3 Y (Emission Scale G) -> cv3_combine.Y
    inner_links.new(cv3_input.outputs[57], cv3_combine.inputs[1])
    #cv3_input.CV 3 Z (Emission Scale B) -> cv3_combine.Z
    inner_links.new(cv3_input.outputs[58], cv3_combine.inputs[2])
    #cv3_combine.Vector -> emission_multiply.Color2
    inner_links.new(cv3_combine.outputs[0], emission_multiply.inputs[2])
    #emission_mix_rgb.Color -> emission_multiply.Color1
    inner_links.new(emission_mix_rgb.outputs[0], emission_multiply.inputs[1])
    #emission_multiply.Color -> cycles_shader.Emission
    inner_links.new(emission_multiply.outputs[0], cycles_shader.inputs[19])
    #layer1_tex_alphas.Texture0 Alpha (Col Map Layer 1) -> get_lowest_tex_alpha.Value
    inner_links.new(layer1_tex_alphas.outputs[1], get_lowest_tex_alpha.inputs[0])
    #layer1_tex_alphas.Texture5 Alpha (Emissive Map Layer 1) -> get_lowest_tex_alpha.Value
    inner_links.new(layer1_tex_alphas.outputs[11], get_lowest_tex_alpha.inputs[1])
    #cv0_x_input.CV 0 X (Min Texture Alpha) -> alpha_maximum.Value
    inner_links.new(cv0_x_input.outputs[44], alpha_maximum.inputs[1])
    #get_lowest_tex_alpha.Value -> alpha_maximum.Value
    inner_links.new(get_lowest_tex_alpha.outputs[0], alpha_maximum.inputs[0])
    #alpha_maximum.Value -> apply_color_set_1_alpha.Value
    inner_links.new(alpha_maximum.outputs[0], apply_color_set_1_alpha.inputs[0])
    #alpha_color_set1_scale.Value -> apply_color_set_1_alpha.Value
    inner_links.new(alpha_color_set1_scale.outputs[0], apply_color_set_1_alpha.inputs[1])
    #colorset1_alpha.colorSet1 Alpha -> alpha_color_set1_scale.Value
    inner_links.new(colorset1_alpha.outputs[41], alpha_color_set1_scale.inputs[0])
    #apply_color_set_1_alpha.Value -> cycles_shader.Alpha
    inner_links.new(apply_color_set_1_alpha.outputs[0], cycles_shader.inputs[21])
    #nor_group_input.Texture4 RGB (NOR Map) -> nor_separate_rgb.Image
    inner_links.new(nor_group_input.outputs[8], nor_separate_rgb.inputs[0])
    #nor_separate_rgb.R -> nor_combine_rgb.R
    inner_links.new(nor_separate_rgb.outputs[0], nor_combine_rgb.inputs[0])
    #nor_separate_rgb.G -> nor_combine_rgb.G
    inner_links.new(nor_separate_rgb.outputs[1], nor_combine_rgb.inputs[1])
    #nor_combine_rgb.Image -> nor_normal_map.Color
    inner_links.new(nor_combine_rgb.outputs[0], nor_normal_map.inputs[1])
    #nor_normal_map.Normal -> cycles_shader.Normal
    inner_links.new(nor_normal_map.outputs[0], cycles_shader.inputs[22])
    #prm_metal_minimum.Value -> eevee_principled_shader.Metallic
    inner_links.new(prm_metal_minimum.outputs[0], eevee_principled_shader.inputs[6])
    #prm_separate_prm_rgb.G -> eevee_principled_shader.Roughness
    inner_links.new(prm_separate_prm_rgb.outputs[1], eevee_principled_shader.inputs[9])
    #apply_color_set_1_alpha.Value -> eevee_principled_shader.Alpha
    inner_links.new(apply_color_set_1_alpha.outputs[0], eevee_principled_shader.inputs[21])
    #nor_normal_map.Normal -> eevee_principled_shader.Normal
    inner_links.new(nor_normal_map.outputs[0], eevee_principled_shader.inputs[22])
    #baked_lighting_mix.Color -> eevee_principled_shader.Base Color
    inner_links.new(baked_lighting_mix.outputs[0], eevee_principled_shader.inputs[0])
    #emission_multiply.Color -> eevee_principled_shader.Emission
    inner_links.new(emission_multiply.outputs[0], eevee_principled_shader.inputs[19])
    #eevee_principled_shader.BSDF -> shader_to_rgb.Shader
    inner_links.new(eevee_principled_shader.outputs[0], shader_to_rgb.inputs[0])
    #eevee_apply_cv8.Color -> eevee_add_shader.Shader
    inner_links.new(eevee_apply_cv8.outputs[0], eevee_add_shader.inputs[0])
    #eevee_transparent_bsdf.BSDF -> eevee_add_shader.Shader
    inner_links.new(eevee_transparent_bsdf.outputs[0], eevee_add_shader.inputs[1])
    #eevee_invert_alpha.Color -> eevee_transparent_bsdf.Color
    inner_links.new(eevee_invert_alpha.outputs[0], eevee_transparent_bsdf.inputs[0])
    #eevee_add_shader.Shader -> unified_output.EEVEE Output
    inner_links.new(eevee_add_shader.outputs[0], unified_output.inputs[1])
    #shader_to_rgb.Color -> eevee_apply_colorset1.Color1
    inner_links.new(shader_to_rgb.outputs[0], eevee_apply_colorset1.inputs[1])
    #eevee_cv8_input.CV 8 X (Final Color Scale R) -> eevee_combine_cv8.Red
    inner_links.new(eevee_cv8_input.outputs[76], eevee_combine_cv8.inputs[0])
    #eevee_cv8_input.CV 8 Y (Final Color Scale G) -> eevee_combine_cv8.Green
    inner_links.new(eevee_cv8_input.outputs[77], eevee_combine_cv8.inputs[1])
    #eevee_cv8_input.CV 8 Z (Final Color Scale B) -> eevee_combine_cv8.Blue
    inner_links.new(eevee_cv8_input.outputs[78], eevee_combine_cv8.inputs[2])
    #eevee_apply_colorset1.Color -> eevee_apply_cv8.Color1
    inner_links.new(eevee_apply_colorset1.outputs[0], eevee_apply_cv8.inputs[1])
    #eevee_combine_cv8.Color -> eevee_apply_cv8.Color2
    inner_links.new(eevee_combine_cv8.outputs[0], eevee_apply_cv8.inputs[2])
    #shader_to_rgb.Alpha -> reroute_1.Input
    inner_links.new(shader_to_rgb.outputs[1], reroute_1.inputs[0])
    #reroute_1.Output -> reroute_2.Input
    inner_links.new(reroute_1.outputs[0], reroute_2.inputs[0])
    #eevee_colorset1_input.colorSet1 RGB -> eevee_colorset1_scale.Color1
    inner_links.new(eevee_colorset1_input.outputs[40], eevee_colorset1_scale.inputs[1])
    #eevee_colorset1_scale.Color -> eevee_apply_colorset1.Color2
    inner_links.new(eevee_colorset1_scale.outputs[0], eevee_apply_colorset1.inputs[2])
    #reroute_4.Output -> eevee_invert_alpha.Color
    inner_links.new(reroute_4.outputs[0], eevee_invert_alpha.inputs[1])
    #reroute_2.Output -> reroute_3.Input
    inner_links.new(reroute_2.outputs[0], reroute_3.inputs[0])
    #reroute_3.Output -> reroute_4.Input
    inner_links.new(reroute_3.outputs[0], reroute_4.inputs[0])
    inner_links.new(prm_multiply_prm_alpha.outputs[0], eevee_principled_shader.inputs['Specular'])

    # Each input node technically has all the group's inputs.
    # The duplicate node group input nodes are used to visually group inputs.
    # Hide the unlinked nodes to make each input node smaller.
    hide_unlinked_outputs(col_textures_group_input)
    hide_unlinked_outputs(color_set_5_alpha_group_input)
    hide_unlinked_outputs(col_tex_layer_2_alpha_group_input)
    hide_unlinked_outputs(fake_sss_factor_group_input)
    hide_unlinked_outputs(cv11_group_input)
    hide_unlinked_outputs(cv13_group_input)
    hide_unlinked_outputs(baked_lighting_group_input)
    hide_unlinked_outputs(cv30_x_input)
    hide_unlinked_outputs(texture6_group_input)
    hide_unlinked_outputs(use_custom_vector_47_group_input)
    hide_unlinked_outputs(cv47_group_input)
    hide_unlinked_outputs(colorset1_group_input)
    hide_unlinked_outputs(emission_textures_group_input)
    hide_unlinked_outputs(cv3_input)
    hide_unlinked_outputs(layer1_tex_alphas)
    hide_unlinked_outputs(cv0_x_input)
    hide_unlinked_outputs(colorset1_alpha)
    hide_unlinked_outputs(nor_group_input)
    hide_unlinked_outputs(eevee_cv8_input)
    hide_unlinked_outputs(eevee_colorset1_input)
