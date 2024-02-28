import bpy
from mathutils import Vector
from bpy.props import FloatVectorProperty
from bpy.types import Operator
from ..modules.anim_data import SUB_PG_mat_track_property

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..modules.anim_data import SUB_PG_sub_anim_data, SUB_PG_mat_track, SUB_PG_mat_track_property
    from ..properties import SubSceneProperties

class SUB_OP_eye_material_custom_vector_31_modal(Operator):
    """Edit EyeL or EyeR CustomVector31 using mouse movement"""
    bl_idname = "sub.eye_material_custom_vector_31_modal"
    bl_label = "Eye Material Custom Vector 31 Modal Operator"

    offset: FloatVectorProperty(
        name="Offset",
        size=3,
    )

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        return context.object.type == 'ARMATURE'

    def execute(self, context):
        pass

    def modal(self, context, event):
        v3d = context.space_data
        rv3d = v3d.region_3d
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        if event.type == 'MOUSEMOVE':
            offset_x = (self.temp_mouse[0] - event.mouse_x) * 0.002
            offset_y = (self.temp_mouse[1] - event.mouse_y) * 0.002
            if self.target_eye in {'LEFT', 'BOTH'}:
                if self.cv31_l:
                    self.cv31_l.custom_vector[2] = self.temp_cv31_l[2] - offset_x
                    self.cv31_l.custom_vector[3] = self.temp_cv31_l[3] - offset_y
            if self.target_eye in {'RIGHT', 'BOTH'}:
                if self.cv31_r:
                    self.cv31_r.custom_vector[2] = self.temp_cv31_r[2] + offset_x
                    self.cv31_r.custom_vector[3] = self.temp_cv31_r[3] - offset_y  
        elif event.type == 'LEFTMOUSE':
            ssp.cv31_modal_last_mode = self.target_eye
            if ssp.cv31_modal_use_auto_keyframe:
                insert_cv31_keyframes(context.object, self.cv31_l, self.cv31_r)
            context.area.header_text_set(None)
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.cv31_l:
                self.cv31_l.custom_vector[2] = self._initial_cv31_l[2]
                self.cv31_l.custom_vector[3] = self._initial_cv31_l[3]
            if self.cv31_r:
                self.cv31_r.custom_vector[2] = self._initial_cv31_r[2]
                self.cv31_r.custom_vector[3] = self._initial_cv31_r[3]
            context.area.header_text_set(None)
            return {'CANCELLED'}
        elif event.type == 'R':
            self.target_eye = 'RIGHT'
        elif event.type == 'L':
            self.target_eye = 'LEFT'
        elif event.type == 'B':
            self.target_eye = 'BOTH'
        elif event.type == 'A' and event.value == 'PRESS':
            ssp.cv31_modal_use_auto_keyframe = not ssp.cv31_modal_use_auto_keyframe
        elif event.type == 'U' and event.value == 'PRESS':
            ssp.cv31_modal_reset_on_mode_switch = not ssp.cv31_modal_reset_on_mode_switch
        
        if event.type in {'R', 'L', 'B'}:
            self.temp_mouse = Vector((event.mouse_x, event.mouse_y, 0.0))
            if ssp.cv31_modal_reset_on_mode_switch:
                if self.cv31_l:
                    self.cv31_l.custom_vector[2] = self._initial_cv31_l[2]
                    self.cv31_l.custom_vector[3] = self._initial_cv31_l[3]
                if self.cv31_r:
                    self.cv31_r.custom_vector[2] = self._initial_cv31_r[2]
                    self.cv31_r.custom_vector[3] = self._initial_cv31_r[3]
            else:
                if self.cv31_l:
                    self.temp_cv31_l[2] = self.cv31_l.custom_vector[2]
                    self.temp_cv31_l[3] = self.cv31_l.custom_vector[3]
                if self.cv31_r:
                    self.temp_cv31_r[2] = self.cv31_r.custom_vector[2]
                    self.temp_cv31_r[3] = self.cv31_r.custom_vector[3]

        text  = f'Current Eye Mode: {self.target_eye} (R=Right L=Left B=Both),'
        text += f' Auto Keyframing: {ssp.cv31_modal_use_auto_keyframe} (A),'
        text += f' Reset On Mode Switch: {ssp.cv31_modal_reset_on_mode_switch} (U)'
        context.area.header_text_set(text)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            v3d = context.space_data
            rv3d = v3d.region_3d

            #if rv3d.view_perspective == 'CAMERA':
            #    rv3d.view_perspective = 'PERSP'

            self._initial_mouse = Vector((event.mouse_x, event.mouse_y, 0.0))
            self.temp_mouse = self._initial_mouse.copy()
            self._initial_location = rv3d.view_location.copy()
            ssp: SubSceneProperties = context.scene.sub_scene_properties
            self.target_eye = ssp.cv31_modal_last_mode

            sap: SUB_PG_sub_anim_data = context.object.data.sub_anim_properties
            eye_l = sap.mat_tracks.get('EyeL')
            if eye_l: 
                cv31_l: SUB_PG_mat_track_property = eye_l.properties.get('CustomVector31')
                if cv31_l:
                    self._initial_cv31_l = [cv31_l.custom_vector[0], cv31_l.custom_vector[1], cv31_l.custom_vector[2], cv31_l.custom_vector[3]]
                    self.temp_cv31_l = [cv31_l.custom_vector[0], cv31_l.custom_vector[1], cv31_l.custom_vector[2], cv31_l.custom_vector[3]]
                    self.cv31_l = cv31_l
            eye_r = sap.mat_tracks.get('EyeR')
            if eye_r: 
                cv31_r: SUB_PG_mat_track_property = eye_r.properties.get('CustomVector31')
                if cv31_r:
                    self._initial_cv31_r = [cv31_r.custom_vector[0], cv31_r.custom_vector[1], cv31_r.custom_vector[2], cv31_r.custom_vector[3]]
                    self.temp_cv31_r = [cv31_r.custom_vector[0], cv31_r.custom_vector[1], cv31_r.custom_vector[2], cv31_r.custom_vector[3]]
                    self.cv31_r = cv31_r                
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

def insert_cv31_keyframes(arma: bpy.types.Object, cv31_l: SUB_PG_mat_track_property, cv31_r: SUB_PG_mat_track_property):
    try:
        arma.data.animation_data.action.fcurves
    except AttributeError:
        return
    sap: SUB_PG_sub_anim_data = arma.data.sub_anim_properties
    if cv31_l:
        mat_track: SUB_PG_mat_track = sap.mat_tracks.get('EyeL')
        mat_track_index = sap.mat_tracks.find('EyeL')
        prop_index = mat_track.properties.find('CustomVector31')
        arma.data.keyframe_insert(data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].custom_vector', group=f'Material ({mat_track.name})', options={'INSERTKEY_NEEDED'})

    if cv31_r:
        mat_track: SUB_PG_mat_track = sap.mat_tracks.get('EyeR')
        mat_track_index = sap.mat_tracks.find('EyeR')
        prop_index = mat_track.properties.find('CustomVector31')
        arma.data.keyframe_insert(data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].custom_vector', group=f'Material ({mat_track.name})', options={'INSERTKEY_NEEDED'})
    