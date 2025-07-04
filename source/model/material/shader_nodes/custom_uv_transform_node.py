import bpy
from bpy.types import (
    NodeSocketFloat, NodeSocketVector, ShaderNodeTree,
    NodeGroupInput, NodeGroupOutput, ShaderNodeVectorMath, ShaderNodeCombineXYZ,)

# So i can know if i made a typo before i test.
NODE_SOCKET_FLOAT       = NodeSocketFloat.bl_rna.identifier
NODE_SOCKET_VECTOR      = NodeSocketVector.bl_rna.identifier
SHADER_NODE_TREE        = ShaderNodeTree.bl_rna.identifier
NODE_GROUP_INPUT        = NodeGroupInput.bl_rna.identifier
NODE_GROUP_OUTPUT       = NodeGroupOutput.bl_rna.identifier
SHADER_NODE_VECTOR_MATH = ShaderNodeVectorMath.bl_rna.identifier
SHADER_NODE_COMBINE_XYZ = ShaderNodeCombineXYZ.bl_rna.identifier

def ultimate_uv_transform_node_group() -> bpy.types.NodeTree: 
    '''
    For some reason, setting the default values just doesn't work here regardelss of how u make the inputs.
    e.g.
    `self.inputs.new(NODE_SOCKET_FLOAT, 'Scale X').default_value = 1.0`, also fails.
    `node_tree.inputs.new(NODE_SOCKET_FLOAT, 'Scale X').default_value = 1.0`, also fails.
    The workaround is for the caller to set the default_value after creating an instance of this custom node. 
    '''
    node_tree = bpy.data.node_groups.new('ultimate_uv_transform', SHADER_NODE_TREE)

    # The sockets that go on the node itself
    # As of blender 3.4.1, creating node sockets using `self.inputs.new` is no longer supported
    # And as of blender 4.0, creating node sockets using `node_tree.inputs.new` is no longer supported
    node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_FLOAT, name='Scale X')
    node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_FLOAT, name='Scale Y')
    node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_FLOAT, name='Translate X')
    node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_FLOAT, name='Translate Y')
    node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_VECTOR, name='UV Input')
    node_tree.interface.new_socket(in_out="OUTPUT", socket_type=NODE_SOCKET_VECTOR, name='UV Output')
    
    # Now handle the internal nodes
    nodes = node_tree.nodes

    input_node = nodes.new(NODE_GROUP_INPUT)

    combine_scale_node: ShaderNodeCombineXYZ = nodes.new(SHADER_NODE_COMBINE_XYZ)

    combine_trans_node: ShaderNodeCombineXYZ = nodes.new(SHADER_NODE_COMBINE_XYZ)

    mult_add_node: ShaderNodeVectorMath = nodes.new(SHADER_NODE_VECTOR_MATH)
    mult_add_node.name = 'mult_add_node'
    mult_add_node.operation = 'MULTIPLY_ADD'
    mult_add_node.inputs[1].default_value = (-1.0, -1.0, -1.0) # Trans Inversion

    mult_node: ShaderNodeVectorMath = nodes.new(SHADER_NODE_VECTOR_MATH)
    mult_node.name = 'mult_node'
    mult_node.operation = 'MULTIPLY'
    
    output_node = nodes.new(NODE_GROUP_OUTPUT) 

    links = node_tree.links
    links.new(combine_scale_node.inputs[0], input_node.outputs[0])
    links.new(combine_scale_node.inputs[1], input_node.outputs[1])
    links.new(combine_trans_node.inputs[0], input_node.outputs[2])
    links.new(combine_trans_node.inputs[1], input_node.outputs[3])
    links.new(mult_add_node.inputs[0], combine_trans_node.outputs[0])
    links.new(mult_add_node.inputs[2], input_node.outputs[4])
    links.new(mult_node.inputs[0], combine_scale_node.outputs[0])
    links.new(mult_node.inputs[1], mult_add_node.outputs[0])
    links.new(output_node.inputs[0], mult_node.outputs[0])

    return node_tree
