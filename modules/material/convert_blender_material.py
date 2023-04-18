import bpy
import ssbh_data_py

from bpy.types import (
    ShaderNode, ShaderNodeOutputMaterial, ShaderNodeBsdfDiffuse, ShaderNodeEmission,ShaderNodeBsdfPrincipled,
    ShaderNodeAttribute, ShaderNodeUVMap, NodeSocketFloat, NodeSocketColor, Image, ShaderNodeVertexColor, ShaderNodeMixRGB, Material, Operator)

from math import isclose

from .load_from_shader_label import create_sub_matl_data_from_shader_label
from .sub_matl_data import *
from .create_blender_materials_from_matl import create_default_textures
ParamId = ssbh_data_py.matl_data.ParamId

def convert_from_no_nodes(operator: bpy.types.Operator, material: bpy.types.Material):
    diffuse_color = material.diffuse_color[:]
    metalness = material.metallic
    specular = material.specular_intensity
    roughness = material.roughness
    create_sub_matl_data_from_shader_label(material, "SFX_PBS_010000000808ba68_opaque")
    sub_matl_data: SUB_PG_sub_matl_data = material.sub_matl_data
    cv47: SUB_PG_matl_vector = sub_matl_data.vectors.get(ParamId.CustomVector47.name)
    cv47.value = (metalness, roughness, 1.0, specular)
    cv13: SUB_PG_matl_vector = sub_matl_data.vectors.get(ParamId.CustomVector13.name)
    cv13.value = diffuse_color[:]

def get_vertex_color_count(nodes: list[bpy.types.ShaderNode]) -> int:
    vertex_color_names = set()
    for node in nodes:
        if not isinstance(node, (ShaderNodeAttribute, ShaderNodeVertexColor)):
            # Not the right node type
            continue
        if isinstance(node, ShaderNodeAttribute):
            if node.attribute_type != 'GEOMETRY':
                # Not vertex colors
                continue
            if not node.outputs['Color'].is_linked:
                # Not being used at all, or not used in a standard way
                continue
            if node.attribute_name == "":
                # Not being used at all, or being used incorrectly
                continue
            vertex_color_names.add(node.attribute_name)
        elif isinstance(node, ShaderNodeVertexColor):
            if not node.outputs['Color'].is_linked:
                # Not being used at all, or not used in a standard way
                continue
            if node.layer_name == "":
                # Not being used at all, or being used incorrectly
                continue
            vertex_color_names.add(node.layer_name)
        

    return len(vertex_color_names)

def get_uv_layer_count(nodes: list[bpy.types.ShaderNode]) -> int:
    uv_layer_names = set()
    for node in nodes:
        if not isinstance(node, ShaderNodeUVMap):
            # Not the right node type
            continue
        if node.from_instancer is True:
            # This means its using the 'Active' uv map rather than any specific one
            continue
        if node.uv_map == "":
            # This means its using the 'Active' uv map rather than any specific one.
            # it would be unusual for a user to intentionally use this and then use a manually specified one later
            continue
        uv_layer_names.add(node.uv_map)

    return len(uv_layer_names)

def is_bsdf_principled_using_emission(node: ShaderNodeBsdfPrincipled) -> bool:
    emission_input: NodeSocketColor = node.inputs['Emission']
    strength_input: NodeSocketFloat = node.inputs['Emission Strength']
    if emission_input.is_linked and strength_input.is_linked:
        return True
    
    if not strength_input.is_linked:
        if isclose(strength_input.default_value,0,abs_tol=0.01):
            return False
    if not emission_input.is_linked:
        if all(isclose(emission_input.default_value[col_index],0,abs_tol=0.01) for col_index in (0,1,2)):
            return False 
        
    return True

def rename_mesh_attributes_of_meshes_using_material(operator: bpy.types.Operator, material: Material, preset:str = "FIGHTER"):
    meshes: set[bpy.types.Mesh] = {mesh for mesh in bpy.data.meshes if material in mesh.materials.values()}
    for mesh in meshes:
        if preset == 'FIGHTER':
            if len(mesh.uv_layers) > 2:
                operator.report({'WARNING'}, f"Can't rename UV Layers of mesh '{mesh.name}', theres more than 2 UV Layers! Please rename them manually, or remove the un-needed layers!")
            else:
                if len(mesh.uv_layers) == 2:
                    mesh.uv_layers[0].name = 'map1'
                    mesh.uv_layers[1].name = 'uvSet'
                if len(mesh.uv_layers) == 1:
                    mesh.uv_layers[0].name = 'map1'
            if len(mesh.color_attributes) > 1:
                operator.report({'WARNING'}, f"Can't rename UV Layers of mesh '{mesh.name}', theres more than 2 UV Layers! Please rename them manually, or remove the un-needed layers!")
            else:
                if len(mesh.color_attributes) == 1:
                    mesh.color_attributes[0].name = 'colorSet1'
                    # Scale color_set_1 for intuitive results
                    for data in mesh.color_attributes[0].data:
                        data.color = [ value / 2 for value in data.color ]

            
def convert_from_nodes(operator: bpy.types.Operator, material: bpy.types.Material):
    '''
    Just trys to handle common simple shader node setups, anything too complicated or broken
    will just be assigned a standard PBR material.
    '''
    # Gets the output node, prioritizing the EEVEE-specific node if multiple are present
    output_node: ShaderNodeOutputMaterial = material.node_tree.get_output_node('EEVEE')
    
    # This would mean the model isn't rendering in eevee, which is probably a good sign the material is incomplete.
    if output_node is None:
        operator.report({'WARNING'}, f'The material "{material.name}" has no eevee output! Converting to default PBR material.')
        create_sub_matl_data_from_shader_label(material, "SFX_PBS_0100000008008269_opaque")
        return
    
    # An eevee output with no links to its surface doesn't make sense anyways
    if len(output_node.inputs['Surface'].links) == 0:
        operator.report({'WARNING'}, f'The material "{material.name}" has an eevee output but nothing connected to it! Converting to default PBR material.')
        create_sub_matl_data_from_shader_label(material, "SFX_PBS_0100000008008269_opaque")
        return
    
    # For now, will handle vertex color counts of 0 or 1, as those can get assigned a standard PBR material.
    # 2+ is a more advanced material, the user can just create from the needed shader label manually.
    vertex_color_count = get_vertex_color_count(material.node_tree.nodes)

    # For now, will handle 1 or 2 UV maps, assume 1 is standard PBR material and 2 is a eye material.
    # 3+ is a more advanced material, the user can just create from the needed shader label manually.
    uv_layer_count = get_uv_layer_count(material.node_tree.nodes)

    final_node:ShaderNode = output_node.inputs['Surface'].links[0].from_node
    if isinstance(final_node, ShaderNodeEmission):
        if final_node.inputs['Color'].is_linked is False:
            emission_color = final_node.inputs['Color'].default_value[:]
            emission_strength = final_node.inputs['Strength'].default_value
            emission_strength_linked = final_node.inputs['Strength'].is_linked
            linked_emission_map: Image = None
            if emission_strength_linked:
                # User may be using a texture for the emission map
                pre_final_node = final_node.inputs['Strength'].links[0].from_node
                if isinstance(pre_final_node, ShaderNodeTexImage):
                    linked_emission_map = pre_final_node.image
            else:
                # User not using a map
                emission_strength = final_node.inputs['Strength'].default_value   
            
            create_sub_matl_data_from_shader_label(material, "SFX_PBS_0000000000000100_opaque") # 1 Layer Shadeless Emissive
            sub_matl_data: SUB_PG_sub_matl_data = material.sub_matl_data
            cv3: SUB_PG_matl_vector = sub_matl_data.vectors.get(ParamId.CustomVector3.name)
            texture5: SUB_PG_matl_texture = sub_matl_data.textures.get(ParamId.Texture5.name)
            if emission_strength_linked:
                cv3.value = [emission_color[i] for i in (0,1,2,3)]
                texture5.image = linked_emission_map
            else:
                cv3.value = [emission_color[i] * emission_strength for i in (0,1,2,3)]
                texture5.image = bpy.data.images.get('/common/shader/sfxpbs/default_white')
        else:
            # Smash's emission texture is both the 'factor' and the 'color' of the emissive effect
            emission_strength = final_node.inputs['Strength'].default_value if not final_node.inputs['Strength'].is_linked else 1.0
            if uv_layer_count >= 2:
                tex_layer_1 = None
                tex_layer_2 = None
                if vertex_color_count >= 1:
                    vertex_color_mix_node = final_node.inputs['Color'].links[0].from_node
                    if isinstance(vertex_color_mix_node, ShaderNodeMixRGB):
                        try:
                            tex_layer_1 = vertex_color_mix_node.inputs[1].links[0].from_node.inputs[1].links[0].from_node.image
                        except AttributeError:
                            pass
                        try:
                            tex_layer_2 = vertex_color_mix_node.inputs[1].links[0].from_node.inputs[2].links[0].from_node.image
                        except AttributeError:
                            pass   
                    create_sub_matl_data_from_shader_label(material, "SFX_PBS_0120000810080100_opaque") # 2 Layer Shadeless + colorSet1
                else:
                    # Check if its using a texture mix node, expect alpha blending using the second texture in the second color input
                    mix_tex_layers_node = final_node.inputs['Color'].links[0].from_node
                    if isinstance(mix_tex_layers_node, ShaderNodeMixRGB):
                        try: 
                            tex_layer_1 = mix_tex_layers_node.inputs[1].links[0].from_node.image
                        except AttributeError:
                            pass
                        try:
                            tex_layer_2 = mix_tex_layers_node.inputs[2].links[0].from_node.image
                        except AttributeError:
                            pass
                    create_sub_matl_data_from_shader_label(material, "SFX_PBS_0120000010008100_opaque") # 2 Layer Shadeless
                sub_matl_data: SUB_PG_sub_matl_data = material.sub_matl_data
                texture5: SUB_PG_matl_texture = sub_matl_data.textures.get(ParamId.Texture5.name)
                texture14: SUB_PG_matl_texture = sub_matl_data.textures.get(ParamId.Texture14.name)
                if tex_layer_1 is not None:
                    texture5.image = tex_layer_1
                if tex_layer_2 is not None:
                    texture14.image = tex_layer_2
                
            else:
                # The texture node should simply be linked to the output
                tex_layer_1 = None
                if vertex_color_count >= 1:
                    vertex_color_mix_node = final_node.inputs['Color'].links[0].from_node
                    if isinstance(vertex_color_mix_node, ShaderNodeMixRGB):
                        try:
                            tex_layer_1 = vertex_color_mix_node.inputs[1].links[0].from_node.image
                        except AttributeError:
                            pass
                    create_sub_matl_data_from_shader_label(material, "SFX_PBS_0000000000080100_opaque") # 1 Layer Shadeless Emissive + colorSet1
                else:
                    texture_mix_node = final_node.inputs['Color'].links[0].from_node
                    if isinstance(texture_mix_node, ShaderNodeTexImage):
                        tex_layer_1 = texture_mix_node.image
                    create_sub_matl_data_from_shader_label(material, "SFX_PBS_0000000000000100_opaque") # 1 Layer Shadeless Emissive
                sub_matl_data: SUB_PG_sub_matl_data = material.sub_matl_data
                texture5: SUB_PG_matl_texture = sub_matl_data.textures.get(ParamId.Texture5.name)
                if tex_layer_1 is not None:
                    texture5.image = tex_layer_1
    elif isinstance(final_node, ShaderNodeBsdfPrincipled):
        if is_bsdf_principled_using_emission(final_node):
            if uv_layer_count >= 2:
                if vertex_color_count >= 1:
                    create_sub_matl_data_from_shader_label(material, "SFX_PBS_0100000818098329_opaque") # PBR, 2 Layer Emmissive + colorset1
                else:
                    create_sub_matl_data_from_shader_label(material, "SFX_PBS_010000001a00824f_opaque") # PBR, 2 Layer Emmissive
            else:
                if vertex_color_count >= 1:
                    create_sub_matl_data_from_shader_label(material, "SFX_PBS_010000000a088269_opaque") # PBR, 1 Layer Emmissive  + colorset1
                else:
                    create_sub_matl_data_from_shader_label(material, "SFX_PBS_010000080a008269_opaque") # PBR, 1 Layer Emmissive
        else: # No Emission
            if uv_layer_count >= 2:
                # No shader for fighters with support for 2 UV maps and colorSet1
                create_sub_matl_data_from_shader_label(material, "SFX_PBS_010000000800824f_opaque") # PBR, 2 Layer
            else:
                if vertex_color_count >= 1:
                    create_sub_matl_data_from_shader_label(material,"SFX_PBS_0100000008088269_opaque") # PBR, 1 Layer + colorSet1
                else:
                    create_sub_matl_data_from_shader_label(material, "SFX_PBS_0100000008008269_opaque") # PBR, 1 Layer
    else: # More complex node setup
        if uv_layer_count >= 2:
            create_sub_matl_data_from_shader_label(material, "SFX_PBS_010000000800824f_opaque") # PBR, 2 Layer
        else:
            if vertex_color_count >= 1:
                    create_sub_matl_data_from_shader_label(material,"SFX_PBS_0100000008088269_opaque") # PBR, 1 Layer + colorSet1
            else:
                create_sub_matl_data_from_shader_label(material, "SFX_PBS_0100000008008269_opaque") # PBR, 1 Layer
   
        

def convert_blender_material(operator: bpy.types.Operator, material: bpy.types.Material):
    
    # Setup default textures if not already made
    create_default_textures()
    
    if material.use_nodes is False:
        convert_from_no_nodes(operator, material)
    else:
        convert_from_nodes(operator, material)
    



    

