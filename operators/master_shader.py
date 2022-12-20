import bpy
from bpy.types import ShaderNodeVertexColor

from . import material_inputs


def get_master_shader_name():
    return 'Smash Ultimate Master Shader'


def create_inputs(node_tree, name_to_inputs):
    for _, inputs in name_to_inputs.items():
        for socket, name, default in inputs:
            input = node_tree.inputs.new(socket, name)
            input.default_value = default


def hide_unlinked_outputs(node):
    for output in node.outputs:
        if output.is_linked is False:
            output.hide = True


def create_master_shader():
    master_shader_name = get_master_shader_name()
    # Check if already exists and just skip if it does
    if bpy.data.node_groups.get(master_shader_name, None) is not None:
        print('Master shader already exists, skipping')
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
    node_group_node_tree.outputs.new('NodeSocketShader', 'Final Output')

    # Now we are ready to start adding inputs
    def add_color_node(name):
        return node_group_node_tree.inputs.new('NodeSocketColor', name)

    def add_float_node(name):
        return node_group_node_tree.inputs.new('NodeSocketFloat', name)

    node_group_node_tree.inputs.new('NodeSocketString', 'Material Name')
    node_group_node_tree.inputs.new('NodeSocketString', 'Shader Label')

    add_color_node('Texture0 RGB (Col Map Layer 1)')
    input = add_float_node('Texture0 Alpha (Col Map Layer 1)')
    input.default_value = 1.0
    add_color_node('Texture1 RGB (Col Map Layer 2)')
    add_float_node('Texture1 Alpha (Col Map Layer 2)')
    add_color_node('Texture2 RGB (Irradiance Cube Map)')
    add_float_node('Texture2 Alpha (Irradiance Cube Map)')
    add_color_node('Texture3 RGB (Ambient Occlusion Map)')
    add_float_node('Texture3 Alpha (Ambient Occlusion Map)')
    input = add_color_node('Texture4 RGB (NOR Map)')
    input.default_value = (0.5, 0.5, 0.0, 1)
    input = add_float_node('Texture4 Alpha (NOR Map Cavity Channel)')
    input.default_value = 1.0
    add_color_node('Texture5 RGB (Emissive Map Layer 1)')
    input = add_float_node('Texture5 Alpha (Emissive Map Layer 1)')
    input.default_value = 1.0
    input = add_color_node('Texture6 RGB (PRM Map)')
    input.default_value = (0.0, 1.0, 1.0, 1.0)
    input = add_float_node('Texture6 Alpha (PRM Map Specular)')
    input.default_value = 0.0
    add_color_node('Texture7 RGB (Specular Cube Map)')
    add_float_node('Texture7 Alpha (Specular Cube Map)')
    add_color_node('Texture8 RGB (Diffuse Cube Map)')
    add_float_node('Texture8 Alpha (Diffuse Cube Map)')
    add_color_node('Texture9 RGB (Baked Lighting Map)')
    input = add_float_node('Texture9 Alpha (Baked Lighting Map)')
    input.default_value = 1.0
    add_color_node('Texture10 RGB (Diffuse Map Layer 1)')
    add_float_node('Texture10 Alpha (Diffuse Map Layer 1)')
    add_color_node('Texture11 RGB (Diffuse Map Layer 2)')
    add_float_node('Texture11 Alpha (Diffuse Map Layer 2)')
    add_color_node('Texture12 RGB (Diffuse Map Layer 3)')
    add_float_node('Texture12 Alpha (Diffuse Map Layer 3)')
    add_color_node('Texture13 RGB (Projection Light Map)')
    add_float_node('Texture13 Alpha (Projection Light Map)')
    add_color_node('Texture14 RGB (Emissive Map Layer 2)')
    add_float_node('Texture14 Alpha (Emissive Map Layer 2)')
    add_color_node('Texture15 RGB (Unused)')
    add_float_node('Texture15 Alpha (Unused)')
    add_color_node('Texture16 RGB (Ink Normal Map)')
    add_float_node('Texture16 Alpha (Ink Normal Map)')
    add_color_node('Texture17 RGB (Unused)')
    add_float_node('Texture17 Alpha (Unused)')
    add_color_node('Texture18 RGB (Unused)')
    add_float_node('Texture18 Alpha (Unused)')
    add_color_node('Texture19 RGB (Unused)')
    add_float_node('Texture19 Alpha (Unused)')

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

    create_inputs(node_group_node_tree, material_inputs.vec4_param_to_inputs)
    create_inputs(node_group_node_tree, material_inputs.float_param_to_inputs)
    create_inputs(node_group_node_tree, material_inputs.bool_param_to_inputs)

    input = node_group_node_tree.inputs.new(
        'NodeSocketString', 'BlendState0 Field1 (Source Color)')
    input.default_value = "One"
    input = node_group_node_tree.inputs.new(
        'NodeSocketString', 'BlendState0 Field3 (Destination Color)')
    input.default_value = "Zero"
    input = node_group_node_tree.inputs.new(
        'NodeSocketBool', 'BlendState0 Field7 (Alpha to Coverage)')
    input.default_value = False
    input = node_group_node_tree.inputs.new(
        'NodeSocketString', 'RasterizerState0 Field1 (Polygon Fill)')
    input.default_value = 'Fill'
    input = node_group_node_tree.inputs.new(
        'NodeSocketString', 'RasterizerState0 Field2 (Cull Mode)')
    input.default_value = 'Back'
    input = add_float_node('RasterizerState0 Field3 (Depth Bias)')
    input.default_value = 0.0
    # Wont be shown to users, should always be hidden
    input = add_float_node('use_custom_vector_47')
    input.default_value = 0.0

    # Allow for wider node
    node_group_node.bl_width_max = 1000

    # Now its time to place nodes
    inner_nodes = node_group_node.node_tree.nodes
    inner_links = node_group_node.node_tree.links

    shader_node = inner_nodes.new('ShaderNodeBsdfPrincipled')
    shader_node.name = 'Shader'
    shader_node.location = (500, 0)
    output_node = inner_nodes.new('NodeGroupOutput')
    output_node.name = 'Output'
    output_node.location = (1200, 0)
    inner_links.new(
        output_node.inputs['Final Output'], shader_node.outputs['BSDF'])

    diffuse_frame = inner_nodes.new('NodeFrame')
    diffuse_frame.name = 'Diffuse Frame'
    diffuse_frame.label = 'Diffuse Color Stuff'
    diffuse_input_node = inner_nodes.new('NodeGroupInput')
    diffuse_input_node.location = (-1500, 0)
    diffuse_input_node.parent = diffuse_frame

    color_set_input_node = inner_nodes.new('NodeGroupInput')
    color_set_input_node.location = (-1500, -300)

    cv13_node = inner_nodes.new('ShaderNodeMixRGB')
    cv13_node.name = 'CustomVector13 Multiply'
    cv13_node.label = 'CustomVector13 Multiply'
    cv13_node.location = (-215, 0)
    cv13_node.blend_type = 'MULTIPLY'
    cv13_node.inputs['Fac'].default_value = 1.0
    cv13_node.parent = diffuse_frame
    inner_links.new(
        cv13_node.inputs['Color1'], diffuse_input_node.outputs['CustomVector13 (Diffuse Color Multiplier)'])
    fake_sss_color_node = inner_nodes.new('ShaderNodeMixRGB')
    fake_sss_color_node.name = 'Fake SSS Color'
    fake_sss_color_node.label = 'Fake SSS Color'
    fake_sss_color_node.location = (-428, 0)
    fake_sss_color_node.parent = diffuse_frame
    inner_links.new(fake_sss_color_node.inputs['Color2'],
                    diffuse_input_node.outputs['CustomVector11 (Fake SSS Color)'])
    inner_links.new(cv13_node.inputs['Color2'],
                    fake_sss_color_node.outputs['Color'])
    fake_sss_factor_node = inner_nodes.new('ShaderNodeMath')
    fake_sss_factor_node.name = 'Fake SSS Factor'
    fake_sss_factor_node.label = 'Fake SSS Factor'
    fake_sss_factor_node.location = (-650, -200)
    fake_sss_factor_node.operation = 'MULTIPLY'
    fake_sss_factor_node.parent = diffuse_frame
    inner_links.new(
        fake_sss_factor_node.inputs[1], diffuse_input_node.outputs['CustomVector30 X (SSS Blend Factor)'])
    inner_links.new(
        fake_sss_color_node.inputs['Fac'], fake_sss_factor_node.outputs['Value'])
    color_map_mix_node = inner_nodes.new('ShaderNodeMixRGB')
    color_map_mix_node.name = 'ColorMapLayerMixer'
    color_map_mix_node.label = 'ColorMapLayerMixer'
    color_map_mix_node.location = (-650, 0)
    color_map_mix_node.parent = diffuse_frame
    inner_links.new(color_map_mix_node.inputs['Color2'],
                    diffuse_input_node.outputs['Texture1 RGB (Col Map Layer 2)'])
    inner_links.new(
        fake_sss_color_node.inputs['Color1'], color_map_mix_node.outputs['Color'])
    df_separate_prm_rgb_node = inner_nodes.new('ShaderNodeSeparateRGB')
    df_separate_prm_rgb_node.name = 'df_separate_prm_rgb_node'
    df_separate_prm_rgb_node.label = 'Separate PRM RGB'
    df_separate_prm_rgb_node.parent = diffuse_frame
    df_separate_prm_rgb_node.location = (-900, -200)
    inner_links.new(
        fake_sss_factor_node.inputs[0], df_separate_prm_rgb_node.outputs['R'])
    inner_links.new(
        df_separate_prm_rgb_node.inputs['Image'], diffuse_input_node.outputs['Texture6 RGB (PRM Map)'])

    color_set5_scale_node = inner_nodes.new('ShaderNodeMath')
    color_set5_scale_node.name = 'color_set5_scale_node'
    color_set5_scale_node.label = 'Color Set 5 Scale'
    color_set5_scale_node.location = (-1200, 500)
    color_set5_scale_node.parent = diffuse_frame
    color_set5_scale_node.operation = 'MULTIPLY'
    color_set5_scale_node.inputs[0].default_value = 3.0

    one_minus_color_set5_node = inner_nodes.new('ShaderNodeMath')
    one_minus_color_set5_node.name = 'one_minus_color_set5_node'
    one_minus_color_set5_node.label = '1 - Alpha'
    one_minus_color_set5_node.parent = diffuse_frame
    one_minus_color_set5_node.location = (-1000, 400)
    one_minus_color_set5_node.operation = 'SUBTRACT'
    one_minus_color_set5_node.inputs[0].default_value = 1.0
    one_minus_color_set5_node.use_clamp = True

    layer_2_alpha_minus_col_set_5 = inner_nodes.new('ShaderNodeMath')
    layer_2_alpha_minus_col_set_5.name = 'layer_2_alpha_minus_col_set_5'
    layer_2_alpha_minus_col_set_5.label = 'Texture Blend'
    layer_2_alpha_minus_col_set_5.parent = diffuse_frame
    layer_2_alpha_minus_col_set_5.location = (-800, 300)
    layer_2_alpha_minus_col_set_5.operation = 'SUBTRACT'
    layer_2_alpha_minus_col_set_5.use_clamp = True

    inner_links.new(
        color_set5_scale_node.inputs[1], color_set_input_node.outputs['colorSet5 Alpha'])
    inner_links.new(
        one_minus_color_set5_node.inputs[1], color_set5_scale_node.outputs[0])
    inner_links.new(
        layer_2_alpha_minus_col_set_5.inputs[0], diffuse_input_node.outputs['Texture1 Alpha (Col Map Layer 2)'])
    inner_links.new(
        layer_2_alpha_minus_col_set_5.inputs[1], one_minus_color_set5_node.outputs[0])
    inner_links.new(
        color_map_mix_node.inputs['Fac'], layer_2_alpha_minus_col_set_5.outputs[0])

    inner_links.new(color_map_mix_node.inputs['Color1'],
                    diffuse_input_node.outputs['Texture0 RGB (Col Map Layer 1)'])
    # Baked Lighting
    baked_lighting_frame = inner_nodes.new('NodeFrame')
    baked_lighting_frame.name = 'baked_lighting_frame'
    baked_lighting_frame.label = 'Baked Lighting'
    baked_lighting_frame.parent = diffuse_frame

    baked_lighting_texture_boost = inner_nodes.new('ShaderNodeMixRGB')
    baked_lighting_texture_boost.name = 'baked_lighting_texture_boost'
    baked_lighting_texture_boost.label = 'Bake Lighting Texture Boost'
    baked_lighting_texture_boost.parent = baked_lighting_frame
    baked_lighting_texture_boost.blend_type = 'MULTIPLY'
    baked_lighting_texture_boost.inputs['Color2'].default_value = (
        8.0, 8.0, 8.0, 1.0)
    baked_lighting_texture_boost.inputs['Fac'].default_value = 1.0

    baked_lighting_alpha_invert = inner_nodes.new('ShaderNodeInvert')
    baked_lighting_alpha_invert.name = 'baked_lighting_alpha_invert'
    baked_lighting_alpha_invert.label = 'Bake Lighting Alpha Invert'
    baked_lighting_alpha_invert.parent = baked_lighting_frame
    baked_lighting_alpha_invert.location = (-200, 0)

    baked_lighting_mix = inner_nodes.new('ShaderNodeMixRGB')
    baked_lighting_mix.name = 'baked_lighting_mix'
    baked_lighting_mix.label = 'Baked Lighting Mix'
    baked_lighting_mix.parent = diffuse_frame
    baked_lighting_mix.blend_type = 'MULTIPLY'

    baked_lighting_input_node = inner_nodes.new('NodeGroupInput')
    baked_lighting_input_node.parent = baked_lighting_frame
    baked_lighting_input_node.location = (-400, 0)

    inner_links.new(baked_lighting_texture_boost.inputs['Color1'],
                    baked_lighting_input_node.outputs['Texture9 RGB (Baked Lighting Map)'])
    inner_links.new(baked_lighting_alpha_invert.inputs['Color'],
                    baked_lighting_input_node.outputs['Texture9 Alpha (Baked Lighting Map)'])
    inner_links.new(
        baked_lighting_mix.inputs['Fac'], baked_lighting_alpha_invert.outputs[0])
    inner_links.new(baked_lighting_mix.inputs['Color1'], cv13_node.outputs[0])
    inner_links.new(
        baked_lighting_mix.inputs['Color2'], baked_lighting_texture_boost.outputs[0])

    baked_lighting_frame.location = (0, 300)

    diffuse_frame.location = (0, 625)
    # PRM Frame Time
    prm_frame = inner_nodes.new('NodeFrame')
    prm_frame.name = 'prm_frame'
    prm_frame.label = 'PRM Stuff'

    prm_group_input = inner_nodes.new('NodeGroupInput')
    prm_group_input.location = (-1200, 0)
    prm_group_input.parent = prm_frame

    prm_compare_cv30_x = inner_nodes.new('ShaderNodeMath')
    prm_compare_cv30_x.name = 'prm_compare_cv30_x'
    prm_compare_cv30_x.label = 'Compare CV30 X'
    prm_compare_cv30_x.operation = 'COMPARE'
    prm_compare_cv30_x.inputs[0].default_value = 0
    prm_compare_cv30_x.inputs[2].default_value = 0.00001
    prm_compare_cv30_x.location = (-600, 0)
    prm_compare_cv30_x.parent = prm_frame

    prm_metal_minimum = inner_nodes.new('ShaderNodeMath')
    prm_metal_minimum.name = 'prm_metal_minimum'
    prm_metal_minimum.label = 'PRM Metal Override'
    prm_metal_minimum.operation = 'MINIMUM'
    prm_metal_minimum.location = (-300, 0)
    prm_metal_minimum.parent = prm_frame

    prm_separate_prm_rgb = inner_nodes.new('ShaderNodeSeparateRGB')
    prm_separate_prm_rgb.name = 'prm_separate_prm_rgb'
    prm_separate_prm_rgb.label = 'Separate PRM RGB'
    prm_separate_prm_rgb.location = (-600, -200)
    prm_separate_prm_rgb.parent = prm_frame

    prm_multiply_prm_alpha = inner_nodes.new('ShaderNodeMath')
    prm_multiply_prm_alpha.name = 'prm_multiply_prm_alpha'
    prm_multiply_prm_alpha.label = 'Specular Boost'
    prm_multiply_prm_alpha.location = (-600, -350)
    prm_multiply_prm_alpha.parent = prm_frame
    prm_multiply_prm_alpha.operation = 'MULTIPLY'
    prm_multiply_prm_alpha.inputs[0].default_value = 2.5

    prm_custom_vector_47_rgb_override = inner_nodes.new('ShaderNodeMixRGB')
    prm_custom_vector_47_rgb_override.name = 'prm_custom_vector_47_rgb_override'
    prm_custom_vector_47_rgb_override.label = 'Custom Vector 47 RGB Overrider'
    prm_custom_vector_47_rgb_override.location = (-900, -150)
    prm_custom_vector_47_rgb_override.parent = prm_frame
    prm_custom_vector_47_rgb_override.blend_type = 'MIX'

    prm_custom_vector_47_alpha_override = inner_nodes.new('ShaderNodeMixRGB')
    prm_custom_vector_47_alpha_override.name = 'prm_custom_vector_47_alpha_override'
    prm_custom_vector_47_alpha_override.label = 'Custom Vector 47 Alpha Overrider'
    prm_custom_vector_47_alpha_override.location = (-900, -300)
    prm_custom_vector_47_alpha_override.parent = prm_frame
    prm_custom_vector_47_alpha_override.blend_type = 'MIX'

    inner_links.new(
        prm_custom_vector_47_rgb_override.inputs['Fac'], prm_group_input.outputs['use_custom_vector_47'])
    inner_links.new(
        prm_custom_vector_47_rgb_override.inputs['Color1'], prm_group_input.outputs['Texture6 RGB (PRM Map)'])
    inner_links.new(
        prm_custom_vector_47_rgb_override.inputs['Color2'], prm_group_input.outputs['CustomVector47 RGB'])
    inner_links.new(
        prm_custom_vector_47_alpha_override.inputs['Fac'], prm_group_input.outputs['use_custom_vector_47'])
    inner_links.new(prm_custom_vector_47_alpha_override.inputs['Color1'],
                    prm_group_input.outputs['Texture6 Alpha (PRM Map Specular)'])
    inner_links.new(
        prm_custom_vector_47_alpha_override.inputs['Color2'], prm_group_input.outputs['CustomVector47 Alpha'])
    inner_links.new(
        prm_compare_cv30_x.inputs[1], prm_group_input.outputs['CustomVector30 X (SSS Blend Factor)'])
    inner_links.new(
        prm_separate_prm_rgb.inputs['Image'], prm_custom_vector_47_rgb_override.outputs['Color'])
    inner_links.new(
        prm_multiply_prm_alpha.inputs[1], prm_custom_vector_47_alpha_override.outputs['Color'])
    inner_links.new(prm_metal_minimum.inputs[0], prm_compare_cv30_x.outputs[0])
    inner_links.new(
        prm_metal_minimum.inputs[1], prm_separate_prm_rgb.outputs['R'])
    inner_links.new(shader_node.inputs['Metallic'],
                    prm_metal_minimum.outputs['Value'])
    inner_links.new(shader_node.inputs['Roughness'],
                    prm_separate_prm_rgb.outputs['G'])

    prm_frame.location = (0, 200)
    # NOR Frame Time
    '''
    Nodes Needed (besides group input + frame):
        nor_separate_rgb
        nor_combine_rgb
        nor_normal_map
    '''
    nor_frame = inner_nodes.new('NodeFrame')
    nor_frame.name = 'nor_frame'
    nor_frame.label = 'NOR Map Stuff'
    nor_group_input = inner_nodes.new('NodeGroupInput')
    nor_group_input.name = 'nor_group_input'
    nor_group_input.location = (-1200, -600)
    nor_group_input.parent = nor_frame
    nor_separate_rgb = inner_nodes.new('ShaderNodeSeparateRGB')
    nor_separate_rgb.name = 'nor_separate_rgb'
    nor_separate_rgb.label = 'Separate NOR RGB'
    nor_separate_rgb.location = (-900, -600)
    nor_separate_rgb.parent = nor_frame
    inner_links.new(
        nor_separate_rgb.inputs['Image'], nor_group_input.outputs['Texture4 RGB (NOR Map)'])
    nor_combine_rgb = inner_nodes.new('ShaderNodeCombineRGB')
    nor_combine_rgb.name = 'nor_combine_rgb'
    nor_combine_rgb.label = 'Combine R + G'
    nor_combine_rgb.location = (-600, -600)
    nor_combine_rgb.parent = nor_frame
    nor_combine_rgb.inputs['B'].default_value = 1.0
    inner_links.new(nor_combine_rgb.inputs['R'], nor_separate_rgb.outputs['R'])
    inner_links.new(nor_combine_rgb.inputs['G'], nor_separate_rgb.outputs['G'])
    nor_normal_map = inner_nodes.new('ShaderNodeNormalMap')
    nor_normal_map.name = 'nor_normal_map'
    nor_normal_map.label = 'Normal Map'
    nor_normal_map.location = (-300, -600)
    nor_normal_map.parent = nor_frame
    inner_links.new(
        nor_normal_map.inputs['Color'], nor_combine_rgb.outputs['Image'])
    inner_links.new(shader_node.inputs['Normal'],
                    nor_normal_map.outputs['Normal'])

    nor_frame.location = (0, -250)

    # Alpha Frame Time
    alpha_frame = inner_nodes.new('NodeFrame')
    alpha_frame.name = 'alpha_frame'
    alpha_frame.label = 'Alpha stuff'

    alpha_group_input = inner_nodes.new('NodeGroupInput')
    alpha_group_input.name = 'alpha_group_input'
    alpha_group_input.parent = alpha_frame
    alpha_group_input.location = (-1200, -400)

    texture_alpha = inner_nodes.new('ShaderNodeMath')
    texture_alpha.name = 'alpha_lowest_from_textures'
    texture_alpha.label = 'Lowest Alpha'
    texture_alpha.parent = alpha_frame
    texture_alpha.location = (-900, -400)
    texture_alpha.operation = 'MINIMUM'

    # alpha = max(alpha, CustomVector0.x)
    alpha_maximum = inner_nodes.new('ShaderNodeMath')
    alpha_maximum.name = 'alpha_maximum'
    alpha_maximum.label = 'Max Alpha'
    alpha_maximum.parent = alpha_frame
    alpha_maximum.location = (-600, -400)
    alpha_maximum.operation = 'MAXIMUM'

    alpha_color_set1_scale = inner_nodes.new('ShaderNodeMath')
    alpha_color_set1_scale.name = 'colorSet1 Alpha Scale'
    alpha_color_set1_scale.label = 'colorSet1 Alpha Scale'
    alpha_color_set1_scale.parent = alpha_frame
    alpha_color_set1_scale.location = (-300, -400)
    alpha_color_set1_scale.operation = 'MULTIPLY'
    alpha_color_set1_scale.inputs[1].default_value = 2.0

    alpha_color_set1 = inner_nodes.new('ShaderNodeMath')
    alpha_color_set1.name = 'colorSet1 Alpha'
    alpha_color_set1.label = 'colorSet1 Alpha'
    alpha_color_set1.parent = alpha_frame
    alpha_color_set1.location = (-100, -400)
    alpha_color_set1.operation = 'MULTIPLY'

    inner_links.new(texture_alpha.inputs[0], alpha_group_input.outputs['Texture0 Alpha (Col Map Layer 1)'])
    inner_links.new(texture_alpha.inputs[1], alpha_group_input.outputs['Texture5 Alpha (Emissive Map Layer 1)'])
    inner_links.new(alpha_maximum.inputs[0], texture_alpha.outputs[0])
    inner_links.new(alpha_maximum.inputs[1], alpha_group_input.outputs['CustomVector0 X (Min Texture Alpha)'])

    inner_links.new(alpha_color_set1_scale.inputs[0], color_set_input_node.outputs['colorSet1 Alpha'])

    inner_links.new(alpha_color_set1.inputs[0], alpha_color_set1_scale.outputs['Value'])
    inner_links.new(alpha_color_set1.inputs[1], alpha_maximum.outputs['Value'])
    inner_links.new(shader_node.inputs['Alpha'], alpha_color_set1.outputs['Value'])

    alpha_frame.location = (0, -225)

    # Emission Frame Time
    emission_frame = inner_nodes.new('NodeFrame')
    emission_frame.name = 'emission_frame'
    emission_frame.label = 'Emission Stuff'
    emission_group_input = inner_nodes.new('NodeGroupInput')
    emission_group_input.name = 'emission_group_input'
    emission_group_input.parent = emission_frame
    emission_group_input.location = (-1200, -400)
    emission_multiply = inner_nodes.new('ShaderNodeMixRGB')
    emission_multiply.name = 'emission_multiply'
    emission_multiply.label = 'CV3 Emission Multiplier'
    emission_multiply.parent = emission_frame
    emission_multiply.location = (-600, -400)
    emission_multiply.blend_type = 'MULTIPLY'
    emission_multiply.inputs[0].default_value = 1.0
    inner_links.new(emission_multiply.inputs['Color2'],
                    emission_group_input.outputs['CustomVector3 (Emission Color Multiplier)'])
    inner_links.new(shader_node.inputs['Emission'],
                    emission_multiply.outputs['Color'])
    emission_mix_rgb = inner_nodes.new('ShaderNodeMixRGB')
    emission_mix_rgb.name = 'emission_mix_rgb'
    emission_mix_rgb.label = 'Emission Layer Mixer'
    emission_mix_rgb.parent = emission_frame
    emission_mix_rgb.location = (-900, -400)

    inner_links.new(
        emission_mix_rgb.inputs['Fac'], emission_group_input.outputs['Texture14 Alpha (Emissive Map Layer 2)'])
    inner_links.new(emission_mix_rgb.inputs['Color1'],
                    emission_group_input.outputs['Texture5 RGB (Emissive Map Layer 1)'])
    inner_links.new(emission_mix_rgb.inputs['Color2'],
                    emission_group_input.outputs['Texture14 RGB (Emissive Map Layer 2)'])
    inner_links.new(
        emission_multiply.inputs['Color1'], emission_mix_rgb.outputs[0])

    emission_frame.location = (0, 20)

    # Approximate colorSet1
    # colorSet1 is technically applied after the principled BSDF.
    # Multiplying the shader value with shader2Rgb isn't portable.
    # Adjusting albedo and specular is a reasonable approximation.
    # This also works well with metals since we multiply albedo.
    color_set1_frame = inner_nodes.new('NodeFrame')
    color_set1_frame.name = 'color_set1_frame'
    color_set1_frame.location = (0, 0)
    color_set1_frame.label = 'colorSet1'

    color_set1_scale = inner_nodes.new('ShaderNodeMixRGB')
    color_set1_scale.name = 'color_set1_scale'
    color_set1_scale.label = 'Color Set 1 Scale'
    color_set1_scale.parent = color_set1_frame
    color_set1_scale.location = (0, 0)
    color_set1_scale.blend_type = 'MULTIPLY'
    color_set1_scale.inputs['Fac'].default_value = 1.0
    color_set1_scale.inputs['Color2'].default_value = (2.0, 2.0, 2.0, 2.0)

    color_set1_albedo = inner_nodes.new('ShaderNodeMixRGB')
    color_set1_albedo.name = 'colorSet1 albedo'
    color_set1_albedo.label = 'colorSet1 albedo'
    color_set1_albedo.parent = color_set1_frame
    color_set1_albedo.location = (200, 0)
    color_set1_albedo.blend_type = 'MULTIPLY'
    color_set1_albedo.inputs['Fac'].default_value = 1.0

    color_set1_spec = inner_nodes.new('ShaderNodeMixRGB')
    color_set1_spec.name = 'colorSet1 spec'
    color_set1_spec.label = 'colorSet1 spec'
    color_set1_spec.parent = color_set1_frame
    color_set1_spec.location = (200, -200)
    color_set1_spec.blend_type = 'MULTIPLY'
    color_set1_spec.inputs['Fac'].default_value = 1.0

    inner_links.new(
        color_set1_scale.inputs['Color1'], color_set_input_node.outputs['colorSet1 RGB'])

    inner_links.new(
        color_set1_albedo.inputs['Color1'], color_set1_scale.outputs['Color'])
    inner_links.new(
        color_set1_albedo.inputs['Color2'], baked_lighting_mix.outputs[0])
    inner_links.new(
        shader_node.inputs['Base Color'], color_set1_albedo.outputs['Color'])

    inner_links.new(
        color_set1_spec.inputs['Color1'], color_set1_scale.outputs['Color'])
    inner_links.new(
        color_set1_spec.inputs['Color2'], prm_multiply_prm_alpha.outputs['Value'])
    inner_links.new(shader_node.inputs['Specular'],
                    color_set1_spec.outputs['Color'])

    # Each input node technically has all the group's inputs.
    # The duplicate node group input nodes are used to visually group inputs.
    # Hide the unlinked nodes to make each input node smaller.
    hide_unlinked_outputs(alpha_group_input)
    hide_unlinked_outputs(color_set_input_node)
    hide_unlinked_outputs(baked_lighting_input_node)
    hide_unlinked_outputs(diffuse_input_node)
    hide_unlinked_outputs(prm_group_input)
    hide_unlinked_outputs(nor_group_input)
    hide_unlinked_outputs(emission_group_input)
