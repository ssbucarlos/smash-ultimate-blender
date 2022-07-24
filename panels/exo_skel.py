import bpy, json, math
from bpy.types import Scene, Object, PropertyGroup, UIList
from bpy.props import CollectionProperty, PointerProperty, StringProperty, IntProperty


def poll_armatures(self, obj):
    return obj.type == 'ARMATURE'

def poll_other_armatures(self, obj):
    return obj.type == 'ARMATURE' and obj != get_smash_armature()

def get_smash_armature():
    return bpy.context.scene.smash_armature

def get_other_armature():
    return bpy.context.scene.other_armature

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

class RenameOtherBones(bpy.types.Operator):
    bl_idname = 'sub.rename_other_bones'
    bl_label = 'Rename Other Bones'
    bl_description = 'Prefixes the "prefix" to all bones in the other armature to ensure functionality within smash and to prevent name collisions. Preserves the rigging so dont worry about rigging dying after this'    
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        armature_other = get_other_armature()
        print('Test: First bone name = %s' % armature_other.data.bones[0].name)
        prefix = bpy.context.scene.armature_prefix
        for bone in armature_other.data.bones:
            bone.name = prefix + bone.name
        return {'FINISHED'}

class BuildBoneList(bpy.types.Operator):
    bl_idname = 'sub.build_bone_list'
    bl_label = 'Make Bone Pairing List'    
    bl_description = 'Creates a pairing list where you match bones from the smash armature to the other armature'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        armature_smash = get_smash_armature()
        armature_other = get_other_armature()
        
        context.scene.bone_list.clear()

        for bone in armature_other.data.bones:
            if not bone.name.startswith('H_'):
                continue
            bone_item = context.scene.bone_list.add()
            bone_item.bone_name_other = bone.name

        context.scene.pairable_bone_list.clear()

        for bone in armature_smash.data.bones:
            # Prevent users from pairing bones with no parent.
            # This ensure the nuhlpb entries can be initialized later.
            if bone.parent:
                bone_item = context.scene.pairable_bone_list.add()
                bone_item.name = bone.name
        
        return {'FINISHED'}

class PopulateBoneList(bpy.types.Operator):
    bl_idname = 'sub.populate_bone_list'
    bl_label = 'Auto Populate Bone List'    
    bl_description = 'Automatically assign a smash bone to an entry if its name matches with the prefix removed.'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        armature_smash = get_smash_armature()
        armature_other = get_other_armature()
        prefix = bpy.context.scene.armature_prefix
        
        for bone_item in context.scene.bone_list:
            # Auto populate list if bone's name without the prefix is in the Smash Armature. If value is already assigned, skip.
            if bone_item.bone_name_other.startswith(prefix):
                # Only replace the prefix once.
                bone_noprefix = bone_item.bone_name_other.replace(prefix, '', 1)
                if bone_noprefix in armature_smash.data.bones and not bone_item.bone_name_smash:
                    if bone_item.bone_name_other in armature_other.data.bones and not armature_smash.data.bones[bone_noprefix].parent:
                        print(f"{bone_noprefix} has no parent, skipping assignment.")
                    else: bone_item.bone_name_smash=bone_noprefix
        
        return {'FINISHED'}

class UpdateBoneList(bpy.types.Operator):
    bl_idname = 'sub.update_bone_list'
    bl_label = 'Update Bone Pairing List'
    bl_description = 'Updates the current pairing list where you match bones from the smash armature to the other armature'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}  
    
    def execute(self, context):
        context.scene.saved_bone_list.clear()
        for bone_item in context.scene.bone_list:
            if bone_item.bone_name_smash:
                saved_bone_item = context.scene.saved_bone_list.add()
                saved_bone_item.bone_name_other = bone_item.bone_name_other
                saved_bone_item.bone_name_smash = bone_item.bone_name_smash

        BuildBoneList.execute(self, context)

        cur_bone_other_list = [bone_item.bone_name_other for bone_item in context.scene.bone_list]
        
        if context.scene.saved_bone_list:
            for saved_bone_item in context.scene.saved_bone_list:
                if saved_bone_item.bone_name_other in cur_bone_other_list:
                    index = cur_bone_other_list.index(saved_bone_item.bone_name_other)
                    context.scene.bone_list[index].bone_name_smash = saved_bone_item.bone_name_smash
          
        return {'FINISHED'}
    
class MakeCombinedSkeleton(bpy.types.Operator):
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
        new_arma_name = 'Combined'
        new_arma = bpy.data.objects.new(
            new_arma_name,
            bpy.data.armatures.new(new_arma_name))
        output_collection = get_script_output_collection()
        output_collection.objects.link(new_arma)
        unselect_all_objects_in_context()
        new_arma.select_set(True)
        bpy.context.view_layer.objects.active = new_arma
        bpy.ops.object.mode_set(mode='EDIT')
        smash_arma = get_smash_armature()
        other_arma = get_other_armature()
        
        new_bones = new_arma.data.edit_bones
        smash_bones = smash_arma.data.bones
        other_bones = other_arma.data.bones
        for smash_bone in smash_bones:
            new_bone = new_bones.new(smash_bone.name)
            new_bone.head = smash_bone.head_local
            new_bone.tail = smash_bone.tail_local
            axis_roll_tuple = smash_bone.AxisRollFromMatrix(smash_bone.matrix_local.to_3x3())
            smash_bone_roll = axis_roll_tuple[1]
            new_bone.roll = smash_bone_roll
            if smash_bone.parent:
                new_bone.parent = new_bones.get(smash_bone.parent.name)
        
        for other_bone in other_arma.data.bones:
            new_bone = new_bones.new(other_bone.name)
            paired_bone_name = None
            for entry in context.scene.bone_list:
                if entry.bone_name_other == other_bone.name:
                    paired_bone_name = entry.bone_name_smash
           
            paired_bone = None
            if paired_bone_name is not None:
                paired_bone = smash_bones.get(paired_bone_name)
                
            print('Paired Bone = %s' % paired_bone)
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
        new_bones = new_arma.pose.bones
        smash_arma = get_smash_armature()
        smash_bones = smash_arma.pose.bones
        from .import_model import create_new_empty, get_from_mesh_list_with_pruned_name, copy_empty
        old_nuhlpb_root_empty = get_from_mesh_list_with_pruned_name(smash_arma.children, '_NUHLPB', None)
        old_interpolation_entries_empty = None
        old_aim_entries_empty = None

        new_nuhlpb_root_empty = None
        new_nuhlpb_root_empty = None
        new_interpolation_entries_empty = None
        new_aim_entries_empty = None

        if old_nuhlpb_root_empty:
            new_nuhlpb_root_empty = copy_empty(old_nuhlpb_root_empty, output_collection)
            new_nuhlpb_root_empty.parent = new_arma
            
            old_aim_entries_empty = get_from_mesh_list_with_pruned_name(old_nuhlpb_root_empty.children, 'aim_entries', None)
            new_aim_entries_empty = copy_empty(old_aim_entries_empty, output_collection)
            new_aim_entries_empty.parent = new_nuhlpb_root_empty
            old_interpolation_entries_empty = get_from_mesh_list_with_pruned_name(old_nuhlpb_root_empty.children, 'interpolation_entries', None)
            new_interpolation_entries_empty = copy_empty(old_interpolation_entries_empty, output_collection)
            new_interpolation_entries_empty.parent = new_nuhlpb_root_empty
        else:
            # This case usually means the user didn't import the smash armature using a more recent version.
            # TODO: Infer the helper bones from constraints and only use custom properties for additional fields?
            message = 'No _NUHLPB empty detected for the Smash Armature. Original helper bones may be lost on export.'
            message += ' Reimport the Smash Armature to include bones and helper bones.'
            self.report({'WARNING'}, message)

            new_nuhlpb_root_empty = create_new_empty('_NUHLPB', new_arma, output_collection)
            new_nuhlpb_root_empty['major_version'] = 1
            new_nuhlpb_root_empty['minor_version'] = 1
            new_aim_entries_empty = create_new_empty('aim_entries', new_nuhlpb_root_empty, output_collection)
            new_interpolation_entries_empty = create_new_empty('interpolation_entries', new_nuhlpb_root_empty, output_collection)

        if old_aim_entries_empty:
            for entry in old_aim_entries_empty.children:
                new_aim_entry_empty = copy_empty(entry, output_collection)
                new_aim_entry_empty.parent = new_aim_entries_empty
        if old_interpolation_entries_empty:
            for entry in old_interpolation_entries_empty.children:
                new_interpolation_entry_empty = copy_empty(entry, output_collection)
                new_interpolation_entry_empty.parent = new_interpolation_entries_empty

        for index, new_bone in enumerate(new_bones):
            paired_bone_name = None
            for entry in context.scene.bone_list:
                if entry.bone_name_other == new_bone.name:
                    paired_bone_name = entry.bone_name_smash
            if paired_bone_name is None:
                continue
            paired_bone = smash_bones.get(paired_bone_name, None)
            if paired_bone is None:
                continue
            
            if paired_bone.parent:
                self.create_constraints(new_arma, new_bone, paired_bone)
                new_interpolation_entry_empty = create_new_empty(f'nuHelperBoneRotateInterp{3000+index}', new_interpolation_entries_empty, output_collection)
                new_interpolation_entry_empty['bone_name'] = paired_bone.parent.name
                new_interpolation_entry_empty['root_bone_name'] = paired_bone.parent.name
                new_interpolation_entry_empty['parent_bone_name'] = paired_bone.name
                new_interpolation_entry_empty['driver_bone_name'] = new_bone.name
                new_interpolation_entry_empty['unk_type'] = 1
                new_interpolation_entry_empty['aoi'] = [1.0, 1.0, 1.0]
                new_interpolation_entry_empty['quat1'] = [0.0, 0.0, 0.0, 1.0]
                new_interpolation_entry_empty['quat2'] = [0.0, 0.0, 0.0, 1.0]
                new_interpolation_entry_empty['range_min'] = [-180, -180, -180]
                new_interpolation_entry_empty['range_max'] = [180, 180, 180]
            else:
                self.report({'ERROR'}, f'Cannot pair {new_bone.name} to {paired_bone.name}. {paired_bone.name} has no parent.')

        return {'FINISHED'}


class SUB_UL_BoneList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        other_armature = get_other_armature()
        smash_armature = get_smash_armature()

        layout = layout.split(factor=0.36, align=True)
        layout.label(text=item.bone_name_other)
        if other_armature and smash_armature:
            # Use a custom collection property to allow for filtering out unwanted bones.
            layout.prop_search(item, 'bone_name_smash', context.scene, 'pairable_bone_list', text='', icon='BONE_DATA')


class VIEW3D_PT_ultimate_exo_skel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Magic Exo Skel Maker'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        
        row = layout.row(align=True)
        row.label(text='Select the armatures')
        
        row = layout.row(align=True)
        row.prop(context.scene, 'smash_armature', icon='ARMATURE_DATA')
        
        row = layout.row(align=True)
        row.prop(context.scene, 'other_armature', icon='ARMATURE_DATA')
        
        row = layout.row(align=True)
        row.prop(context.scene, 'armature_prefix')
        
        scene = context.scene
        if scene.other_armature is not None:
            row = layout.row(align=True)
            row.operator(RenameOtherBones.bl_idname)
        
        if not context.scene.bone_list:
            row = layout.row(align=True)
            row.operator(BuildBoneList.bl_idname)
            return
        
        row = layout.row(align=True)
        row.operator(BuildBoneList.bl_idname, text='Rebuild Bone List')
        
        row = layout.row(align=True)
        row.operator(PopulateBoneList.bl_idname)

        row = layout.row(align=True)
        row.operator(UpdateBoneList.bl_idname)
        
        layout.separator()
        
        row = layout.row(align=True)
        row.template_list('SUB_UL_BoneList', 'Bone List', context.scene, 'bone_list', context.scene, 'bone_list_index', rows=1, maxrows=10)
    
        row = layout.row(align=True)
        row.operator(MakeCombinedSkeleton.bl_idname, text='Make New Combined Skeleton')