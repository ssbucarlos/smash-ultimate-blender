from bpy.types import Panel
from . import version_check

class SUB_PT_update_plugin(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Update Available!'

    @classmethod
    def poll(cls, context):
        from ...__init__ import bl_info
        current_version = bl_info['version']
        if version_check.LATEST_VERSION:
            return current_version < version_check.LATEST_VERSION
        else:
            return False
    
    def draw(self, context):
        from ...__init__ import bl_info
        layout = self.layout
        layout.use_property_split = False
        
        layout.row().label(text="An update is available!")
        layout.row().label(text="Please download it from github when you get the chance :) ")
        current_version = bl_info['version']
        layout.row().label(text=f"Current version = {current_version}")
        layout.row().label(text=f"Latest version  = {version_check.LATEST_VERSION}")
