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
    
from .convert_blender_material import convert_blender_material, rename_mesh_attributes_of_meshes_using_material
from .texture.convert_textures import create_prm_from_material
from ....dependencies import ssbh_data_py
ParamId = ssbh_data_py.matl_data.ParamId

class SUB_OP_convert_blender_material(Operator):
    bl_idname = 'sub.convert_blender_material'
    bl_label = 'Convert Blender Material'
    bl_description = 'Convert a Blender material to Ultimate format by analyzing its shader nodes and assigning appropriate textures and parameters'

    def execute(self, context):
        rename_mesh_attributes_of_meshes_using_material(self, context.object.active_material)
        convert_blender_material(self, context.object.active_material)
        return {'FINISHED'}

class SUB_OP_convert_blender_material_with_prm(Operator):
    bl_idname = 'sub.convert_blender_material_with_prm'
    bl_label = 'Convert Blender Material (With PRM)'
    bl_description = 'Convert a Blender material to Ultimate format and automatically generate a PRM texture from Principled BSDF properties (Metalness, Roughness, Specular) assigned to Texture6'

    def execute(self, context):
        material = context.object.active_material
        
        # First do the standard conversion
        rename_mesh_attributes_of_meshes_using_material(self, material)
        convert_blender_material(self, material)
        
        # Then generate and assign PRM texture
        try:
            # Generate PRM texture (keep in Blender, don't save to file)
            prm_image = create_prm_from_material(material, output_path=None, bake_size=1024)
            
            # Get the sub_matl_data and assign to Texture6 if it exists
            if hasattr(material, 'sub_matl_data'):
                sub_matl_data = material.sub_matl_data
                texture6 = sub_matl_data.textures.get(ParamId.Texture6.name)
                if texture6:
                    texture6.image = prm_image
                    self.report({'INFO'}, f"PRM texture generated and assigned to Texture6 for material '{material.name}'")
                else:
                    self.report({'WARNING'}, f"Material '{material.name}' doesn't have a Texture6 slot to assign PRM to")
            else:
                self.report({'WARNING'}, f"Material '{material.name}' doesn't have Ultimate material data")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to generate PRM texture: {str(e)}")
            
        return {'FINISHED'} 

class SUB_OP_copy_from_ult_material(Operator):
    bl_idname = 'sub.copy_from_ult_material'
    bl_label = 'Copy From Other Material'

    def execute(self, context):
        return {'FINISHED'} 
