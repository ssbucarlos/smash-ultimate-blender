import bpy
import mathutils
from mathutils import Vector
import math
from . import fk_to_ik

class SUB_OP_create_foot_ik_operator(bpy.types.Operator):
    """Generate Foot and Knee IK Bones with Constraints"""
    bl_idname = "sub.create_foot_ik"
    bl_label = "Create Foot IK Bones"
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
        
        bpy.ops.object.mode_set(mode="EDIT")
        side = ("L", "R")
        length_factor = 10.0  # Increased factor to make foot IK bones much longer

        # Add small offsets to help with IK alignment
        for i in side:
            leg_bone = armature.edit_bones.get("Leg"+i)
            knee_bone = armature.edit_bones.get("Knee"+i)
            foot_bone = armature.edit_bones.get("Foot"+i)
            
            if not knee_bone or not foot_bone or not leg_bone:
                continue
                
            # Add small offset to improve IK solving
            leg_bone.tail += Vector((0.0, -0.05, 0.0))
            knee_bone.head += Vector((0.0, -0.05, 0.0))

            knee_ik_bone = armature.edit_bones.new("KneeIK"+i)
            # Position the pole target at a fixed distance in front
            knee_ik_bone.head = Vector((knee_bone.head.x, -4.0, knee_bone.head.z))
            knee_ik_bone.tail = Vector((knee_bone.head.x, -5.5, knee_bone.head.z))

            foot_ik_bone = armature.edit_bones.new("FootIK"+i)
            foot_ik_bone.head = knee_bone.tail
            foot_ik_bone.tail = Vector((knee_bone.tail.x, knee_bone.tail.y, -2.5))
            foot_ik_bone.roll = math.radians(90.0)  # Set explicit roll value

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
