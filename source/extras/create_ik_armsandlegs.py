import bpy
import mathutils
from mathutils import Vector
import math  # Import the math module
from . import fk_to_ik

class SUB_OP_create_ik_bones_operator(bpy.types.Operator):
    """Generate IK Bones for Arms and Legs with Automatic Setup"""
    bl_idname = "sub.create_ik_bones"
    bl_label = "Create IK Bones Arms + Legs"
    bl_options = {'REGISTER', 'UNDO'}
    
    match_position: bpy.props.BoolProperty(
        name="Match IK to FK Position",
        description="Match IK bones position to FK bones after creation",
        default=True
    )

    def execute(self, context):
        armature_object = context.object
        
        if not armature_object or armature_object.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected. Please select an armature in Object Mode.")
            return {'CANCELLED'}

        armature = armature_object.data
        side = ("L", "R")
        
        bpy.ops.object.mode_set(mode="EDIT")
        
        for i in side:
            # Get edit bones
            leg_bone = armature.edit_bones.get("Leg"+i)
            knee_bone = armature.edit_bones.get("Knee"+i)
            foot_bone = armature.edit_bones.get("Foot"+i)
            shoulder_bone = armature.edit_bones.get("Shoulder"+i)
            arm_bone = armature.edit_bones.get("Arm"+i)
            hand_bone = armature.edit_bones.get("Hand"+i)
            
            # Skip if bones don't exist
            if not all([bone for bone in [leg_bone, knee_bone, foot_bone, arm_bone, hand_bone]]):
                continue
            
            # Add small offset to improve IK solving
            leg_bone.tail += Vector((0.0, -0.05, 0.0))
            knee_bone.head += Vector((0.0, -0.05, 0.0))
            if shoulder_bone:
                shoulder_bone.tail += Vector((0.0, -0.05, 0.0))
            arm_bone.head += Vector((0.0, -0.05, 0.0))
            
            # Create knee IK pole target
            knee_ik_bone = armature.edit_bones.new("KneeIK"+i)
            knee_ik_bone.head = Vector((knee_bone.head.x, -4.0, knee_bone.head.z))
            knee_ik_bone.tail = Vector((knee_bone.head.x, -5.5, knee_bone.head.z))
            
            # Create arm IK pole target
            arm_ik_bone = armature.edit_bones.new("ArmIK"+i)
            arm_ik_bone.head = Vector((arm_bone.head.x, 4.0, arm_bone.head.z))
            arm_ik_bone.tail = Vector((arm_bone.head.x, 5.5, arm_bone.head.z))
            
            # Create foot IK target
            foot_ik_bone = armature.edit_bones.new("FootIK"+i)
            foot_ik_bone.head = knee_bone.tail
            foot_ik_bone.tail = Vector((knee_bone.tail.x, knee_bone.tail.y, -2.5))
            foot_ik_bone.roll = math.radians(90.0)
            
            # Create hand IK target
            hand_ik_bone = armature.edit_bones.new("HandIK"+i)
            hand_ik_bone.head = arm_bone.tail
            hand_ik_bone.tail = Vector((arm_bone.tail.x, arm_bone.tail.y, 0.5))
            hand_ik_bone.roll = math.radians(0.0)
        
        bpy.ops.object.mode_set(mode="POSE")
        
        for i in side:
            # Get pose bones
            knee_pose = armature_object.pose.bones.get("Knee"+i)
            arm_pose = armature_object.pose.bones.get("Arm"+i)
            foot_pose = armature_object.pose.bones.get("Foot"+i)
            hand_pose = armature_object.pose.bones.get("Hand"+i)
            
            # Setup knee IK constraint
            if knee_pose:
                knee_ik_constraint = knee_pose.constraints.new("IK")
                knee_ik_constraint.target = armature_object
                knee_ik_constraint.subtarget = "FootIK"+i
                knee_ik_constraint.pole_target = armature_object
                knee_ik_constraint.pole_subtarget = "KneeIK"+i
                knee_ik_constraint.chain_count = 2
            
            # Setup arm IK constraint
            if arm_pose:
                arm_ik_constraint = arm_pose.constraints.new("IK")
                arm_ik_constraint.target = armature_object
                arm_ik_constraint.subtarget = "HandIK"+i
                arm_ik_constraint.pole_target = armature_object
                arm_ik_constraint.pole_subtarget = "ArmIK"+i
                arm_ik_constraint.chain_count = 2
                if i == "L":
                    arm_ik_constraint.pole_angle = math.radians(-90)
            
            # Setup foot copy rotation constraint
            if foot_pose:
                foot_rot_constraint = foot_pose.constraints.new("COPY_ROTATION")
                foot_rot_constraint.target = armature_object
                foot_rot_constraint.subtarget = "FootIK"+i
            
            # Setup hand copy rotation constraint
            if hand_pose:
                hand_rot_constraint = hand_pose.constraints.new("COPY_ROTATION")
                hand_rot_constraint.target = armature_object
                hand_rot_constraint.subtarget = "HandIK"+i
        
        # Color IK bones red
        bpy.ops.object.mode_set(mode="POSE")
        for bone in armature.bones:
            if "IK" in bone.name:
                bone.color.palette = 'THEME01'
        
        # Create and assign bones to IK collection
        ik_bone_collection_name = "IK Bones"
        if ik_bone_collection_name not in armature.collections:
            ik_bone_collection = armature.collections.new(name=ik_bone_collection_name)
        else:
            ik_bone_collection = armature.collections[ik_bone_collection_name]

        for bone in armature.bones:
            if "IK" in bone.name:
                ik_bone_collection.assign(bone)
        
        self.report({'INFO'}, "IK bones successfully created, aligned, colored red, and added to the 'IK Bones' collection.")
        
        # Prompt for position matching if requested
        if self.match_position:
            fk_to_ik.invoke_position_match_dialog()
            
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "match_position")

class SUB_PT_ik_bones_panel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport"""
    bl_label = "IK Bone Generator"
    bl_idname = "SUB_PT_ik_bones_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IK Bones'

    def draw(self, context):
        layout = self.layout
        layout.operator("sub.create_ik_bones", text="Generate IK Bones")


def register():
    bpy.utils.register_class(SUB_OP_create_ik_bones_operator)
    bpy.utils.register_class(SUB_PT_ik_bones_panel)

def unregister():
    bpy.utils.unregister_class(SUB_OP_create_ik_bones_operator)
    bpy.utils.unregister_class(SUB_PT_ik_bones_panel)

if __name__ == "__main__":
    register()