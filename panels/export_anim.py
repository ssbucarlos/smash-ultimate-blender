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
        row.label(text="Select an Armature or Camera. It's current animation will be exported.")

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
            row.operator('sub.anim_model_exporter', icon='FILE', text='Export a Model Animation')
        elif context.scene.sub_anim_camera is not None:
            row = layout.row(align=True)
            row.label(text=f'Selected camera: {context.scene.sub_anim_camera.name}')
            row.operator('sub.anim_camera_clear', icon='CANCEL', text='Clear Selected Camera')
            row = layout.row(align=True)
            row.operator('sub.anim_camera_importer', icon='FILE', text='Export a Camera Animation')

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
    trans_type = ssbh_data_py.anim_data.GroupType.Transform
    trans_group = ssbh_data_py.anim_data.GroupData(trans_type)
    ssbh_anim_data.groups.append(trans_group)
    # Armature animation data is stored at the 'Object' level, not the 'Data' level.
    arma_obj = context.scene.sub_anim_armature
    all_bone_names = [b.name for b in arma_obj.pose.bones]
    fcurves = arma_obj.animation_data.action.fcurves
    curve_names = {curve.data_path.split('"')[1] for curve in fcurves}
    animated_bone_names = [cn for cn in curve_names if cn in all_bone_names]
    animated_bones = [bone for bone in arma_obj.pose.bones if bone.name in animated_bone_names]
    bone_to_trans_values = {bone:[] for bone in animated_bones}
    for bone in animated_bones:
        node = ssbh_data_py.anim_data.NodeData(bone.name)
        track = ssbh_data_py.anim_data.TrackData('Transform')
        node.tracks.append(track)
        trans_group.nodes.append(node)
    name_to_node = {node.name:node for node in trans_group.nodes}
    # changing frames is expensive so need to setup loop to only do once
    for frame in range(first_blender_frame, last_blender_frame+1):
        context.scene.frame_set(frame)
        for bone in animated_bones:
            from .export_model import unreorient_matrix
            m:bpy.types.Matrix = None
            if bone.parent:
                m = bone.parent.matrix.inverted() @ bone.matrix
                m = unreorient_matrix(m).transposed()
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
            else:
                pass
            
    print(ssbh_anim_data.groups)

    ssbh_anim_data.save(filepath)
    








