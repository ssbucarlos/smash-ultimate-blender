import bpy
import mathutils
from mathutils import Vector, Matrix
import math

# Function to invoke the position matching dialog that can be imported by other scripts
def invoke_position_match_dialog():
    bpy.ops.sub.fk_to_ik_transfer('INVOKE_DEFAULT')

class SUB_OP_fk_to_ik_transfer(bpy.types.Operator):
    """Perfectly positions IK controls to match the FK bone positions"""
    bl_idname = "sub.fk_to_ik_transfer"
    bl_label = "Position IK Controls"
    bl_options = {'REGISTER', 'UNDO'}
    
    entire_animation: bpy.props.BoolProperty(
        name="Entire Animation",
        description="Apply to the entire animation instead of just the current frame",
        default=False
    )
    
    auto_keyframe: bpy.props.BoolProperty(
        name="Auto Keyframe",
        description="Automatically insert keyframes when applying to the entire animation",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return (context.object and 
                context.object.type == 'ARMATURE' and 
                context.mode == 'POSE')

    def process_frame(self, context):
        armature_object = context.object
        armature = armature_object.data
        transfer_count = 0
        
        # Store all constraints states and disable them
        constraint_states = {}
        for pose_bone in armature_object.pose.bones:
            for i, constraint in enumerate(pose_bone.constraints):
                constraint_key = (pose_bone.name, i)
                constraint_states[constraint_key] = constraint.mute
                constraint.mute = True
        
        # Update the view layer to see the pure FK pose
        context.view_layer.update()
        
        # Track bones that need keyframes
        bones_to_keyframe = []
        
        # Process arms and legs with IK
        for side in ["L", "R"]:
            # -- LEG CHAIN --
            leg_bone = armature_object.pose.bones.get(f"Leg{side}")
            knee_bone = armature_object.pose.bones.get(f"Knee{side}")
            foot_bone = armature_object.pose.bones.get(f"Foot{side}")
            foot_ik_bone = armature_object.pose.bones.get(f"FootIK{side}")
            knee_ik_bone = armature_object.pose.bones.get(f"KneeIK{side}")
            
            if all([leg_bone, knee_bone, foot_bone, foot_ik_bone, knee_ik_bone]):
                # Get world space positions
                leg_pos = leg_bone.matrix.to_translation()
                knee_pos = knee_bone.matrix.to_translation()
                foot_pos = foot_bone.matrix.to_translation()
                
                # Position foot IK at exact foot position with rotation
                foot_ik_bone.matrix = foot_bone.matrix.copy()
                
                # Calculate knee pole target position
                # Vector from leg to foot (IK chain direction)
                leg_to_foot = foot_pos - leg_pos
                leg_to_foot.normalize()
                
                # Projected knee position onto leg-foot line
                knee_proj = leg_pos + leg_to_foot * leg_to_foot.dot(knee_pos - leg_pos)
                
                # Vector from projected knee to actual knee (bend direction)
                pole_dir = knee_pos - knee_proj
                
                # If knee is almost perfectly straight, use a default direction
                if pole_dir.length < 0.001:
                    # Use a vector pointing backward for legs
                    pole_dir = Vector((0, -1, 0))
                else:
                    pole_dir.normalize()
                    
                # Scale the vector and position the pole target
                pole_distance = 4.0
                knee_ik_bone.matrix = Matrix.Translation(knee_pos + pole_dir * pole_distance)
                
                # Add to keyframing list
                bones_to_keyframe.append(foot_ik_bone)
                bones_to_keyframe.append(knee_ik_bone)
                
                transfer_count += 1
                
            # -- ARM CHAIN --
            shoulder_bone = armature_object.pose.bones.get(f"Shoulder{side}")
            arm_bone = armature_object.pose.bones.get(f"Arm{side}")
            hand_bone = armature_object.pose.bones.get(f"Hand{side}")
            hand_ik_bone = armature_object.pose.bones.get(f"HandIK{side}")
            arm_ik_bone = armature_object.pose.bones.get(f"ArmIK{side}")
            
            if all([arm_bone, hand_bone, hand_ik_bone, arm_ik_bone]):
                # Get world space positions
                if shoulder_bone:
                    shoulder_pos = shoulder_bone.matrix.to_translation()
                else:
                    # Fake a shoulder position if none exists
                    shoulder_dir = arm_bone.matrix.to_translation() - hand_bone.matrix.to_translation()
                    shoulder_dir.normalize()
                    shoulder_pos = arm_bone.matrix.to_translation() + shoulder_dir * 1.0
                
                arm_pos = arm_bone.matrix.to_translation()
                hand_pos = hand_bone.matrix.to_translation()
                
                # Position hand IK at exact hand position with rotation
                hand_ik_bone.matrix = hand_bone.matrix.copy()
                
                # Calculate elbow pole target position
                # Vector from shoulder to hand (IK chain direction)
                shoulder_to_hand = hand_pos - shoulder_pos
                shoulder_to_hand.normalize()
                
                # Projected elbow position onto shoulder-hand line
                arm_proj = shoulder_pos + shoulder_to_hand * shoulder_to_hand.dot(arm_pos - shoulder_pos)
                
                # Vector from projected elbow to actual elbow (bend direction)
                pole_dir = arm_pos - arm_proj
                
                # If elbow is almost perfectly straight, use a default direction
                if pole_dir.length < 0.001:
                    # Use a vector pointing forward for arms
                    pole_dir = Vector((0, 1, 0))
                else:
                    pole_dir.normalize()
                    
                # Scale the vector and position the pole target
                pole_distance = 4.0
                arm_ik_bone.matrix = Matrix.Translation(arm_pos + pole_dir * pole_distance)
                
                # Add to keyframing list
                bones_to_keyframe.append(hand_ik_bone)
                bones_to_keyframe.append(arm_ik_bone)
                
                transfer_count += 1
        
        # Update view layer before restoring constraints
        context.view_layer.update()
        
        # Restore all constraints
        for (bone_name, constraint_idx), original_state in constraint_states.items():
            bone = armature_object.pose.bones.get(bone_name)
            if bone and constraint_idx < len(bone.constraints):
                bone.constraints[constraint_idx].mute = original_state
                
                # Set ArmL pole angle to 0
                if bone_name == "ArmL" and bone.constraints[constraint_idx].type == 'IK':
                    bone.constraints[constraint_idx].pole_angle = 0.0
        
        # Auto keyframe if needed
        if self.entire_animation and self.auto_keyframe:
            current_frame = context.scene.frame_current
            for bone in bones_to_keyframe:
                bone.keyframe_insert(data_path="location", frame=current_frame)
                bone.keyframe_insert(data_path="rotation_quaternion", frame=current_frame)
                bone.keyframe_insert(data_path="rotation_euler", frame=current_frame)
                bone.keyframe_insert(data_path="scale", frame=current_frame)
        
        # Final update
        context.view_layer.update()
        
        return transfer_count

    def execute(self, context):
        if self.entire_animation:
            # Process all frames in the animation
            original_frame = context.scene.frame_current
            start_frame = context.scene.frame_start
            end_frame = context.scene.frame_end
            
            total_frames = end_frame - start_frame + 1
            total_transfers = 0
            
            # Show a progress indicator in the status bar
            context.window_manager.progress_begin(0, 100)
            
            try:
                for frame_num in range(start_frame, end_frame + 1):
                    # Update progress
                    progress = (frame_num - start_frame) / total_frames * 100
                    context.window_manager.progress_update(progress)
                    
                    # Set the current frame
                    context.scene.frame_set(frame_num)
                    
                    # Process this frame
                    transfers = self.process_frame(context)
                    total_transfers += transfers
                    
                # End progress indicator
                context.window_manager.progress_end()
                
                # Return to the original frame
                context.scene.frame_set(original_frame)
                
                # Report success
                self.report({'INFO'}, f"Successfully positioned IK controllers across {total_frames} frames")
                return {'FINISHED'}
                
            except Exception as e:
                # End progress indicator if there was an error
                context.window_manager.progress_end()
                context.scene.frame_set(original_frame)
                self.report({'ERROR'}, f"Error processing animation: {str(e)}")
                return {'CANCELLED'}
        else:
            # Process only the current frame
            transfer_count = self.process_frame(context)
            
            # Report success
            if transfer_count > 0:
                self.report({'INFO'}, f"Successfully positioned {transfer_count} IK controllers")
            else:
                self.report({'WARNING'}, "No IK controllers could be positioned")
                
            return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Match IK positions to FK bones?")
        layout.prop(self, "entire_animation")
        
        # Only show auto keyframe option if entire animation is selected
        if self.entire_animation:
            layout.prop(self, "auto_keyframe")

def register():
    bpy.utils.register_class(SUB_OP_fk_to_ik_transfer)

def unregister():
    bpy.utils.unregister_class(SUB_OP_fk_to_ik_transfer)

if __name__ == "__main__":
    register() 