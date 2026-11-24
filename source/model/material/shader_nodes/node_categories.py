from nodeitems_utils import NodeCategory, NodeItem

from .custom_sampler_node import SUB_CSN_ultimate_sampler


class UltimateNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "ShaderNodeTree"


node_categories = [
    UltimateNodeCategory(
        "ULTIMATENODES",
        "Smash Ultimate",
        items=[
            NodeItem(SUB_CSN_ultimate_sampler.bl_idname),
        ],
    ),
]
