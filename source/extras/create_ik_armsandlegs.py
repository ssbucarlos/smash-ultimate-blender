import bpy
import mathutils
from mathutils import Vector
import math  # Import the math module

class SUB_OP_create_ik_bones_operator(bpy.types.Operator):
    """Generate IK Bones for Arms and Legs with Automatic Setup"""
    bl_idname = "sub.create_ik_bones"
    bl_label = "Create IK Bones Arms + Legs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature_object = context.object
        
        if not armature_object or armature_object.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected. Please select an armature in Object Mode.")
            return {'CANCELLED'}

        armature = armature_object.data
        side = ("L", "R")
        length_factor = 10.0
        
        bpy.ops.object.mode_set(mode="EDIT")
        
        for i in side:
            bones = {
                "Leg": armature_object.pose.bones.get("Leg"+i),
                "Knee": armature_object.pose.bones.get("Knee"+i),
                "Foot": armature_object.pose.bones.get("Foot"+i),
                "Arm": armature_object.pose.bones.get("Arm"+i),
                "Hand": armature_object.pose.bones.get("Hand"+i)
            }
            
            if None in bones.values():
                continue
            
            new_bones = {
                "KneeIK": armature.edit_bones.new("KneeIK"+i),
                "ArmIK": armature.edit_bones.new("ArmIK"+i),
                "FootIK": armature.edit_bones.new("FootIK"+i),
                "HandIK": armature.edit_bones.new("HandIK"+i)
            }
            
            new_bones["KneeIK"].head = bones["Knee"].head.copy()
            new_bones["KneeIK"].tail = bones["Knee"].head + Vector((0, -1.5, 0))
            
            new_bones["ArmIK"].head = bones["Arm"].head.copy()
            new_bones["ArmIK"].tail = bones["Arm"].head + Vector((0, 1.5, 0))
            
            new_bones["FootIK"].head = bones["Foot"].head.copy()
            new_bones["FootIK"].tail = bones["Foot"].head + Vector((0, 0, -0.5 * length_factor))
            new_bones["FootIK"].matrix = bones["Foot"].matrix.copy()
            
            new_bones["HandIK"].head = bones["Hand"].head.copy()
            new_bones["HandIK"].tail = bones["Hand"].head + Vector((0, 0, 0.5 * length_factor))
            new_bones["HandIK"].matrix = bones["Hand"].matrix.copy()
        
        bpy.ops.object.mode_set(mode="POSE")
        
        for i in side:
            knee_pose = armature_object.pose.bones.get("Knee"+i)
            arm_pose = armature_object.pose.bones.get("Arm"+i)
            foot_pose = armature_object.pose.bones.get("Foot"+i)
            hand_pose = armature_object.pose.bones.get("Hand"+i)
            
            if knee_pose:
                knee_ik_constraint = knee_pose.constraints.new("IK")
                knee_ik_constraint.target = armature_object
                knee_ik_constraint.subtarget = "FootIK"+i
                knee_ik_constraint.pole_target = armature_object
                knee_ik_constraint.pole_subtarget = "KneeIK"+i
                knee_ik_constraint.chain_count = 2
            
            if arm_pose:
                arm_ik_constraint = arm_pose.constraints.new("IK")
                arm_ik_constraint.target = armature_object
                arm_ik_constraint.subtarget = "HandIK"+i
                arm_ik_constraint.pole_target = armature_object
                arm_ik_constraint.pole_subtarget = "ArmIK"+i
                arm_ik_constraint.chain_count = 2
                if i == "L":
                    arm_ik_constraint.pole_angle = math.radians(-90)
            
            if foot_pose:
                foot_rot_constraint = foot_pose.constraints.new("COPY_ROTATION")
                foot_rot_constraint.target = armature_object
                foot_rot_constraint.subtarget = "FootIK"+i
            
            if hand_pose:
                hand_rot_constraint = hand_pose.constraints.new("COPY_ROTATION")
                hand_rot_constraint.target = armature_object
                hand_rot_constraint.subtarget = "HandIK"+i
        
        bpy.ops.object.mode_set(mode="POSE")
        
        for bone in armature.bones:
            if "IK" in bone.name:
                bone.color.palette = 'THEME01'
        
        ik_bone_collection_name = "IK Bones"
        if ik_bone_collection_name not in armature.collections:
            ik_bone_collection = armature.collections.new(name=ik_bone_collection_name)
        else:
            ik_bone_collection = armature.collections[ik_bone_collection_name]

        for bone in armature.bones:
            if "IK" in bone.name:
                ik_bone_collection.assign(bone)
        
        print("IK bones successfully created, aligned, colored red, and added to the 'IK Bones' collection.")
        return {'FINISHED'}

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