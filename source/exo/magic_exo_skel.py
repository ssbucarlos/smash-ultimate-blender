import bpy 
import math
from bpy.types import Object, PropertyGroup, UIList, Operator, Panel
from bpy.props import CollectionProperty, PointerProperty, StringProperty, IntProperty
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..blender_property_extensions import SubSceneProperties
    from ..model.skel.helper_bone_data import SubHelperBoneData, OrientConstraint
    from bpy.types import PoseBone

def poll_armatures(self, obj:bpy.types.Object):
    return obj.type == 'ARMATURE' and obj.name in bpy.context.view_layer.objects

def poll_other_armatures(self, obj):
    return obj.type == 'ARMATURE' and obj != get_smash_armature()

def get_smash_armature() -> Object:
    return bpy.context.scene.sub_scene_properties.smash_armature

def get_other_armature() -> Object:
    return bpy.context.scene.sub_scene_properties.other_armature

def unselect_all_objects_in_context():
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
        
def get_script_output_collection():
    collections = bpy.data.collections
    col_name = 'SUB Output'
    col = collections.get(col_name, None)
    if col is None:
        col = collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
    return col

class BoneListItem(PropertyGroup):
    '''
    bone_name_smash: StringProperty(
        name='Smash Bone',
        description='The original smash bone',
        #default='Undefined'
        default=''
    )
    
    bone_name_other: StringProperty(
        name='Other Bone',
        description='The bone from the other armature',
        default=''
    )
    '''
    bone_name_other: StringProperty(
        name='Other Bone',
        description='The bone from the other armature',
        default=''
    )
    
    bone_name_smash: StringProperty(
        name='Smash Bone',
        description='The original smash bone',
        #default='Undefined'
        default=''
    )


class PairableBoneListItem(PropertyGroup):
    name: StringProperty('bone name')

class SUB_OP_rename_other_bones(Operator):
    bl_idname = 'sub.rename_other_bones'
    bl_label = 'Rename Other Bones'
    bl_description = 'Prefixes the "prefix" to all bones in the other armature to ensure functionality within smash and to prevent name collisions. Preserves the rigging so dont worry about rigging dying after this'    
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        armature_other = get_other_armature()
        prefix = bpy.context.scene.sub_scene_properties.armature_prefix
        for bone in armature_other.data.bones:
            bone.name = prefix + bone.name
        return {'FINISHED'}

class SUB_OP_build_bone_list(Operator):
    bl_idname = 'sub.build_bone_list'
    bl_label = 'Make Bone Pairing List'    
    bl_description = 'Creates a pairing list where you match bones from the smash armature to the other armature'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        armature_smash = get_smash_armature()
        armature_other = get_other_armature()
        
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        bone_list = ssp.bone_list
        bone_list.clear()

        for bone in armature_other.data.bones:
            if not bone.name.startswith('H_'):
                continue
            bone_item = bone_list.add()
            bone_item.bone_name_other = bone.name

        pairable_bone_list = ssp.pairable_bone_list
        pairable_bone_list.clear()

        for bone in armature_smash.data.bones:
            # Prevent users from pairing bones with no parent.
            # This ensure the nuhlpb entries can be initialized later.
            if bone.parent:
                bone_item = pairable_bone_list.add()
                bone_item.name = bone.name
        
        return {'FINISHED'}

class SUB_OP_populate_bone_list(Operator):
    bl_idname = 'sub.populate_bone_list'
    bl_label = 'Auto Populate Bone List'    
    bl_description = 'Automatically assign a smash bone to an entry if its name matches with the prefix removed.'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        armature_smash = get_smash_armature()
        armature_other = get_other_armature()
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        prefix = ssp.armature_prefix
        
        for bone_item in ssp.bone_list:
            # Auto populate list if bone's name without the prefix is in the Smash Armature. If value is already assigned, skip.
            if bone_item.bone_name_other.startswith(prefix):
                # Only replace the prefix once.
                bone_noprefix = bone_item.bone_name_other.replace(prefix, '', 1)
                if bone_noprefix in armature_smash.data.bones and not bone_item.bone_name_smash:
                    if bone_item.bone_name_other in armature_other.data.bones and not armature_smash.data.bones[bone_noprefix].parent:
                        print(f"{bone_noprefix} has no parent, skipping assignment.")
                    else: bone_item.bone_name_smash=bone_noprefix
        
        return {'FINISHED'}

class SUB_OP_update_bone_list(Operator):
    bl_idname = 'sub.update_bone_list'
    bl_label = 'Update Bone Pairing List'
    bl_description = 'Updates the current pairing list where you match bones from the smash armature to the other armature'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}  
    
    def execute(self, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        ssp.saved_bone_list.clear()
        for bone_item in ssp.bone_list:
            if bone_item.bone_name_smash:
                saved_bone_item = ssp.saved_bone_list.add()
                saved_bone_item.bone_name_other = bone_item.bone_name_other
                saved_bone_item.bone_name_smash = bone_item.bone_name_smash

        SUB_OP_build_bone_list.execute(self, context)

        cur_bone_other_list = [bone_item.bone_name_other for bone_item in ssp.bone_list]
        
        if ssp.saved_bone_list:
            for saved_bone_item in ssp.saved_bone_list:
                if saved_bone_item.bone_name_other in cur_bone_other_list:
                    index = cur_bone_other_list.index(saved_bone_item.bone_name_other)
                    ssp.bone_list[index].bone_name_smash = saved_bone_item.bone_name_smash
          
        return {'FINISHED'}
    
class SUB_OP_make_combined_skeleton(Operator):
    bl_idname = 'sub.make_combined_skeleton'
    bl_label = 'Make New Combined Skeleton'
    bl_description = 'Creates a new skeleton that basically appends the "Other" armature to the "Smash" armature'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def create_constraints(self, armature, imposter_bone, original_bone):
        '''
        Creates a Copy Rotation Constrain
        '''
        smash_armature = get_smash_armature()
        other_armature = get_other_armature()
        
        x = 'X'
        y = 'Y'
        z = 'Z'
        for axis in [x, y, z]:
            crc = imposter_bone.constraints.new('COPY_ROTATION')
            crc.name = 'SUB CRC %s' % axis
            crc.target = armature
            crc.subtarget =  original_bone.name
            crc.target_space = 'POSE'
            crc.owner_space = 'POSE'
            crc.use_x = True if axis is x else False
            crc.use_y = True if axis is y else False
            crc.use_z = True if axis is z else False
        
        lrc = imposter_bone.constraints.new('LIMIT_ROTATION')
        lrc.name = 'SUB LRC'
        lrc.use_limit_x = True
        lrc.use_limit_y = True
        lrc.use_limit_z = True
        lrc.min_x = math.radians(-180)
        lrc.min_y = math.radians(-180)
        lrc.min_z = math.radians(-180)
        lrc.max_x = math.radians(180)
        lrc.max_y = math.radians(180)
        lrc.max_z = math.radians(180)
        lrc.use_transform_limit = False
        lrc.owner_space = 'POSE'    
            
    
    def execute(self, context):
        '''
        First, copy "Smash" bones as-is.
        Then, copy the "Other" bones into the "Smash" bones,
           preserving the heirarchy of "Other",
           just replacing the head/tail data with Smash's when available.
        Note, for proper implementation in Smash Ultimate,
            'Hip' is the bone to parent the 'root' bone of "Other" to.
        '''
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        smash_arma = get_smash_armature()
        other_arma = get_other_armature()
        new_arma:Object = smash_arma.copy()
        new_arma.data = smash_arma.data.copy()
        new_arma.name = 'Combined'
        output_collection = get_script_output_collection()
        output_collection.objects.link(new_arma)
        unselect_all_objects_in_context()
        new_arma.select_set(True)
        bpy.context.view_layer.objects.active = new_arma
        bpy.ops.object.mode_set(mode='EDIT')

        
        new_bones = new_arma.data.edit_bones
        smash_bones = smash_arma.data.bones
        other_bones = other_arma.data.bones

        for other_bone in other_arma.data.bones:
            new_bone = new_bones.new(other_bone.name)
            paired_bone_name = None
            for entry in ssp.bone_list:
                if entry.bone_name_other == other_bone.name:
                    paired_bone_name = entry.bone_name_smash
           
            paired_bone = None
            if paired_bone_name is not None:
                paired_bone = smash_bones.get(paired_bone_name)
                
            if paired_bone is not None:
                '''
                Need to create the head+tail to match the original smash one, but move it to the new position
                '''
                new_bone.head = paired_bone.head_local 
                new_bone.tail = paired_bone.tail_local
                AxisRollFromMatrix = bpy.types.Bone.AxisRollFromMatrix
                axis_roll_tuple = AxisRollFromMatrix(paired_bone.matrix_local.to_3x3())
                new_bone.roll = axis_roll_tuple[1]
                new_bone_head_vector = new_bone.head.copy()
                new_bone.head = new_bone.head - new_bone_head_vector
                new_bone.tail = new_bone.tail - new_bone_head_vector
                new_bone.head = new_bone.head + other_bone.head_local
                new_bone.tail = new_bone.tail + other_bone.head_local
                
            else:
                new_bone.head = other_bone.head_local
                new_bone.tail = other_bone.tail_local
                AxisRollFromMatrix = bpy.types.Bone.AxisRollFromMatrix
                axis_roll_tuple = AxisRollFromMatrix(other_bone.matrix_local.to_3x3())
                new_bone.roll = axis_roll_tuple[1]
                
            if other_bone.parent:
                new_bone.parent = new_bones.get(other_bone.parent.name)
            
            
        bpy.ops.object.mode_set(mode='POSE')

        smash_arma = get_smash_armature()
        smash_bones = smash_arma.pose.bones

        for new_bone in new_arma.pose.bones:
            new_bone: PoseBone
            if new_bone.name.startswith('H_Exo_'):
                exo_collection = new_arma.data.collections.get('"Exo" Helper Bones')
                if exo_collection:
                    exo_collection.assign(new_bone)
                    new_bone.color.palette = 'THEME09'
                    new_bone.bone.color.palette = 'THEME09'

        for index, new_bone in enumerate(new_arma.pose.bones):
            new_bone: PoseBone
            paired_bone_name = None
            for entry in ssp.bone_list:
                if entry.bone_name_other == new_bone.name:
                    paired_bone_name = entry.bone_name_smash
            if paired_bone_name is None:
                continue
            paired_bone = smash_bones.get(paired_bone_name, None)
            if paired_bone is None:
                continue
            if paired_bone.parent:
                shbd: SubHelperBoneData = new_arma.data.sub_helper_bone_data
                new_interpolation_entry: OrientConstraint = shbd.orient_constraints.add()
                new_interpolation_entry.name = f'nuHelperBoneRotateInterp{3000+index}'
                new_interpolation_entry.parent_bone_name1 = paired_bone.parent.name
                new_interpolation_entry.parent_bone_name2 = paired_bone.parent.name
                new_interpolation_entry.source_bone_name = paired_bone.name
                new_interpolation_entry.target_bone_name = new_bone.name
                new_interpolation_entry.unk_type = 1
                new_interpolation_entry.constraint_axes = [1.0, 1.0, 1.0]
                new_interpolation_entry.quat1 = [0.0, 0.0, 0.0, 1.0]
                new_interpolation_entry.quat2 = [0.0, 0.0, 0.0, 1.0]
                new_interpolation_entry.range_min = [-180.0, -180.0, -180.0]
                new_interpolation_entry.range_max = [180.0, 180.0, 180.0]

            else:
                self.report({'ERROR'}, f'Cannot pair {new_bone.name} to {paired_bone.name}. {paired_bone.name} has no parent.')
        
        from ..model.import_model import refresh_helper_bone_constraints
        refresh_helper_bone_constraints(new_arma)

        return {'FINISHED'}


class SUB_UL_BoneList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        other_armature = get_other_armature()
        smash_armature = get_smash_armature()

        layout = layout.split(factor=0.36, align=True)
        layout.label(text=item.bone_name_other)
        if other_armature and smash_armature:
            # Use a custom collection property to allow for filtering out unwanted bones.
            layout.prop_search(item, 'bone_name_smash', context.scene.sub_scene_properties, 'pairable_bone_list', text='', icon='BONE_DATA')


class SUB_PT_ultimate_exo_skel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Magic Exo Skel Maker'
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        # Allow the panel in both object mode and edit mode
        return context.mode in ['OBJECT', 'EDIT_ARMATURE']
    
    def draw(self, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        layout = self.layout
        layout.use_property_split = False
        
        # Original panel content - Select armatures section
        row = layout.row(align=True)
        row.label(text='Select the armatures')
        
        row = layout.row(align=True)
        row.prop(ssp, 'smash_armature', icon='ARMATURE_DATA')
        
        row = layout.row(align=True)
        row.prop(ssp, 'other_armature', icon='ARMATURE_DATA')
        
        row = layout.row(align=True)
        row.prop(ssp, 'armature_prefix')
        
        if ssp.other_armature is not None:
            row = layout.row(align=True)
            row.operator(SUB_OP_rename_other_bones.bl_idname)
        
        # Bone list section
        if not ssp.bone_list:
            row = layout.row(align=True)
            row.operator(SUB_OP_build_bone_list.bl_idname)
            
            # Smart un-exo model section - Always visible
            layout.separator()
            box = layout.box()
            box.label(text="Smart un-exo model (for movesets)")
            
            # Add explanatory text
            row = box.row(align=True)
            row.label(text="This process is primarily meant for movesets, not skins")
            
            # Cleanup Unused Exo Bones button (at the top)
            row = box.row(align=True)
            row.operator("sub.cleanup_unused_exo_bones", text="Cleanup Unused Exo Bones")
            
            # Transfer Exo Weights button (moved up)
            row = box.row(align=True)
            row.operator("sub.transfer_exo_weights", text="Transfer Exo Weights")
            
            # Align Smash Bones to Exo Bones button (moved down)
            row = box.row(align=True)
            row.operator("sub.align_exo_bones", text="Align Smash Bones to Exo Bones")
            
            return
        
        row = layout.row(align=True)
        row.operator(SUB_OP_build_bone_list.bl_idname, text='Rebuild Bone List')
        
        row = layout.row(align=True)
        row.operator(SUB_OP_populate_bone_list.bl_idname)

        row = layout.row(align=True)
        row.operator(SUB_OP_update_bone_list.bl_idname)
        
        layout.separator()
        
        row = layout.row(align=True)
        row.template_list('SUB_UL_BoneList', 'Bone List', ssp, 'bone_list', ssp, 'bone_list_index', rows=1, maxrows=10)
    
        row = layout.row(align=True)
        row.operator(SUB_OP_make_combined_skeleton.bl_idname, text='Make New Combined Skeleton')
        
        # Smart un-exo model section is duplicated here for when a bone list exists
        layout.separator()
        box = layout.box()
        box.label(text="Smart un-exo model (for movesets)")
        
        # Add explanatory text
        row = box.row(align=True)
        row.label(text="This process is primarily meant for movesets, not skins")
        
        # Cleanup Unused Exo Bones button (at the top)
        row = box.row(align=True)
        row.operator("sub.cleanup_unused_exo_bones", text="Cleanup Unused Exo Bones")
        
        # Transfer Exo Weights button (moved up)
        row = box.row(align=True)
        row.operator("sub.transfer_exo_weights", text="Transfer Exo Weights")
        
        # Align Smash Bones to Exo Bones button (moved down)
        row = box.row(align=True)
        row.operator("sub.align_exo_bones", text="Align Smash Bones to Exo Bones")