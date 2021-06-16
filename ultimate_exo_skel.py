bl_info = {
    'name': 'Smash Ultimate Exo Skeleton Maker',
    'author': 'Carlos Aguilar',
    'description': 'Appends new helper bones to a smash ultimate skeleton for ease of import into smash ultimate.',
    'blender': (2, 91, 0),
    'category': 'Import-Export',
    'Location': '3D Viewport',
    'references': 'The Rokoko Plugin'
}

import bpy, json
from bpy.types import Scene, Object, PropertyGroup, UIList
from bpy.props import CollectionProperty, PointerProperty, StringProperty, IntProperty


def poll_armatures(self, obj):
    return obj.type == 'ARMATURE'

def poll_other_armatures(self, obj):
    return obj.type == 'ARMATURE' and obj != get_smash_armature()

def get_smash_armature():
    return bpy.context.scene.sub_exo_arma_ult

def get_other_armature():
    return bpy.context.scene.sub_exo_arma_other

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
    bone_name_smash: StringProperty(
        name='Smash Bone',
        description='The original smash bone',
        default='Undefined'
    )
    
    bone_name_other: StringProperty(
        name='Other Bone',
        description='The bone from the other armature',
        default=''
    )
    

class RenameOtherBones(bpy.types.Operator):
    bl_idname = 'sub.rename_other_bones'
    bl_label = 'Rename Other Bones'
    bl_description = 'Prefixes "H_EXO_" to all bones in the other armature to ensure functionality within smash and to prevent name collisions. Preserves the rigging so dont worry about rigging dying after this'    
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        armature_other = get_other_armature()
        print('Test: First bone name = %s' % armature_other.data.bones[0].name)
        for bone in armature_other.data.bones:
            bone.name = 'H_Exo_' + bone.name
        return {'FINISHED'}

class BuildBoneList(bpy.types.Operator):
    bl_idname = 'sub.build_bone_list'
    bl_label = 'Make Bone Pairing List'    
    bl_description = 'Creates a pairing list where you match bones from the smash armature to the other armature'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        armature_smash = get_smash_armature()
        armature_other = get_other_armature()
        
        context.scene.sub_exo_bone_list.clear()
        
        for bone in armature_smash.data.bones:
            bone_item = context.scene.sub_exo_bone_list.add()
            bone_item.bone_name_smash = bone.name
            
        return {'FINISHED'}
    
class MakeCombinedSkeleton(bpy.types.Operator):
    bl_idname = 'sub.make_combined_skeleton'
    bl_label = 'Make New Combined Skeleton'
    bl_description = 'Creates a new skeleton that basically appends the "Other" armature to the "Smash" armature'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
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
            for entry in context.scene.sub_exo_bone_list:
                if entry.bone_name_other == other_bone.name:
                    paired_bone_name = entry.bone_name_smash
           
            paired_bone = None
            print('Paired Bone Name = %s' % paired_bone_name)
            if paired_bone_name is not None:
                paired_bone = smash_bones.get(paired_bone_name)
                
            print('Paired Bone = %s' % paired_bone)
            if paired_bone is not None:
                print('paired_bone.head_local = %s' % paired_bone.head_local)
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
                print('other_bone.head_local = %s' % other_bone.head_local)
                new_bone.head = other_bone.head_local
                new_bone.tail = other_bone.tail_local
                AxisRollFromMatrix = bpy.types.Bone.AxisRollFromMatrix
                axis_roll_tuple = AxisRollFromMatrix(other_bone.matrix_local.to_3x3())
                new_bone.roll = axis_roll_tuple[1]
                
            if other_bone.parent:
                new_bone.parent = new_bones.get(other_bone.parent.name)
            
            print('')
        
        return {'FINISHED'}    

class ExportHelperBoneJson(bpy.types.Operator):
    bl_idname = 'sub.export_helper_bone_json'
    bl_label = 'Export Heler Bone Json'
    bl_description = 'Exports a JSON that you can then convert to .NUHLPB'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        '''
        For every bone in the other bone list, if it has
        a paired bone then create an entry in the
        helper bone json file
        '''
        output = {}
        output['data'] = {}
        output['data']['Hlpb'] = {}
        output['data']['Hlpb']['major_version'] = 1
        output['data']['Hlpb']['minor_version'] = 1
        output['data']['Hlpb']['aim_entries'] = []
        output['data']['Hlpb']['interpolation_entries'] = []
        output['data']['Hlpb']['list1'] = []
        output['data']['Hlpb']['list2'] = []
        interpolation_entries = output['data']['Hlpb']['interpolation_entries']
        list_one = output['data']['Hlpb']['list1']
        list_two = output['data']['Hlpb']['list2']
        other_bones = get_other_armature().data.bones
        smash_bones = get_smash_armature().data.bones
        
        paired_bones = {}
        for entry in context.scene.sub_exo_bone_list:
            paired_bones['%s' % entry.bone_name_other] = '%s' % entry.bone_name_smash
        
        index = 0
        for other_bone_name, smash_bone_name in paired_bones.items():
            if 'H_' not in other_bone_name:
                continue
            interpolation_entry = {}
            interpolation_entry['name'] = 'nuHelperBoneRotateInterp%s' % (index + 3000)
            smash_bone = smash_bones.get(smash_bone_name, None)
            interpolation_entry['bone_name'] = smash_bone.parent.name
            interpolation_entry['root_bone_name'] = smash_bone.parent.name
            interpolation_entry['parent_bone_name'] = smash_bone.name
            interpolation_entry['driver_bone_name'] = other_bone_name
            interpolation_entry['unk_type'] = 1
            interpolation_entry['aoi'] = {}
            interpolation_entry['aoi']['x'] = 1.0
            interpolation_entry['aoi']['y'] = 1.0
            interpolation_entry['aoi']['z'] = 1.0
            interpolation_entry['quat1'] = {}
            interpolation_entry['quat1']['x'] = 0.0
            interpolation_entry['quat1']['y'] = 0.0
            interpolation_entry['quat1']['z'] = 0.0
            interpolation_entry['quat1']['w'] = 1.0
            interpolation_entry['quat2'] = {}
            interpolation_entry['quat2']['x'] = 0.0
            interpolation_entry['quat2']['y'] = 0.0
            interpolation_entry['quat2']['z'] = 0.0
            interpolation_entry['quat2']['w'] = 1.0
            interpolation_entry['range_min'] = {}
            interpolation_entry['range_min']['x'] = -180.0
            interpolation_entry['range_min']['y'] = -180.0
            interpolation_entry['range_min']['z'] = -180.0
            interpolation_entry['range_max'] = {}
            interpolation_entry['range_max']['x'] = 180.0
            interpolation_entry['range_max']['y'] = 180.0
            interpolation_entry['range_max']['z'] = 180.0
            interpolation_entries.append(interpolation_entry)  
            list_one.append(index)
            list_two.append(1)
            index = index + 1
        text = bpy.data.texts.new('SUB_HELPER_BONE_JSON')
        text.write(json.dumps(output, indent = 2))
        return {'FINISHED'}       
        
class SUB_UL_BoneList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        other_armature = get_other_armature()
        
        layout = layout.split(factor=0.36, align=True)
        layout.label(text=item.bone_name_smash)
        if other_armature:
            layout.prop_search(item, 'bone_name_other', other_armature.pose, 'bones', text='')
    
class VIEW3D_PT_ultimate_exo_skel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Exo Skel Maker'
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        
        row = layout.row(align=True)
        row.label(text='Select the armatures')
        
        row = layout.row(align=True)
        row.prop(context.scene, 'sub_exo_arma_ult', icon='ARMATURE_DATA')
        
        row = layout.row(align=True)
        row.prop(context.scene, 'sub_exo_arma_other', icon='ARMATURE_DATA')
        
        scene = context.scene
        if scene.sub_exo_arma_other is not None:
            row = layout.row(align=True)
            row.operator(RenameOtherBones.bl_idname)
        
        if not context.scene.sub_exo_bone_list:
            row = layout.row(align=True)
            row.operator(BuildBoneList.bl_idname)
            return
        
        row = layout.row(align=True)
        row.operator(BuildBoneList.bl_idname, text='Rebuild Bone List')
        
        layout.separator()
        
        row = layout.row(align=True)
        row.template_list('SUB_UL_BoneList', 'Bone List', context.scene, 'sub_exo_bone_list', context.scene, 'sub_exo_bone_list_index', rows=1, maxrows=10)
    
        row = layout.row(align=True)
        row.operator(MakeCombinedSkeleton.bl_idname, text='Make New Combined Skeleton')
        
        row = layout.row(align=True)
        row.operator(ExportHelperBoneJson.bl_idname, text='Create Helper Bone JSON Text')
        
def register():
    bpy.utils.register_class(BuildBoneList)
    bpy.utils.register_class(RenameOtherBones)
    bpy.utils.register_class(VIEW3D_PT_ultimate_exo_skel)
    bpy.utils.register_class(BoneListItem)
    bpy.utils.register_class(SUB_UL_BoneList)
    bpy.utils.register_class(MakeCombinedSkeleton)
    bpy.utils.register_class(ExportHelperBoneJson)
    
    Scene.sub_exo_arma_ult = PointerProperty(
        name='Smash Armature',
        description='Select the Smash armature',
        type=Object,
        poll=poll_armatures,
        #update=?
    )
    Scene.sub_exo_arma_other = PointerProperty(
        name='Other Armature',
        description='Select the Other armature',
        type=Object,
        poll=poll_other_armatures,
        #update=?
    )
    Scene.sub_exo_bone_list = CollectionProperty(
        type=BoneListItem
    )
    Scene.sub_exo_bone_list_index = IntProperty(
        name="Index for the exo bone list",
        default=0
    )
    
def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_ultimate_exo_skel)
    