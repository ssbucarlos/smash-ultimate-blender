import bpy
import mathutils
import math

from mathutils import Matrix
from bpy.types import Operator, Panel, Context
from bpy.props import IntProperty, StringProperty, BoolProperty
from .. import ssbh_data_py

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..properties import SubSceneProperties
    from bpy.types import PoseBone

class SUB_PT_export_anim(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Ultimate'
    bl_label = 'Animation Exporter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        arma: bpy.types.Object = ssp.anim_export_arma
        camera: bpy.types.Camera = ssp.anim_export_camera

        layout = self.layout
        layout.use_property_split = False

        row = layout.row()
        row.label(text="Select an Armature or Camera.")
        if not arma and not camera:
            row = layout.row()
            row.prop(ssp, 'anim_export_arma', icon='ARMATURE_DATA', text='')
            row = layout.row()
            row.prop(ssp, 'anim_export_camera', icon='VIEW_CAMERA', text='')
        elif arma:
            row = layout.row()
            row.prop(ssp, 'anim_export_arma', icon='ARMATURE_DATA', text='')
            if not arma.animation_data:
                row = layout.row()
                row.label(text='The selected armature has no animation data!', icon='ERROR')
            elif not arma.animation_data.action:
                row = layout.row()
                row.label(text='The selected armature has no action!', icon='ERROR')
            if arma.name not in context.view_layer.objects:
                row = layout.row()
                row.label(text='The selected armature is not in the active view layer!', icon='ERROR')
            row = layout.row()
            row.operator('sub.anim_model_exporter', icon='EXPORT', text='Export a Model Animation')
        elif camera:
            row = layout.row()
            row.prop(ssp, 'anim_export_camera', icon='VIEW_CAMERA', text='')
            row = layout.row()
            row.operator('sub.export_camera_anim', icon='EXPORT', text='Export a Camera Animation')

class SUB_OP_export_model_anim(Operator):
    bl_idname = 'sub.anim_model_exporter'
    bl_label = 'Export Anim'   

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
        description='First Exported Frame',
        default=1,
    )
    last_blender_frame: IntProperty(
        name='End Frame',
        description='Last Exported Frame',
        default=1,
    )
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        arma: bpy.types.Object = ssp.anim_export_arma
        if not arma:
            return False
        if arma.name not in context.view_layer.objects:
            return False
        if arma.animation_data is None:
            return False
        if arma.animation_data.action is None:
            return False
        return True

    def invoke(self, context, _event):
        self.first_blender_frame = context.scene.frame_start
        self.last_blender_frame = context.scene.frame_end
        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        arma: bpy.types.Object = ssp.anim_export_arma
        arma.hide_viewport = False
        arma.hide_set(False)
        arma.select_set(True)
        context.view_layer.objects.active = arma

        initial_auto_keying_value = context.scene.tool_settings.use_keyframe_insert_auto
        context.scene.tool_settings.use_keyframe_insert_auto = False

        if self.filepath == "":
            self.filepath = f'{arma.animation_data.action.name}.nuanmb'
        if not self.filepath.endswith('.nuanmb'):
            self.filepath += '.nuanmb'

        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        export_model_anim(context, self.filepath,
                        self.include_transform_track, self.include_material_track,
                        self.include_visibility_track, self.first_blender_frame,
                        self.last_blender_frame)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        context.scene.tool_settings.use_keyframe_insert_auto = initial_auto_keying_value

        return {'FINISHED'}    

class SUB_OP_export_camera_anim(Operator):
    bl_idname = 'sub.export_camera_anim'
    bl_label = 'Export Anim'   

    filter_glob: StringProperty(
        default='*.nuanmb',
        options={'HIDDEN'}
    )

    first_blender_frame: IntProperty(
        name='Start Frame',
        description='First Exported Frame',
        default=1,
    )
    last_blender_frame: IntProperty(
        name='End Frame',
        description='Last Exported Frame',
        default=1,
    )
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        self.first_blender_frame = context.scene.frame_start
        self.last_blender_frame = context.scene.frame_end
        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath.endswith('.nuanmb'):
            self.filepath += '.nuanmb'
        export_camera_anim(self, context, self.filepath, self.first_blender_frame, self.last_blender_frame)
        return {'FINISHED'}  

def export_camera_anim(operator: Operator, context: Context, filepath, first_blender_frame, last_blender_frame):
    scene = context.scene
    ssp: SubSceneProperties = context.scene.sub_scene_properties
    camera: bpy.types.Object = ssp.anim_export_camera
    ssbh_anim_data = ssbh_data_py.anim_data.AnimData()
    ssbh_anim_data.final_frame_index = last_blender_frame - first_blender_frame
    
    transform_group = ssbh_data_py.anim_data.GroupData(ssbh_data_py.anim_data.GroupType.Transform)
    transform_group.nodes.append(ssbh_data_py.anim_data.NodeData('gya_camera'))
    transform_group.nodes[0].tracks.append(ssbh_data_py.anim_data.TrackData('Transform'))

    camera_group = ssbh_data_py.anim_data.GroupData(ssbh_data_py.anim_data.GroupType.Camera)
    camera_group.nodes.append(ssbh_data_py.anim_data.NodeData('gya_cameraShape'))
    camera_group.nodes[0].tracks.append(ssbh_data_py.anim_data.TrackData('FarClip'))
    camera_group.nodes[0].tracks.append(ssbh_data_py.anim_data.TrackData('FieldOfView'))
    camera_group.nodes[0].tracks.append(ssbh_data_py.anim_data.TrackData('NearClip'))

    track_name_to_track = {track.name : track for track in camera_group.nodes[0].tracks}
    trans_track = transform_group.nodes[0].tracks[0]
    for index, frame in enumerate(range(first_blender_frame, last_blender_frame + 1)):
        scene.frame_set(frame)
        track_name_to_track['FieldOfView'].values.append(camera.data.angle_y)
        track_name_to_track['FarClip'].values.append(camera.data.clip_end)
        track_name_to_track['NearClip'].values.append(camera.data.clip_start)
        fixed_matrix = camera.matrix_local.copy()
        axis_correction = Matrix.Rotation(math.radians(90), 4, 'X') 
        original_matrix = axis_correction.inverted() @ fixed_matrix

        mt, mq, ms = original_matrix.decompose()
        new_ssbh_transform = ssbh_data_py.anim_data.Transform(
            [ms[0], ms[1], ms[2]], 
            [mq.x, mq.y, mq.z, mq.w],
            [mt[0], mt[1], mt[2]]
        )
        trans_track.values.append(new_ssbh_transform)
        # Check for quaternion interpolation issues
        if index > 0:
            pq = mathutils.Quaternion(trans_track.values[index-1].rotation)
            cq = mathutils.Quaternion(trans_track.values[index].rotation)
            if pq.dot(cq) < 0:
                trans_track.values[index].rotation = [-c for c in trans_track.values[index].rotation]

    ssbh_anim_data.groups.append(transform_group)
    ssbh_anim_data.groups.append(camera_group)

    ssbh_anim_data.save(filepath)

def export_model_anim(context, filepath,
                    include_transform_track, include_material_track,
                    include_visibility_track, first_blender_frame,
                    last_blender_frame):
    ssbh_anim_data = ssbh_data_py.anim_data.AnimData()
    ssbh_anim_data.final_frame_index = last_blender_frame - first_blender_frame
    if include_transform_track:
        trans_group = make_transform_group(context, first_blender_frame, last_blender_frame)
        ssbh_anim_data.groups.append(trans_group)
    if include_visibility_track:
        vis_group = make_visibility_group(context, first_blender_frame, last_blender_frame)
        ssbh_anim_data.groups.append(vis_group)
    if include_material_track:
        mat_group = make_material_group(context, first_blender_frame, last_blender_frame)
        ssbh_anim_data.groups.append(mat_group)
    ssbh_anim_data.save(filepath)
    
def make_transform_group(context, first_blender_frame, last_blender_frame):
    trans_type = ssbh_data_py.anim_data.GroupType.Transform
    trans_group = ssbh_data_py.anim_data.GroupData(trans_type)
    ssp: SubSceneProperties = context.scene.sub_scene_properties   
    arma: bpy.types.Object = ssp.anim_export_arma
    all_bone_names: list[str] = [b.name for b in arma.pose.bones]
    fcurves = arma.animation_data.action.fcurves
    curve_names = {curve.data_path.split('"')[1] for curve in fcurves}
    animated_bone_names = [cn for cn in curve_names if cn in all_bone_names]
    animated_bones: list[PoseBone] = [bone for bone in arma.pose.bones if bone.name in animated_bone_names]
    for bone in animated_bones:
        node = ssbh_data_py.anim_data.NodeData(bone.name)
        track = ssbh_data_py.anim_data.TrackData('Transform')
        bone_is = bone.get('inherit_scale')
        bone_cs = bone.get('compensate_scale')
        track.scale_options = ssbh_data_py.anim_data.ScaleOptions(
            bool(bone_is) if bone_is is not None else True,
            bool(bone_cs) if bone_cs is not None else True)
        node.tracks.append(track)
        trans_group.nodes.append(node)
    name_to_node = {node.name:node for node in trans_group.nodes}
    # changing frames is expensive so need to setup loop to only do once

    from .export_model import get_smash_transform, get_smash_root_transform
    for index, frame in enumerate(range(first_blender_frame, last_blender_frame+1)):
        context.scene.frame_set(frame)

        for bone in animated_bones:
            m:mathutils.Matrix = None
            if bone.parent:
                m = bone.parent.matrix.inverted() @ bone.matrix
                m = get_smash_transform(m).transposed()
            else:
                arma.data.bones.active = bone.bone
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis='X', center_override=arma.location)
                bpy.ops.transform.rotate(value=math.radians(-90), orient_axis='Z', center_override=arma.location)
                m = get_smash_transform(bone.matrix).transposed()

            # TODO: Investigate why this can cause twists on Mario's foot with the vanilla skel.
            mt, mq, ms = m.decompose()
            '''
            Checking here and fixing the quaternion before using ssbh_data_py seems to not work.
            Luckily ssbh_data_py allows manual editing of the rotation values so can just fix after creation of the
            transform.
            '''
            node = name_to_node[bone.name]
            track = node.tracks[0]
            new_ssbh_transform = ssbh_data_py.anim_data.Transform(
                [ms[0], ms[1], ms[2]], 
                [mq.x, mq.y, mq.z, mq.w],
                [mt[0], mt[1], mt[2]]
            )
            track.values.append(new_ssbh_transform)
            # Check for quaternion interpolation issues
            if index > 0:
                pq = mathutils.Quaternion(track.values[index-1].rotation)
                cq = mathutils.Quaternion(track.values[index].rotation)
                if pq.dot(cq) < 0:
                    track.values[index].rotation = [-c for c in track.values[index].rotation]

    return trans_group

def make_visibility_group(context, first_blender_frame, last_blender_frame):
    # Setup SSBH group
    vis_type = ssbh_data_py.anim_data.GroupType.Visibility
    vis_group = ssbh_data_py.anim_data.GroupData(vis_type)
    # Setup SSBH Node
    ssp = context.scene.sub_scene_properties
    entries = ssp.anim_export_arma.data.sub_anim_properties.vis_track_entries
    for entry in entries:
        node = ssbh_data_py.anim_data.NodeData(entry.name)
        track = ssbh_data_py.anim_data.TrackData('Visibility')
        node.tracks.append(track)
        vis_group.nodes.append(node)
    name_to_node = {node.name:node for node in vis_group.nodes}
    # Set Node Values
    for frame in range(first_blender_frame, last_blender_frame + 1):
        context.scene.frame_set(frame)
        for entry in entries:
            node = name_to_node[entry.name]
            track = node.tracks[0]
            track.values.append(entry.value)
    return vis_group
    
def make_material_group(context, first_blender_frame, last_blender_frame):
    # Setup SSBH group
    mat_type = ssbh_data_py.anim_data.GroupType.Material
    mat_group = ssbh_data_py.anim_data.GroupData(mat_type)
    # Setup SSBH Node
    ssp = context.scene.sub_scene_properties
    sap = ssp.anim_export_arma.data.sub_anim_properties
    for mat_track in sap.mat_tracks:
        node = ssbh_data_py.anim_data.NodeData(mat_track.name)
        for property in mat_track.properties:
            track = ssbh_data_py.anim_data.TrackData(property.name)
            node.tracks.append(track)
        mat_group.nodes.append(node)
    # Setup convenience dict
    node_name_track_name_to_track = {} # node_name_track_name_to_track['EyeL']['CustomVector6'] -> nodes['EyeL'].tracks['CustomVector6']
    for node in mat_group.nodes:
        node_name_track_name_to_track[node.name] = {}
        for track in node.tracks:
            node_name_track_name_to_track[node.name][track.name] = track
    # Set Node Values
    for frame in range(first_blender_frame, last_blender_frame + 1):
        context.scene.frame_set(frame)
        for mat_track in sap.mat_tracks:
            for prop in mat_track.properties:
                if prop.sub_type == 'VECTOR':
                    track = node_name_track_name_to_track[mat_track.name][prop.name]
                    track.values.append([prop.custom_vector[0], prop.custom_vector[1], prop.custom_vector[2], prop.custom_vector[3]])
                elif prop.sub_type == 'FLOAT':
                    track = node_name_track_name_to_track[mat_track.name][prop.name]
                    track.values.append(prop.custom_float)
                elif prop.sub_type == 'BOOL':
                    track = node_name_track_name_to_track[mat_track.name][prop.name]
                    track.values.append(prop.custom_bool)
                elif prop.sub_type == 'PATTERN':
                    track = node_name_track_name_to_track[mat_track.name][prop.name]
                    track.values.append(prop.pattern_index)
                elif prop.sub_type == 'TEXTURE':
                    track = node_name_track_name_to_track[mat_track.name][prop.name]
                    tt = prop.texture_transform
                    uvt = ssbh_data_py.anim_data.UvTransform(tt[0], tt[1], tt[2], tt[3], tt[4])
                    track.values.append(uvt)
    return mat_group

