import math
import bpy
import mathutils
import re
import collections
import time
import numpy as np
import cProfile
import pstats

from .. import ssbh_data_py
from bpy_extras.io_utils import ImportHelper
from bpy.props import IntProperty, StringProperty, BoolProperty
from bpy.types import Operator, Panel
from mathutils import Matrix, Quaternion, Vector
from .import_model import get_blender_transform
from pathlib import Path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .anim_data import SubAnimProperties, MatTrack, MatTrackProperty
    from bpy.types import ShaderNodeGroup, Material

class SUB_PT_import_anim(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Animation Importer'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.mode == "POSE" or context.mode == "OBJECT":
            return True
        return False
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        obj: bpy.types.Object = context.active_object
        row = layout.row()
        if obj is None:
            row.label(text="Click on an Armature or Camera.")
        elif obj.select_get() is False:
            row.label(text="Click on an Armature or Camera.")
        elif obj.type == 'ARMATURE' or obj.type == 'CAMERA':
            row.operator(SUB_OP_import_anim.bl_idname, icon='IMPORT', text='Import .NUANMB')
        else:
            row.label(text=f'The selected {obj.type.lower()} is not an armature or a camera.')

class SUB_OP_import_anim(Operator, ImportHelper):
    bl_idname = 'sub.import_anim'
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
    use_debug_timer: BoolProperty(
        name='Debug timing stats',
        description='Print advance import timing info to the console',
        default=False,
    )

    @classmethod
    def poll(cls, context):
        obj: bpy.types.Object = context.object
        if obj is None:
            return False
        elif obj.type != 'ARMATURE' and obj.type != 'CAMERA':
            return False
        return True
    
    def execute(self, context):
        print('Starting anim import...')
        start = time.perf_counter()
        obj: bpy.types.Object = context.object
        
        with cProfile.Profile() as pr:
            if obj.type == 'ARMATURE':
                import_model_anim(context, self.filepath,
                                        self.include_transform_track, self.include_material_track,
                                        self.include_visibility_track, self.first_blender_frame)
            else:
                import_camera_anim(self, context, self.filepath, self.first_blender_frame)
        if self.use_debug_timer:
            stats = pstats.Stats(pr)
            stats.sort_stats(pstats.SortKey.TIME)
            stats.print_stats()
        end = time.perf_counter()
        print(f'Anim import finished in {end-start} seconds!')
        return {'FINISHED'}
  
def poll_cameras(self, obj):
    return obj.type == 'CAMERA'

def heirarchy_order(bone, reordered):
        if bone not in reordered:
            reordered.append(bone)
        for child in bone.children:
            heirarchy_order(child, reordered)

def get_heirarchy_order(bone_list: list[bpy.types.PoseBone]) -> list[bpy.types.PoseBone]:
    root_bone: bpy.types.PoseBone = None
    for bone in bone_list:
        if bone.parent is None:
            root_bone = bone
            break
    return [root_bone] + [c for c in root_bone.children_recursive if c in bone_list]

class BoneTranslationFCurves():
    def __init__(self, fcurves, bone_name, values_length):
        self.data_path = f'pose.bones["{bone_name}"].location'
        self.x: bpy.types.FCurve = fcurves.new(self.data_path , index=0, action_group=f'{bone_name}')
        self.y: bpy.types.FCurve = fcurves.new(self.data_path , index=1, action_group=f'{bone_name}')
        self.z: bpy.types.FCurve = fcurves.new(self.data_path , index=2, action_group=f'{bone_name}')
        self.x_stashed_values = [[0.0, 0.0]] * values_length
        self.y_stashed_values = [[0.0, 0.0]] * values_length
        self.z_stashed_values = [[0.0, 0.0]] * values_length
    def get_translation_matrix(self, index: int):
        if index < len(self.x.keyframe_points):
            x = self.x_stashed_values[index][1]
            y = self.y_stashed_values[index][1]
            z = self.z_stashed_values[index][1]
        else:
            x = self.x_stashed_values[0][1]
            y = self.y_stashed_values[0][1]
            z = self.z_stashed_values[0][1]
        return Matrix.Translation([x,y,z])
    def stash_keyframe_set_from_vector(self, index, frame, translation_vector: Vector):
        x, y, z = translation_vector
        self.x_stashed_values[index] = [frame, x]
        self.y_stashed_values[index] = [frame, y]
        self.z_stashed_values[index] = [frame, z]
    def set_keyframe_values_from_stash(self):
        self.x.keyframe_points.add(count=len(self.x_stashed_values))
        self.y.keyframe_points.add(count=len(self.y_stashed_values))
        self.z.keyframe_points.add(count=len(self.z_stashed_values))
        self.x.keyframe_points.foreach_set('co', [x for tup in self.x_stashed_values for x in tup])
        self.y.keyframe_points.foreach_set('co', [x for tup in self.y_stashed_values for x in tup])
        self.z.keyframe_points.foreach_set('co', [x for tup in self.z_stashed_values for x in tup])

class BoneRotationFCurves():
    '''
    def __init__(self, fcurves, base_data_path, bone_name):
        self.w: bpy.types.FCurve = fcurves.new(f'{base_data_path}.rotation_quaternion', index=0, action_group=f'{bone_name}')
        self.x: bpy.types.FCurve = fcurves.new(f'{base_data_path}.rotation_quaternion', index=1, action_group=f'{bone_name}')
        self.y: bpy.types.FCurve = fcurves.new(f'{base_data_path}.rotation_quaternion', index=2, action_group=f'{bone_name}')
        self.z: bpy.types.FCurve = fcurves.new(f'{base_data_path}.rotation_quaternion', index=3, action_group=f'{bone_name}')
        self.w_stashed_values: list[(int,float)] = []
        self.x_stashed_values: list[(int,float)] = []
        self.y_stashed_values: list[(int,float)] = []
        self.z_stashed_values: list[(int,float)] = []
    '''
    def __init__(self, fcurves, base_data_path, bone_name, values_length):
        self.w: bpy.types.FCurve = fcurves.new(f'{base_data_path}.rotation_quaternion', index=0, action_group=f'{bone_name}')
        self.x: bpy.types.FCurve = fcurves.new(f'{base_data_path}.rotation_quaternion', index=1, action_group=f'{bone_name}')
        self.y: bpy.types.FCurve = fcurves.new(f'{base_data_path}.rotation_quaternion', index=2, action_group=f'{bone_name}')
        self.z: bpy.types.FCurve = fcurves.new(f'{base_data_path}.rotation_quaternion', index=3, action_group=f'{bone_name}')
        self.w_stashed_values = [[0.0, 0.0]] * values_length
        self.x_stashed_values = [[0.0, 0.0]] * values_length
        self.y_stashed_values = [[0.0, 0.0]] * values_length
        self.z_stashed_values = [[0.0, 0.0]] * values_length
    def get_rotation_matrix(self, index: int):
        if index < len(self.w.keyframe_points):
            w = self.w_stashed_values[index][1]
            x = self.x_stashed_values[index][1]
            y = self.y_stashed_values[index][1]
            z = self.z_stashed_values[index][1]
        else:
            w = self.w_stashed_values[0][1]
            x = self.x_stashed_values[0][1]
            y = self.y_stashed_values[0][1]
            z = self.z_stashed_values[0][1]           
        q = Quaternion([w,x,y,z])
        return Matrix.Rotation(q.angle, 4, q.axis)
    '''
    def stash_keyframe_values_from_quaternion(self, index, frame, quaternion: Quaternion):
        self.w_stashed_values.append((frame, quaternion.w))
        self.x_stashed_values.append((frame, quaternion.x))
        self.y_stashed_values.append((frame, quaternion.y))
        self.z_stashed_values.append((frame, quaternion.z))
    '''
    def stash_keyframe_values_from_quaternion(self, index, frame, quaternion: Quaternion):
        w,x,y,z = quaternion
        self.w_stashed_values[index] = [frame, w]
        self.x_stashed_values[index] = [frame, x]
        self.y_stashed_values[index] = [frame, y]
        self.z_stashed_values[index] = [frame, z]
    def set_keyframe_values_from_stash(self):
        self.w.keyframe_points.add(count=len(self.w_stashed_values))
        self.x.keyframe_points.add(count=len(self.x_stashed_values))
        self.y.keyframe_points.add(count=len(self.y_stashed_values))
        self.z.keyframe_points.add(count=len(self.z_stashed_values))
        self.w.keyframe_points.foreach_set('co', [x for tup in self.w_stashed_values for x in tup])
        self.x.keyframe_points.foreach_set('co', [x for tup in self.x_stashed_values for x in tup])
        self.y.keyframe_points.foreach_set('co', [x for tup in self.y_stashed_values for x in tup])
        self.z.keyframe_points.foreach_set('co', [x for tup in self.z_stashed_values for x in tup])

class BoneScaleFCurves():
    def __init__(self, fcurves, base_data_path, bone_name, values_length):
        self.x: bpy.types.FCurve = fcurves.new(f'{base_data_path}.scale', index=0, action_group=f'{bone_name}')
        self.y: bpy.types.FCurve = fcurves.new(f'{base_data_path}.scale', index=1, action_group=f'{bone_name}')
        self.z: bpy.types.FCurve = fcurves.new(f'{base_data_path}.scale', index=2, action_group=f'{bone_name}')
        self.x_stashed_values = [[0.0, 0.0]] * values_length
        self.y_stashed_values = [[0.0, 0.0]] * values_length
        self.z_stashed_values = [[0.0, 0.0]] * values_length
    def get_scale_matrix(self, index: int):
        if index < len(self.x.keyframe_points):
            x = self.x_stashed_values[index][1]
            y = self.y_stashed_values[index][1]
            z = self.z_stashed_values[index][1]
        else:
            x = self.x_stashed_values[0][1]
            y = self.y_stashed_values[0][1]
            z = self.z_stashed_values[0][1]
        return Matrix.Diagonal([x,y,z,1.0])
    def stash_keyframe_set_from_vector(self, index, frame, scale_vector: Vector):
        x, y, z = scale_vector
        self.x_stashed_values[index] = [frame, x]
        self.y_stashed_values[index] = [frame, y]
        self.z_stashed_values[index] = [frame, z]
    def set_keyframe_values_from_stash(self):
        self.x.keyframe_points.add(count=len(self.x_stashed_values))
        self.y.keyframe_points.add(count=len(self.y_stashed_values))
        self.z.keyframe_points.add(count=len(self.z_stashed_values))
        self.x.keyframe_points.foreach_set('co', [x for tup in self.x_stashed_values for x in tup])
        self.y.keyframe_points.foreach_set('co', [x for tup in self.y_stashed_values for x in tup])
        self.z.keyframe_points.foreach_set('co', [x for tup in self.z_stashed_values for x in tup])

class BoneFCurves():
    '''
    def __init__(self, bone_name, fcurves):
        self.bone_name: str = bone_name
        self.base_data_path: str = f'pose.bones["{bone_name}"]'
        self.translation = BoneTranslationFCurves(fcurves, bone_name)
        self.rotation = BoneRotationFCurves(fcurves, self.base_data_path, bone_name)
        self.scale = BoneScaleFCurves(fcurves, self.base_data_path, bone_name)
    '''
    def __init__(self, bone_name, fcurves, values_length):
        self.bone_name: str = bone_name
        self.base_data_path: str = f'pose.bones["{bone_name}"]'
        self.translation = BoneTranslationFCurves(fcurves, bone_name, values_length)
        self.rotation = BoneRotationFCurves(fcurves, self.base_data_path, bone_name, values_length)
        self.scale = BoneScaleFCurves(fcurves, self.base_data_path, bone_name, values_length)
    def get_matrix_basis(self, index):
        tm = self.translation.get_translation_matrix(index)
        rm = self.rotation.get_rotation_matrix(index)
        sm = self.scale.get_scale_matrix(index)
        return Matrix(tm @ rm @ sm)
    '''
    def stash_keyframe_set_from_matrix(self, frame, matrix: Matrix):
        t, r, s = matrix.decompose()
        self.translation.stash_keyframe_set_from_vector(frame, t)
        self.rotation.stash_keyframe_values_from_quaternion(frame, r)
        self.scale.stash_keyframe_set_from_vector(frame, s)
    '''
    def stash_keyframe_set_from_matrix(self, index, frame, matrix: Matrix):
        t, r, s = matrix.decompose()
        self.translation.stash_keyframe_set_from_vector(index, frame, t)
        self.rotation.stash_keyframe_values_from_quaternion(index, frame, r)
        self.scale.stash_keyframe_set_from_vector(index, frame, s)
    def set_keyframe_values_from_stash(self):
        self.translation.set_keyframe_values_from_stash()
        self.rotation.set_keyframe_values_from_stash()
        self.scale.set_keyframe_values_from_stash()


def import_model_anim(context: bpy.types.Context, filepath: str,
                      include_transform_track, include_material_track,
                      include_visibility_track, first_blender_frame):
    # Load the anim data first with ssbh_data_py since blender setup relies on data from it
    ssbh_anim_data = ssbh_data_py.anim_data.read_anim(filepath)
    # Blender Action setup
    arma: bpy.types.Object = context.object
    if arma.animation_data is None: # For the bones
        arma.animation_data_create()
    arma.animation_data.action = bpy.data.actions.new(arma.name + ' ' + Path(filepath).name)
    if arma.data.animation_data is None: # For vis and mat tracks
        arma.data.animation_data_create()
    arma.data.animation_data.action = bpy.data.actions.new(arma.name + ' ' + Path(filepath).name + ' SAP Data')
    # Blender frame range setup
    scene = context.scene
    frame_count = int(ssbh_anim_data.final_frame_index + 1)
    scene.frame_start = first_blender_frame
    scene.frame_end = scene.frame_start + frame_count - 1
    # Convenience dict for group gathering
    name_to_group_dict = {group.group_type.name : group for group in ssbh_anim_data.groups}
    # Transform group import stuff
    transform_group = name_to_group_dict.get('Transform') if include_transform_track else None
    if transform_group:
        bones: list[bpy.types.PoseBone] = arma.pose.bones
        bone_to_node = {bones[n.name]:n for n in transform_group.nodes if n.name in bones}
        reordered: list[bpy.types.PoseBone] = get_heirarchy_order(list(bones)) # Do this to gaurantee we never process a child before its parent
        #bone_to_fcurves = {b:BoneFCurves(b.name, arma.animation_data.action.fcurves) for b in bone_to_node.keys()} # only create fcurves for animated bones
        bone_to_fcurves = {b:BoneFCurves(b.name, arma.animation_data.action.fcurves, len(n.tracks[0].values)) for b,n in bone_to_node.items()} # only create fcurves for animated bones
        #bone_to_rel_matrix_local = {b:b.parent.bone.matrix_local.inverted() @ b.bone.matrix_local for b in bones if b.parent} # non-root bones
        bone_to_rel_matrix_local = {}
        for bone in bones:
            if bone.parent: # non-root bones
                bone_to_rel_matrix_local[bone] = bone.parent.bone.matrix_local.inverted() @ bone.bone.matrix_local
            else: # root bones
                bone_to_rel_matrix_local[bone] = bone.bone.matrix_local
        bone_to_matrix: dict[bpy.types.PoseBone, Matrix] = {}
        for index, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)): # +1 because range() excludes the final value
            #context.scene.frame_set(frame)
            for bone in reordered:
                node = bone_to_node.get(bone)
                if node is None: # Some bones may not be animated, but their children may be
                    if bone.parent:
                        bone_to_matrix[bone] = bone_to_matrix[bone.parent] @ bone_to_rel_matrix_local[bone]
                    else:
                        bone_to_matrix[bone] = bone_to_rel_matrix_local[bone]
                    continue
                if index >= len(node.tracks[0].values): # Bones either have a value on the first frame, or every frame
                    if bone.parent:
                        matrix_basis = bone_to_fcurves[bone].get_matrix_basis(0)
                        bone_to_matrix[bone] = bone_to_matrix[bone.parent] @ bone_to_rel_matrix_local[bone] @ matrix_basis
                    else: # TODO: This is probably unecessary
                        matrix_basis = bone_to_fcurves[bone].get_matrix_basis(0)
                        bone_to_matrix[bone] = bone_to_rel_matrix_local[bone] @ matrix_basis
                    continue 
                t = translation = node.tracks[0].values[index].translation
                r = rotation = node.tracks[0].values[index].rotation
                s = scale = node.tracks[0].values[index].scale
                tm = translation_matrix = Matrix.Translation(t)
                qr = quaternion_rotation = Quaternion([r[3], r[0], r[1], r[2]])
                rm = rotation_matrix = Matrix.Rotation(qr.angle, 4, qr.axis)
                compensate_scale = node.tracks[0].scale_options.compensate_scale
                # Blender doesn't have this built in for some reason.
                scale_matrix = Matrix.Diagonal((s[0], s[1], s[2], 1.0))

                scale_compensation = Matrix.Diagonal((1.0, 1.0, 1.0, 1.0))
                    # TODO: Figure out why this doesn't match ssbh_wgpu.
                    # Scale compensation "compensates" the effect of the immediate parent's scale.
                    parent_node = bone_to_node.get(bone.parent, None)
                    if parent_node is not None:
                        try:
                            # The parent may not have the same frame count.
                            # Handle the case where the parent has only one frame.
                            if index >= len(parent_node.tracks[0].values):
                                parent_scale = parent_node.tracks[0].values[0].scale
                            else:
                                parent_scale = parent_node.tracks[0].values[index].scale

                            # TODO: Does this handle axes correctly with non uniform scale?
                            scale_compensation = Matrix.Diagonal((1.0 / parent_scale[0], 1.0 / parent_scale[1], 1.0 / parent_scale[2], 1.0))
                        except IndexError:
                            pass

                raw_matrix = mathutils.Matrix(tm @ scale_compensation @ rm @ scale_matrix)
                bone_fcurves = bone_to_fcurves[bone]
                if bone.parent is None: # The root bone
                    fixed_matrix = get_blender_transform(raw_matrix, transpose=False)
                    bone_fcurves.stash_keyframe_set_from_matrix(index, frame, fixed_matrix)
                    bone_to_matrix[bone] = fixed_matrix
                else:
                    fixed_child_matrix = get_blender_transform(raw_matrix, transpose=False)
                    parent_matrix = bone_to_matrix[bone.parent]
                    pose_matrix = parent_matrix @ fixed_child_matrix
                    matrix_basis: Matrix = bone_to_rel_matrix_local[bone].inverted() @ parent_matrix.inverted() @ pose_matrix
                    mbtv, mbrq, mbsv = matrix_basis.decompose()
                    if node.tracks[0].transform_flags.override_translation is True:
                        mbtv = [0.0, 0.0, 0.0]
                    mbtm = Matrix.Translation(mbtv)
                    if node.tracks[0].transform_flags.override_rotation is True:
                        mbrq = Quaternion([1,0,0,0])
                    mbrm = Matrix.Rotation(mbrq.angle, 4, mbrq.axis)
                    if node.tracks[0].transform_flags.override_scale is True:
                        mbsv = [1.0, 1.0, 1.0]
                    mbsm = Matrix.Diagonal((mbsv[0], mbsv[1], mbsv[2], 1.0))

                    matrix_basis = (mbtm @ mbrm @ mbsm)
                    bone_to_matrix[bone] = bone_to_matrix[bone.parent] @ bone_to_rel_matrix_local[bone] @ matrix_basis
                    bone_fcurves.stash_keyframe_set_from_matrix(index, frame, matrix_basis)
        for bone, bone_fcurves in bone_to_fcurves.items():
            bone_fcurves.set_keyframe_values_from_stash()
    # Visibility group import stuff
    visibility_group = name_to_group_dict.get('Visibility') if include_visibility_track else None
    if visibility_group:
        sap: SubAnimProperties = arma.data.sub_anim_properties
        for node in visibility_group.nodes:
            # Setup vis_tracks in sub_anim_properties incase they haven't already been setup
            sub_vis_track_entry = sap.vis_track_entries.get(node.name)
            if sub_vis_track_entry is None:
                sub_vis_track_entry = sap.vis_track_entries.add()
                sub_vis_track_entry.name = node.name
            # Setup FCurve
            sub_vis_track_entry_index = sap.vis_track_entries.find(sub_vis_track_entry.name)
            data_path = f'sub_anim_properties.vis_track_entries[{sub_vis_track_entry_index}].value'
            fcurve = arma.data.animation_data.action.fcurves.new(data_path, action_group='Visibility')
            # Now create and set the keyframe points
            fcurve.keyframe_points.add(count=len(node.tracks[0].values))
            frame_and_value_flattened = []
            for index, value in enumerate(node.tracks[0].values):
                frame_and_value_flattened.extend([scene.frame_start + index, value])
            fcurve.keyframe_points.foreach_set('co', frame_and_value_flattened)
    # Material group import stuff
    material_group = name_to_group_dict.get('Material') if include_material_track else None
    if material_group:
        sap: SubAnimProperties = arma.data.sub_anim_properties
        # Initial Setup
        for node in material_group.nodes:
            mat_track: MatTrack = sap.mat_tracks.get(node.name)
            if mat_track is None:
                mat_track = sap.mat_tracks.add()
                mat_track.name = node.name
            for track in node.tracks:
                prop: MatTrackProperty = mat_track.properties.get(track.name)
                if prop is None:
                    prop = mat_track.properties.add()
                    prop.name = track.name
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
        # Now import the values
        for node in material_group.nodes:
            mat_track: MatTrack = sap.mat_tracks.get(node.name)
            mat_track_index = sap.mat_tracks.find(mat_track.name)
            for track in node.tracks:
                prop = mat_track.properties.get(track.name)
                prop_index = mat_track.properties.find(prop.name)
                if prop.sub_type == 'VECTOR':
                    data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].custom_vector'
                    for index in (0,1,2,3):
                        vector_index_values = [vector[index] for vector in track.values]
                        fcurve = arma.data.animation_data.action.fcurves.new(data_path, index=index, action_group=f'Material ({mat_track.name})')
                        fcurve.keyframe_points.add(count=len(vector_index_values))
                        frame_and_value_flattened = []
                        for index, value in enumerate(vector_index_values):
                            frame_and_value_flattened.extend([scene.frame_start + index, value])
                        fcurve.keyframe_points.foreach_set('co', frame_and_value_flattened)
                elif prop.sub_type == 'FLOAT':
                    data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].custom_float'
                    fcurve = arma.data.animation_data.action.fcurves.new(data_path, action_group=f'Material ({mat_track.name})')
                    fcurve.keyframe_points.add(count=len(track.values))
                    frame_and_value_flattened = []
                    for index, value in enumerate(track.values):
                        frame_and_value_flattened.extend([scene.frame_start + index, value])
                    fcurve.keyframe_points.foreach_set('co', frame_and_value_flattened)
                elif prop.sub_type == 'BOOL':
                    data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].custom_bool'
                    fcurve = arma.data.animation_data.action.fcurves.new(data_path, action_group=f'Material ({mat_track.name})')
                    fcurve.keyframe_points.add(count=len(track.values))
                    frame_and_value_flattened = []
                    for index, value in enumerate(track.values):
                        frame_and_value_flattened.extend([scene.frame_start + index, value])
                    fcurve.keyframe_points.foreach_set('co', frame_and_value_flattened)
                elif prop.sub_type == 'PATTERN':
                    data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].pattern_index'
                    fcurve = arma.data.animation_data.action.fcurves.new(data_path, action_group=f'Material ({mat_track.name})')
                    fcurve.keyframe_points.add(count=len(track.values))
                    frame_and_value_flattened = []
                    for index, value in enumerate(track.values):
                        frame_and_value_flattened.extend([scene.frame_start + index, value])
                    fcurve.keyframe_points.foreach_set('co', frame_and_value_flattened)
                elif prop.sub_type == 'TEXTURE':
                    data_path=f'sub_anim_properties.mat_tracks[{mat_track_index}].properties[{prop_index}].texture_transform'
                    for index in (0,1,2,3,4):
                        if index == 0:
                            vector_index_values = [uv_transform.scale_u for uv_transform in track.values]
                        elif index == 1:
                            vector_index_values = [uv_transform.scale_v for uv_transform in track.values]
                        elif index == 2:
                            vector_index_values = [uv_transform.rotation for uv_transform in track.values]
                        elif index == 3:
                            vector_index_values = [uv_transform.translate_u for uv_transform in track.values]
                        elif index == 4:
                            vector_index_values = [uv_transform.translate_v for uv_transform in track.values]
                        fcurve = arma.data.animation_data.action.fcurves.new(data_path, index=index, action_group=f'Material ({mat_track.name})')
                        fcurve.keyframe_points.add(count=len(vector_index_values))
                        frame_and_value_flattened = []
                        for index, value in enumerate(vector_index_values):
                            frame_and_value_flattened.extend([scene.frame_start + index, value])
                        fcurve.keyframe_points.foreach_set('co', frame_and_value_flattened)
    
    if visibility_group:
        setup_visibility_drivers(arma)
    if material_group:
        setup_material_drivers(arma)


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
    sap: SubAnimProperties = arma.data.sub_anim_properties
    mesh_children = [child for child in arma.children if child.type == 'MESH']
    materials: set[Material] = {material_slot.material for mesh in mesh_children for material_slot in mesh.material_slots}
    for material in materials:
        sus: ShaderNodeGroup = material.node_tree.nodes.get('smash_ultimate_shader')
        if not sus:
            continue
        mat_name_input = sus.inputs.get('Material Name')
        sap_mat_track = sap.mat_tracks.get(mat_name_input.default_value, None)
        if sap_mat_track is None:
            continue # This is very common, most fighter anims only contain material info for the eye materials for instance
        # Set up CustomVector31
        cv31 = sap_mat_track.properties.get('CustomVector31', None)
        if cv31 is not None:
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
        if cv6 is not None:
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

        # Set up CustomVector3
        cv3 = sap_mat_track.properties.get('CustomVector3')
        if cv3:
            input = sus.inputs.get('CustomVector3 (Emission Color Multiplier)')
            if input:
                for index in [0,1,2,3]:
                    driver_handle = input.driver_add('default_value', index)
                    var = driver_handle.driver.variables.new()
                    var.name = 'var'
                    target = var.targets[0]
                    target.id_type = 'ARMATURE'
                    target.id = arma.data
                    mti = material_track_index = sap.mat_tracks.find(sap_mat_track.name)
                    pi = property_index = sap_mat_track.properties.find(cv3.name)
                    target.data_path = f'sub_anim_properties.mat_tracks[{mti}].properties[{pi}].custom_vector[{index}]'
                    driver_handle.driver.expression = f'{var.name}'


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
def import_camera_anim(operator, context:bpy.types.Context, filepath, first_blender_frame):
    camera: bpy.types.Object = context.object
    ssbh_anim_data = ssbh_data_py.anim_data.read_anim(filepath)
    name_group_dict = {group.group_type.name : group for group in ssbh_anim_data.groups}
    transform_group = name_group_dict.get('Transform')
    camera_group = name_group_dict.get('Camera')

    frame_count = int(ssbh_anim_data.final_frame_index + 1)
    scene = context.scene
    scene.frame_start = first_blender_frame
    scene.frame_end = scene.frame_start + frame_count - 1
    scene.frame_set(scene.frame_start)

    #try:
    #    bpy.ops.object.mode_set(mode='OBJECT', toggle=False) # whatever object is currently selected, exit whatever mode its in
    #except RuntimeError: # There may not have been any active or selected object
    #    pass
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
            update_camera_properties(operator, camera, camera_group, index, frame)
        if transform_group is not None:
            update_camera_transforms(camera, transform_group, index, frame)

def update_camera_properties(operator: bpy.types.Operator, camera:bpy.types.Object, camera_group, index, frame):
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

def update_camera_transforms(camera: bpy.types.Object, transform_group, index, frame):
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
    camera.matrix_local = fm
    keyframe_insert_camera_locrotscale(camera, frame)

