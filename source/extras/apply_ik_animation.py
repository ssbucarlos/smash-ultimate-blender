import bpy

class SUB_OP_apply_ik_animation_operator(bpy.types.Operator):
    """Bake IK Animation to Original Bones and Remove IK Bones"""
    bl_idname = "sub.apply_ik_animation"
    bl_label = "Apply IK Animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature_object = context.object
        
        if not armature_object or armature_object.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected. Please select an armature in Object Mode.")
            return {'CANCELLED'}

        # First, bake animation for all bones
        bpy.ops.object.mode_set(mode='POSE')
        
        # Select all bones before baking
        for bone in armature_object.pose.bones:
            bone.bone.select = True
            
        # Bake the animation
        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        
        bpy.ops.nla.bake(
            frame_start=frame_start, 
            frame_end=frame_end, 
            visual_keying=True,
            clear_constraints=False, 
            use_current_action=True, 
            bake_types={'POSE'}
        )
        
        # After baking, remove all constraints from original bones
        side = ("L", "R")
        for i in side:
            for bone_type in ["Arm", "Hand", "Leg", "Knee", "Foot"]:
                bone_name = f"{bone_type}{i}"
                bone = armature_object.pose.bones.get(bone_name)
                
                if bone:
                    # Clear all constraints on the original bone
                    while bone.constraints:
                        bone.constraints.remove(bone.constraints[0])
        
        # Get a list of IK bones to delete (store them before switching to edit mode)
        ik_bones_to_delete = []
        for bone in armature_object.pose.bones:
            if "IK" in bone.name:
                ik_bones_to_delete.append(bone.name)
        
        # Now delete the IK bones
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Delete all IK bones
        for bone_name in ik_bones_to_delete:
            bone = armature_object.data.edit_bones.get(bone_name)
            if bone:
                armature_object.data.edit_bones.remove(bone)
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Clean up keyframes for deleted bones
        if armature_object.animation_data and armature_object.animation_data.action:
            action = armature_object.animation_data.action
            fcurves_to_remove = []
            
            # Find all fcurves related to the deleted IK bones
            for i, fcurve in enumerate(action.fcurves):
                for bone_name in ik_bones_to_delete:
                    # Check if fcurve data_path contains bone name in the format pose.bones["BoneName"]
                    if f'pose.bones["{bone_name}"]' in fcurve.data_path:
                        fcurves_to_remove.append(i)
                        break
            
            # Remove the identified fcurves in reverse order to avoid index shifting issues
            for i in sorted(fcurves_to_remove, reverse=True):
                action.fcurves.remove(action.fcurves[i])
            
            if fcurves_to_remove:
                self.report({'INFO'}, f"Removed {len(fcurves_to_remove)} keyframe channels from deleted IK bones.")
        
        self.report({'INFO'}, "Animation baked to original bones and IK bones removed.")
        return {'FINISHED'}


class SUB_PT_apply_ik_animation_panel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport"""
    bl_label = "Apply IK Animation"
    bl_idname = "SUB_PT_apply_ik_animation_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IK Bones'

    def draw(self, context):
        layout = self.layout
        layout.operator("sub.apply_ik_animation", text="Bake & Remove IK")


def register():
    bpy.utils.register_class(SUB_OP_apply_ik_animation_operator)
    bpy.utils.register_class(SUB_PT_apply_ik_animation_panel)


def unregister():
    bpy.utils.unregister_class(SUB_OP_apply_ik_animation_operator)
    bpy.utils.unregister_class(SUB_PT_apply_ik_animation_panel)


if __name__ == "__main__":
    register()