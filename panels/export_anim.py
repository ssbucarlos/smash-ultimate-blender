import bpy
from bpy.types import Operator
from bpy.props import IntProperty, StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from .. import ssbh_data_py
from .import_anim import AnimArmatureClearOperator, AnimCameraClearOperator

class ExportAnimPanel(bpy.types.Panel):
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

        if context.scene.sub_anim_armature is None and context.scene.sub_anim_camera is None:
            row = layout.row(align=True)
            row.prop(context.scene, 'sub_anim_armature', icon='ARMATURE_DATA')
            row = layout.row(align=True)
            row.prop(context.scene, 'sub_anim_camera', icon='VIEW_CAMERA')
            return
        elif context.scene.sub_anim_armature is not None:
            row = layout.row(align=True)
            row.prop(context.scene, 'sub_anim_armature', icon='ARMATURE_DATA')
            if context.scene.sub_anim_armature.animation_data is None:
                row = layout.row(align=True)
                row.label(text='The selected armature has no loaded animation!', icon='ERROR')
            else:
                row = layout.row(align=True)
                row.operator('sub.anim_model_exporter', icon='FILE', text='Export a Model Animation')
        elif context.scene.sub_anim_camera is not None:
            row = layout.row(align=True)
            row.prop(context.scene, 'sub_anim_camera', icon='VIEW_CAMERA')
            row.operator('sub.anim_camera_exporter', icon='FILE', text='Export a Camera Animation')

class AnimModelExporterOperator(Operator):
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

    def invoke(self, context, event):
        self.first_blender_frame = context.scene.frame_start
        self.last_blender_frame = context.scene.frame_end
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        export_model_anim(context, self.filepath,
                        self.include_transform_track, self.include_material_track,
                        self.include_visibility_track, self.first_blender_frame,
                        self.last_blender_frame)
        return {'FINISHED'}    

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
        pass
        #mat_group = make_material_group(context, first_blender_frame, last_blender_frame)
        #ssbh_anim_data.groups.append(mat_group)
    ssbh_anim_data.save(filepath)
    
def make_transform_group(context, first_blender_frame, last_blender_frame):
    trans_type = ssbh_data_py.anim_data.GroupType.Transform
    trans_group = ssbh_data_py.anim_data.GroupData(trans_type)   
    arma_obj = context.scene.sub_anim_armature
    all_bone_names = [b.name for b in arma_obj.pose.bones]
    fcurves = arma_obj.animation_data.action.fcurves
    curve_names = {curve.data_path.split('"')[1] for curve in fcurves}
    animated_bone_names = [cn for cn in curve_names if cn in all_bone_names]
    animated_bones = [bone for bone in arma_obj.pose.bones if bone.name in animated_bone_names]
    for bone in animated_bones:
        node = ssbh_data_py.anim_data.NodeData(bone.name)
        track = ssbh_data_py.anim_data.TrackData('Transform')
        node.tracks.append(track)
        trans_group.nodes.append(node)
    name_to_node = {node.name:node for node in trans_group.nodes}
    # changing frames is expensive so need to setup loop to only do once
    from .export_model import unreorient_matrix
    for frame in range(first_blender_frame, last_blender_frame+1):
        context.scene.frame_set(frame)
        for bone in animated_bones:
            m:bpy.types.Matrix = None
            if bone.parent:
                m = bone.parent.matrix.inverted() @ bone.matrix
                m = unreorient_matrix(m).transposed()
            else:
                from bpy_extras.io_utils import axis_conversion
                converter_matrix = axis_conversion(
                    from_forward='Z', 
                    from_up='-X',
                    to_forward='-Y',
                    to_up='Z').to_4x4()
                m = converter_matrix.inverted() @ bone.matrix
            ms = m.to_scale()
            mq = m.to_quaternion()
            mt = m.to_translation()
            node = name_to_node[bone.name]
            track = node.tracks[0]
            new_ssbh_transform = ssbh_data_py.anim_data.Transform(
                [ms[0], ms[1], ms[2]], 
                [mq[1], mq[2], mq[3], mq[0]],
                [mt[0], mt[1], mt[2]]
            )
            track.values.append(new_ssbh_transform)
    return trans_group

def make_visibility_group(context, first_blender_frame, last_blender_frame):
    # Setup SSBH group
    vis_type = ssbh_data_py.anim_data.GroupType.Visibility
    vis_group = ssbh_data_py.anim_data.GroupData(vis_type)
    # Setup SSBH Node
    entries = context.scene.sub_anim_armature.data.sub_anim_properties.vis_track_entries
    for entry in entries:
        if entry.deleted == True:
            pass
        node = ssbh_data_py.anim_data.NodeData(entry.name)
        track = ssbh_data_py.anim_data.TrackData('Visibility')
        node.tracks.append(track)
        vis_group.nodes.append(node)
    name_to_node = {node.name:node for node in vis_group.nodes}
    # Set Node Values
    for frame in range(first_blender_frame, last_blender_frame + 1):
        context.scene.frame_set(frame)
        for entry in entries:
            if entry.deleted == True:
                pass
            node = name_to_node[entry.name]
            track = node.tracks[0]
            track.values.append(entry.value)
    return vis_group
    
def make_material_group():
    pass



