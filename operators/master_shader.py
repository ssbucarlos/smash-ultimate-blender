import bpy

def get_master_shader_name():
    return 'Smash Ultimate Master Shader'

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
    new_node_group = bpy.data.node_groups.new(master_shader_name, 'ShaderNodeTree')

    # Connect that new node_group to the node_group_node
    # (this should get rid of the 'missing data block', blender fills it out automatically)
    node_group_node.node_tree = new_node_group

    node_group_node.name = 'Master'

    # Make the one output
    output = node_group_node.outputs.new('NodeSocketShader', 'Final Output')

    # Now we are ready to start adding inputs
    input = node_group_node.inputs.new('NodeSocketString', 'Material Name')
    input = node_group_node.inputs.new('NodeSocketString', 'Shader Label')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture0 RGB (Col Map Layer 1)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture0 Alpha (Col Map Layer 1)')
    input.default_value = 1.0
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture1 RGB (Col Map Layer 2)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture1 Alpha (Col Map Layer 2)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture2 RGB (Irradiance Cube Map)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture2 Alpha (Irradiance Cube Map)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture3 RGB (Ambient Occlusion Map)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture3 Alpha (Ambient Occlusion Map)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture4 RGB (NOR Map)')
    input.default_value = (0.5, 0.5, 0.0, 1)
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture4 Alpha (NOR Map Cavity Channel)')
    input.default_value = 1.0
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture5 RGB (Emissive Map Layer 1)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture5 Alpha (Emissive Map Layer 1)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture6 RGB (PRM Map)')
    input.default_value = (0.0, 1.0, 1.0, 1.0)
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture6 Alpha (PRM Map Specular)')
    input.default_value = 0.0
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture7 RGB (Specular Cube Map)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture7 Alpha (Specular Cube Map)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture8 RGB (Diffuse Cube Map)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture8 Alpha (Diffuse Cube Map)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture9 RGB (Baked Lighting Map)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture9 Alpha (Baked Lighting Map)')
    input.default_value = 1.0
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture10 RGB (Diffuse Map Layer 1)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture10 Alpha (Diffuse Map Layer 1)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture11 RGB (Diffuse Map Layer 2)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture11 Alpha (Diffuse Map Layer 2)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture12 RGB (Diffuse Map Layer 3)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture12 Alpha (Diffuse Map Layer 3)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture13 RGB (Projection Light Map)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture13 Alpha (Projection Light Map)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture14 RGB (Emissive Map Layer 2)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture14 Alpha (Emissive Map Layer 2)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture15 RGB (Unused)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture15 Alpha (Unused)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture16 RGB (Ink Normal Map)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture16 Alpha (Ink Normal Map)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture17 RGB (Unused)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture17 Alpha (Unused)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture18 RGB (Unused)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture18 Alpha (Unused)')
    input = node_group_node.inputs.new('NodeSocketColor', 'Texture19 RGB (Unused)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'Texture19 Alpha (Unused)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector0 X (Min Texture Alpha)') # Affects alpha testing. X = min texture alpha
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector0 Y (???)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector0 Z (???)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector0 W (???)') 
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector1')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector2')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector3 (Emission Color Multiplier)') #Color multiplier for emission color. 
    input.default_value = (1.0, 1.0, 1.0, 1.0)
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector4')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector5')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector6 X (UV Transform Layer 1)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector6 Y (UV Transform Layer 1)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector6 Z (UV Transform Layer 1)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector6 W (UV Transform Layer 1)')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector7')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector8 (Final Color Multiplier)')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector9')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector10')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector11 (Fake SSS Color)')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector12')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector13 (Diffuse Color Multiplier)')
    input.default_value = (1.0, 1.0, 1.0, 1.0)
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector14 RGB (Rim Lighting Color)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector14 Alpha (Rim Lighting Blend Factor)')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector15 RGB')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector15 Alpha')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector16')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector17')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector18 X (Sprite Sheet Column Count)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector18 Y (Sprite Sheet Row Count)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector18 Z (Sprite Sheet Frames Per Sprite)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector18 W (Sprite Sheet Sprite Count)')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector19')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector20')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector21')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector22')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector23')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector24')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector25')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector26')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector27 (Controls Distant Fog, X = Intensity)')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector28')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector29')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector30 X (SSS Blend Factor)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector30 Y (SSS Diffuse Shading Smooth Factor)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector30 Z (Unused)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector30 W (Unused)')                 
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector31 X (UV Transform Layer 2)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector31 Y (UV Transform Layer 2)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector31 Z (UV Transform Layer 2)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector31 W (UV Transform Layer 2)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector32 X (UV Transform Layer 3)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector32 Y (UV Transform Layer 3)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector32 Z (UV Transform Layer 3)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector32 W (UV Transform Layer 3)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector33 X (UV Transform ?)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector33 Y (UV Transform ?)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector33 Z (UV Transform ?)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector33 W (UV Transform ?)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector34 X (UV Transform ?)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector34 Y (UV Transform ?)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector34 Z (UV Transform ?)')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomVector34 W (UV Transform ?)')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector35')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector36')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector37')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector38')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector39')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector40')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector41')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector42')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector43')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector44')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector45')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector46')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector47')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector48')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector49')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector50')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector51')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector52')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector53')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector54')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector55')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector56')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector57')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector58')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector59')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector60')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector61')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector62')
    input = node_group_node.inputs.new('NodeSocketColor', 'CustomVector63')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat0')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat1')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat2')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat3')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat4')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat5')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat6')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat7')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat8')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat9')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat10')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat11')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat12')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat13')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat14')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat15')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat16')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat17')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat18')
    input = node_group_node.inputs.new('NodeSocketFloat', 'CustomFloat19')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean0')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean1')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean2')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean3')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean4')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean5')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean6')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean7')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean8')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean9')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean10')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean11')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean12')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean13')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean14')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean15')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean16')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean17')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean18')
    input = node_group_node.inputs.new('NodeSocketBool', 'CustomBoolean19')
    input = node_group_node.inputs.new('NodeSocketString', 'BlendState0 Field1 (Source Color)')
    input.default_value = "One"
    input = node_group_node.inputs.new('NodeSocketInt', 'BlendState0 Field2 (Unk2)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketString', 'BlendState0 Field3 (Destination Color)')
    input.default_value = "Zero"
    input = node_group_node.inputs.new('NodeSocketInt', 'BlendState0 Field4 (Unk4)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketInt', 'BlendState0 Field5 (Unk5)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketInt', 'BlendState0 Field6 (Unk6)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketInt', 'BlendState0 Field7 (Alpha to Coverage)')
    input.default_value = 1
    input = node_group_node.inputs.new('NodeSocketInt', 'BlendState0 Field8 (Unk8)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketInt', 'BlendState0 Field9 (Unk9)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketInt', 'BlendState0 Field10 (Unk10)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketInt', 'RasterizerState0 Field1 (Polygon Fill)')
    input.default_value = 1
    input = node_group_node.inputs.new('NodeSocketInt', 'RasterizerState0 Field2 (Cull Mode)')
    input.default_value = 1
    input = node_group_node.inputs.new('NodeSocketFloat', 'RasterizerState0 Field3 (Depth Bias)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketInt', 'RasterizerState0 Field4 (Unk4)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketInt', 'RasterizerState0 Field5 (Unk5)')
    input.default_value = 0
    input = node_group_node.inputs.new('NodeSocketInt', 'RasterizerState0 Field6 (Unk6)')
    input.default_value = 16777217


    # Allow for wider node
    node_group_node.bl_width_max = 1000

    # Now its time to place nodes
    inner_nodes = node_group_node.node_tree.nodes
    inner_links = node_group_node.node_tree.links

    shader_node = inner_nodes.new('ShaderNodeBsdfPrincipled')
    shader_node.name = 'Shader'
    output_node = inner_nodes.new('NodeGroupOutput')
    output_node.name = 'Output'
    output_node.location = (277,0)
    inner_links.new(output_node.inputs['Final Output'], shader_node.outputs['BSDF'])
    diffuse_frame = inner_nodes.new('NodeFrame')
    diffuse_frame.name = 'Diffuse Frame'
    diffuse_frame.label = 'Diffuse Color Stuff'
    diffuse_input_node = inner_nodes.new('NodeGroupInput')
    diffuse_input_node.location = (-1500, 0)
    diffuse_input_node.parent = diffuse_frame
    cv13_node = inner_nodes.new('ShaderNodeMixRGB')
    cv13_node.name = 'CustomVector13 Multiply'
    cv13_node.label = 'CustomVector13 Multiply'
    cv13_node.location = (-215, 0)
    cv13_node.blend_type = 'MULTIPLY'
    cv13_node.inputs['Fac'].default_value = 1.0
    cv13_node.parent = diffuse_frame
    #inner_links.new(shader_node.inputs['Base Color'], cv13_node.outputs['Color'])
    inner_links.new(cv13_node.inputs['Color1'], diffuse_input_node.outputs['CustomVector13 (Diffuse Color Multiplier)'])
    fake_sss_color_node = inner_nodes.new('ShaderNodeMixRGB')
    fake_sss_color_node.name = 'Fake SSS Color'
    fake_sss_color_node.label = 'Fake SSS Color'
    fake_sss_color_node.location = (-428,0)
    fake_sss_color_node.parent = diffuse_frame
    inner_links.new(fake_sss_color_node.inputs['Color2'], diffuse_input_node.outputs['CustomVector11 (Fake SSS Color)'])
    inner_links.new(cv13_node.inputs['Color2'], fake_sss_color_node.outputs['Color'])
    fake_sss_factor_node = inner_nodes.new('ShaderNodeMath')
    fake_sss_factor_node.name = 'Fake SSS Factor'
    fake_sss_factor_node.label = 'Fake SSS Factor'
    fake_sss_factor_node.location = (-650, -200)
    fake_sss_factor_node.operation = 'MULTIPLY'
    fake_sss_factor_node.parent = diffuse_frame
    inner_links.new(fake_sss_factor_node.inputs[1], diffuse_input_node.outputs['CustomVector30 X (SSS Blend Factor)'])
    inner_links.new(fake_sss_color_node.inputs['Fac'], fake_sss_factor_node.outputs['Value'])
    color_map_mix_node = inner_nodes.new('ShaderNodeMixRGB')
    color_map_mix_node.name = 'ColorMapLayerMixer'
    color_map_mix_node.label = 'ColorMapLayerMixer'
    color_map_mix_node.location = (-650,0)
    color_map_mix_node.parent = diffuse_frame
    #inner_links.new(color_map_mix_node.inputs['Color1'], diffuse_input_node.outputs['Texture0 RGB (Col Map Layer 1)'])
    inner_links.new(color_map_mix_node.inputs['Color2'], diffuse_input_node.outputs['Texture1 RGB (Col Map Layer 2)'])
    #inner_links.new(color_map_mix_node.inputs['Fac'], diffuse_input_node.outputs['Texture1 Alpha (Col Map Layer 2)'])
    inner_links.new(fake_sss_color_node.inputs['Color1'], color_map_mix_node.outputs['Color'])
    df_separate_prm_rgb_node = inner_nodes.new('ShaderNodeSeparateRGB')
    df_separate_prm_rgb_node.name = 'df_separate_prm_rgb_node'
    df_separate_prm_rgb_node.label = 'Separate PRM RGB'
    df_separate_prm_rgb_node.parent = diffuse_frame
    df_separate_prm_rgb_node.location = (-900, -200)
    inner_links.new(fake_sss_factor_node.inputs[0], df_separate_prm_rgb_node.outputs['R'])
    inner_links.new(df_separate_prm_rgb_node.inputs['Image'], diffuse_input_node.outputs['Texture6 RGB (PRM Map)'])
    color_set_5_node = inner_nodes.new('ShaderNodeVertexColor')
    color_set_5_node.name = 'color_set_5_node'
    color_set_5_node.label = 'Color Set 5'
    color_set_5_node.parent = diffuse_frame
    color_set_5_node.location = (-1500, 600)
    color_set_5_node.layer_name = 'colorSet5'
    
    color_set_5_scale_node = inner_nodes.new('ShaderNodeMath')
    color_set_5_scale_node.name = 'color_set_5_scale_node'
    color_set_5_scale_node.label = 'Color Set 5 Scale'
    color_set_5_scale_node.location = (-1200, 500)
    color_set_5_scale_node.parent = diffuse_frame
    color_set_5_scale_node.operation = 'MULTIPLY'
    color_set_5_scale_node.inputs[0].default_value = 3.0

    one_minus_color_set_5_node = inner_nodes.new('ShaderNodeMath')
    one_minus_color_set_5_node.name = 'one_minus_color_set_5_node'
    one_minus_color_set_5_node.label = '1 - Alpha'
    one_minus_color_set_5_node.parent = diffuse_frame
    one_minus_color_set_5_node.location = (-1000, 400)
    one_minus_color_set_5_node.operation = 'SUBTRACT'
    one_minus_color_set_5_node.inputs[0].default_value = 1.0
    one_minus_color_set_5_node.use_clamp = True

    layer_2_alpha_minus_col_set_5 = inner_nodes.new('ShaderNodeMath')
    layer_2_alpha_minus_col_set_5.name = 'layer_2_alpha_minus_col_set_5'
    layer_2_alpha_minus_col_set_5.label = 'Texture Blend'
    layer_2_alpha_minus_col_set_5.parent = diffuse_frame
    layer_2_alpha_minus_col_set_5.location = (-800, 300)
    layer_2_alpha_minus_col_set_5.operation = 'SUBTRACT'
    layer_2_alpha_minus_col_set_5.use_clamp = True

    inner_links.new(color_set_5_scale_node.inputs[1], color_set_5_node.outputs['Alpha'])
    inner_links.new(one_minus_color_set_5_node.inputs[1], color_set_5_scale_node.outputs[0])
    inner_links.new(layer_2_alpha_minus_col_set_5.inputs[0], diffuse_input_node.outputs['Texture1 Alpha (Col Map Layer 2)'])
    inner_links.new(layer_2_alpha_minus_col_set_5.inputs[1], one_minus_color_set_5_node.outputs[0])
    inner_links.new(color_map_mix_node.inputs['Fac'], layer_2_alpha_minus_col_set_5.outputs[0])

    # Color Set 1
    diffuse_color_set_1_node = inner_nodes.new('ShaderNodeVertexColor')
    diffuse_color_set_1_node.name = 'diffuse_color_set_1_node'
    diffuse_color_set_1_node.label = 'Color Set 1'
    diffuse_color_set_1_node.parent = diffuse_frame
    diffuse_color_set_1_node.location = (-1500, 300)
    diffuse_color_set_1_node.layer_name = 'colorSet1'

    diffuse_color_set_1_scale_node = inner_nodes.new('ShaderNodeMixRGB')
    diffuse_color_set_1_scale_node.name = 'diffuse_color_set_1_scale_node'
    diffuse_color_set_1_scale_node.label = 'Color Set 1 Scale'
    diffuse_color_set_1_scale_node.parent = diffuse_frame
    diffuse_color_set_1_scale_node.blend_type = 'MULTIPLY'
    diffuse_color_set_1_scale_node.location = (-1200, 200)
    diffuse_color_set_1_scale_node.inputs['Fac'].default_value = 1.0
    diffuse_color_set_1_scale_node.inputs['Color1'].default_value = (2.0,2.0,2.0,1.0)

    diffuse_color_set_1_mix_node = inner_nodes.new('ShaderNodeMixRGB')
    diffuse_color_set_1_mix_node.name = 'diffuse_color_set_1_mix_node'
    diffuse_color_set_1_mix_node.label = 'Color Set 1 Mixer'
    diffuse_color_set_1_mix_node.parent = diffuse_frame
    diffuse_color_set_1_mix_node.location = (-900, 100)
    diffuse_color_set_1_mix_node.blend_type = 'MULTIPLY'
    diffuse_color_set_1_mix_node.inputs['Fac'].default_value = 1.0
    
    inner_links.new(diffuse_color_set_1_scale_node.inputs['Color2'], diffuse_color_set_1_node.outputs[0])
    inner_links.new(diffuse_color_set_1_mix_node.inputs['Color2'], diffuse_color_set_1_scale_node.outputs[0])
    inner_links.new(diffuse_color_set_1_mix_node.inputs['Color1'], diffuse_input_node.outputs['Texture0 RGB (Col Map Layer 1)'])
    inner_links.new(color_map_mix_node.inputs['Color1'], diffuse_color_set_1_mix_node.outputs[0])

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
    baked_lighting_texture_boost.inputs['Color2'].default_value = (8.0, 8.0, 8.0, 1.0)
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

    inner_links.new(baked_lighting_texture_boost.inputs['Color1'], baked_lighting_input_node.outputs['Texture9 RGB (Baked Lighting Map)'])
    inner_links.new(baked_lighting_alpha_invert.inputs['Color'], baked_lighting_input_node.outputs['Texture9 Alpha (Baked Lighting Map)'])
    inner_links.new(baked_lighting_mix.inputs['Fac'], baked_lighting_alpha_invert.outputs[0])
    inner_links.new(baked_lighting_mix.inputs['Color1'], cv13_node.outputs[0])
    inner_links.new(baked_lighting_mix.inputs['Color2'], baked_lighting_texture_boost.outputs[0])
    inner_links.new(shader_node.inputs['Base Color'], baked_lighting_mix.outputs[0])

    baked_lighting_frame.location = (0, 300)

    for output in baked_lighting_input_node.outputs:
        if output.is_linked is False:
            output.hide = True
    
    for output in diffuse_input_node.outputs:
        if output.is_linked is False:
            output.hide = True
    diffuse_frame.location = (0, 625)       
    # PRM Frame Time
    '''
    Nodes Needed: 
        prm_compare_cv30_x 
        prm_metal_minimum
        prm_separate_prm_rgb
        prm_multiply_prm_alpha
    '''
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
    prm_compare_cv30_x.location = (-600,0)
    prm_compare_cv30_x.parent = prm_frame
    inner_links.new(prm_compare_cv30_x.inputs[1], prm_group_input.outputs['CustomVector30 X (SSS Blend Factor)'])
    prm_metal_minimum = inner_nodes.new('ShaderNodeMath')
    prm_metal_minimum.name = 'prm_metal_minimum'
    prm_metal_minimum.label = 'PRM Metal Override'
    prm_metal_minimum.operation = 'MINIMUM'
    prm_metal_minimum.location = (-300,0)
    prm_metal_minimum.parent = prm_frame
    inner_links.new(prm_metal_minimum.inputs[0], prm_compare_cv30_x.outputs[0])
    inner_links.new(shader_node.inputs['Metallic'], prm_metal_minimum.outputs['Value'])
    prm_separate_prm_rgb = inner_nodes.new('ShaderNodeSeparateRGB')
    prm_separate_prm_rgb.name = 'prm_separate_prm_rgb'
    prm_separate_prm_rgb.label = 'Separate PRM RGB'
    prm_separate_prm_rgb.location = (-600,-200)
    prm_separate_prm_rgb.parent = prm_frame
    inner_links.new(prm_separate_prm_rgb.inputs['Image'], prm_group_input.outputs['Texture6 RGB (PRM Map)'])
    inner_links.new(prm_metal_minimum.inputs[1], prm_separate_prm_rgb.outputs['R'])
    inner_links.new(shader_node.inputs['Roughness'], prm_separate_prm_rgb.outputs['G'])
    prm_multiply_prm_alpha = inner_nodes.new('ShaderNodeMath')
    prm_multiply_prm_alpha.name = 'prm_multiply_prm_alpha'
    prm_multiply_prm_alpha.label = 'Specular Boost'
    prm_multiply_prm_alpha.location = (-600, -350)
    prm_multiply_prm_alpha.parent = prm_frame
    prm_multiply_prm_alpha.operation = 'MULTIPLY'
    prm_multiply_prm_alpha.inputs[0].default_value = 2.5
    inner_links.new(prm_multiply_prm_alpha.inputs[1], prm_group_input.outputs['Texture6 Alpha (PRM Map Specular)'])
    inner_links.new(shader_node.inputs['Specular'], prm_multiply_prm_alpha.outputs['Value'])
    for output in prm_group_input.outputs:
        if output.is_linked is False:
            output.hide = True
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
    inner_links.new(nor_separate_rgb.inputs['Image'], nor_group_input.outputs['Texture4 RGB (NOR Map)'])
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
    inner_links.new(nor_normal_map.inputs['Color'], nor_combine_rgb.outputs['Image'])
    inner_links.new(shader_node.inputs['Normal'], nor_normal_map.outputs['Normal'])
    for output in nor_group_input.outputs:
        if output.is_linked is False:
            output.hide = True
    nor_frame.location = (0,-250)

    # Alpha Frame Time
    alpha_frame = inner_nodes.new('NodeFrame')
    alpha_frame.name = 'alpha_frame'
    alpha_frame.label = 'Alpha stuff'
    alpha_group_input = inner_nodes.new('NodeGroupInput')
    alpha_group_input.name = 'alpha_group_input'
    alpha_group_input.parent = alpha_frame
    alpha_group_input.location = (-1200, -400)
    alpha_maximum = inner_nodes.new('ShaderNodeMath')
    alpha_maximum.name = 'alpha_maximum'
    alpha_maximum.label = 'Max Alpha'
    alpha_maximum.parent = alpha_frame
    alpha_maximum.location = (-600, -400)
    alpha_maximum.operation = 'MAXIMUM'
    inner_links.new(alpha_maximum.inputs[0], alpha_group_input.outputs['Texture0 Alpha (Col Map Layer 1)'])
    inner_links.new(alpha_maximum.inputs[1], alpha_group_input.outputs['CustomVector0 X (Min Texture Alpha)'])
    inner_links.new(shader_node.inputs['Alpha'], alpha_maximum.outputs['Value'])
    for output in alpha_group_input.outputs:
        if output.is_linked is False:
            output.hide = True
    alpha_frame.location = (0,-225)

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
    #inner_links.new(emission_multiply.inputs['Color1'], emission_group_input.outputs['Texture5 RGB (Emissive Map Layer 1)'])
    inner_links.new(emission_multiply.inputs['Color2'], emission_group_input.outputs['CustomVector3 (Emission Color Multiplier)'] )
    inner_links.new(shader_node.inputs['Emission'], emission_multiply.outputs['Color'])
    emission_mix_rgb = inner_nodes.new('ShaderNodeMixRGB')
    emission_mix_rgb.name = 'emission_mix_rgb'
    emission_mix_rgb.label = 'Emission Layer Mixer'
    emission_mix_rgb.parent = emission_frame
    emission_mix_rgb.location = (-900, -400)

    # Emission colorSet1 stuff
    emission_color_set_1 = inner_nodes.new('ShaderNodeVertexColor')
    emission_color_set_1.name = 'emission_color_set_1'
    emission_color_set_1.label = 'Color Set 1'
    emission_color_set_1.parent = emission_frame
    emission_color_set_1.layer_name = 'colorSet1'
    emission_color_set_1.location = (-2100, -400)
    
    emission_color_set_1_scale = inner_nodes.new('ShaderNodeMixRGB')
    emission_color_set_1_scale.name = 'emission_color_set_1_scale'
    emission_color_set_1_scale.label = 'Color Set 1 Scale'
    emission_color_set_1_scale.parent = emission_frame
    emission_color_set_1_scale.inputs['Fac'].default_value = 1.0
    emission_color_set_1_scale.inputs['Color1'].default_value = (2.0,2.0,2.0,2.0)
    emission_color_set_1_scale.blend_type = 'MULTIPLY'
    emission_color_set_1_scale.location = (-1800, -400)

    emission_color_set_1_mixer = inner_nodes.new('ShaderNodeMixRGB')
    emission_color_set_1_mixer.name = 'emission_color_set_1_mixer'
    emission_color_set_1_mixer.label = 'Color Set 1 Mixer'
    emission_color_set_1_mixer.parent = emission_frame
    emission_color_set_1_mixer.inputs['Fac'].default_value = 1.0
    emission_color_set_1_mixer.blend_type = 'MULTIPLY'
    emission_color_set_1_mixer.location = (-1500, -400)

    inner_links.new(emission_color_set_1_scale.inputs['Color2'],emission_color_set_1.outputs[0])
    inner_links.new(emission_color_set_1_mixer.inputs['Color2'],emission_color_set_1_scale.outputs[0])
    inner_links.new(emission_color_set_1_mixer.inputs['Color1'],emission_group_input.outputs['Texture5 RGB (Emissive Map Layer 1)'])
    inner_links.new(emission_mix_rgb.inputs['Color1'], emission_color_set_1_mixer.outputs[0])
    inner_links.new(emission_mix_rgb.inputs['Fac'], emission_group_input.outputs['Texture14 Alpha (Emissive Map Layer 2)'])
    #inner_links.new(emission_mix_rgb.inputs['Color1'], emission_group_input.outputs['Texture5 RGB (Emissive Map Layer 1)'])
    inner_links.new(emission_mix_rgb.inputs['Color2'], emission_group_input.outputs['Texture14 RGB (Emissive Map Layer 2)'])
    inner_links.new(emission_multiply.inputs['Color1'], emission_mix_rgb.outputs[0])
    for output in emission_group_input.outputs:
        if output.is_linked is False:
            output.hide = True
    emission_frame.location = (0, 20)
