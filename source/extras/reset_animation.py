import bpy
from bpy.types import Operator
from bpy.props import BoolProperty
import logging

# Set up logging
logger = logging.getLogger(__name__)

class SUB_OT_reset_bone_locations(Operator):
    """Reset bone locations and scales to 0/1 at frame 1 and delete their keyframes, except for hip/trans/rot bones"""
    bl_idname = "sub.reset_bone_locations"
    bl_label = "Reset Bone Locations"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Check if we have an armature selected
        if not context.object or context.object.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select an armature")
            return {'CANCELLED'}
        
        armature = context.object
        
        # Check if the armature has an action
        if not armature.animation_data or not armature.animation_data.action:
            self.report({'ERROR'}, "Armature must have an action/animation")
            return {'CANCELLED'}
        
        # Store original mode to restore later
        original_mode = context.mode
        
        # Switch to pose mode if not already
        if original_mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
        
        # Store original frame
        original_frame = context.scene.frame_current
        
        # Jump to frame 1
        context.scene.frame_set(1)
        
        # Get action
        action = armature.animation_data.action
        
        # Identify excluded bones (hip, trans, rot)
        excluded_bones = []
        for bone in armature.pose.bones:
            if any(keyword in bone.name.lower() for keyword in ['hip', 'trans', 'rot']):
                excluded_bones.append(bone.name)
                print(f"Excluding bone from reset: {bone.name}")
        
        # Find all location and scale fcurves
        location_fcurves = []
        scale_fcurves = []
        
        for fcurve in action.fcurves:
            # Parse the data path to get bone name
            # Format: pose.bones["BoneName"].location[0]
            if "pose.bones" not in fcurve.data_path:
                continue
                
            # Extract bone name
            bone_name = fcurve.data_path.split('"')[1]
            
            # Skip excluded bones
            if bone_name in excluded_bones:
                continue
            
            # Categorize fcurve
            if ".location" in fcurve.data_path:
                location_fcurves.append(fcurve)
            elif ".scale" in fcurve.data_path:
                scale_fcurves.append(fcurve)
        
        # Reset location to 0 and scale to 1 for all bones except excluded ones
        bones_affected = set()
        
        for bone in armature.pose.bones:
            if bone.name in excluded_bones:
                continue
                
            # Reset location to 0
            bone.location = (0, 0, 0)
            
            # Reset scale to 1
            bone.scale = (1, 1, 1)
            
            bones_affected.add(bone.name)
        
        # Insert keyframes at frame 1 for all affected bones
        for bone_name in bones_affected:
            bone = armature.pose.bones[bone_name]
            bone.keyframe_insert(data_path="location", frame=1)
            bone.keyframe_insert(data_path="scale", frame=1)
        
        # Delete all other keyframes for location and scale fcurves
        fcurves_to_clear = location_fcurves + scale_fcurves
            
        keyframes_removed = 0
        for fcurve in fcurves_to_clear:
            # Keep only keyframe at frame 1, delete all others
            to_remove = []
            for i, keyframe in enumerate(fcurve.keyframe_points):
                if abs(keyframe.co[0] - 1.0) > 0.01:  # If not frame 1 (allowing small float difference)
                    to_remove.append(i)
            
            # Remove keyframes in reverse order to avoid index shifting
            for i in reversed(to_remove):
                fcurve.keyframe_points.remove(fcurve.keyframe_points[i])
                keyframes_removed += 1
        
        # Update the view
        context.scene.frame_set(original_frame)
        
        # Force a redraw
        for area in context.screen.areas:
            if area.type in ['DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'TIMELINE']:
                area.tag_redraw()
        
        # Restore original mode
        if original_mode != 'POSE':
            bpy.ops.object.mode_set(mode=original_mode.replace('_', ' ').title())
        
        self.report({'INFO'}, f"Reset {len(bones_affected)} bones to zero location and default scale at frame 1. Removed {keyframes_removed} keyframes.")
        return {'FINISHED'}

def draw_reset_animation_button(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.operator("sub.reset_bone_locations", text="Reset Bone Locations")

# List of classes to register
classes = (
    SUB_OT_reset_bone_locations,
)

def register():
    logger.info("Registering reset_animation.py classes")
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            logger.info(f"Successfully registered {cls.__name__}")
        except Exception as e:
            logger.error(f"Failed to register {cls.__name__}: {str(e)}")

def unregister():
    logger.info("Unregistering reset_animation.py classes")
    for cls in reversed(classes):
        if hasattr(bpy.types, cls.__name__):
            try:
                bpy.utils.unregister_class(cls)
                logger.info(f"Successfully unregistered {cls.__name__}")
            except Exception as e:
                logger.error(f"Failed to unregister {cls.__name__}: {str(e)}")

# Test if registration works when this script is run directly
if __name__ == "__main__":
    register() 