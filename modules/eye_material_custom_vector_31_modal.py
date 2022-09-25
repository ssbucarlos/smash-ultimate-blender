import bpy
from mathutils import Vector
from bpy.props import FloatVectorProperty
from bpy.types import Operator

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .anim_data import SubAnimProperties, MatTrack, MatTrackProperty

class SUB_OP_eye_material_custom_vector_31_modal(Operator):
    """Edit EyeL or EyeR CustomVector31 using mouse movement"""
    bl_idname = "sub.eye_material_custom_vector_31_modal"
    bl_label = "Eye Material Custom Vector 31 Modal Operator"

    offset: FloatVectorProperty(
        name="Offset",
        size=3,
    )

    def execute(self, context):
        v3d = context.space_data
        rv3d = v3d.region_3d

        rv3d.view_location = self._initial_location + Vector(self.offset)

    def modal(self, context, event):
        v3d = context.space_data
        rv3d = v3d.region_3d
        
        if context.object.type == 'ARMATURE':
            sap: SubAnimProperties = context.object.data.sub_anim_properties
            if self.target_eye == 'LEFT':
                eye_l: MatTrack = sap.mat_tracks.get('EyeL')
                if eye_l: 
                    cv31: MatTrackProperty = eye_l.properties.get('CustomVector31')
                    if not cv31:
                        context.area.header_text_set('No CustomVector31 for EyeL')
                        return {'RUNNING_MODAL'}
                else:
                    context.area.header_text_set(f"No EyeL Material")
                    return {'RUNNING_MODAL'}
            elif self.target_eye == 'RIGHT':
                eye_r: MatTrack = sap.mat_tracks.get('EyeR')
                if eye_r:
                    cv31: MatTrackProperty = eye_r.properties.get('CustomVector31')
                    if not cv31:
                        context.area.header_text_set('No CustomVector31 for EyeR')
                        return {'RUNNING_MODAL'}
                else:
                    context.area.header_text_set(f"No EyeR Material")
                    return {'RUNNING_MODAL'}                    
        else:
            return {'CANCELLED'}
        
        if event.type == 'MOUSEMOVE':
            self.offset = (self._initial_mouse - Vector((event.mouse_x, event.mouse_y, 0.0))) * 0.02
            #self.execute(context)
            
            offset_x = (self._initial_mouse[0] - event.mouse_x) * 0.002
            offset_y = (self._initial_mouse[1] - event.mouse_y) * 0.002
            if self.target_eye == 'LEFT':
                cv31.custom_vector[2] = self._initial_cv31[2] - offset_x
                cv31.custom_vector[3] = self._initial_cv31[3] - offset_y
            elif self.target_eye == 'RIGHT':
                cv31.custom_vector[2] = self._initial_cv31[2] + offset_x
                cv31.custom_vector[3] = self._initial_cv31[3] - offset_y                

        elif event.type == 'LEFTMOUSE':
            context.area.header_text_set(None)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            rv3d.view_location = self._initial_location
            if context.object.type == 'ARMATURE':
                sap = context.object.data.sub_anim_properties
                eye_l = sap.mat_tracks.get('EyeL')
                if eye_l: 
                    cv31 = eye_l.properties.get('CustomVector31')
                    if cv31:
                        cv31.custom_vector[2] = self._initial_cv31[2]
                        cv31.custom_vector[3] = self._initial_cv31[3]
            context.area.header_text_set(None)
            return {'CANCELLED'}
        elif event.type == 'R':
            self.target_eye = 'RIGHT'
        elif event.type == 'L':
            self.target_eye = 'LEFT'
            
        context.area.header_text_set(f"Target Eye={self.target_eye}, CustomVector31: z={cv31.custom_vector[2]} w={cv31.custom_vector[3]}")
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            v3d = context.space_data
            rv3d = v3d.region_3d

            if rv3d.view_perspective == 'CAMERA':
                rv3d.view_perspective = 'PERSP'

            self._initial_mouse = Vector((event.mouse_x, event.mouse_y, 0.0))
            self._initial_location = rv3d.view_location.copy()
            self.target_eye = 'LEFT'
            if context.object.type == 'ARMATURE':
                sap = context.object.data.sub_anim_properties
                eye_l = sap.mat_tracks.get('EyeL')
                if eye_l: 
                    cv31 = eye_l.properties.get('CustomVector31')
                    if cv31:
                        self._initial_cv31 = [cv31.custom_vector[0], cv31.custom_vector[1], cv31.custom_vector[2], cv31.custom_vector[3]]
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}