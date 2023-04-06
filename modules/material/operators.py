import bpy
from bpy.types import Operator

class SUB_OP_change_render_pass(Operator):
    bl_idname = 'sub.change_render_pass'
    bl_label = 'Change Render Pass'

    def execute(self, context):
        return {'FINISHED'} 

class SUB_OP_change_shader_label(Operator):
    bl_idname = 'sub.change_shader_label'
    bl_label = 'Change Shader Label'

    def execute(self, context):
        return {'FINISHED'} 
    
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
