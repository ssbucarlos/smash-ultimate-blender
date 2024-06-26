ones = (1.0, 1.0, 1.0, 1.0)
zeros = (0.0, 0.0, 0.0, 0.0)

# Assign a (socket, description, default) for each parameter.
vec4_param_to_inputs = {
    'CustomVector0': [
        ('NodeSocketFloat', 'CustomVector0 X (Min Texture Alpha)', 0.0),
        ('NodeSocketFloat', 'CustomVector0 Y (???)', 0.0),
        ('NodeSocketFloat', 'CustomVector0 Z (???)', 0.0),
        ('NodeSocketFloat', 'CustomVector0 W (???)', 0.0),
    ],
    'CustomVector1': [('NodeSocketColor', 'CustomVector1', zeros)],
    'CustomVector2': [('NodeSocketColor', 'CustomVector2', zeros)],
    'CustomVector3': [('NodeSocketColor', 'CustomVector3 (Emission Color Multiplier)', ones)],
    'CustomVector4': [('NodeSocketColor', 'CustomVector4', zeros)],
    'CustomVector5': [('NodeSocketColor', 'CustomVector5', zeros)],
    'CustomVector6': [
        ('NodeSocketFloat', 'CustomVector6 X (UV Transform Layer 1)', 0.0),
        ('NodeSocketFloat', 'CustomVector6 Y (UV Transform Layer 1)', 0.0),
        ('NodeSocketFloat', 'CustomVector6 Z (UV Transform Layer 1)', 0.0),
        ('NodeSocketFloat', 'CustomVector6 W (UV Transform Layer 1)', 0.0),
    ],
    'CustomVector7': [('NodeSocketColor', 'CustomVector7', zeros)],
    'CustomVector8': [('NodeSocketColor', 'CustomVector8 (Final Color Multiplier)', zeros)],
    'CustomVector9': [('NodeSocketColor', 'CustomVector9', zeros)],
    'CustomVector10': [('NodeSocketColor', 'CustomVector10', zeros)],
    'CustomVector11': [('NodeSocketColor', 'CustomVector11 (Fake SSS Color)', zeros)],
    'CustomVector12': [('NodeSocketColor', 'CustomVector12', zeros)],
    'CustomVector13': [('NodeSocketColor', 'CustomVector13 (Diffuse Color Multiplier)', ones)],
    'CustomVector14': [
        ('NodeSocketColor', 'CustomVector14 RGB (Rim Lighting Color)', zeros),
        ('NodeSocketFloat', 'CustomVector14 Alpha (Rim Lighting Blend Factor)', 0.0),
    ],
    'CustomVector15': [
        ('NodeSocketColor', 'CustomVector15 RGB', zeros),
        ('NodeSocketFloat', 'CustomVector15 Alpha', 0.0),
    ],
    'CustomVector16': [('NodeSocketColor', 'CustomVector16', zeros)],
    'CustomVector17': [('NodeSocketColor', 'CustomVector17', zeros)],
    'CustomVector18': [
        ('NodeSocketFloat', 'CustomVector18 X (Sprite Sheet Column Count)', 0.0),
        ('NodeSocketFloat', 'CustomVector18 Y (Sprite Sheet Row Count)', 0.0),
        ('NodeSocketFloat', 'CustomVector18 Z (Sprite Sheet Frames Per Sprite)', 0.0),
        ('NodeSocketFloat', 'CustomVector18 W (Sprite Sheet Sprite Count)', 0.0),
    ],
    'CustomVector19': [('NodeSocketColor', 'CustomVector19', zeros)],
    'CustomVector20': [('NodeSocketColor', 'CustomVector20', zeros)],
    'CustomVector21': [('NodeSocketColor', 'CustomVector21', zeros)],
    'CustomVector22': [('NodeSocketColor', 'CustomVector22', zeros)],
    'CustomVector23': [('NodeSocketColor', 'CustomVector23', zeros)],
    'CustomVector24': [('NodeSocketColor', 'CustomVector24', zeros)],
    'CustomVector25': [('NodeSocketColor', 'CustomVector25', zeros)],
    'CustomVector26': [('NodeSocketColor', 'CustomVector26', zeros)],
    'CustomVector26': [('NodeSocketColor', 'CustomVector26', zeros)],
    'CustomVector27': [('NodeSocketColor', 'CustomVector27 (Controls Distant Fog, X = Intensity)', zeros)],
    'CustomVector28': [('NodeSocketColor', 'CustomVector28', zeros)],
    'CustomVector29': [('NodeSocketColor', 'CustomVector29', zeros)],
    'CustomVector30': [
        ('NodeSocketFloat', 'CustomVector30 X (SSS Blend Factor)', 0.0),
        ('NodeSocketFloat', 'CustomVector30 Y (SSS Diffuse Shading Smooth Factor)', 0.0),
        ('NodeSocketFloat', 'CustomVector30 Z (Unused)', 0.0),
        ('NodeSocketFloat', 'CustomVector30 W (Unused)', 0.0),
    ],
    'CustomVector31': [
        ('NodeSocketFloat', 'CustomVector31 X (UV Transform Layer 2)', 0.0),
        ('NodeSocketFloat', 'CustomVector31 Y (UV Transform Layer 2)', 0.0),
        ('NodeSocketFloat', 'CustomVector31 Z (UV Transform Layer 2)', 0.0),
        ('NodeSocketFloat', 'CustomVector31 W (UV Transform Layer 2)', 0.0),
    ],
    'CustomVector32': [
        ('NodeSocketFloat', 'CustomVector32 X (UV Transform Layer 3)', 0.0),
        ('NodeSocketFloat', 'CustomVector32 Y (UV Transform Layer 3)', 0.0),
        ('NodeSocketFloat', 'CustomVector32 Z (UV Transform Layer 3)', 0.0),
        ('NodeSocketFloat', 'CustomVector32 W (UV Transform Layer 3)', 0.0),
    ],
    'CustomVector33': [
        ('NodeSocketFloat', 'CustomVector33 X (UV Transform ?)', 0.0),
        ('NodeSocketFloat', 'CustomVector33 Y (UV Transform ?)', 0.0),
        ('NodeSocketFloat', 'CustomVector33 Z (UV Transform ?)', 0.0),
        ('NodeSocketFloat', 'CustomVector33 W (UV Transform ?)', 0.0),
    ],
    'CustomVector34': [
        ('NodeSocketFloat', 'CustomVector34 X (UV Transform ?)', 0.0),
        ('NodeSocketFloat', 'CustomVector34 Y (UV Transform ?)', 0.0),
        ('NodeSocketFloat', 'CustomVector34 Z (UV Transform ?)', 0.0),
        ('NodeSocketFloat', 'CustomVector34 W (UV Transform ?)', 0.0),
    ],
    'CustomVector35': [('NodeSocketColor', 'CustomVector35', zeros)],
    'CustomVector36': [('NodeSocketColor', 'CustomVector36', zeros)],
    'CustomVector37': [('NodeSocketColor', 'CustomVector37', zeros)],
    'CustomVector38': [('NodeSocketColor', 'CustomVector38', zeros)],
    'CustomVector39': [('NodeSocketColor', 'CustomVector39', zeros)],
    'CustomVector40': [('NodeSocketColor', 'CustomVector40', zeros)],
    'CustomVector41': [('NodeSocketColor', 'CustomVector41', zeros)],
    'CustomVector42': [('NodeSocketColor', 'CustomVector42', zeros)],
    'CustomVector43': [('NodeSocketColor', 'CustomVector43', zeros)],
    'CustomVector44': [('NodeSocketColor', 'CustomVector44', zeros)],
    'CustomVector45': [('NodeSocketColor', 'CustomVector45', zeros)],
    'CustomVector46': [
        ('NodeSocketColor', 'CustomVector46 RGB', zeros),
        ('NodeSocketFloat', 'CustomVector46 Alpha', 0.0),
    ],
    'CustomVector47': [
        ('NodeSocketColor', 'CustomVector47 RGB', zeros),
        ('NodeSocketFloat', 'CustomVector47 Alpha', 0.0),
    ],
    'CustomVector48': [('NodeSocketColor', 'CustomVector48', zeros)],
    'CustomVector49': [('NodeSocketColor', 'CustomVector49', zeros)],
    'CustomVector50': [('NodeSocketColor', 'CustomVector50', zeros)],
    'CustomVector51': [('NodeSocketColor', 'CustomVector51', zeros)],
    'CustomVector52': [('NodeSocketColor', 'CustomVector52', zeros)],
    'CustomVector53': [('NodeSocketColor', 'CustomVector53', zeros)],
    'CustomVector54': [('NodeSocketColor', 'CustomVector54', zeros)],
    'CustomVector55': [('NodeSocketColor', 'CustomVector55', zeros)],
    'CustomVector56': [('NodeSocketColor', 'CustomVector56', zeros)],
    'CustomVector57': [('NodeSocketColor', 'CustomVector57', zeros)],
    'CustomVector58': [('NodeSocketColor', 'CustomVector58', zeros)],
    'CustomVector59': [('NodeSocketColor', 'CustomVector59', zeros)],
    'CustomVector60': [('NodeSocketColor', 'CustomVector60', zeros)],
    'CustomVector61': [('NodeSocketColor', 'CustomVector61', zeros)],
    'CustomVector62': [('NodeSocketColor', 'CustomVector62', zeros)],
    'CustomVector63': [('NodeSocketColor', 'CustomVector63', zeros)],
}

float_param_to_inputs = {
    'CustomFloat0': [('NodeSocketFloat', 'CustomFloat0', 0.0)],
    'CustomFloat1': [('NodeSocketFloat', 'CustomFloat1', 0.0)],
    'CustomFloat2': [('NodeSocketFloat', 'CustomFloat2', 0.0)],
    'CustomFloat3': [('NodeSocketFloat', 'CustomFloat3', 0.0)],
    'CustomFloat4': [('NodeSocketFloat', 'CustomFloat4', 0.0)],
    'CustomFloat5': [('NodeSocketFloat', 'CustomFloat5', 0.0)],
    'CustomFloat6': [('NodeSocketFloat', 'CustomFloat6', 0.0)],
    'CustomFloat7': [('NodeSocketFloat', 'CustomFloat7', 0.0)],
    'CustomFloat8': [('NodeSocketFloat', 'CustomFloat8', 0.0)],
    'CustomFloat9': [('NodeSocketFloat', 'CustomFloat9', 0.0)],
    'CustomFloat10': [('NodeSocketFloat', 'CustomFloat10', 0.0)],
    'CustomFloat11': [('NodeSocketFloat', 'CustomFloat11', 0.0)],
    'CustomFloat12': [('NodeSocketFloat', 'CustomFloat12', 0.0)],
    'CustomFloat13': [('NodeSocketFloat', 'CustomFloat13', 0.0)],
    'CustomFloat14': [('NodeSocketFloat', 'CustomFloat14', 0.0)],
    'CustomFloat15': [('NodeSocketFloat', 'CustomFloat15', 0.0)],
    'CustomFloat16': [('NodeSocketFloat', 'CustomFloat16', 0.0)],
    'CustomFloat17': [('NodeSocketFloat', 'CustomFloat17', 0.0)],
    'CustomFloat18': [('NodeSocketFloat', 'CustomFloat18', 0.0)],
    'CustomFloat19': [('NodeSocketFloat', 'CustomFloat19', 0.0)],
}

bool_param_to_inputs = {
    'CustomBoolean0': [('NodeSocketBool', 'CustomBoolean0', False)],
    'CustomBoolean1': [('NodeSocketBool', 'CustomBoolean1', False)],
    'CustomBoolean2': [('NodeSocketBool', 'CustomBoolean2', False)],
    'CustomBoolean3': [('NodeSocketBool', 'CustomBoolean3', False)],
    'CustomBoolean4': [('NodeSocketBool', 'CustomBoolean4', False)],
    'CustomBoolean5': [('NodeSocketBool', 'CustomBoolean5', False)],
    'CustomBoolean6': [('NodeSocketBool', 'CustomBoolean6', False)],
    'CustomBoolean7': [('NodeSocketBool', 'CustomBoolean7', False)],
    'CustomBoolean8': [('NodeSocketBool', 'CustomBoolean8', False)],
    'CustomBoolean9': [('NodeSocketBool', 'CustomBoolean9', False)],
    'CustomBoolean10': [('NodeSocketBool', 'CustomBoolean10', False)],
    'CustomBoolean11': [('NodeSocketBool', 'CustomBoolean11', False)],
    'CustomBoolean12': [('NodeSocketBool', 'CustomBoolean12', False)],
    'CustomBoolean13': [('NodeSocketBool', 'CustomBoolean13', False)],
    'CustomBoolean14': [('NodeSocketBool', 'CustomBoolean14', False)],
    'CustomBoolean15': [('NodeSocketBool', 'CustomBoolean15', False)],
    'CustomBoolean16': [('NodeSocketBool', 'CustomBoolean16', False)],
    'CustomBoolean17': [('NodeSocketBool', 'CustomBoolean17', False)],
    'CustomBoolean18': [('NodeSocketBool', 'CustomBoolean18', False)],
    'CustomBoolean19': [('NodeSocketBool', 'CustomBoolean19', False)],
}
