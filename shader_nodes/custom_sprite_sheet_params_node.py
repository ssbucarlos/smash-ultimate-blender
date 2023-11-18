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

class SUB_CSN_ultimate_sprite_sheet_params(ShaderNodeCustomGroup):
    bl_idname = 'SUB_CSN_ultimate_sprite_sheet_params'
    bl_label = "Ultimate Sprite Sheet Params"

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ShaderNodeTree'
    
    def init(self, context):
        # This has to be first, or the inputs to the node cannot be made at all
        self.node_tree: ShaderNodeTree = bpy.data.node_groups.new(self.bl_idname + '_node_tree', SHADER_NODE_TREE)

        self.node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_FLOAT, name='CV 18 X (Column Count)')
        self.node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_FLOAT, name='CV 18 Y (Row Count)')
        self.node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_FLOAT, name='CV 18 Z (Active Sprite Number)')
        self.node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_FLOAT, name='CV 18 W (Total Sprite Count)') # Not used but dont remove because for ease of writing some input logic, its easier to have it here
        self.node_tree.interface.new_socket(in_out="INPUT", socket_type=NODE_SOCKET_VECTOR, name='UV Input')
        self.node_tree.interface.new_socket(in_out="OUTPUT", socket_type=NODE_SOCKET_VECTOR, name='UV Output')

        # Now handle the internal nodes
        nodes = self.node_tree.nodes

        # The following was copy-pasted from NodeToPython
        #initialize sprite_sheet_param nodes
        #node Vector Math
        vector_math = nodes.new("ShaderNodeVectorMath")
        vector_math.operation = 'DIVIDE'
        #Vector_002
        vector_math.inputs[2].default_value = (0.0, 0.0, 0.0)
        #Scale
        vector_math.inputs[3].default_value = 1.0

        #node Combine XYZ
        combine_xyz = nodes.new("ShaderNodeCombineXYZ")
        #Z
        combine_xyz.inputs[2].default_value = 1.0

        #node Math.001
        math_001 = nodes.new("ShaderNodeMath")
        math_001.operation = 'DIVIDE'
        #Value
        math_001.inputs[0].default_value = 1.0
        #Value_002
        math_001.inputs[2].default_value = 0.5

        #node Math
        math = nodes.new("ShaderNodeMath")
        math.operation = 'SUBTRACT'
        #Value
        math.inputs[0].default_value = 1.0
        #Value_002
        math.inputs[2].default_value = 0.5

        #node Combine XYZ.001
        combine_xyz_001 = nodes.new("ShaderNodeCombineXYZ")
        #X
        combine_xyz_001.inputs[0].default_value = 0.0
        #Z
        combine_xyz_001.inputs[2].default_value = 0.0

        #node Group Input.001
        group_input_001 = nodes.new("NodeGroupInput")

        #node Math.002
        math_002 = nodes.new("ShaderNodeMath")
        math_002.operation = 'SUBTRACT'
        #Value_001
        math_002.inputs[1].default_value = 1.0
        #Value_002
        math_002.inputs[2].default_value = 0.5

        #node Math.003
        math_003 = nodes.new("ShaderNodeMath")
        math_003.operation = 'DIVIDE'
        #Value_002
        math_003.inputs[2].default_value = 0.5

        #node Math.004
        math_004 = nodes.new("ShaderNodeMath")
        math_004.operation = 'TRUNC'
        #Value_001
        math_004.inputs[1].default_value = 0.5
        #Value_002
        math_004.inputs[2].default_value = 0.5

        #node Math.008
        math_008 = nodes.new("ShaderNodeMath")
        math_008.operation = 'MULTIPLY'
        #Value_001
        math_008.inputs[1].default_value = -1.0
        #Value_002
        math_008.inputs[2].default_value = 0.5

        #node Group Output
        group_output = nodes.new("NodeGroupOutput")

        #node Vector Math.002
        vector_math_002 = nodes.new("ShaderNodeVectorMath")
        vector_math_002.operation = 'ADD'
        #Vector_002
        vector_math_002.inputs[2].default_value = (0.0, 0.0, 0.0)
        #Scale
        vector_math_002.inputs[3].default_value = 1.0

        #node Combine XYZ.002
        combine_xyz_002 = nodes.new("ShaderNodeCombineXYZ")
        #Z
        combine_xyz_002.inputs[2].default_value = 0.0

        #node Group Input.004
        group_input_004 = nodes.new("NodeGroupInput")

        #node Math.006
        math_006 = nodes.new("ShaderNodeMath")
        math_006.operation = 'DIVIDE'
        #Value
        math_006.inputs[0].default_value = 1.0
        #Value_002
        math_006.inputs[2].default_value = 0.5

        #node Math.007
        math_007 = nodes.new("ShaderNodeMath")
        math_007.operation = 'MULTIPLY'
        #Value_002
        math_007.inputs[2].default_value = 0.5

        #node Math.010
        math_010 = nodes.new("ShaderNodeMath")
        math_010.operation = 'MULTIPLY'
        #Value_002
        math_010.inputs[2].default_value = 0.5

        #node Group Input.003
        group_input_003 = nodes.new("NodeGroupInput")

        #node Group Input.006
        group_input_006 = nodes.new("NodeGroupInput")

        #node Group Input.005
        group_input_005 = nodes.new("NodeGroupInput")

        #node Math.009
        math_009 = nodes.new("ShaderNodeMath")
        math_009.operation = 'DIVIDE'
        #Value
        math_009.inputs[0].default_value = 1.0
        #Value_002
        math_009.inputs[2].default_value = 0.5

        #node Math.005
        math_005 = nodes.new("ShaderNodeMath")
        math_005.operation = 'MODULO'
        #Value_002
        math_005.inputs[2].default_value = 0.5

        #node Math.011
        math_011 = nodes.new("ShaderNodeMath")
        math_011.operation = 'SUBTRACT'
        #Value_001
        math_011.inputs[1].default_value = 1.0
        #Value_002
        math_011.inputs[2].default_value = 0.5

        #node Group Input.007
        group_input_007 = nodes.new("NodeGroupInput")

        #node Vector Math.001
        vector_math_001 = nodes.new("ShaderNodeVectorMath")
        vector_math_001.operation = 'ADD'
        #Vector_002
        vector_math_001.inputs[2].default_value = (0.0, 0.0, 0.0)
        #Scale
        vector_math_001.inputs[3].default_value = 1.0

        #node Group Input.002
        group_input_002 = nodes.new("NodeGroupInput")

        #node Group Input
        group_input = nodes.new("NodeGroupInput")

        #Set parents

        #Set locations
        vector_math.location = (-60.2877197265625, 223.17950439453125)
        combine_xyz.location = (-253.66661071777344, 1.4013652801513672)
        math_001.location = (-252.8219451904297, -131.60067749023438)
        math.location = (-47.00254821777344, -64.9926528930664)
        combine_xyz_001.location = (131.21080017089844, -45.29370880126953)
        group_input_001.location = (-502.6980895996094, -178.9137725830078)
        math_002.location = (487.40960693359375, -54.39963912963867)
        math_003.location = (666.2578735351562, -53.424888610839844)
        math_004.location = (888.1119995117188, 43.559974670410156)
        math_008.location = (1510.0045166015625, 73.04647827148438)
        group_output.location = (2222.230712890625, 367.3106689453125)
        vector_math_002.location = (1989.3179931640625, 352.914306640625)
        combine_xyz_002.location = (1731.39599609375, 125.525634765625)
        group_input_004.location = (894.6957397460938, 195.51510620117188)
        math_006.location = (1099.3682861328125, 175.62112426757812)
        math_007.location = (1307.9930419921875, 58.23833084106445)
        math_010.location = (1304.7529296875, -122.19625854492188)
        group_input_003.location = (478.4427490234375, -241.81007385253906)
        group_input_006.location = (479.9869689941406, -388.6886291503906)
        group_input_005.location = (1012.549072265625, -577.27099609375)
        math_009.location = (1183.270263671875, -407.17254638671875)
        math_005.location = (922.7777709960938, -354.5285339355469)
        math_011.location = (668.524658203125, -514.1769409179688)
        group_input_007.location = (481.0368957519531, -540.4091186523438)
        vector_math_001.location = (590.071533203125, 355.6821594238281)
        group_input_002.location = (306.2225646972656, -140.86985778808594)
        group_input.location = (-497.8994140625, -0.0)

        #sSet dimensions
        vector_math.width, vector_math.height = 140.0, 100.0
        combine_xyz.width, combine_xyz.height = 140.0, 100.0
        math_001.width, math_001.height = 140.0, 100.0
        math.width, math.height = 140.0, 100.0
        combine_xyz_001.width, combine_xyz_001.height = 140.0, 100.0
        group_input_001.width, group_input_001.height = 140.0, 100.0
        math_002.width, math_002.height = 140.0, 100.0
        math_003.width, math_003.height = 140.0, 100.0
        math_004.width, math_004.height = 140.0, 100.0
        math_008.width, math_008.height = 140.0, 100.0
        group_output.width, group_output.height = 140.0, 100.0
        vector_math_002.width, vector_math_002.height = 140.0, 100.0
        combine_xyz_002.width, combine_xyz_002.height = 140.0, 100.0
        group_input_004.width, group_input_004.height = 140.0, 100.0
        math_006.width, math_006.height = 140.0, 100.0
        math_007.width, math_007.height = 140.0, 100.0
        math_010.width, math_010.height = 140.0, 100.0
        group_input_003.width, group_input_003.height = 140.0, 100.0
        group_input_006.width, group_input_006.height = 140.0, 100.0
        group_input_005.width, group_input_005.height = 140.0, 100.0
        math_009.width, math_009.height = 140.0, 100.0
        math_005.width, math_005.height = 140.0, 100.0
        math_011.width, math_011.height = 140.0, 100.0
        group_input_007.width, group_input_007.height = 140.0, 100.0
        vector_math_001.width, vector_math_001.height = 140.0, 100.0
        group_input_002.width, group_input_002.height = 140.0, 100.0
        group_input.width, group_input.height = 140.0, 100.0

        #initialize sprite_sheet_param links
        links = self.node_tree.links
        #group_input.UV -> vector_math.Vector
        links.new(group_input.outputs[4], vector_math.inputs[0])
        #group_input.X (Column Count) -> combine_xyz.X
        links.new(group_input.outputs[0], combine_xyz.inputs[0])
        #group_input.Y (Row Count) -> combine_xyz.Y
        links.new(group_input.outputs[1], combine_xyz.inputs[1])
        #combine_xyz.Vector -> vector_math.Vector
        links.new(combine_xyz.outputs[0], vector_math.inputs[1])
        #vector_math.Vector -> vector_math_001.Vector
        links.new(vector_math.outputs[0], vector_math_001.inputs[0])
        #math_001.Value -> math.Value
        links.new(math_001.outputs[0], math.inputs[1])
        #math.Value -> combine_xyz_001.Y
        links.new(math.outputs[0], combine_xyz_001.inputs[1])
        #combine_xyz_001.Vector -> vector_math_001.Vector
        links.new(combine_xyz_001.outputs[0], vector_math_001.inputs[1])
        #group_input_001.Y (Row Count) -> math_001.Value
        links.new(group_input_001.outputs[1], math_001.inputs[1])
        #group_input_002.Z (Sprite Number) -> math_002.Value
        links.new(group_input_002.outputs[2], math_002.inputs[0])
        #math_002.Value -> math_003.Value
        links.new(math_002.outputs[0], math_003.inputs[0])
        #math_003.Value -> math_004.Value
        links.new(math_003.outputs[0], math_004.inputs[0])
        #group_input_004.Y (Row Count) -> math_006.Value
        links.new(group_input_004.outputs[1], math_006.inputs[1])
        #math_004.Value -> math_007.Value
        links.new(math_004.outputs[0], math_007.inputs[0])
        #math_006.Value -> math_007.Value
        links.new(math_006.outputs[0], math_007.inputs[1])
        #math_008.Value -> combine_xyz_002.Y
        links.new(math_008.outputs[0], combine_xyz_002.inputs[1])
        #math_007.Value -> math_008.Value
        links.new(math_007.outputs[0], math_008.inputs[0])
        #vector_math_001.Vector -> vector_math_002.Vector
        links.new(vector_math_001.outputs[0], vector_math_002.inputs[0])
        #vector_math_002.Vector -> group_output.Vector
        links.new(vector_math_002.outputs[0], group_output.inputs[0])
        #combine_xyz_002.Vector -> vector_math_002.Vector
        links.new(combine_xyz_002.outputs[0], vector_math_002.inputs[1])
        #group_input_005.X (Column Count) -> math_009.Value
        links.new(group_input_005.outputs[0], math_009.inputs[1])
        #math_005.Value -> math_010.Value
        links.new(math_005.outputs[0], math_010.inputs[0])
        #math_009.Value -> math_010.Value
        links.new(math_009.outputs[0], math_010.inputs[1])
        #group_input_003.X (Column Count) -> math_003.Value
        links.new(group_input_003.outputs[0], math_003.inputs[1])
        #math_010.Value -> combine_xyz_002.X
        links.new(math_010.outputs[0], combine_xyz_002.inputs[0])
        #group_input_007.Z (Sprite Number) -> math_011.Value
        links.new(group_input_007.outputs[2], math_011.inputs[0])
        #math_011.Value -> math_005.Value
        links.new(math_011.outputs[0], math_005.inputs[0])
        #group_input_006.X (Column Count) -> math_005.Value
        links.new(group_input_006.outputs[0], math_005.inputs[1])