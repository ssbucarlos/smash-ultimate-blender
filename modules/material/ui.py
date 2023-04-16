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
        box.prop(sub_matl_data, "shader_label", emboss=False)
        box.menu(SUB_MT_material_specials.bl_idname)

class SUB_PT_matl_data_bools(MaterialPanel):
    bl_label = "Bools"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        layout = self.layout
        box = layout.box()
        for matl_bool in sub_matl_data.bools:
            row = box.row()
            row.alignment = 'EXPAND'
            row.label(text=matl_bool.ui_name)
            row = row.row()
            row.alignment = 'RIGHT'
            row.prop(matl_bool, "value", text="")


class SUB_PT_matl_data_floats(MaterialPanel):
    bl_label = "Floats"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        layout = self.layout
        box = layout.box()
        for matl_float in sub_matl_data.floats:
            row = box.row()
            row.alignment = 'EXPAND'
            row.label(text=matl_float.ui_name)
            row = row.row()
            row.alignment = 'RIGHT'
            row.prop(matl_float, "value", text="")
            
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
            sub_row.alignment = 'EXPAND'
            sub_row.label(text=vector.ui_name)
            sub_row = row.row(align=True)
            sub_row.alignment = 'RIGHT'
            sub_row.prop(vector, "value", text="")
            sub_row.prop(vector, "value", text="", index=0)
            sub_row.prop(vector, "value", text="", index=1)
            sub_row.prop(vector, "value", text="", index=2)
            sub_row.prop(vector, "value", text="", index=3)

class SUB_PT_matl_data_textures(MaterialPanel):
    bl_label = "Textures"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        layout = self.layout

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
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        layout = self.layout

        for sampler in sub_matl_data.samplers:
            box = layout.box()
            row = box.row()
            row.label(text=sampler.ui_name)
            row = box.row()
            cf = row.column_flow(columns=4)
            cf.label(text='Wrap Settings')
            cf.separator()
            cf.label(text='Filter Settings')
            cf.separator()
            cf.label(text='Other Settings')
            cf.prop(sampler, 'wrap_s')
            cf.separator()
            cf.prop(sampler, 'min_filter')
            cf.separator()
            sub_row = cf.row() # Prevents border color from taking up 2 rows
            sub_row.prop(sampler, 'border_color')
            cf.prop(sampler, 'wrap_t')
            cf.separator()
            cf.prop(sampler, 'mag_filter')
            cf.separator()
            cf.prop(sampler, 'lod_bias')
            cf.prop(sampler, 'wrap_r')
            cf.separator()
            cf.prop(sampler, 'anisotropic_filtering')
            cf.separator()
            cf.prop(sampler, 'max_anisotropy')

class SUB_PT_matl_data_blend_states(MaterialPanel):
    bl_label = "Blend States"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        layout = self.layout

        for blend_state in sub_matl_data.blend_states:
            box = layout.box()
            row = box.row()
            row.label(text=blend_state.ui_name)
            row = box.row()
            row.label(text="Source Color")
            row.prop(blend_state, "source_color", text="")
            row = box.row()
            row.label(text='Destination Color')
            row.prop(blend_state, "destination_color", text="")
            row = box.row()
            row.label(text="Alpha Sample To Coverage")
            row.prop(blend_state, "alpha_sample_to_coverage", text="")


class SUB_PT_matl_data_rasterizer_states(MaterialPanel):
    bl_label = "Rasterizer States"
    bl_parent_id = SUB_PT_matl_data_master.bl_idname

    def draw(self, context):
        sub_matl_data: SUB_PG_sub_matl_data = context.object.active_material.sub_matl_data
        layout = self.layout

        for rasterizer_state in sub_matl_data.rasterizer_states:
            box = layout.box()
            row = box.row()
            row.label(text=rasterizer_state.ui_name)
            row = box.row()
            row.label(text="Cull Mode")
            row.prop(rasterizer_state, "cull_mode", text="")
            row = box.row()
            row.label(text='Depth Bias')
            row.prop(rasterizer_state, "depth_bias", text="")
            row = box.row()
            row.label(text="Fill Mode")
            row.prop(rasterizer_state, "fill_mode", text="")


class SUB_MT_material_specials(Menu):
    bl_label = "Material Specials"
    bl_idname = "SUB_MT_material_specials"

    def draw(self, context):
        layout = self.layout
        
        layout.operator(SUB_OP_change_render_pass.bl_idname, icon="RENDERLAYERS")
        layout.operator(SUB_OP_create_sub_matl_data_from_shader_label.bl_idname, icon="SHADERFX")


