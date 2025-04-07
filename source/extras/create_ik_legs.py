import bpy
import mathutils
from mathutils import Vector

class SUB_OP_create_foot_ik_operator(bpy.types.Operator):
    """Generate Foot and Knee IK Bones with Constraints"""
    bl_idname = "sub.create_foot_ik"
    bl_label = "Create Foot IK Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature_object = context.object
        
        if not armature_object or armature_object.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected. Please select an armature in Object Mode.")
            return {'CANCELLED'}

        armature = armature_object.data
        
        bpy.ops.object.mode_set(mode="EDIT")
        side = ("L", "R")
        length_factor = 10.0  # Increased factor to make foot IK bones much longer

        for i in side:
            knee_pose = armature_object.pose.bones.get("Knee"+i)
            foot_pose = armature_object.pose.bones.get("Foot"+i)
            if not knee_pose or not foot_pose:
                continue

            knee_ik_bone = armature.edit_bones.new("KneeIK"+i)
            knee_ik_bone.head = knee_pose.head.copy()
            knee_ik_bone.tail = knee_pose.head.copy() + Vector((0, -1.5, 0))

            foot_ik_bone = armature.edit_bones.new("FootIK"+i)
            foot_ik_bone.head = foot_pose.head.copy()
            foot_ik_bone.tail = foot_pose.head.copy() + Vector((0, 0, -0.5 * length_factor))
            foot_ik_bone.matrix = foot_pose.matrix.copy()

        bpy.ops.object.mode_set(mode="POSE")

        for i in side:
            knee_pose = armature_object.pose.bones.get("Knee"+i)
            foot_pose = armature_object.pose.bones.get("Foot"+i)
            if not knee_pose or not foot_pose:
                continue

            knee_ik_constraint = knee_pose.constraints.new("IK")
            knee_ik_constraint.target = armature_object
            knee_ik_constraint.subtarget = "FootIK"+i
            knee_ik_constraint.pole_target = armature_object
            knee_ik_constraint.pole_subtarget = "KneeIK"+i
            knee_ik_constraint.chain_count = 2

            foot_rot_constraint = foot_pose.constraints.new("COPY_ROTATION")
            foot_rot_constraint.target = armature_object
            foot_rot_constraint.subtarget = "FootIK"+i

        # Apply red color to all IK bones
        bpy.ops.object.mode_set(mode="POSE")
        for bone in armature.bones:
            if "IK" in bone.name:
                bone.color.palette = 'THEME01'

        # Create and assign bones to the "IK Bones" collection
        ik_bone_collection_name = "FootIK Bones"
        if ik_bone_collection_name not in armature.collections:
            ik_bone_collection = armature.collections.new(name=ik_bone_collection_name)
        else:
            ik_bone_collection = armature.collections[ik_bone_collection_name]

        for bone in armature.bones:
            if "IK" in bone.name:
                ik_bone_collection.assign(bone)

        self.report({'INFO'}, "Foot and knee IK bones successfully created and assigned.")
        return {'FINISHED'}


class SUB_PT_foot_ik_panel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport"""
    bl_label = "Foot IK Bone Generator"
    bl_idname = "SUB_PT_foot_ik_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IK Bones'

    def draw(self, context):
        layout = self.layout
        layout.operator("sub.create_foot_ik", text="Generate Foot IK Bones")


def register():
    bpy.utils.register_class(SUB_OP_create_foot_ik_operator)
    bpy.utils.register_class(SUB_PT_foot_ik_panel)


def unregister():
    bpy.utils.unregister_class(SUB_OP_create_foot_ik_operator)
    bpy.utils.unregister_class(SUB_PT_foot_ik_panel)


if __name__ == "__main__":
    register()
