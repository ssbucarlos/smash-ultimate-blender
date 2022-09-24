import math
import bpy
import mathutils
import re

from .. import ssbh_data_py
from bpy_extras.io_utils import ImportHelper
from bpy.props import IntProperty, StringProperty, BoolProperty
from bpy.types import Operator, Panel
from mathutils import Matrix, Quaternion
from .import_model import get_blender_transform

class SUB_PT_import_anim(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Animation Importer'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ssp = context.scene.sub_scene_properties
        camera = ssp.anim_import_camera
        arma = ssp.anim_import_arma
        layout = self.layout
        layout.use_property_split = False
        row = layout.row(align=True)
        row.label(text="Select an Armature or Camera.")
        if arma is None and camera is None:
            row = layout.row(align=True)
            row.prop(ssp, 'anim_import_arma', icon='ARMATURE_DATA', text='')
            row = layout.row(align=True)
            row.prop(ssp, 'anim_import_camera', icon='VIEW_CAMERA', text='')
            return
        elif arma is not None:
            row = layout.row(align=True)
            row.prop(ssp, 'anim_import_arma', icon='ARMATURE_DATA', text='')
            row = layout.row(align=True)
            row.operator('sub.anim_model_importer', icon='IMPORT', text='Import a Model Animation')
        elif camera is not None:
            row = layout.row(align=True)
            row.prop(ssp, 'anim_import_camera', icon='VIEW_CAMERA', text='')
            row = layout.row(align=True)
            row.operator('sub.anim_camera_importer', icon='IMPORT', text='Import a Camera Animation')

class SUB_OP_import_model_anim(Operator, ImportHelper):
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

class SUB_OP_import_camera_anim(Operator, ImportHelper):
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
        import_camera_anim(self, context, self.filepath, self.first_blender_frame)
        return {'FINISHED'}
    
def poll_cameras(self, obj):
    return obj.type == 'CAMERA'

def import_model_anim(context: bpy.types.Context, filepath,
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
    arma = scene.sub_scene_properties.anim_import_arma
    scene.frame_start = first_blender_frame
    scene.frame_end = scene.frame_start + frame_count - 1
    scene.frame_set(scene.frame_start)
    if context.active_object is not None:
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False) # whatever object is currently selected, exit whatever mode its in
    context.view_layer.objects.active = arma
    bpy.ops.object.mode_set(mode='EDIT', toggle=False) 
    bone_name_to_edit_bone_matrix = {bone.name:bone.matrix.copy() for bone in arma.data.edit_bones}
    bpy.ops.object.mode_set(mode='POSE', toggle=False) # put our armature in pose mode
    
    from pathlib import Path
    action_name = arma.name + ' ' + Path(filepath).name
    if arma.animation_data is None:
        arma.animation_data_create()
    action = bpy.data.actions.new(action_name)
    arma.animation_data.action = action

    if include_transform_track and transform_group is not None:
        bones = arma.pose.bones
        bone_to_node = {b:n for n in transform_group.nodes for b in bones if b.name == n.name}
        setup_bone_scale_drivers(bone_to_node.keys()) # Only want to setup drivers for the bones that have an entry in the anim

    if include_material_track and material_group is not None:
        setup_sap_material_properties(context, material_group)

    for index, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)): # +1 because range() excludes the final value
        scene.frame_set(frame)
        if include_transform_track and transform_group is not None:
            do_armature_transform_stuff(context, transform_group, index, frame, bone_to_node, bone_name_to_edit_bone_matrix)
        if include_material_track and material_group is not None:
            do_material_stuff(context, material_group, index, frame)
        if include_visibility_track and visibility_group is not None:
            do_visibility_stuff(context, visibility_group, index, frame)

    if include_visibility_track and visibility_group is not None:
        setup_visibility_drivers(arma)
    if include_material_track and material_group is not None:
        setup_material_drivers(arma)

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
        target.id = bpy.context.scene.sub_scene_properties.anim_import_arma
        target.data_path = f'pose.bones["{pose_bone.name}"]["inherit_scale"]'
        # TODO: Figure out how to incorporate compensate scale
        driver_handle.driver.expression = f'0 if {isv.name} == 1 else 3' # 0 is 'FULL' and 3 is 'NONE'


def do_armature_transform_stuff(context, transform_group, index, frame, bone_to_node, bone_name_to_edit_bone_matrix):
    arma = context.scene.sub_scene_properties.anim_import_arma
    bones = arma.pose.bones
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
        tm = translation_matrix = Matrix.Translation(t)
        qr = quaternion_rotation = Quaternion([r[3], r[0], r[1], r[2]])
        rm = rotation_matrix = Matrix.Rotation(qr.angle, 4, qr.axis)
        # Blender doesn't have this built in for some reason.
        scale_matrix = Matrix.Diagonal((s[0], s[1], s[2], 1.0))

        raw_matrix = mathutils.Matrix(tm @ rm @ scale_matrix)
        if bone.parent is not None:
            # TODO: Investigate twisting on mario's wait animations.
            fixed_matrix = get_blender_transform(raw_matrix, transpose=False)
            bone.matrix = bone.parent.matrix @ fixed_matrix

            if compensate_scale:
                # Scale compensation "compensates" the effect of the immediate parent's scale.
                # We don't want the compensation to accumulate along a bone chain. 
                # HACK: Use the transform itself since we may overwrite a scale value.
                # This assumes the parent is in the animation.
                # TODO(SMG): Investigate where the parent scale value comes from.
                parent_node = bone_to_node.get(bone.parent, None)
                if parent_node is not None:
                    try:
                        parent_scale = parent_node.tracks[0].values[index].scale
                        # TODO: Does this handle axes correctly with non uniform scale?
                        bone.scale = (bone.scale[0] / parent_scale[0], bone.scale[1] / parent_scale[1], bone.scale[2] / parent_scale[2])
                    except IndexError:
                        # TODO: A single frame in ssbh_data_py should be assumed to be a constant animation.
                        # The single element value applies to all frames.
                        # This matches the convention used for Smash Ultimate.
                        pass
        else:
            # TODO: Investigate how to do this without bpy.ops
            bone.matrix = get_blender_transform(raw_matrix, transpose=False)
            arma.data.bones.active = bone.bone
            bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Z', center_override=arma.location)
            bpy.ops.transform.rotate(value=math.radians(-90), orient_axis='X', center_override=arma.location)
        keyframe_insert_bone_locrotscale(arma, bone.name, frame, 'Transform')

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


def keyframe_insert_bone_locrotscale(arma: bpy.types.Object, bone_name, frame, group_name):
    for parameter in ['location', 'rotation_quaternion', 'scale']:
        arma.keyframe_insert(
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

def uvtransform_to_list(uvtransform) -> list[float]:
    scale_u = uvtransform.scale_u
    scale_v = uvtransform.scale_v
    rotation = uvtransform.rotation
    translate_u = uvtransform.translate_u
    translate_v = uvtransform.translate_v
    return [scale_u, scale_v, rotation, translate_u, translate_v]

def setup_material_drivers(arma: bpy.types.Object):
    sap = arma.data.sub_anim_properties
    mesh_children = [child for child in arma.children if child.type == 'MESH']
    materials = {material_slot.material for mesh in mesh_children for material_slot in mesh.material_slots}
    for material in materials:
        bsn = blender_shader_node = material.node_tree.nodes.get('smash_ultimate_shader', None)
        if bsn is None:
            #logging.info(f'Material {material.name} did not have the smash_ultimate_shader node, will not have material animations')
            continue
        mat_name_input = bsn.inputs.get('Material Name')
        sap_mat_track = sap.mat_tracks.get(mat_name_input.default_value, None)
        if sap_mat_track is None:
            continue # This is very common, most fighter anims only contain material info for the eye materials for instance
        # Set up Custom Vector 31
        cv31 = sap_mat_track.properties.get('CustomVector31', None)
        if cv31:
            labels_nodes_dict = {node.label:node for node in material.node_tree.nodes}
            sampler_1_node = labels_nodes_dict.get('Sampler1', None)
            if sampler_1_node is not None:
                input = sampler_1_node.inputs.get('UV Transform')
                for row in [0,1]:
                    driver_handle = input.driver_add('default_value', row)
                    var = driver_handle.driver.variables.new()
                    var.name = "var"
                    target = var.targets[0]
                    target.id_type = 'ARMATURE'
                    target.id = arma.data
                    mti = sap.mat_tracks.find(sap_mat_track.name)
                    pi = sap_mat_track.properties.find(cv31.name)
                    cvi = 2 if row == 0 else 3 # CustomVector31.Z and .W control translation
                    target.data_path = f'sub_anim_properties.mat_tracks[{mti}].properties[{pi}].custom_vector[{cvi}]'
                    driver_handle.driver.expression = f'0 - {var.name}'
        # Set up CustomVector6
        cv6 = sap_mat_track.properties.get('CustomVector6', None)
        if cv6:
            nodes = {node.label:node for node in material.node_tree.nodes}
            samplers = [nodes.get('Sampler0'), nodes.get('Sampler4'), nodes.get('Sampler6')]
            if all(sampler is not None for sampler in samplers):
                for sampler in samplers:
                    input = sampler.inputs.get('UV Transform')
                    for row in [0,1]:
                        driver_handle = input.driver_add('default_value', row)
                        var = driver_handle.driver.variables.new()
                        var.name = "var"
                        target = var.targets[0]
                        target.id_type = 'ARMATURE'
                        target.id = arma.data
                        mti = sap.mat_tracks.find(sap_mat_track.name)
                        pi = sap_mat_track.properties.find(cv6.name)
                        cvi = 2 if row == 0 else 3 # CustomVector6 .Z and .W control translation
                        target.data_path = f'sub_anim_properties.mat_tracks[{mti}].properties[{pi}].custom_vector[{cvi}]'
                        driver_handle.driver.expression = f'0 - {var.name}'     

def do_material_stuff(context, material_group, index, frame):
    arma = context.scene.sub_scene_properties.anim_import_arma
    sap = arma.data.sub_anim_properties
    for node in material_group.nodes:
        mat_track = sap.mat_tracks.get(node.name)
        mat_track_index = sap.mat_tracks.find(mat_track.name)
        for track in node.tracks:
            try:
                track.values[index]
            except IndexError:
                continue
            value = track.values[index]
            prop = mat_track.properties.get(track.name)
            prop_index = mat_track.properties.find(prop.name)
            if prop.sub_type == 'VECTOR':
                prop.custom_vector = value
                arma.data.keyframe_insert(data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].custom_vector', frame=frame, group=f'Material ({mat_track.name})', options={'INSERTKEY_NEEDED'})
            elif prop.sub_type == 'FLOAT':
                prop.custom_float = value
                arma.data.keyframe_insert(data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].custom_float', frame=frame,  group=f'Material ({mat_track.name})', options={'INSERTKEY_NEEDED'})
            elif prop.sub_type == 'BOOL':
                prop.custom_bool = value
                arma.data.keyframe_insert(data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].custom_bool', frame=frame,  group=f'Material ({mat_track.name})', options={'INSERTKEY_NEEDED'})
            elif prop.sub_type == 'PATTERN':
                prop.pattern_index = value
                arma.data.keyframe_insert(data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].pattern_index', frame=frame,  group=f'Material ({mat_track.name})', options={'INSERTKEY_NEEDED'})
            elif prop.sub_type == 'TEXTURE':
                prop.texture_transform = [value.scale_u, value.scale_v, value.rotation, value.translate_u, value.translate_v]
                arma.data.keyframe_insert(data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].texture_transform', frame=frame,  group=f'Material ({mat_track.name})', options={'INSERTKEY_NEEDED'})

def setup_sap_material_properties(context, material_group):
    arma = context.scene.sub_scene_properties.anim_import_arma
    sap = arma.data.sub_anim_properties
    # Setup
    for node in material_group.nodes:
        mat_track = sap.mat_tracks.get(node.name, None)
        if mat_track is None:
            mat_track = sap.mat_tracks.add()
            mat_track.name = node.name
        for track in node.tracks:
            prop = mat_track.properties.get(track.name, None)
            if prop is None:
                prop = mat_track.properties.add()
                prop.name = track.name
                if 'CustomBoolean' in track.name:
                    prop.sub_type = 'BOOL'
                elif 'CustomFloat' in track.name:
                    prop.sub_type = 'FLOAT'
                elif 'CustomVector' in track.name:
                    prop.sub_type = 'VECTOR'
                elif 'PatternIndex' in track.name:
                    prop.sub_type = 'PATTERN'
                elif 'Texture' in track.name:
                    prop.sub_type = 'TEXTURE'
                else:
                    raise TypeError(f'Unsupported track name {track.name}')         
            

def setup_visibility_drivers(arma:bpy.types.Object):
    # Setup Vis Drivers
    vis_track_entries = arma.data.sub_anim_properties.vis_track_entries
    mesh_children = [child for child in arma.children if child.type == 'MESH']
    for mesh in mesh_children:
        true_mesh_name = re.split('Shape|_VIS_|_O_', mesh.name)[0]
        if any(true_mesh_name == key for key in vis_track_entries.keys()):
            entries_index = vis_track_entries.find(true_mesh_name)
            for property in ['hide_viewport', 'hide_render']:
                driver_handle = mesh.driver_add(property)
                var = driver_handle.driver.variables.new()
                var.name = "var"
                target = var.targets[0]
                target.id_type = 'ARMATURE'
                target.id = arma.data
                target.data_path = f'sub_anim_properties.vis_track_entries[{entries_index}].value'
                driver_handle.driver.expression = f'1 - {var.name}'

def do_visibility_stuff(context, visibility_group, index, frame):
    for node in visibility_group.nodes:
        try:
            node.tracks[0].values[index]
        except IndexError: # Not every vis track entry will have values on every frame. Many only have the first frame.
            continue
        value = node.tracks[0].values[index]

        arma = context.scene.sub_scene_properties.anim_import_arma
        entries = arma.data.sub_anim_properties.vis_track_entries
        sub_vis_track_entry = entries.get(node.name, None)
        if sub_vis_track_entry is None:
            sub_vis_track_entry = entries.add()
            sub_vis_track_entry.name = node.name
        sub_vis_track_entry.value = value
        entry_index = entries.find(sub_vis_track_entry.name)
        arma.data.keyframe_insert(data_path=f'sub_anim_properties.vis_track_entries[{entry_index}].value', frame=frame, group='Visibility', options={'INSERTKEY_NEEDED'})

'''
Typical SSBH Camera Layout.
Group: 'Transform'
    Node: 'gya_camera'
        Track: 'Transform'
Group: 'Camera'
    Node: 'gya_cameraShape'
        Track: 'FarClip'
        Track: 'FieldOfView'
        Track: 'NearClip'
'''
def import_camera_anim(operator, context, filepath, first_blender_frame):
    camera = context.scene.sub_scene_properties.anim_import_camera
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
            update_camera_properties(operator, context, camera_group, index, frame)
        if transform_group is not None:
            update_camera_transforms(context, transform_group, index, frame)

def update_camera_properties(operator, context, camera_group, index, frame):
    node: ssbh_data_py.anim_data.NodeData = None
    # Imported anim should always have at least one node under the camera group
    if len(camera_group.nodes) == 0:
        message = f'The camera anim has no Nodes in the Camera group! Skipping setting camera properties'
        operator.report({'WARNING'}, message)
        return
    # The standard behavior
    if len(camera_group.nodes) == 1:
        node = camera_group.nodes[0]
    # If the camera group has multiple nodes instead of just 'gya_cameraShape', just use the 'gya_cameraShape' one
    if len(camera_group.nodes) > 1:
        message = f'The camera anim has multiple Camera Property Nodes! Will use the one called "gya_camera_Shape", but will not be able to export the other Node!'
        operator.report({'WARNING'}, message)
        for n in camera_group.nodes:
            if n.name == 'gya_cameraShape':
                node = n
        if node is None:
            node = camera_group.nodes[0]
    camera = context.scene.sub_scene_properties.anim_import_camera
    #scp = camera.data.sub_camera_properties
    for track in node.tracks:
        if track.name == 'FieldOfView':
            if index < len(track.values):
                #scp.field_of_view = track.values[index]
                #cam_keyframe_insert(camera, 'field_of_view', frame)
                camera.data.angle_y = track.values[index]
                camera.data.keyframe_insert(data_path = 'lens', frame=frame)
        elif track.name == 'FarClip':
            if index < len(track.values):
                #scp.far_clip = track.values[index]
                #cam_keyframe_insert(camera, 'far_clip', frame)
                camera.data.clip_end= track.values[index]
                camera.data.keyframe_insert(data_path = 'clip_end', frame=frame)
        elif track.name == 'NearClip':
            if index < len(track.values):
                #scp.near_clip = track.values[index]
                #cam_keyframe_insert(camera, 'near_clip', frame)
                camera.data.clip_start = track.values[index]
                camera.data.keyframe_insert(data_path = 'clip_start', frame=frame)
        else:
            operator.report({'WARNING'}, f'Unsupported track {track.name} in camera group, skipping!')

def update_camera_transforms(context, transform_group, index, frame):
    value = transform_group.nodes[0].tracks[0].values[index]
    rt = raw_translation = value.translation
    rr = raw_rotation = value.rotation
    rs = raw_scale = value.scale
    rtm = raw_translation_matrix =  Matrix.Translation(rt)
    rqr = raw_quaternion_rotation = Quaternion([rr[3], rr[0], rr[1], rr[2]])
    rrm = raw_rotation_matrix = Matrix.Rotation(rqr.angle, 4, rqr.axis)
    # Blender doesn't have this built in for some reason.
    rsm = raw_scale_matrix = Matrix.Diagonal((rs[0], rs[1], rs[2], 1.0))
    axis_correction = Matrix.Rotation(math.radians(90), 4, 'X')   
    fm = final_matrix = Matrix(axis_correction @ rtm @ rrm @ rsm)
    context.scene.sub_scene_properties.anim_import_camera.matrix_local = fm
    keyframe_insert_camera_locrotscale(context.scene.sub_scene_properties.anim_import_camera, frame)

