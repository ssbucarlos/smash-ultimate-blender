import bpy
import mathutils
from mathutils import Vector
import math

class SUB_OP_create_arm_ik_operator(bpy.types.Operator):
    """Generate Arm and Hand IK Bones with Constraints and Coloring"""
    bl_idname = "sub.create_arm_ik"
    bl_label = "Create Arm IK Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True  # Always show the button

    def execute(self, context):
        armature_object = context.object

        if not armature_object or armature_object.type != 'ARMATURE':
            self.report({'ERROR'}, "No active armature selected")
            return {'CANCELLED'}

        armature = armature_object.data
        bpy.ops.object.mode_set(mode="EDIT")
        
        side = ("L", "R")
        length_factor = 10.0
        
        for i in side:
            arm_pose = armature_object.pose.bones.get("Arm" + i)
            hand_pose = armature_object.pose.bones.get("Hand" + i)
            
            if not arm_pose or not hand_pose:
                continue
            
            arm_ik_bone = armature.edit_bones.new("ArmIK" + i)
            arm_ik_bone.head = arm_pose.head.copy()
            arm_ik_bone.tail = arm_pose.head.copy() + Vector((0, 1.5, 0))
            
            hand_ik_bone = armature.edit_bones.new("HandIK" + i)
            hand_ik_bone.head = hand_pose.head.copy()
            hand_ik_bone.tail = hand_pose.head.copy() + Vector((0, 0, 0.5 * length_factor))
            hand_ik_bone.matrix = hand_pose.matrix.copy()
        
        bpy.ops.object.mode_set(mode="POSE")
        
        for i in side:
            arm_pose = armature_object.pose.bones.get("Arm" + i)
            hand_pose = armature_object.pose.bones.get("Hand" + i)
            
            if not arm_pose or not hand_pose:
                continue
            
            arm_ik_constraint = arm_pose.constraints.new("IK")
            arm_ik_constraint.target = armature_object
            arm_ik_constraint.subtarget = "HandIK" + i
            arm_ik_constraint.pole_target = armature_object
            arm_ik_constraint.pole_subtarget = "ArmIK" + i
            arm_ik_constraint.chain_count = 2

            if i == "L":
                arm_ik_constraint.pole_angle = math.radians(-90)
            
            hand_rot_constraint = hand_pose.constraints.new("COPY_ROTATION")
            hand_rot_constraint.target = armature_object
            hand_rot_constraint.subtarget = "HandIK" + i
        
        bpy.ops.object.mode_set(mode="POSE")
        
        for bone in armature_object.pose.bones:
            if "IK" in bone.name:
                bone.color.palette = 'THEME01'
        
        ik_bone_collection_name = "ArmsIK Bones"
        
        if ik_bone_collection_name not in armature.collections:
            ik_bone_collection = armature.collections.new(name=ik_bone_collection_name)
        else:
            ik_bone_collection = armature.collections[ik_bone_collection_name]
        
        for bone in armature.bones:
            if "IK" in bone.name:
                ik_bone_collection.assign(bone)
        
        self.report({'INFO'}, "IK bones created, colored red, and assigned to 'IK Bones' collection.")
        return {'FINISHED'}

class SUB_PT_arm_ik_panel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport"""
    bl_label = "IK Bone Generator"
    bl_idname = "SUB_PT_arm_ik_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IK Bones'

    def draw(self, context):
        layout = self.layout
        layout.operator("sub.create_arm_ik", text="Generate Arm IK Bones")


def register():
    bpy.utils.register_class(SUB_OP_create_arm_ik_operator)
    bpy.utils.register_class(SUB_PT_arm_ik_panel)

def unregister():
    bpy.utils.unregister_class(SUB_OP_create_arm_ik_operator)
    bpy.utils.unregister_class(SUB_PT_arm_ik_panel)

if __name__ == "__main__":
    register()
