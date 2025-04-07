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
class SUB_OP_convert_blender_material(Operator):
    bl_idname = 'sub.convert_blender_material'
    bl_label = 'Convert Blender Material (Creates PRM, uses existing normal)'
    bl_options = {'REGISTER', 'INTERNAL'}
    
    bake_size: bpy.props.IntProperty(
        name="Texture Size",
        description="Size of the generated PRM texture (width and height)",
        default=1024,
        min=64,
        max=8192,
        step=1,
        subtype='PIXEL'
    )
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Warning: Creating textures is resource-intensive.", icon='ERROR')
        layout.label(text="Larger textures require more memory and time.")
        layout.separator()
        
        # Display requirements
        box = layout.box()
        box.label(text="Requirements:", icon='INFO')
        box.label(text="• Cycles render engine must be enabled")
        box.label(text="• GPU acceleration recommended for speed")
        
        # Display the custom size input field
        layout.separator()
        layout.prop(self, "bake_size")
    
    def execute(self, context):
        rename_mesh_attributes_of_meshes_using_material(self, context.object.active_material)
        convert_blender_material(self, context.object.active_material, self.bake_size)
        return {'FINISHED'} 
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

class SUB_OP_convert_blender_material_no_textures(Operator):
    bl_idname = 'sub.convert_blender_material_no_textures'
    bl_label = 'Convert Blender Material (Diffuse only)'

    def execute(self, context):
        rename_mesh_attributes_of_meshes_using_material(self, context.object.active_material)
        # Import the original implementation without texture creation
        from .convert_blender_material_original import convert_blender_material_original
        convert_blender_material_original(self, context.object.active_material)
        return {'FINISHED'} 

class SUB_OP_set_texture_size(Operator):
    bl_idname = 'sub.set_texture_size'
    bl_label = 'Set Texture Size'
    bl_options = {'INTERNAL'}
    
    size: bpy.props.IntProperty(default=1024)
    operator_id: bpy.props.StringProperty(default="sub.convert_blender_material")
    
    def execute(self, context):
        # Find the active operator and set its size
        if hasattr(context, 'window_manager'):
            for area in context.screen.areas:
                if area.type == 'PROPERTIES':
                    for space in area.spaces:
                        if space.type == 'PROPERTIES':
                            for region in area.regions:
                                if region.type == 'WINDOW':
                                    override = context.copy()
                                    override['area'] = area
                                    override['region'] = region
                                    override['space_data'] = space
                                    bpy.context.window_manager.operator_properties_last(self.operator_id).bake_size = self.size
        return {'FINISHED'}

class SUB_OP_copy_from_ult_material(Operator):
    bl_idname = 'sub.copy_from_ult_material'
    bl_label = 'Copy From Other Material'

    def execute(self, context):
        return {'FINISHED'} 
