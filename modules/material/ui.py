from bpy.types import Panel, Menu

from .operators import *
from .sub_matl_data import SUB_PG_sub_matl_data
 
class MaterialPanel(Panel):
    '''
    This class is made to avoid repeating these lines in every single panel
    '''
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    
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
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        if sub_matl_data.shader_label == "":
            return False 
        return True
    
class SUB_PT_matl_data_master(MaterialPanel):
    bl_label = "Ultimate Material Data"
    bl_idname = "SUB_PT_matl_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        if context.object.type != 'MESH':
            return False
        if context.object.active_material is None:
            return False
        return True
    
    def draw(self, context):
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        layout = self.layout
        if sub_matl_data.shader_label == "":
            row = layout.row()
            row.label(text="The current blender material is not an ultimate material!")
            row = layout.row()
            row.label(text="The blender material will be replaced with a default smash material on export")
            row = layout.row()
            row.label(text="You can alternatively choose to convert the existing material to an ultimate material.")
            row = layout.row()
            row.operator(SUB_OP_convert_blender_material.bl_idname)
            row.scale_y = 2
            row.scale_x = 2
            return
        box = layout.box()
        box.prop(sub_matl_data, "shader_label")
        box.menu(SUB_MT_material_specials.bl_idname)

class SUB_PT_matl_data_bools(MaterialPanel):
    bl_label = "Bools"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        layout = self.layout

class SUB_PT_matl_data_floats(MaterialPanel):
    bl_label = "Floats"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        layout = self.layout
        box = layout.box()
        for float in sub_matl_data.floats:
            row = box.row()
            row.prop(float, "value")

class SUB_PT_matl_data_vectors(MaterialPanel):
    bl_label = "Vectors"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        layout = self.layout
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        box = layout.box()
        for vector in sub_matl_data.vectors:
            row = box.row()
            sub_row = row.row()
            sub_row.alignment = 'LEFT'
            sub_row.label(text=vector.ui_name)
            sub_row = row.row(align=True)
            sub_row.alignment = 'EXPAND'
            sub_row.prop(vector, "value", text="")
            sub_row.prop(vector, "value", text="X", index=0)
            sub_row.prop(vector, "value", text="Y", index=1)
            sub_row.prop(vector, "value", text="Z", index=2)
            sub_row.prop(vector, "value", text="W", index=3)

class SUB_PT_matl_data_textures(MaterialPanel):
    bl_label = "Textures"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        layout = self.layout
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data

        box = layout.box()
        for texture in sub_matl_data.textures:
            tex_row = box.row()
            tex_name_subrow = tex_row.row()
            tex_name_subrow.alignment = 'EXPAND'
            if texture.image.preview is not None:
                tex_name_subrow.label(text=texture.ui_name, translate=False, icon_value=texture.image.preview.icon_id)
            else:
                tex_name_subrow.label(text=texture.ui_name, translate=False, icon="IMAGE_DATA")
            prop_subrow = tex_row.row()
            prop_subrow.alignment = 'RIGHT'
            prop_subrow.scale_x = 1.5
            prop_subrow.prop(texture, "image", text="")

class SUB_PT_matl_data_samplers(MaterialPanel):
    bl_label = "Samplers"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        layout = self.layout

class SUB_PT_matl_data_blend_states(MaterialPanel):
    bl_label = "Blend States"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        layout = self.layout

class SUB_PT_matl_data_rasterizer_states(MaterialPanel):
    bl_label = "Rasterizer States"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        layout = self.layout

class SUB_MT_material_specials(Menu):
    bl_label = "Material Specials"
    bl_idname = "SUB_MT_material_specials"

    def draw(self, context):
        layout = self.layout
        
        layout.operator(SUB_OP_change_render_pass.bl_idname, icon="RENDERLAYERS")
        layout.operator(SUB_OP_change_shader_label.bl_idname, icon="SHADERFX")


