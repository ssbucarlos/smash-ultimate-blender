import bpy

from bpy.types import Panel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..anim.anim_data import SUB_PG_sub_anim_data

class SUB_PT_misc(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Misc.'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        modes = ['POSE', 'OBJECT']
        return context.mode in modes

    def draw(self, context):
        ssp: SUB_PG_sub_anim_data = context.scene.sub_scene_properties

        layout = self.layout
        layout.use_property_split = False
        
        row = layout.row(align=True)
        row.operator("sub.eye_material_custom_vector_31_modal")

    