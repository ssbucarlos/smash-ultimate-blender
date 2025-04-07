import bpy
from bpy.types import Operator
from bpy.props import BoolProperty
from mathutils import Vector

class SUB_OP_align_exo_bones(Operator):
    bl_idname = "sub.align_exo_bones"
    bl_label = "Align Exo Bones"
    bl_description = "Align Smash bones to their corresponding Exo bones. IMPORTANT: You must be in EDIT MODE to use this function."
    bl_options = {'REGISTER', 'UNDO'}
    
    finger_chains_as_units: BoolProperty(
        name="Move Finger Chains as Units",
        description="Move entire finger chains together as units",
        default=True
    )
    
    adjust_children: BoolProperty(
        name="Adjust Children",
        description="Adjust child bone positions to maintain their relative positions",
        default=True
    )
    
    maintain_roll: BoolProperty(
        name="Maintain Roll",
        description="Maintain the original roll angle of the bones",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        # Ensure we're in edit mode with an armature that has helper bone data
        return (context.mode == 'EDIT_ARMATURE' and 
                context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                hasattr(context.active_object.data, "sub_helper_bone_data"))
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "finger_chains_as_units")
        layout.prop(self, "adjust_children")
        layout.prop(self, "maintain_roll")
    
    def execute(self, context):
        armature = context.active_object
        helper_bone_data = armature.data.sub_helper_bone_data
        
        # Must be in edit mode
        if context.mode != 'EDIT_ARMATURE':
            bpy.ops.object.mode_set(mode='EDIT')
        
        # Get exo bone mapping from helper bone data
        exo_bone_mapping = {}
        
        # Process orient constraints - they connect Exo bones to controlling bones
        for constraint in helper_bone_data.orient_constraints:
            # Check if this is an Exo bone constraint
            if "H_Exo_" in constraint.target_bone_name:
                exo_bone_mapping[constraint.target_bone_name] = constraint.source_bone_name
        
        # Store original bone rolls if maintaining roll
        original_rolls = {}
        if self.maintain_roll:
            for smash_bone_name in exo_bone_mapping.values():
                if smash_bone_name in armature.data.edit_bones:
                    original_rolls[smash_bone_name] = armature.data.edit_bones[smash_bone_name].roll
        
        # Store original lengths for bones
        original_lengths = {}
        for smash_bone_name in exo_bone_mapping.values():
            if smash_bone_name in armature.data.edit_bones:
                original_lengths[smash_bone_name] = armature.data.edit_bones[smash_bone_name].length
        
        # Pre-processing: identify finger bones by patterns
        finger_bones = {}  # Format: {bone_name: (finger_side, finger_num, position)}
        finger_chains = {}  # Format: {(side, num): [bone_names_in_chain]}
        
        for bone in armature.data.edit_bones:
            # Check for finger naming pattern (like FingerR41, FingerL12, etc.)
            if "Finger" in bone.name and len(bone.name) >= 9:
                try:
                    # Extract the finger number and position from the name
                    # Format is "FingerXYZ" where X is side (R/L), Y is finger number (1-5), Z is position (1-3)
                    side = bone.name[6]  # R or L
                    if side in ["R", "L"]:
                        finger_num = int(bone.name[7])
                        position = int(bone.name[8])
                        
                        # Store bone in finger_bones dictionary
                        finger_bones[bone.name] = (side, finger_num, position)
                        
                        # Add to finger chains
                        chain_key = (side, finger_num)
                        if chain_key not in finger_chains:
                            finger_chains[chain_key] = []
                        finger_chains[chain_key].append(bone.name)
                except (IndexError, ValueError):
                    pass  # Not a standard finger bone name format
        
        # Store original child positions relative to their parents
        child_offsets = {}
        if self.adjust_children:
            for bone in armature.data.edit_bones:
                if bone.parent:
                    # Store position relative to parent
                    parent_head = bone.parent.head
                    child_offsets[bone.name] = [
                        bone.head[0] - parent_head[0],
                        bone.head[1] - parent_head[1],
                        bone.head[2] - parent_head[2]
                    ]
        
        # Track which bones have been moved already (to avoid double-processing)
        processed_bones = set()
        
        # First phase: Process bones and move finger chains as units
        aligned_bones = 0
        for exo_bone_name, smash_bone_name in exo_bone_mapping.items():
            # Skip if either bone doesn't exist
            if (exo_bone_name not in armature.data.edit_bones or 
                smash_bone_name not in armature.data.edit_bones or
                smash_bone_name in processed_bones):
                continue
            
            exo_bone = armature.data.edit_bones[exo_bone_name]
            smash_bone = armature.data.edit_bones[smash_bone_name]
            
            # Check if this is a finger bone and move the whole chain if enabled
            is_finger_bone = smash_bone_name in finger_bones
            
            if is_finger_bone and self.finger_chains_as_units:
                # Get finger chain information
                side, finger_num, position = finger_bones[smash_bone_name]
                
                # Only process finger chains starting with the first bone (position 1)
                if position == 1:  # This is the first bone in the chain
                    # Get the offset needed to move this bone
                    offset = exo_bone.head - smash_bone.head
                    
                    # Move all bones in this finger chain by the same offset
                    chain_key = (side, finger_num)
                    for bone_name in finger_chains[chain_key]:
                        if bone_name in armature.data.edit_bones:
                            bone = armature.data.edit_bones[bone_name]
                            bone.head += offset
                            bone.tail += offset
                            processed_bones.add(bone_name)
                    
                    aligned_bones += 1
                else:
                    # Skip other finger bones - they'll be moved as part of their chain
                    continue
            
            else:
                # Hand bones move as a unit
                if "Hand" in exo_bone_name:
                    # Move the whole bone as a unit
                    offset = exo_bone.head - smash_bone.head
                    smash_bone.head += offset
                    smash_bone.tail += offset
                    processed_bones.add(smash_bone_name)
                    
                    # If there's a "Have" bone that should follow this Hand bone, move it too
                    have_bone_name = smash_bone_name.replace("Hand", "Have")
                    if have_bone_name in armature.data.edit_bones:
                        have_bone = armature.data.edit_bones[have_bone_name]
                        have_bone.head += offset
                        have_bone.tail += offset
                        processed_bones.add(have_bone_name)
                
                # Wrist bones should move as a unit
                elif "Wrist" in exo_bone_name:
                    # Move the whole bone as a unit
                    offset = exo_bone.head - smash_bone.head
                    smash_bone.head += offset
                    smash_bone.tail += offset
                    processed_bones.add(smash_bone_name)
                
                # LegC bone should move as a unit
                elif "LegC" in exo_bone_name or "LegC" == smash_bone_name:
                    # Move the whole bone as a unit without connecting to any children
                    offset = exo_bone.head - smash_bone.head
                    smash_bone.head += offset
                    smash_bone.tail += offset
                    processed_bones.add(smash_bone_name)
                    
                    # Make sure we mark any children that might be from the Exo bone
                    # to avoid them being handled in the default case
                    exo_children = [b for b in armature.data.edit_bones if b.parent == exo_bone]
                    for child in exo_children:
                        processed_bones.add(child.name)
                
                # Foot bones should move as a unit
                elif "Foot" in exo_bone_name or "Foot" in smash_bone_name:
                    # Move the whole bone as a unit
                    offset = exo_bone.head - smash_bone.head
                    smash_bone.head += offset
                    smash_bone.tail += offset
                    processed_bones.add(smash_bone_name)
                
                # Neck bone should move as a unit
                elif "Neck" in exo_bone_name or "Neck" == smash_bone_name:
                    # Move the whole bone as a unit
                    offset = exo_bone.head - smash_bone.head
                    smash_bone.head += offset
                    smash_bone.tail += offset
                    processed_bones.add(smash_bone_name)
                
                # Head bone should move as a unit
                elif "Head" == exo_bone_name or "Head" == smash_bone_name:
                    # Move the whole bone as a unit
                    offset = exo_bone.head - smash_bone.head
                    smash_bone.head += offset
                    smash_bone.tail += offset
                    processed_bones.add(smash_bone_name)
                    
                    # Make all children of the Head bone follow it with the same offset
                    head_children = [bone for bone in armature.data.edit_bones if bone.parent and bone.parent.name == smash_bone_name]
                    for child_bone in head_children:
                        child_bone.head += offset
                        child_bone.tail += offset
                        processed_bones.add(child_bone.name)
                        
                        # Also move grandchildren (recursive approach for the entire head hierarchy)
                        def move_child_bones(parent_bone, offset_vector):
                            for bone in armature.data.edit_bones:
                                if bone.parent and bone.parent.name == parent_bone.name:
                                    bone.head += offset_vector
                                    bone.tail += offset_vector
                                    processed_bones.add(bone.name)
                                    # Recursive call to move this bone's children
                                    move_child_bones(bone, offset_vector)
                        
                        # Apply to all descendants
                        move_child_bones(child_bone, offset)
                
                # Regular processing for all other bones
                else:
                    # Find the children of the Exo bone
                    exo_children = [b for b in armature.data.edit_bones if b.parent == exo_bone]
                    
                    if exo_children:
                        # Has children - Set the head to match the Exo bone's head
                        smash_bone.head = exo_bone.head.copy()
                        # Use the first child's head as the tail target
                        smash_bone.tail = exo_children[0].head.copy()
                    else:
                        # No children - move as a unit (like in TRANSLATE mode)
                        # Calculate the offset vector
                        offset = exo_bone.head - smash_bone.head
                        
                        # Move head and tail by the same offset
                        smash_bone.head += offset
                        smash_bone.tail += offset
                    
                    processed_bones.add(smash_bone_name)
            
            # Restore original roll if requested
            if self.maintain_roll and smash_bone_name in original_rolls:
                smash_bone.roll = original_rolls[smash_bone_name]
            
            aligned_bones += 1
        
        # Only adjust non-finger children if finger chains are moved as units
        if self.adjust_children:
            for bone in armature.data.edit_bones:
                # Skip finger bones and already processed bones
                if bone.name in processed_bones or bone.name in finger_bones:
                    continue
                    
                if bone.parent and bone.name in child_offsets:
                    # Only adjust children of bones we haven't aligned directly
                    parent_name = bone.parent.name
                    if parent_name in exo_bone_mapping.values():
                        # Skip children of aligned bones as they've already been handled
                        continue
                    
                    # Restore position relative to parent
                    offset = child_offsets[bone.name]
                    parent_head = bone.parent.head
                    bone.head = Vector([
                        parent_head[0] + offset[0],
                        parent_head[1] + offset[1],
                        parent_head[2] + offset[2]
                    ])
        
        # Report results
        if aligned_bones == 0:
            self.report({'WARNING'}, "No bones were aligned. Make sure you have Exo bones set up with constraints.")
            return {'CANCELLED'}
        else:
            self.report({'INFO'}, f"Successfully aligned {aligned_bones} bones")
            return {'FINISHED'}

def register():
    bpy.utils.register_class(SUB_OP_align_exo_bones)

def unregister():
    bpy.utils.unregister_class(SUB_OP_align_exo_bones)

if __name__ == "__main__":
    register() 