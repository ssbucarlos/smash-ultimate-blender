import math
from os import name
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
            row = layout.row(align=True)
            row.operator('sub.anim_camera_importer', icon='FILE', text='Import a Camera Animation')

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

class AnimCameraImporterOperator(Operator, ImportHelper):
    bl_idname = 'sub.anim_camera_importer'
    bl_label = 'Import Camera Anim'

    filter_glob: StringProperty(
        default='*.nuanmb',
        options={'HIDDEN'}
    )

    first_blender_frame: IntProperty(
        name='Start Frame',
        description='What frame to start importing the track on',
        default=1,
    )
    def execute(self, context):
        import_camera_anim(context, self.filepath, self.first_blender_frame)
        return {'FINISHED'}
    
def poll_cameras(self, obj):
    return obj.type == 'CAMERA'

def import_model_anim(context, filepath,
                    include_transform_track, include_material_track,
                    include_visibility_track, first_blender_frame):
    ssbh_anim_data = ssbh_data_py.anim_data.read_anim(filepath)
    name_group_dict = {group.group_type.name : group for group in ssbh_anim_data.groups}
    transform_group = name_group_dict.get('Transform', None)
    visibility_group = name_group_dict.get('Visibility', None)
    material_group = name_group_dict.get('Material', None)

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

    if include_transform_track and transform_group is not None:
        bones = context.scene.sub_anim_armature.pose.bones
        bone_to_node = {b:n for n in transform_group.nodes for b in bones if b.name == n.name}
        setup_bone_scale_drivers(bone_to_node.keys()) # Only want to setup drivers for the bones that have an entry in the anim
    
    if include_visibility_track and visibility_group is not None:
        setup_visibility_drivers(context, visibility_group)

    if include_material_track and material_group is not None:
        setup_material_drivers(context, material_group)

    for index, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)): # +1 because range() excludes the final value
        scene.frame_set(frame)
        if include_transform_track and transform_group is not None:
            do_armature_transform_stuff(context, transform_group, index, frame, bone_to_node, bone_name_to_edit_bone_matrix)
        if include_material_track and material_group is not None:
            do_material_stuff(context, material_group, index, frame)
        if include_visibility_track and visibility_group is not None:
            do_visibility_stuff(context, visibility_group, index, frame)
    
    scene.frame_set(scene.frame_start) # Return to the first frame for convenience
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False) # Done with our object, return to pose mode

def setup_bone_scale_drivers(pose_bones):
    for pose_bone in pose_bones:
        # Setup default values for drivers to work, will get overwritten by the anim later anyways
        # TODO: theres 4 combos of inherit_scale and compensate_scale together, i am honestly not sure how to make use
        # of compensate_scale, however whenever 'inherit_scale' is 0, setting the blender scale inheritance to 'None' seems
        # to do the trick. Its possible the other blender scale inheritance types can approximate
        pose_bone['inherit_scale'] = 1 # The custom properties exist on the pose_bone, not the bone...
        pose_bone['compensate_scale'] = 1
        driver_handle = pose_bone.bone.driver_add('inherit_scale') # ... but drivers belong on the bone, not the pose_bone
        inheritscale_var = driver_handle.driver.variables.new()
        inheritscale_var.name = "inherit_scale"
        isv = inheritscale_var # shorthand for this var
        target = inheritscale_var.targets[0]
        target.id = bpy.context.scene.sub_anim_armature
        target.data_path = f'pose.bones["{pose_bone.name}"]["inherit_scale"]'
        # TODO: Figure out how to incorporate compensate scale
        driver_handle.driver.expression = f'0 if {isv.name} == 1 else 3' # 0 is 'FULL' and 3 is 'NONE'


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

        from mathutils import Matrix, Quaternion
        t = translation = node.tracks[0].values[index].translation
        r = rotation = node.tracks[0].values[index].rotation
        s = scale = node.tracks[0].values[index].scale
        compensate_scale = node.tracks[0].scale_options.compensate_scale
        inherit_scale = node.tracks[0].scale_options.inherit_scale
        tm = translation_matrix = Matrix.Translation(t)
        qr = quaternion_rotation = Quaternion([r[3], r[0], r[1], r[2]])
        rm = rotation_matrix = Matrix.Rotation(qr.angle, 4, qr.axis)
        sx = scale_matrix_x = Matrix.Scale(s[0], 4, (1,0,0))
        sy = scale_matrix_y = Matrix.Scale(s[1], 4, (0,1,0))
        sz = scale_matrix_z = Matrix.Scale(s[2], 4, (0,0,1))
        '''
        Ok the old code was taking the parents matrix and then mutliplying the childs matrix
        but im pretty sure this would mutiply the scales together, which is not what i want
        raw_m = raw_matrix = mathutils.Matrix(tm @ rm @ sx @ sy @ sz)       
        
        if bone.parent is not None:
            fm = fixed_matrix = reorient(raw_m, transpose=False)
            bone.matrix = bone.parent.matrix @ fm
        else:
            fm = fixed_matrix = reorient_root(raw_m, transpose=False)
            bone.matrix = fm
        '''


        raw_m = raw_matrix = mathutils.Matrix(tm @ rm @ sx @ sy @ sz)   
        if bone.parent is not None:
            if compensate_scale and not inherit_scale:
                '''
                pm = parent_matrix = bone.parent.matrix
                pmsv = parent_matrix_scale_vector = pm.to_scale()
                pmsmx = parent_matrix_scale_matrix_x = Matrix.Scale(pmsv[0], 4, (1,0,0))
                pmsmy = parent_matrix_scale_matrix_y = Matrix.Scale(pmsv[1], 4, (0,1,0))
                pmsmz = parent_matrix_scale_matrix_z = Matrix.Scale(pmsv[2], 4, (0,0,1))
                pmsm = parent_matrix_scale_matrix = pmsmx @ pmsmy @ pmsmz
                '''
                fm = fixed_matrix = reorient(raw_m, transpose=False)
                '''
                #bone.matrix = pm @ pmsm.inverted() @ fm
                debug_bone_names = ['LegR', 'KneeR', 'FootR', 'ToeR']
                if bone.name in debug_bone_names and frame==9:
                    print(f'bone={bone.name}, {bone.matrix.to_translation()}, {pm.to_translation()}, {fm.to_translation()}')
                    rm = bone.bone.parent.matrix_local.inverted() @ bone.bone.matrix_local # Rest Pose Relative Matrix
                    bone.matrix_basis = rm.inverted() @ fm
                else:
                    bone.matrix = pm @ pmsm.inverted() @ fm
                '''
                rm = bone.bone.parent.matrix_local.inverted() @ bone.bone.matrix_local # Rest Pose Relative Matrix
                bone.matrix_basis = rm.inverted() @ fm
            else:
                fm = fixed_matrix = reorient(raw_m, transpose=False)
                bone.matrix = bone.parent.matrix @ fm
        else:
            fm = fixed_matrix = reorient_root(raw_m, transpose=False)
            bone.matrix = fm

        keyframe_insert_bone_locrotscale(context.scene.sub_anim_armature, bone.name, frame, 'Transform')

        bone['compensate_scale'] = compensate_scale
        bone['inherit_scale'] = inherit_scale
        bone.keyframe_insert(
            data_path=f'["compensate_scale"]',
            frame=frame,
            group='Transform',
            options={'INSERTKEY_NEEDED'},
        )
        bone.keyframe_insert(
            data_path=f'["inherit_scale"]',
            frame=frame,
            group='Transform',
            options={'INSERTKEY_NEEDED'},
        )


def keyframe_insert_bone_locrotscale(armature, bone_name, frame, group_name):
    for parameter in ['location', 'rotation_quaternion', 'scale']:
        armature.keyframe_insert(
            data_path=f'pose.bones["{bone_name}"].{parameter}',
            frame=frame,
            group=group_name,
            options={'INSERTKEY_NEEDED'},
        )

def keyframe_insert_camera_locrotscale(camera, frame):
    for parameter in ['location', 'rotation_quaternion', 'scale']:
        camera.keyframe_insert(
            data_path=f'{parameter}',
            frame=frame,
            group='Transform',
            options={'INSERTKEY_NEEDED'},
        ) 

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

def uvtransform_to_list(uvtransform) -> list[float]:
    scale_u = uvtransform.scale_u
    scale_v = uvtransform.scale_v
    rotation = uvtransform.rotation
    translate_u = uvtransform.translate_u
    translate_v = uvtransform.translate_v
    return [scale_u, scale_v, rotation, translate_u, translate_v]

def setup_material_drivers(context, material_group):
    mesh_children = [child for child in context.scene.sub_anim_armature.children if child.type == 'MESH']
    materials = {material_slot.material for mesh in mesh_children for material_slot in mesh.material_slots }
    name_node_dict = {node.name : node for node in material_group.nodes}

    for node in material_group.nodes:
        for track in node.tracks:
            value = track.values[0]
            if isinstance(value, ssbh_data_py.anim_data.UvTransform):
                context.scene.sub_anim_armature[f'{node.name}:{track.name}'] = uvtransform_to_list(value)
            else:
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
            if isinstance(value, ssbh_data_py.anim_data.UvTransform):
                arma[f'{node.name}:{track.name}'] = uvtransform_to_list(value)
            else:
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

def import_camera_anim(context, filepath, first_blender_frame):
    camera = context.scene.sub_anim_camera
    ssbh_anim_data = ssbh_data_py.anim_data.read_anim(filepath)
    name_group_dict = {group.group_type.name : group for group in ssbh_anim_data.groups}
    transform_group = name_group_dict.get('Transform')
    camera_group = name_group_dict.get('Camera')

    frame_count = ssbh_anim_data.final_frame_index + 1
    scene = context.scene
    scene.frame_start = first_blender_frame
    scene.frame_end = scene.frame_start + frame_count - 1
    scene.frame_set(scene.frame_start)

    try:
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False) # whatever object is currently selected, exit whatever mode its in
    except RuntimeError: # There may not have been any active or selected object
        pass
    context.view_layer.objects.active = camera

    from pathlib import Path
    action_name = camera.name + ' ' + Path(filepath).name
    if camera.animation_data is None:
        camera.animation_data_create()
    action = bpy.data.actions.new(action_name)
    camera.animation_data.action = action
    camera.matrix_local.identity()
    camera.rotation_mode = 'QUATERNION'

    for index, frame in enumerate(range(scene.frame_start, scene.frame_end+1)):
        scene.frame_set(frame)
        if camera_group is not None:
            update_camera_properties(context, camera_group, index, frame)
        if transform_group is not None:
            update_camera_transforms(context, transform_group, index, frame)

def update_camera_properties(context, camera_group, index, frame):
    camera = context.scene.sub_anim_camera
    for node in camera_group.nodes:
        for track in node.tracks:
            try: 
                track.values[index]
            except IndexError:
                continue
            value = track.values[index]
            camera[f'{track.name}'] = value
            camera.keyframe_insert(
                data_path=f'["{track.name}"]',
                frame=frame,
                group='Camera',
                options={'INSERTKEY_NEEDED'},
            ) 

def update_camera_transforms(context, transform_group, index, frame):
    value = transform_group.nodes[0].tracks[0].values[index]
    from mathutils import Matrix, Quaternion
    rt = raw_translation = value.translation
    rr = raw_rotation = value.rotation
    rs = raw_scale = value.scale
    rtm = raw_translation_matrix =  Matrix.Translation(rt)
    rqr = raw_quaternion_rotation = Quaternion([rr[3], rr[0], rr[1], rr[2]])
    rrm = raw_rotation_matrix = Matrix.Rotation(rqr.angle, 4, rqr.axis)
    rsmx = raw_scale_matrix_x = mathutils.Matrix.Scale(rs[0], 4, (1,0,0))
    rsmy = raw_scale_matrix_y = mathutils.Matrix.Scale(rs[1], 4, (0,1,0))
    rsmz = raw_scale_matrix_z = mathutils.Matrix.Scale(rs[2], 4, (0,0,1))
    axis_correction = Matrix.Rotation(math.radians(90), 4, 'X')   
    fm = final_matrix = Matrix(axis_correction @ rtm @ rrm @ rsmx @ rsmy @ rsmz)
    context.scene.sub_anim_camera.matrix_local = fm
    keyframe_insert_camera_locrotscale(context.scene.sub_anim_camera, frame)

