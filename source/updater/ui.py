from bpy.types import Panel

class SUB_PT_update_plugin(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Update Available!'

    @classmethod
    def poll(cls, context):
        from .version_check import COMPATIBLE_UPDATE_AVAILABLE
        return COMPATIBLE_UPDATE_AVAILABLE
    
    def draw(self, context):
        from ...__init__ import bl_info
        from .version_check import LATEST_COMPATIBLE_VERSION

        layout = self.layout
        layout.use_property_split = False
        
        layout.row().label(text="An update compatible with your current blender version is available!")
        layout.row().label(text="Please download it from github when you get the chance :) ")
        current_version = bl_info['version']
        layout.row().label(text=f"Current version = {current_version}")
        layout.row().label(text=f"Latest compatible version  = {LATEST_COMPATIBLE_VERSION}")
