import bpy
from bpy.types import Operator

class SUB_OP_transfer_hip_animation(Operator):
    bl_idname = "sub.transfer_hip_animation"
    bl_label = "Transfer Hip Animation"
    bl_description = "Transfer X motion from Hip to Z of Trans bone, zero out Hip X"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' or context.mode == 'OBJECT') and context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}

        # Find hip and trans bones
        hip_bone = None
        trans_bone = None
        
        for bone in armature.pose.bones:
            if "hip" in bone.name.lower():
                hip_bone = bone
            if "trans" in bone.name.lower():
                trans_bone = bone
        
        if not hip_bone:
            self.report({'ERROR'}, "Hip bone not found in armature")
            return {'CANCELLED'}
        
        if not trans_bone:
            self.report({'ERROR'}, "Trans bone not found in armature")
            return {'CANCELLED'}

        # Get animation data
        if not armature.animation_data or not armature.animation_data.action:
            self.report({'ERROR'}, "No animation data found for armature")
            return {'CANCELLED'}
        
        action = armature.animation_data.action
        
        # Find hip X location fcurve
        hip_x_fcurve = None
        hip_path = f'pose.bones["{hip_bone.name}"].location'
        
        for fc in action.fcurves:
            if fc.data_path == hip_path and fc.array_index == 0:  # X location
                hip_x_fcurve = fc
                break
                
        if not hip_x_fcurve:
            self.report({'ERROR'}, "No X location keyframes found for Hip bone")
            return {'CANCELLED'}
        
        # Get cursor value for mirroring
        cursor_value = context.scene.cursor.location.x
        
        # Store hip X keyframes
        keyframes = []
        first_value = None
        
        for kp in hip_x_fcurve.keyframe_points:
            if first_value is None:
                first_value = kp.co[1]
            keyframes.append((kp.co[0], kp.co[1], kp.interpolation))
        
        if not keyframes:
            self.report({'ERROR'}, "No keyframes found on Hip bone X location")
            return {'CANCELLED'}
        
        # Shift values so first keyframe is at 0m
        for i in range(len(keyframes)):
            keyframes[i] = (keyframes[i][0], keyframes[i][1] - first_value, keyframes[i][2])
        
        # Create or get Trans Z fcurve
        trans_z_fcurve = None
        trans_path = f'pose.bones["{trans_bone.name}"].location'
        
        for fc in action.fcurves:
            if fc.data_path == trans_path and fc.array_index == 2:  # Z location
                trans_z_fcurve = fc
                break
        
        if not trans_z_fcurve:
            trans_z_fcurve = action.fcurves.new(trans_path, index=2)
        else:
            # Clear existing keyframes
            trans_z_fcurve.keyframe_points.clear()
        
        # Copy keyframes to Trans Z and mirror them over cursor value
        for frame, value, interpolation in keyframes:
            # Mirror value over cursor
            mirrored_value = 2 * cursor_value - value
            
            kp = trans_z_fcurve.keyframe_points.insert(frame, mirrored_value)
            kp.interpolation = interpolation
        
        # Remove hip X keyframes
        action.fcurves.remove(hip_x_fcurve)
        
        # Set hip X to 0 and keyframe it on frame 1
        hip_bone.location[0] = 0
        hip_bone.keyframe_insert(data_path="location", index=0, frame=1)
        
        # Update the view
        for area in context.screen.areas:
            if area.type == 'GRAPH_EDITOR':
                area.tag_redraw()
        
        self.report({'INFO'}, "Hip animation transferred to Trans bone Z")
        return {'FINISHED'} 