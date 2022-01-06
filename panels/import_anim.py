import math
import bpy
from .. import ssbh_data_py
from bpy_extras.io_utils import ImportHelper
from bpy.props import IntProperty, StringProperty, BoolProperty
from bpy.types import Operator
import mathutils

def poll_cameras(self, obj):
    return obj.type == 'CAMERA'

class ImportAnimPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Animation Importer'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        row = layout.row(align=True)
        row.label(text='Select an armature or camera to import an animation over')

        if context.scene.sub_anim_armature is None and context.scene.sub_anim_camera is None:
            row = layout.row(align=True)
            row.prop(context.scene, 'sub_anim_armature', icon='ARMATURE_DATA')
            row = layout.row(align=True)
            row.prop(context.scene, 'sub_anim_camera', icon='VIEW_CAMERA')
            return
        elif context.scene.sub_anim_armature is not None:
            row = layout.row(align=True)
            row.label(text=f'Selected armature: {context.scene.sub_anim_armature.name}')
            row.operator('sub.anim_armature_clear', icon='CANCEL', text='Clear Selected Armature')
            row = layout.row(align=True)
            row.operator('sub.anim_model_importer', icon='FILE', text='Import a Model Animation')
        elif context.scene.sub_anim_camera is not None:
            row = layout.row(align=True)
            row.label(text=f'Selected camera: {context.scene.sub_anim_camera.name}')
            row.operator('sub.anim_camera_clear', icon='CANCEL', text='Clear Selected Camera')
        
        

class AnimArmatureClearOperator(Operator):
    bl_idname = 'sub.anim_armature_clear'
    bl_label = 'Anim Armature Clear Operator'

    def execute(self, context):
        context.scene.sub_anim_armature = None
        return {'FINISHED'}

class AnimCameraClearOperator(Operator):
    bl_idname = 'sub.anim_camera_clear'
    bl_label = 'Anim Camera Clear Operator'

    def execute(self, context):
        context.scene.sub_anim_camera = None
        return {'FINISHED'}

class AnimModelImporterOperator(Operator, ImportHelper):
    bl_idname = 'sub.anim_model_importer'
    bl_label = 'Import Anim'

    filter_glob: StringProperty(
        default='*.nuanmb',
        options={'HIDDEN'}
    )
    include_transform_track: BoolProperty(
        name='Include Transform',
        description='Include Transform Track',
        default=True,
    )
    include_material_track: BoolProperty(
        name='Include Material',
        description='Include Material Track',
        default=True,
    )
    include_visibility_track: BoolProperty(
        name='Include Visibility',
        description='Include Visibility Track',
        default=True,
    )
    first_blender_frame: IntProperty(
        name='Start Frame',
        description='What frame to start importing the track on',
        default=1,
    )
    def execute(self, context):
        import_model_anim(context, self.filepath,
                        self.include_transform_track, self.include_material_track,
                        self.include_visibility_track, self.first_blender_frame)
        return {'FINISHED'}
    
def import_model_anim(context, filepath,
                    include_transform_track, include_material_track,
                    include_visibility_track, first_blender_frame):
    ssbh_anim_data = ssbh_data_py.anim_data.read_anim(filepath)
    transform_group, visibility_group, material_group = None, None, None
    for group in ssbh_anim_data.groups:
        if group.group_type.name == 'Transform':
            transform_group = group
        elif group.group_type.name == 'Visibility':
            visibility_group = group
        elif group.group_type.name == 'Material':
            material_group = group
        else:
            print(f'Unknown Group Type {group.group_type.name} detected!')

    # Find max frame count
    frame_count = 0
    for group in ssbh_anim_data.groups:
        for node in group.nodes:
            for track in node.tracks:
                frame_count = max(frame_count, len(track.values))

    scene = context.scene
    scene.frame_start = first_blender_frame
    scene.frame_end = scene.frame_start + frame_count - 1
    scene.frame_set(scene.frame_start)
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False) # whatever object is currently selected, exit whatever mode its in
    context.view_layer.objects.active = context.scene.sub_anim_armature
    bpy.ops.object.mode_set(mode='EDIT', toggle=False) 
    bone_name_to_edit_bone_matrix = {bone.name:bone.matrix.copy() for bone in context.scene.sub_anim_armature.data.edit_bones}
    print(bone_name_to_edit_bone_matrix) # DEBUG, remove for release
    bpy.ops.object.mode_set(mode='POSE', toggle=False) # put our armature in pose mode
    
    if include_transform_track:
        from pathlib import Path
        action_name = context.scene.sub_anim_armature.name + ' ' + Path(filepath).name
        if context.scene.sub_anim_armature.animation_data is None:
            context.scene.sub_anim_armature.animation_data_create()
        action = bpy.data.actions.new(action_name)
        context.scene.sub_anim_armature.animation_data.action = action
        bones = context.scene.sub_anim_armature.pose.bones
        bone_to_node = {b:n for n in transform_group.nodes for b in bones if b.name == n.name}
    
    for index, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)): # +1 because range() excludes the final value
        scene.frame_set(frame)
        if include_transform_track:
            do_armature_transform_stuff(context, transform_group, index, frame, bone_to_node, bone_name_to_edit_bone_matrix)
        if include_material_track:
            do_material_stuff(context, material_group, index, frame)
        if include_visibility_track:
            do_visibility_stuff(context, visibility_group, index, frame)
    
    scene.frame_set(scene.frame_start) # Return to the first frame for convenience
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False) # Done with our object, return to pose mode
    

def do_armature_transform_stuff(context, transform_group, index, frame, bone_to_node, bone_name_to_edit_bone_matrix):
    bones = context.scene.sub_anim_armature.pose.bones
    for bone in bones: # Traverses the bone array in heirarchy order, starting from the root
        node = bone_to_node.get(bone, None)
        if node is None: # Not all bones will have a transform node. For example, helper bones never have transforms in the anim.
            #print(f'Skipping bone "{bone.name}", no associated node')
            continue   
        try:
            node.tracks[0].values[index]
        except IndexError: # Not all bones will have a value at every frame. Many bones only have one frame.
            continue

        t = translation = node.tracks[0].values[index].translation
        r = rotation = node.tracks[0].values[index].rotation
        '''
         for i in [0,1,2,3]:
            if math.isnan(r[i]):
                #print(f'bone="{bone.name}", index = "{index}", rotation ={r}')
        '''
        s = scale = node.tracks[0].values[index].scale
        cs = compensate_scale = node.tracks[0].scale_options.compensate_scale
        
        tm = translation_matrix = mathutils.Matrix.Translation(t)
        qr = quaternion_rotation = mathutils.Quaternion([r[3], r[0], r[1], r[2]])
        rm = rotation_matrix = mathutils.Matrix.Rotation(qr.angle, 4, qr.axis)
        sx = scale_matrix_x = mathutils.Matrix.Scale(s[0], 4, (1,0,0))
        sy = scale_matrix_y = mathutils.Matrix.Scale(s[1], 4, (0,1,0))
        sz = scale_matrix_z = mathutils.Matrix.Scale(s[2], 4, (0,1,0))
        nm = new_matrix = mathutils.Matrix(tm @ rm @ sx @ sy @ sz)

        true_row_0 = bone.bone['row_0'][:]
        true_row_1 = bone.bone['row_1'][:]
        true_row_2 = bone.bone['row_2'][:]
        true_row_3 = bone.bone['row_3'][:]

        if bone.parent is not None:
            p_true_row_0 = bone.parent.bone['row_0'][:]
            p_true_row_1 = bone.parent.bone['row_1'][:]
            p_true_row_2 = bone.parent.bone['row_2'][:]
            p_true_row_3 = bone.parent.bone['row_3'][:]
            p_offset_row_0 = bone.parent.bone['offset_row_0'][:]
            p_offset_row_1 = bone.parent.bone['offset_row_1'][:]
            p_offset_row_2 = bone.parent.bone['offset_row_2'][:]
            p_offset_row_3 = bone.parent.bone['offset_row_3'][:]
            m_p_true = matrix_parent_true = mathutils.Matrix([p_true_row_0, p_true_row_1, p_true_row_2, p_true_row_3])
            m_p_edit = matrix_parent_edit_bone_matrix = bone_name_to_edit_bone_matrix[bone.parent.name]
            #m_p_off = matrix_parent_offset = m_p_true.inverted() @ m_p_edit
            m_p_off = matrix_parent_offset = mathutils.Matrix([p_offset_row_0, p_offset_row_1, p_offset_row_2, p_offset_row_3])

        m_true = matrix_true = mathutils.Matrix([true_row_0, true_row_1, true_row_2, true_row_3])
        m_edit = matrix_edit_bone_matrix = bone_name_to_edit_bone_matrix[bone.name]
        #m_off = matrix_offset = m_true.inverted() @ m_edit
        offset_row_0 = bone.bone['offset_row_0'][:]
        offset_row_1 = bone.bone['offset_row_1'][:]
        offset_row_2 = bone.bone['offset_row_2'][:]
        offset_row_3 = bone.bone['offset_row_3'][:]
        m_off = mathutils.Matrix([offset_row_0, offset_row_1, offset_row_2, offset_row_3])
        if bone.parent is None:
            bone.matrix = new_matrix @ m_off
        else:
            bone.matrix = bone.parent.matrix @ m_p_off.inverted() @ new_matrix @ m_off
        '''
        Turns out this wasn't correct, still dont know what "compensate scale" even does.
        Its not set for any of sonics main bones, so i still have no idea what im missing
        to properly predict scaling inheritance, or how to properly export it.
        
        bone.bone.inherit_scale = 'NONE' if cs == 1.0 else 'FULL'
        context.scene.sub_anim_armature.data.bones[bone.name].keyframe_insert(
                    data_path='inherit_scale',
                    frame=frame,
                    group=bone.name
                )
        '''
        
        keyframe_insert_bone_locrotscale(context.scene.sub_anim_armature, bone.name, frame, bone.name)

def keyframe_insert_bone_locrotscale(armature, bone_name, frame, group_name):
    for parameter in ['location', 'rotation_quaternion', 'scale']:
        armature.keyframe_insert(
            data_path=f'pose.bones["{bone_name}"].{parameter}',
            frame=frame,
            group=group_name
        )

def do_camera_transform_stuff(context, transform_group, index, frame):
    pass

def do_material_stuff(context, material_group, index, frame):
    pass

def do_visibility_stuff(context, visibility_group, index, frame):
    pass

def do_camera_settings_stuff(context, camera_group, index, frame):
    pass

