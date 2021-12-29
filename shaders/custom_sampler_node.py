import bpy
from bpy.types import ShaderNodeCustomGroup

class CustomNodeUltimateBase:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ShaderNodeTree'

class CustomNodeUltimateSampler(ShaderNodeCustomGroup, CustomNodeUltimateBase):
    '''A custom node to implement Smash Ultimate Samplers'''
    bl_idname = 'CustomNodeUltimateSampler'
    bl_label = "Ultimate Sampler"

    def update_internal_nodes(self, context):
        math_x = self.node_tree.nodes['math_x']
 
        if self.wrap_s == 'Repeat':
            math_x.operation = 'MULTIPLY'
            math_x.use_clamp = False
            math_x.inputs[1].default_value = 1.0
        elif self.wrap_s == 'MirroredRepeat':
            math_x.operation = 'PINGPONG'
            math_x.use_clamp = False
            math_x.inputs[1].default_value = 1.0
        else:
            math_x.operation = 'MULTIPLY'
            math_x.use_clamp = True
            math_x.inputs[1].default_value = 1.0
        
        math_y = self.node_tree.nodes['math_y']
        
        if self.wrap_t == 'Repeat':
            math_y.operation = 'MULTIPLY'
            math_y.use_clamp = False
            math_y.inputs[1].default_value = 1.0
        elif self.wrap_t == 'MirroredRepeat':
            math_y.operation = 'PINGPONG'
            math_y.use_clamp = False
            math_y.inputs[1].default_value = 1.0
        else:
            math_y.operation = 'MULTIPLY'
            math_y.use_clamp = True
            math_y.inputs[1].default_value = 1.0

    wrap_types = (
        ('Repeat', "Repeat", "The texture just keeps repeating"),
        ('ClampToEdge', "Clamp To Edge", "Out-of-bounds UVs just get clamped to the edge"),
        ('MirroredRepeat', "Mirrored Repeat", "Repeats, but mirrored"),
        ('ClampToBorder', "Clamp To Border", "Out-of-bounds UVs just get clamped to one pixel before the edge"),
    )
    min_filter_types = (
        ('Nearest', 'Nearest', 'Nearest'),
        ('LinearMipmapLinear', 'LinearMipmapLinear', 'LinearMipmapLinear'),
        ('LinearMipmapLinear2', 'LinearMipmapLinear2', 'LinearMipmapLinear2'),
    )
    mag_filter_types = (
        ('Nearest', 'Nearest', 'Nearest'),
        ('Linear', 'Linear', 'Linear'),
        ('Linear2', 'Linear2', 'Linear2'),
    )
    max_anisotropy_levels = (
        ('One', '1x', '1x'),
        ('Two', '2x', '2x'),
        ('Four', '4x', '4x'),
        ('Eight', '8x', '8x'),
        ('Sixteen', '16x', '16x'),
    )
    wrap_s: bpy.props.EnumProperty(
        name="S",
        description="Wrap S",
        items=wrap_types,
        default='Repeat',
        update=update_internal_nodes,
    )
    wrap_t: bpy.props.EnumProperty(
        name="T",
        description="Wrap T",
        items=wrap_types,
        default='Repeat',
        update=update_internal_nodes,
    )
    wrap_r: bpy.props.EnumProperty(
        name="R",
        description="Wrap R",
        items=wrap_types,
        default='Repeat',
    )
    
    min_filter: bpy.props.EnumProperty(
        name='Min',
        description='Min Filter',
        items=min_filter_types,
        default='Nearest',
    )
    
    mag_filter: bpy.props.EnumProperty(
        name='Mag',
        description='Mag Filter',
        items=mag_filter_types,
        default='Nearest',
    )
    
    anisotropic_filtering: bpy.props.BoolProperty(
        name='Anisotropic Filtering',
        description='Anisotropic Filtering',
        default=False,
    )
    
    border_color: bpy.props.FloatVectorProperty(
        name='Border Color',
        description='Border Color',
        subtype='COLOR',
        size=4,
        default=(1.0,1.0,1.0,1.0),
        soft_max=1.0,
        soft_min=0.0,
    )

    lod_bias: bpy.props.FloatProperty(
        name='LOD Bias',
        description='LOD Bias',
        default=0.0,
    )
    
    max_anisotropy: bpy.props.EnumProperty(
        name='Max Anisotropy',
        description='Max Anisotropy',
        items=max_anisotropy_levels,
        default='One',
    )

    def init(self, context):
        self.node_tree = bpy.data.node_groups.new(self.bl_idname + '_node_tree', 'ShaderNodeTree')
        
        internal_input = self.node_tree.nodes.new('NodeGroupInput')
        internal_output = self.node_tree.nodes.new('NodeGroupOutput') 

        inner_links = self.node_tree.links
        inner_nodes = self.node_tree.nodes
        
        self.node_tree.inputs.new('NodeSocketVector', 'UV Input')
        self.node_tree.inputs.new('NodeSocketVector', 'UV Transform')
        self.node_tree.outputs.new('NodeSocketVector', 'UV Output')
        
        separate_xyz = inner_nodes.new('ShaderNodeSeparateXYZ')
        separate_xyz.name = 'separate_xyz'
        separate_xyz.label = 'separate_xyz'
        
        combine_xyz = inner_nodes.new('ShaderNodeCombineXYZ')
        combine_xyz.name = 'combine_xyz'
        combine_xyz.label = 'combine_xyz'
        
        math_x = inner_nodes.new('ShaderNodeMath')
        math_x.name = 'math_x'
        math_x.label = 'math_x'
        if self.wrap_s == 'Repeat':
            math_x.operation = 'MULTIPLY'
            math_x.use_clamp = False
            math_x.inputs[1].default_value = 1.0
        elif self.wrap_s == 'MirroredRepeat':
            math_x.operation = 'PINGPONG'
            math_x.use_clamp = False
            math_x.inputs[1].default_value = 1.0
        else:
            math_x.operation = 'MULTIPLY'
            math_x.use_clamp = True
            math_x.inputs[1].default_value = 1.0
        
        math_y = inner_nodes.new('ShaderNodeMath')
        math_y.name = 'math_y'
        math_y.label = 'math_y'
        if self.wrap_t == 'Repeat':
            math_y.operation = 'MULTIPLY'
            math_y.use_clamp = False
            math_y.inputs[1].default_value = 1.0
        elif self.wrap_t == 'MirroredRepeat':
            math_y.operation = 'PINGPONG'
            math_y.use_clamp = False
            math_y.inputs[1].default_value = 1.0
        else:
            math_y.operation = 'MULTIPLY'
            math_y.use_clamp = True
            math_y.inputs[1].default_value = 1.0
        
        vector_math = inner_nodes.new('ShaderNodeVectorMath')
        vector_math.name = 'vector_math'
        vector_math.label = 'vector_math'
        vector_math.operation = 'ADD'
        
        
        inner_links.new(vector_math.inputs[0], internal_input.outputs[0])
        inner_links.new(vector_math.inputs[1], internal_input.outputs[1])
        inner_links.new(separate_xyz.inputs[0], vector_math.outputs[0])
        inner_links.new(math_x.inputs[0], separate_xyz.outputs['X'])
        inner_links.new(math_y.inputs[0], separate_xyz.outputs['Y'])
        inner_links.new(combine_xyz.inputs['X'], math_x.outputs[0])
        inner_links.new(combine_xyz.inputs['Y'], math_y.outputs[0])
        inner_links.new(combine_xyz.inputs['Z'], separate_xyz.outputs['Z'])
        inner_links.new(internal_output.inputs[0], combine_xyz.outputs[0])

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        layout.label(text='Wrap Settings')
        row = layout.row()
        row.prop(self, 'wrap_s')
        row.prop(self, 'wrap_t')
        row.prop(self, 'wrap_r')
        layout.label(text='Filter Settings')
        row = layout.row()
        row.prop(self, 'min_filter')
        row.prop(self, 'mag_filter')
        row.prop(self, 'anisotropic_filtering')
        layout.prop(self, 'border_color')
        layout.prop(self, 'lod_bias')
        layout.prop(self, 'max_anisotropy')


import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

class UltimateNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

node_categories = [
    UltimateNodeCategory('ULTIMATENODES', 'Smash Ultimate', items = [
        NodeItem("CustomNodeUltimateSampler")
    ]),
]

classes = (
    CustomNodeUltimateSampler,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    nodeitems_utils.register_node_categories('CUSTOM_ULTIMATE_NODES', node_categories)

def unregister():
    nodeitems_utils.unregister_node_categories('CUSTOM_ULTIMATE_NODES')
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

