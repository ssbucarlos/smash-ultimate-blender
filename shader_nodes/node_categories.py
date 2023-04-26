from .custom_sampler_node import SUB_CSN_ultimate_sampler
from .custom_uv_transform_node import SUB_CSN_ultimate_uv_transform
from .custom_sprite_sheet_params_node import SUB_CSN_ultimate_sprite_sheet_params
from nodeitems_utils import NodeCategory, NodeItem

class UltimateNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

node_categories = [
    UltimateNodeCategory('ULTIMATENODES', 'Smash Ultimate', items = [
        NodeItem(SUB_CSN_ultimate_sampler.bl_idname),
        NodeItem(SUB_CSN_ultimate_uv_transform.bl_idname),
        NodeItem(SUB_CSN_ultimate_sprite_sheet_params.bl_idname)
    ]),
]
