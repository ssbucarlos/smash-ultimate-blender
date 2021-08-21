'''
bl_info = {
    'name': 'Smash Ultimate Exo Skeleton Maker',
    'author': 'Carlos Aguilar',
    'description': 'Appends new helper bones to a smash ultimate skeleton for ease of import into smash ultimate.',
    'blender': (2, 91, 0),
    'category': 'Import-Export',
    'Location': '3D Viewport',
    'references': 'The Rokoko Plugin'
}
'''
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
        
        #for bone in armature_smash.data.bones:
        for bone in armature_other.data.bones:
            bone_item = context.scene.bone_list.add()
            #bone_item.bone_name_smash = bone.name
            bone_item.bone_name_other = bone.name
            
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
            
        bpy.ops.object.mode_set(mode='POSE')
        new_bones = new_arma.pose.bones
        smash_arma = get_smash_armature()
        smash_bones = smash_arma.pose.bones
        for new_bone in new_bones:
            paired_bone_name = None
            for entry in context.scene.bone_list:
                if entry.bone_name_other == new_bone.name:
                    paired_bone_name = entry.bone_name_smash
            if paired_bone_name is None:
                continue
            print('Paired Bone Name = %s' % paired_bone_name)
            paired_bone = smash_bones.get(paired_bone_name, None)
            if paired_bone is None:
                continue
            
            self.create_constraints(new_arma, new_bone, paired_bone)
        
        return {'FINISHED'}    

class ExportSkelJson(bpy.types.Operator):
    bl_idname = 'sub.export_skel_json'
    bl_label =  'Exports Armature to JSON'
    bl_description = 'Exports the armature to a JSON that you can then convert to a .NUSKTB'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        normalBones = []
        swingBones = []
        miscBones = []
        nullBones = []
        helperBones = []

        outputBones = []
        eb = bpy.context.object.data.edit_bones
        keys = eb.keys()
        for key in keys:
            if 'S_' in key:
                swingBones.append(eb[key])
            elif any(ss in key for ss in ['_eff', '_offset'] ):
                nullBones.append(eb[key])
            elif 'H_' in key:
                helperBones.append(eb[key])
            elif any(ss in key for ss in ['Mouth', 'Finger', 'Face']) or key == 'Have':
                miscBones.append(eb[key])
                for child in eb[key].children_recursive:
                    if any(ss in child.name for ss in ['_eff', '_offset']):
                        continue
                    miscBones.append(child)
                    keys.remove(child.name)
            else:
                normalBones.append(eb[key])
                
        for boneList in [normalBones, swingBones, miscBones, nullBones, helperBones]:
            for bone in boneList:
                if bone.use_deform == False:
                    continue
                outputBones.append(bone)

        output = {}
        output['data'] = {}
        output['data']['Skel'] = {}
        output['data']['Skel']['major_version'] = 1
        output['data']['Skel']['minor_version'] = 0
        output['data']['Skel']['bone_entries'] = []
        boneEntries = output['data']['Skel']['bone_entries']
        for index, bone in enumerate(outputBones):
            boneEntry = {}
            boneEntry['name'] = bone.name
            boneEntry['index'] = index
            boneEntry['parent_index'] = outputBones.index(bone.parent) if bone.parent else -1
            boneEntry['flags'] = {}
            boneEntry['flags']['bytes'] = [1,0,0,0]
            boneEntries.append(boneEntry)
            
        output['data']['Skel']['world_transforms'] = []
        worldTransforms = output['data']['Skel']['world_transforms']
        for bone in outputBones:
            transform = {}
            m = bone.matrix
            for row in [1,2,3,4]:
                transform['row%s' % row] = {}
                transform['row%s' % row]['x'] = m[0][row - 1]
                transform['row%s' % row]['y'] = m[1][row - 1]
                transform['row%s' % row]['z'] = m[2][row - 1]
                transform['row%s' % row]['w'] = m[3][row - 1]
            worldTransforms.append(transform)       

        output['data']['Skel']['inv_world_transforms'] = []          
        invWorldTransforms = output['data']['Skel']['inv_world_transforms']
        for bone in outputBones:
            transform = {}
            m = bone.matrix.inverted()
            for row in [1,2,3,4]:
                transform['row%s' % row] = {}
                transform['row%s' % row]['x'] = m[0][row - 1]
                transform['row%s' % row]['y'] = m[1][row - 1]
                transform['row%s' % row]['z'] = m[2][row - 1]
                transform['row%s' % row]['w'] = m[3][row - 1]
            invWorldTransforms.append(transform) 

        output['data']['Skel']['transforms'] = []
        relativeTransforms = output['data']['Skel']['transforms']   
        for bone in outputBones:
            transform = {}
            m = bone.parent.matrix.inverted() @ bone.matrix if bone.parent else bone.matrix
            for row in [1,2,3,4]:
                transform['row%s' % row] = {}
                transform['row%s' % row]['x'] = m[0][row - 1]
                transform['row%s' % row]['y'] = m[1][row - 1]
                transform['row%s' % row]['z'] = m[2][row - 1]
                transform['row%s' % row]['w'] = m[3][row - 1]
            relativeTransforms.append(transform) 
            
        output['data']['Skel']['inv_transforms'] = []
        invRelativeTransforms = output['data']['Skel']['inv_transforms']   
        for bone in outputBones:
            transform = {}
            m = bone.parent.matrix.inverted() @ bone.matrix if bone.parent else bone.matrix
            m = m.inverted()
            for row in [1,2,3,4]:
                transform['row%s' % row] = {}
                transform['row%s' % row]['x'] = m[0][row - 1]
                transform['row%s' % row]['y'] = m[1][row - 1]
                transform['row%s' % row]['z'] = m[2][row - 1]
                transform['row%s' % row]['w'] = m[3][row - 1]
            invRelativeTransforms.append(transform)
        text = bpy.data.texts.new('SUB_SKEL_JSON')
        text.write(json.dumps(output, indent = 2))
        return {'FINISHED'}  

class ExportHelperBoneJson(bpy.types.Operator):
    bl_idname = 'sub.export_helper_bone_json'
    bl_label = 'Export Helper Bone Json'
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
        
        #other_bones = get_other_armature().pose.bones
        smash_bones = get_smash_armature().pose.bones
        new_bones = bpy.context.object.pose.bones
        
        paired_bones = {}
        for entry in context.scene.bone_list:
            if entry.bone_name_other is '' or entry.bone_name_smash is '':
                continue
            paired_bones['%s' % entry.bone_name_other] = '%s' % entry.bone_name_smash
        
        index = 0
        for other_bone_name, smash_bone_name in paired_bones.items():
            if 'H_' not in other_bone_name:
                continue
            interpolation_entry = {}
            interpolation_entry['name'] = 'nuHelperBoneRotateInterp%s' % (index + 3000)
            smash_bone = smash_bones.get(smash_bone_name, None)
            #other_bone = other_bones.get(other_bone_name, None)
            new_bone = new_bones.get(other_bone_name, None)
            '''
            print('??? smash_bone=%s, other_bone=%s' % (smash_bone_name, other_bone_name))
            if smash_bone is None or other_bone is None:
                print(" :sadness:   smash_bone = %s, smash_bone_name = %s, other_bone=%s, other_bone_name=%s"
                      % (smash_bone, smash_bone_name, other_bone, other_bone_name))
                print('\U0001f44d')
            '''
            degrees = math.degrees
            interpolation_entry['bone_name'] = smash_bone.parent.name
            interpolation_entry['root_bone_name'] = smash_bone.parent.name
            interpolation_entry['parent_bone_name'] = smash_bone.name
            interpolation_entry['driver_bone_name'] = other_bone_name
            interpolation_entry['unk_type'] = 1
            interpolation_entry['aoi'] = {}
            interpolation_entry['aoi']['x'] = new_bone.constraints.get('SUB CRC X').influence
            interpolation_entry['aoi']['y'] = new_bone.constraints.get('SUB CRC Y').influence
            interpolation_entry['aoi']['z'] = new_bone.constraints.get('SUB CRC Z').influence
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
            lrc = new_bone.constraints.get('SUB LRC', None)
            interpolation_entry['range_min']['x'] = max(-180, degrees(lrc.min_x))
            interpolation_entry['range_min']['y'] = max(-180, degrees(lrc.min_y))
            interpolation_entry['range_min']['z'] = max(-180, degrees(lrc.min_z))
            interpolation_entry['range_max'] = {}
            interpolation_entry['range_max']['x'] = min(180, degrees(lrc.max_x))
            interpolation_entry['range_max']['y'] = min(180, degrees(lrc.max_y))
            interpolation_entry['range_max']['z'] = min(180, degrees(lrc.max_z))
            interpolation_entries.append(interpolation_entry)  
            list_one.append(index)
            list_two.append(1)
            index = index + 1
        text = bpy.data.texts.new('SUB_HELPER_BONE_JSON')
        text.write(json.dumps(output, indent = 2))
        return {'FINISHED'}       
        
class SUB_UL_BoneList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        #other_armature = get_other_armature()
        other_armature = get_other_armature()
        smash_armature = get_smash_armature()
        
        layout = layout.split(factor=0.36, align=True)
        #layout.label(text=item.bone_name_smash)\
        layout.label(text=item.bone_name_other)
        if other_armature and smash_armature:
            layout.prop_search(item, 'bone_name_smash', smash_armature.pose, 'bones', text='')
    
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
        
        layout.separator()
        
        row = layout.row(align=True)
        row.template_list('SUB_UL_BoneList', 'Bone List', context.scene, 'bone_list', context.scene, 'bone_list_index', rows=1, maxrows=10)
    
        row = layout.row(align=True)
        row.operator(MakeCombinedSkeleton.bl_idname, text='Make New Combined Skeleton')
        
        row = layout.row(align=True)
        row.operator(ExportHelperBoneJson.bl_idname, text='Create Helper Bone JSON Text')
        
        row = layout.row(align=True)
        row.operator(ExportSkelJson.bl_idname, text='Create Skel Json')
'''
class ExoSkelProperties(bpy.types.PropertyGroup):
    smash_armature = PointerProperty(
        name='Smash Armature',
        description='Select the Smash armature',
        type=Object,
        poll=poll_armatures,
        #update=?
    )

    other_armature = PointerProperty(
        name='Other Armature',
        description='Select the Other armature',
        type=Object,
        poll=poll_other_armatures,
        #update=?
    )

    bone_list = CollectionProperty(
        type=BoneListItem
    )

    bone_list_index = IntProperty(
        name="Index for the exo bone list",
        default=0
    )
    armature_prefix = StringProperty(
        name="Prefix",
        description="The Prefix that will be added to the bones in the 'Other' armature. Must begin with H_ or else it wont work!",
        default="H_Exo_"
    )
'''
    