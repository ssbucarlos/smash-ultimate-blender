import bpy
from bpy.types import (
    ShaderNodeCustomGroup, NodeSocketFloat, NodeSocketVector, ShaderNodeTree,
    NodeGroupInput, NodeGroupOutput, ShaderNodeVectorMath, ShaderNodeCombineXYZ,)

# So i can know if i made a typo before i test.
NODE_SOCKET_FLOAT       = NodeSocketFloat.bl_rna.identifier
NODE_SOCKET_VECTOR      = NodeSocketVector.bl_rna.identifier
SHADER_NODE_TREE        = ShaderNodeTree.bl_rna.identifier
NODE_GROUP_INPUT        = NodeGroupInput.bl_rna.identifier
NODE_GROUP_OUTPUT       = NodeGroupOutput.bl_rna.identifier
SHADER_NODE_VECTOR_MATH = ShaderNodeVectorMath.bl_rna.identifier
SHADER_NODE_COMBINE_XYZ = ShaderNodeCombineXYZ.bl_rna.identifier
 
class SUB_CSN_ultimate_uv_transform(ShaderNodeCustomGroup):
    '''
    The reason this is handled with the jank "set the default_value using unlinked sockets, and then put drivers on the
    default_value" method, instead of using actual class variables, is because when drivers update class variables, the "update" function that you
    provide does not get called
    '''
    bl_idname = 'SUB_CSN_ultimate_uv_transform'
    bl_label = "Ultimate UV Transform"

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ShaderNodeTree'


    def init(self, context):
        '''
        For some reason, setting the default values just doesn't work here regardelss of how u make the inputs.
        e.g.
        `self.inputs.new(NODE_SOCKET_FLOAT, 'Scale X').default_value = 1.0`, also fails.
        `self.node_tree.inputs.new(NODE_SOCKET_FLOAT, 'Scale X').default_value = 1.0`, also fails.
        The workaround is for the caller to set the default_value after creating an instance of this custom node. 
        '''
        # This has to be first, or the inputs to the node cannot be made at all
        self.node_tree: ShaderNodeTree = bpy.data.node_groups.new(self.bl_idname + '_node_tree', SHADER_NODE_TREE)
        
        # The sockets that go on the node itself
        # As of blender 3.4.1, creating node sockets using `self.inputs.new` is no longer supported
        self.node_tree.inputs.new(NODE_SOCKET_FLOAT, 'Scale X')
        self.node_tree.inputs.new(NODE_SOCKET_FLOAT, 'Scale Y')
        self.node_tree.inputs.new(NODE_SOCKET_FLOAT, 'Translate X')
        self.node_tree.inputs.new(NODE_SOCKET_FLOAT, 'Translate Y')
        self.node_tree.inputs.new(NODE_SOCKET_VECTOR, 'UV Input')
        self.node_tree.outputs.new(NODE_SOCKET_VECTOR, 'UV Output')
        
        # Now handle the internal nodes
        nodes = self.node_tree.nodes

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

        links = self.node_tree.links
        links.new(combine_scale_node.inputs[0], input_node.outputs[0])
        links.new(combine_scale_node.inputs[1], input_node.outputs[1])
        links.new(combine_trans_node.inputs[0], input_node.outputs[2])
        links.new(combine_trans_node.inputs[1], input_node.outputs[3])
        links.new(mult_add_node.inputs[0], combine_trans_node.outputs[0])
        links.new(mult_add_node.inputs[2], input_node.outputs[4])
        links.new(mult_node.inputs[0], combine_scale_node.outputs[0])
        links.new(mult_node.inputs[1], mult_add_node.outputs[0])
        links.new(output_node.inputs[0], mult_node.outputs[0])






