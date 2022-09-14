import bpy
import mathutils
import math
from bpy.types import Operator, Panel
from bpy.props import IntProperty, StringProperty, BoolProperty
from .. import ssbh_data_py

class SUB_PT_export_anim(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Animation Exporter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        row = layout.row(align=True)
        row.label(text="Select an Armature or Camera.")

        ssp = context.scene.sub_scene_properties
        if ssp.anim_export_arma is None and ssp.anim_export_camera is None:
            row = layout.row(align=True)
            row.prop(ssp, 'anim_export_arma', icon='ARMATURE_DATA', text='')
            row = layout.row(align=True)
            row.prop(ssp, 'anim_export_camera', icon='VIEW_CAMERA', text='')
            return
        elif ssp.anim_export_arma is not None:
            row = layout.row(align=True)
            row.prop(ssp, 'anim_export_arma', icon='ARMATURE_DATA', text='')
            if ssp.anim_export_arma.animation_data is None:
                row = layout.row(align=True)
                row.label(text='The selected armature has no loaded animation!', icon='ERROR')
            else:
                row = layout.row(align=True)
                row.operator('sub.anim_model_exporter', icon='EXPORT', text='Export a Model Animation')
        elif ssp.anim_export_camera is not None:
            row = layout.row(align=True)
            row.prop(ssp, 'anim_export_camera', icon='VIEW_CAMERA', text='')
            row.operator('sub.anim_camera_exporter', icon='EXPORT', text='Export a Camera Animation')

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

    def invoke(self, context, _event):
        self.first_blender_frame = context.scene.frame_start
        self.last_blender_frame = context.scene.frame_end
        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath.endswith('.nuanmb'):
            self.filepath += '.nuanmb'
        arma:bpy.types.Object = context.scene.sub_scene_properties.anim_export_arma
        arma.hide_viewport = False
        arma.hide_set(False)
        arma.select_set(True)
        context.view_layer.objects.active = arma
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        export_model_anim(context, self.filepath,
                        self.include_transform_track, self.include_material_track,
                        self.include_visibility_track, self.first_blender_frame,
                        self.last_blender_frame)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
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

def export_camera_anim(operator: Operator, context, filepath, first_blender_frame, last_blender_frame):
    ssbh_anim_data = ssbh_data_py.anim_data.AnimData()
    ssbh_anim_data.final_frame_index = last_blender_frame - first_blender_frame
    
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
    ssp = context.scene.sub_scene_properties   
    arma = ssp.anim_export_arma
    all_bone_names = [b.name for b in arma.pose.bones]
    fcurves = arma.animation_data.action.fcurves
    curve_names = {curve.data_path.split('"')[1] for curve in fcurves}
    animated_bone_names = [cn for cn in curve_names if cn in all_bone_names]
    animated_bones = [bone for bone in arma.pose.bones if bone.name in animated_bone_names]
    for bone in animated_bones:
        node = ssbh_data_py.anim_data.NodeData(bone.name)
        track = ssbh_data_py.anim_data.TrackData('Transform')
        node.tracks.append(track)
        trans_group.nodes.append(node)
    name_to_node = {node.name:node for node in trans_group.nodes}
    # changing frames is expensive so need to setup loop to only do once
    from .export_model import unreorient_matrix, get_unreoriented_root
    for index, frame in enumerate(range(first_blender_frame, last_blender_frame+1)):
        context.scene.frame_set(frame)
        for bone in animated_bones:
            m:mathutils.Matrix = None
            if bone.parent:
                m = bone.parent.matrix.inverted() @ bone.matrix
                m = unreorient_matrix(m).transposed()
            else:
                '''
                from bpy_extras.io_utils import axis_conversion
                converter_matrix = axis_conversion(
                    from_forward='Z', 
                    from_up='-X',
                    to_forward='-Y',
                    to_up='Z').to_4x4()
                m = converter_matrix.inverted() @ bone.matrix
                '''
                #t = bone.matrix.translation
                #m = mathutils.Matrix.Translation([t[0], t[2], -t[1]])
                #m = get_unreoriented_root(bone)
                arma.data.bones.active = bone.bone
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis='X', center_override=arma.location)
                bpy.ops.transform.rotate(value=math.radians(-90), orient_axis='Z', center_override=arma.location)
                m = unreorient_matrix(bone.matrix).transposed()
            ms = m.to_scale()
            mq = m.to_quaternion()
            '''
            Checking here and fixing the quaternion before using ssbh_data_py seems to not work.
            Luckily ssbh_data_py allows manual editing of the rotation values so can just fix after creation of the
            transform.
            # Check for quaternion interpolation issues
            if frame != first_blender_frame:
                pq = mathutils.Quaternion(track.values[index-1].rotation)
                if pq.dot(mq) < 0:
                    #print(f'{node.name}, frame={frame}, mq={mq}, pq={pq}')
                    mq.negate()
            '''
            mt = m.to_translation()
            node = name_to_node[bone.name]
            track = node.tracks[0]
            new_ssbh_transform = ssbh_data_py.anim_data.Transform(
                [ms[0], ms[1], ms[2]], 
                [mq[1], mq[2], mq[3], mq[0]],
                [mt[0], mt[1], mt[2]]
            )
            track.values.append(new_ssbh_transform)
            # Check for quaternion interpolation issues
            if index > 0:
                pq = mathutils.Quaternion(track.values[index-1].rotation)
                cq = mathutils.Quaternion(track.values[index].rotation)
                if pq.dot(cq) < 0:
                    #print(f'! {node.name}, frame={frame}, mq={mq}, pq={pq}')
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

