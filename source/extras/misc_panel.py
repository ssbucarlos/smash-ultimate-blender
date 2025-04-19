import bpy

from bpy.types import Panel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..anim.anim_data import SUB_PG_sub_anim_data

class SUB_PT_animation_tools(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Animation Tools'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        modes = ['POSE', 'OBJECT', 'EDIT_ARMATURE']  # Allow panel in all these modes
        return context.mode in modes

    def draw(self, context):
        ssp: SUB_PG_sub_anim_data = context.scene.sub_scene_properties

        layout = self.layout
        layout.use_property_split = False

        if context.mode != 'EDIT_ARMATURE':
            row = layout.row(align=True)
            row.operator("sub.create_ik_bones")
            
            row = layout.row(align=True)
            row.operator("sub.create_arm_ik")
            
            row = layout.row(align=True)
            row.operator("sub.create_foot_ik")
            layout.separator()
        
        # Add button to apply IK animation
        layout.separator()  # Add a separator for better UI organization
        layout.operator("sub.apply_ik_animation", text="Apply IK Animation")
        
        # Add button for IK influence toggle
        layout.operator("sub.toggle_ik_influence", text="Toggle IK Influence")
        
        # Add FK to IK transfer button (disabled if not in pose mode)
        row = layout.row()
        if context.mode == 'POSE':
            row.operator("sub.fk_to_ik_transfer", text="Position IK to Match FK Pose")
        else:
            row.enabled = False
            row.operator("sub.fk_to_ik_transfer", text="Position IK to Match FK Pose (Pose Mode Only)")
        
        # Add button for hip animation transfer
        layout.separator()
        row = layout.row(align=True)
        row.operator("sub.transfer_hip_animation", text="Transfer Hip Animation to Trans")
        
        # Add Reset Bone Locations button - just a button, not a section
        layout.separator()
        row = layout.row(align=True)
        row.operator("sub.reset_bone_locations", text="Reset Bone Locations")
        
        # Add idle pose library buttons
        layout.separator()
        box = layout.box()
        box.label(text="Idle Pose Library")
        
        row = box.row(align=True)
        row.operator("sub.store_idle_pose", text="Store Idle Pose")
        
        # Only show apply button if there's stored data
        row = box.row(align=True)
        if "idle_pose_name" in context.scene:
            row.operator("sub.apply_idle_pose", text=f"Apply '{context.scene.get('idle_pose_name', '')}' Pose")
        else:
            row.enabled = False
            row.operator("sub.apply_idle_pose", text="Apply Idle Pose (None Stored)")

class SUB_PT_misc_utilities(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Misc.'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        modes = ['POSE', 'OBJECT', 'EDIT_ARMATURE']  # Allow panel in all these modes
        return context.mode in modes

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        # Eye Material Custom Vector 31 Modal Operator
        row = layout.row(align=True)
        row.operator("sub.eye_material_custom_vector_31_modal")
        
        # Show bone removal button only in edit mode or grayed out
        row = layout.row(align=True)
        if context.mode == 'EDIT_ARMATURE':
            row.operator("sub.remove_selected_bones")
        else:
            row.enabled = False
            row.operator("sub.remove_selected_bones", text="Remove Bones (Edit Mode Only)")
        
        # Add weight limiting operator
        layout.separator()
        box = layout.box()
        box.label(text="Weight Tools")
        row = box.row(align=True)
        row.operator("sub.limit_weights", text="Limit Weights to 4")
        
        # Add renaming tools operators (only available in Object mode)
        layout.separator()
        box = layout.box()
        box.label(text="Renaming Tools")
        
        # Rename Materials to Mesh button
        row = box.row(align=True)
        if context.mode == 'OBJECT':
            row.operator("sub.rename_materials_to_mesh", text="Rename Materials to Mesh")
        else:
            row.enabled = False
            row.operator("sub.rename_materials_to_mesh", text="Rename Materials to Mesh (Object Mode Only)")
        
        # Rename Textures to Material button
        row = box.row(align=True)
        if context.mode == 'OBJECT':
            row.operator("sub.rename_textures_to_material", text="Rename Textures to Material")
        else:
            row.enabled = False
            row.operator("sub.rename_textures_to_material", text="Rename Textures to Material (Object Mode Only)")
        
    
        