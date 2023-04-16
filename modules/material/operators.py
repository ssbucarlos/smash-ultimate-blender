import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from .load_from_shader_label import is_valid_shader_label, create_sub_matl_data_from_shader_label

class SUB_OP_change_render_pass(Operator):
    bl_idname = 'sub.change_render_pass'
    bl_label = 'Change Render Pass'

    def execute(self, context):
        return {'FINISHED'} 

class SUB_OP_create_sub_matl_data_from_shader_label(Operator):
    bl_idname = 'sub.create_sub_matl_data_from_shader_label'
    bl_label = 'Create New Material from Shader Label'
    
    new_shader_label: StringProperty(
        name="New Shader Label",
        description="The New Shader Label",
        default="SFX_PBS_0100000008008269_opaque"
        )
    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        if context.object.type != 'MESH':
            return False
        if context.object.active_material is None:
            return False
        if context.object.active_material.sub_matl_data is None:
            return False
        if context.object.active_material.sub_matl_data.shader_label == "":
            return False
        return True
    
    def execute(self, context):
        if not is_valid_shader_label(self, self.new_shader_label):
            return{'CANCELLED'}
        create_sub_matl_data_from_shader_label(context.object.active_material, self.new_shader_label)
        return {'FINISHED'} 
    
    def invoke(self, context, event):
        wm = context.window_manager
        self.new_shader_label = context.object.active_material.sub_matl_data.shader_label
        return wm.invoke_props_dialog(self)

class SUB_OP_apply_material_preset(Operator):
    bl_idname = 'sub.change_shader_label'
    bl_label = 'Change Shader Label'

    def execute(self, context):
        return {'FINISHED'} 
    
class SUB_OP_convert_blender_material(Operator):
    bl_idname = 'sub.convert_blender_material'
    bl_label = 'Convert Blender Material'

    def execute(self, context):
        return {'FINISHED'} 

class SUB_OP_copy_from_ult_material(Operator):
    bl_idname = 'sub.convert_blender_material'
    bl_label = 'Convert Blender Material'

    def execute(self, context):
        return {'FINISHED'} 
