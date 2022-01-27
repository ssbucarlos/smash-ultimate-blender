import math
import bpy
from .. import ssbh_data_py
from bpy_extras.io_utils import ImportHelper
from bpy.props import IntProperty, StringProperty, BoolProperty
from bpy.types import Operator
import mathutils
from .import_model import reorient, reorient_root
import re

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
    frame_count = ssbh_anim_data.final_frame_index + 1

    scene = context.scene
    scene.frame_start = first_blender_frame
    scene.frame_end = scene.frame_start + frame_count - 1
    scene.frame_set(scene.frame_start)
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False) # whatever object is currently selected, exit whatever mode its in
    context.view_layer.objects.active = context.scene.sub_anim_armature
    bpy.ops.object.mode_set(mode='EDIT', toggle=False) 
    bone_name_to_edit_bone_matrix = {bone.name:bone.matrix.copy() for bone in context.scene.sub_anim_armature.data.edit_bones}
    #print(bone_name_to_edit_bone_matrix) # DEBUG, remove for release
    bpy.ops.object.mode_set(mode='POSE', toggle=False) # put our armature in pose mode
    
    from pathlib import Path
    action_name = context.scene.sub_anim_armature.name + ' ' + Path(filepath).name
    if context.scene.sub_anim_armature.animation_data is None:
        context.scene.sub_anim_armature.animation_data_create()
    action = bpy.data.actions.new(action_name)
    context.scene.sub_anim_armature.animation_data.action = action

    if include_transform_track:
        bones = context.scene.sub_anim_armature.pose.bones
        bone_to_node = {b:n for n in transform_group.nodes for b in bones if b.name == n.name}
    
    if include_visibility_track:
        setup_visibility_drivers(context, visibility_group)

    if include_material_track:
        setup_material_drivers(context, material_group)

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

def poll_cameras(self, obj):
    return obj.type == 'CAMERA'

def do_armature_transform_stuff(context, transform_group, index, frame, bone_to_node, bone_name_to_edit_bone_matrix):
    bones = context.scene.sub_anim_armature.pose.bones
    # Get a list of bones in 'heirarchal' order
    # TODO: make own function
    def heirarchy_order(bone, reordered):
        if bone not in reordered:
            reordered.append(bone)
        for child in bone.children:
            heirarchy_order(child, reordered)
    reordered = []
    heirarchy_order(bones[0], reordered)

    for bone in reordered:
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
        s = scale = node.tracks[0].values[index].scale
        compensate_scale = node.tracks[0].scale_options.compensate_scale
        inherit_scale = node.tracks[0].scale_options.inherit_scale
        tm = translation_matrix = mathutils.Matrix.Translation(t)
        qr = quaternion_rotation = mathutils.Quaternion([r[3], r[0], r[1], r[2]])
        rm = rotation_matrix = mathutils.Matrix.Rotation(qr.angle, 4, qr.axis)
        sx = scale_matrix_x = mathutils.Matrix.Scale(s[0], 4, (1,0,0))
        sy = scale_matrix_y = mathutils.Matrix.Scale(s[1], 4, (0,1,0))
        sz = scale_matrix_z = mathutils.Matrix.Scale(s[2], 4, (0,0,1))
        raw_m = raw_matrix = mathutils.Matrix(tm @ rm @ sx @ sy @ sz)       
        
        if bone.parent is not None:
            fm = fixed_matrix = reorient(raw_m, transpose=False)
            bone.matrix = bone.parent.matrix @ fm
        else:
            fm = fixed_matrix = reorient_root(raw_m, transpose=False)
            bone.matrix = fm
        
        keyframe_insert_bone_locrotscale(context.scene.sub_anim_armature, bone.name, frame, 'Transform')

def keyframe_insert_bone_locrotscale(armature, bone_name, frame, group_name):
    for parameter in ['location', 'rotation_quaternion', 'scale']:
        armature.keyframe_insert(
            data_path=f'pose.bones["{bone_name}"].{parameter}',
            frame=frame,
            group=group_name
        )

def do_camera_transform_stuff(context, transform_group, index, frame):
    pass

def node_input_driver_add(input, data_path):
    driver_handle = input.driver_add('default_value')
    var = driver_handle.driver.variables.new()
    var.name = "var"
    target = var.targets[0]
    target.id = bpy.context.scene.sub_anim_armature
    target.data_path = f'{data_path}'
    driver_handle.driver.expression = f'{var.name}'

def sampler_uv_transform_driver_add(sampler_node, row, var_name, material, target, target_data_path, expression):
    input = sampler_node.inputs.get('UV Transform')
    driver_handle = input.driver_add('default_value', row)
    var = driver_handle.driver.variables.new()
    var.name = var_name
    driver_target = var.targets[0]
    driver_target.id_type = 'MATERIAL'
    driver_target.id = material
    driver_target.data_path = "node_tree." + target.path_from_id(target_data_path)
    driver_handle.driver.expression = expression

def setup_material_drivers(context, material_group):
    mesh_children = [child for child in context.scene.sub_anim_armature.children if child.type == 'MESH']
    materials = {material_slot.material for mesh in mesh_children for material_slot in mesh.material_slots }
    name_node_dict = {node.name : node for node in material_group.nodes}

    for node in material_group.nodes:
        for track in node.tracks:
            value = track.values[0]
            context.scene.sub_anim_armature[f"{node.name}:{track.name}"] = value


    for material in materials:
        bsn = blender_shader_node = material.node_tree.nodes.get('smash_ultimate_shader', None)
        if bsn is None:
            #logging.info(f'Material {material.name} did not have the smash_ultimate_shader node, will not have material animations')
            continue
        mat_name_input = bsn.inputs.get('Material Name')
        anim_node = name_node_dict.get(mat_name_input.default_value, None)
        if anim_node is None:
            continue # This is very common, most fighter anims only contain material info for the eye materials for instance
        for track in anim_node.tracks:
            if track.name == 'CustomVector31':
                x,y,z,w = [i for i in bsn.inputs if 'CustomVector31' in i.name]
                for index, var in enumerate([x,y,z,w]):
                    node_input_driver_add(var, f'["{anim_node.name}:{track.name}"][{index}]')
                labels_nodes_dict = {node.label:node for node in material.node_tree.nodes}
                sampler_1_node = labels_nodes_dict.get('Sampler1', None)
                if sampler_1_node is not None:
                    sampler_uv_transform_driver_add(sampler_1_node, 0, "var", material, z, 'default_value', "0 - var")
                    sampler_uv_transform_driver_add(sampler_1_node, 1, "var", material, w, 'default_value', "0 - var")


def do_material_stuff(context, material_group, index, frame):
    for node in material_group.nodes:
        for track in node.tracks:
            try:
                track.values[index]
            except IndexError:
                continue
            value = track.values[index]
            arma = context.scene.sub_anim_armature
            arma[f'{node.name}:{track.name}'] = value
            arma.keyframe_insert(data_path=f'["{node.name}:{track.name}"]', frame=frame, group='Material', options={'INSERTKEY_NEEDED'})


def setup_visibility_drivers(context, visibility_group):
    mesh_children = [child for child in context.scene.sub_anim_armature.children if child.type == 'MESH']
    
    # Create the custom property on the armature
    for node in visibility_group.nodes:
        context.scene.sub_anim_armature[f"{node.name}"] = True

    # Setup the mesh drivers
    for node in visibility_group.nodes:
        for mesh in mesh_children:
            true_mesh_name = re.split('Shape|_VIS_|_O_', mesh.name)[0]
            if true_mesh_name == node.name:
                for property in ['hide_viewport', 'hide_render']:
                    driver_handle = mesh.driver_add(property)
                    var = driver_handle.driver.variables.new()
                    var.name = "var"
                    target = var.targets[0]
                    target.id = context.scene.sub_anim_armature
                    target.data_path = f'["{true_mesh_name}"]'
                    driver_handle.driver.expression = f'1 - {var.name}'

def do_visibility_stuff(context, visibility_group, index, frame):
    for node in visibility_group.nodes:
        try:
            node.tracks[0].values[index]
        except IndexError: # Not every vis track entry will have values on every frame. Many only have the first frame.
            continue
        value = node.tracks[0].values[index]

        arma = context.scene.sub_anim_armature
        arma[f'{node.name}'] = value
        arma.keyframe_insert(data_path=f'["{node.name}"]', frame=frame, group='Visibility', options={'INSERTKEY_NEEDED'})


def do_camera_settings_stuff(context, camera_group, index, frame):
    pass