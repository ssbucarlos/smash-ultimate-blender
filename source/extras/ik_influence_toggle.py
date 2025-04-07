import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty

class SUB_OP_toggle_ik_influence(Operator):
    bl_idname = "sub.toggle_ik_influence"
    bl_label = "Toggle IK Influence"
    bl_description = "Toggle constraint influence for arms and legs"
    bl_options = {'REGISTER', 'UNDO'}
    
    influence_value: FloatProperty(
        name="Influence Value",
        description="Constraint influence (0 = off, 1 = on)",
        default=1.0,
        min=0.0,
        max=1.0
    )
    
    arms_enabled: BoolProperty(
        name="Arms",
        description="Toggle influence for arm and hand constraints",
        default=True
    )
    
    legs_enabled: BoolProperty(
        name="Legs",
        description="Toggle influence for leg and foot constraints",
        default=True
    )
    
    insert_keyframe: BoolProperty(
        name="Insert Keyframe",
        description="Insert keyframe for the influence value",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' or context.mode == 'OBJECT') and context.active_object and context.active_object.type == 'ARMATURE'
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "influence_value", slider=True)
        
        # Bone categories
        row = layout.row()
        row.prop(self, "arms_enabled")
        row.prop(self, "legs_enabled")
        
        layout.prop(self, "insert_keyframe")
    
    def execute(self, context):
        armature = context.active_object
        current_frame = context.scene.frame_current
        
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}
        
        # Lists of bone name patterns to identify different bone types
        arm_bones = ['arm', 'elbow', 'clavicle', 'shoulder', 'upperarm', 'ArmIK', 
                     'hand', 'wrist', 'finger', 'thumb', 'palm', 'HandIK']
        leg_bones = ['leg', 'knee', 'thigh', 'calf', 'shin', 'LegIK',
                     'foot', 'ankle', 'toe', 'heel', 'ball', 'FootIK']
        
        constraints_modified = 0
        modified_types = set()
        
        # Process all pose bones
        for bone in armature.pose.bones:
            # Check if the bone has relevant constraints
            for constraint in bone.constraints:
                # For IK or Copy Rotation constraints
                if constraint.type in ['IK', 'COPY_ROTATION']:
                    # Check which type of bone this is
                    is_arm_bone = any(arm_pattern.lower() in bone.name.lower() for arm_pattern in arm_bones)
                    is_leg_bone = any(leg_pattern.lower() in bone.name.lower() for leg_pattern in leg_bones)
                    
                    # Apply influence based on selection
                    should_modify = (is_arm_bone and self.arms_enabled) or \
                                   (is_leg_bone and self.legs_enabled)
                    
                    # If bone doesn't match any categories but has one of these constraints, 
                    # do a simpler check
                    if not (is_arm_bone or is_leg_bone):
                        if 'arm' in bone.name.lower() or 'hand' in bone.name.lower():
                            should_modify = self.arms_enabled
                            is_arm_bone = True
                        elif 'leg' in bone.name.lower() or 'foot' in bone.name.lower():
                            should_modify = self.legs_enabled
                            is_leg_bone = True
                    
                    if should_modify:
                        # Set the influence value
                        constraint.influence = self.influence_value
                        
                        # Insert keyframe if requested
                        if self.insert_keyframe:
                            constraint.keyframe_insert(data_path="influence", frame=current_frame)
                        
                        constraints_modified += 1
                        
                        # Track which types of bones were modified for reporting
                        if is_arm_bone: 
                            modified_types.add("arms")
                        if is_leg_bone: 
                            modified_types.add("legs")
        
        # Report the result
        if constraints_modified > 0:
            modified_types_str = ", ".join(modified_types)
            self.report({'INFO'}, f"Modified {constraints_modified} constraints on {modified_types_str} with influence {self.influence_value}")
        else:
            self.report({'WARNING'}, "No matching constraints found to modify")
        
        # Update the view
        for area in context.screen.areas:
            area.tag_redraw()
        
        return {'FINISHED'} 