import bpy
import os
import json
import math
from pathlib import Path
from bpy.types import Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty
from mathutils import Matrix, Quaternion, Vector

from ...dependencies import ssbh_data_py
from ..model.import_model import get_blender_transform
from ..anim.import_anim import get_raw_matrix, apply_transform_flags

class SUB_OP_store_idle_pose(Operator):
    bl_idname = "sub.store_idle_pose"
    bl_label = "Store Idle Pose"
    bl_description = "Store the first frame of an idle animation for later use"
    bl_options = {'REGISTER', 'UNDO'}
    
    filter_glob: StringProperty(
        default='*.nuanmb',
        options={'HIDDEN'}
    )
    filepath: StringProperty(subtype="FILE_PATH")
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' or context.mode == 'OBJECT') and context.active_object and context.active_object.type == 'ARMATURE'
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        armature = context.active_object
        
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}
        
        # Store the filepath to access it later
        context.scene["idle_pose_filepath"] = self.filepath
        
        try:
            # Read the animation data
            ssbh_anim_data = ssbh_data_py.anim_data.read_anim(self.filepath)
            
            # Get the transform group
            transform_group = None
            for group in ssbh_anim_data.groups:
                if group.group_type.name == 'Transform':
                    transform_group = group
                    break
            
            if not transform_group:
                self.report({'ERROR'}, "No transform data found in animation")
                return {'CANCELLED'}
            
            # Store first frame pose data in scene properties
            pose_data = {}
            
            for node in transform_group.nodes:
                # Check if the bone exists in the armature
                if node.name in armature.pose.bones:
                    # Only process if there are values (should always be true)
                    if node.tracks and len(node.tracks) > 0 and len(node.tracks[0].values) > 0:
                        # Get the first frame's data
                        track = node.tracks[0]
                        
                        if len(track.values) > 0:
                            transform = track.values[0]
                            
                            # Store the serializable data
                            transform_data = {
                                "scale": [transform.scale[0], transform.scale[1], transform.scale[2]],
                                "rotation": [transform.rotation[0], transform.rotation[1], transform.rotation[2], transform.rotation[3]],
                                "translation": [transform.translation[0], transform.translation[1], transform.translation[2]],
                                "flags": {
                                    "override_translation": track.transform_flags.override_translation,
                                    "override_rotation": track.transform_flags.override_rotation,
                                    "override_scale": track.transform_flags.override_scale,
                                    "compensate_scale": track.compensate_scale
                                }
                            }
                            
                            # Store the data
                            pose_data[node.name] = transform_data
            
            # Store the pose data in a custom property as a JSON string
            context.scene["idle_pose_data"] = json.dumps(pose_data)
            
            # Store animation name for display
            context.scene["idle_pose_name"] = Path(self.filepath).stem
            
            self.report({'INFO'}, f"Successfully stored idle pose from {Path(self.filepath).name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error reading animation file: {str(e)}")
            return {'CANCELLED'}


class SUB_OP_apply_idle_pose(Operator):
    bl_idname = "sub.apply_idle_pose"
    bl_label = "Apply Idle Pose"
    bl_description = "Apply the stored idle pose to the current frame"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' or context.mode == 'OBJECT') and \
               context.active_object and context.active_object.type == 'ARMATURE' and \
               "idle_pose_data" in context.scene
    
    def execute(self, context):
        armature = context.active_object
        current_frame = context.scene.frame_current
        
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}
        
        if "idle_pose_data" not in context.scene:
            self.report({'ERROR'}, "No idle pose data stored. Please store an idle pose first.")
            return {'CANCELLED'}
        
        try:
            # Prepare bone hierarchy order to process parent bones before their children
            from ..anim.import_anim import get_heirarchy_order
            reordered_bones = get_heirarchy_order(list(armature.pose.bones))
            
            # Get the stored pose data
            pose_data_str = context.scene["idle_pose_data"]
            pose_data = json.loads(pose_data_str)
            
            # Create a mapping for quick access to stored node data
            bone_to_node_data = {}
            for bone in armature.pose.bones:
                if bone.name in pose_data:
                    bone_to_node_data[bone] = pose_data[bone.name]
            
            # Process bones in hierarchy order
            for bone in reordered_bones:
                if bone not in bone_to_node_data:
                    continue
                    
                node_data = bone_to_node_data[bone]
                
                # Create transform flags
                flags = ssbh_data_py.anim_data.TransformFlags()
                flags.override_translation = node_data["flags"]["override_translation"]
                flags.override_rotation = node_data["flags"]["override_rotation"] 
                flags.override_scale = node_data["flags"]["override_scale"]
                
                # Create Transform
                transform = ssbh_data_py.anim_data.Transform(
                    node_data["scale"],
                    node_data["rotation"],
                    node_data["translation"]
                )
                
                # Set bone transformation based on imported data
                if bone.parent is None:
                    # Root bone handling similar to import_model_anim
                    y_up_to_z_up = Matrix.Rotation(math.radians(90), 4, 'X')
                    x_major_to_y_major = Matrix.Rotation(math.radians(-90), 4, 'Z')
                    
                    # Create transform matrix
                    translation = Vector(transform.translation)
                    tm = Matrix.Translation(translation)
                    
                    rotation = Quaternion([transform.rotation[3], transform.rotation[0], 
                                          transform.rotation[1], transform.rotation[2]])
                    rm = Matrix.Rotation(rotation.angle, 4, rotation.axis)
                    
                    scale = Vector(transform.scale)
                    sm = Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
                    
                    raw_matrix = tm @ rm @ sm
                    
                    bone.matrix = y_up_to_z_up @ raw_matrix @ x_major_to_y_major
                else:
                    # Non-root bones
                    # Create transform matrix
                    translation = Vector(transform.translation)
                    tm = Matrix.Translation(translation)
                    
                    rotation = Quaternion([transform.rotation[3], transform.rotation[0], 
                                          transform.rotation[1], transform.rotation[2]])
                    rm = Matrix.Rotation(rotation.angle, 4, rotation.axis)
                    
                    scale = Vector(transform.scale)
                    sm = Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
                    
                    raw_matrix = tm @ rm @ sm
                    
                    # Apply to bone similar to import_model_anim
                    bone.matrix = bone.parent.matrix @ get_blender_transform(raw_matrix).transposed()
                
                # Always keyframe all transform properties to ensure they're saved
                # Ensure keyframe insertion regardless of transform flags
                bone.keyframe_insert(data_path="location", frame=current_frame)
                
                if bone.rotation_mode == 'QUATERNION':
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=current_frame)
                else:
                    bone.keyframe_insert(data_path="rotation_euler", frame=current_frame)
                
                bone.keyframe_insert(data_path="scale", frame=current_frame)
            
            # Update the view
            for area in context.screen.areas:
                area.tag_redraw()
            
            self.report({'INFO'}, f"Applied idle pose to frame {current_frame}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error applying idle pose: {str(e)}")
            return {'CANCELLED'} 