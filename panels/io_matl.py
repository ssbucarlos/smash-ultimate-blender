import bpy

class MaterialPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Material Stuff'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        
        row = layout.row(align=True)
        row.label(text='Select ssbh_lib_json.exe')
