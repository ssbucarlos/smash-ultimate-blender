import bpy
import mathutils
import math
import re
#import numpy as np
import time
import cProfile
import pstats

from mathutils import Matrix, Quaternion
from bpy.types import Operator, Panel, Context
from bpy.props import IntProperty, StringProperty, BoolProperty

from pathlib import Path

from .. import ssbh_data_py
from .import_anim import get_heirarchy_order

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .anim_data import SUB_PG_vis_track_entry, SUB_PG_sub_anim_data, SUB_PG_mat_track, SUB_PG_mat_track_property
    CustomVector = list[int]
    CustomFloat = float
    CustomBool = bool
    PatternIndex = int
    TextureTransform = ssbh_data_py.anim_data.UvTransform
    pose_bone: bpy.types.PoseBone # Workaround for typechecking, remove if obsolete
    fcurve: bpy.types.FCurve # Workaround for typechecking, remove if obsolete
    from ..properties import SubSceneProperties

class SUB_PT_export_anim(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Animation Exporter'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.mode == "POSE" or context.mode == "OBJECT":
            return True
        return False
    
    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.use_property_split = False
        
        obj: bpy.types.Object = context.active_object
        row = layout.row()
        if obj is None:
            row.label(text="Click on an Armature or Camera.")
        elif obj.select_get() is False:
            row.label(text="Click on an Armature or Camera.")
        elif obj.type == 'ARMATURE' or obj.type == 'CAMERA':
            if obj.animation_data is None:
                row.label(text=f'The selected {obj.type.lower()} has no animation data!', icon='ERROR')
            elif obj.animation_data.action is None:
                row.label(text=f'The selected {obj.type.lower()} has no action!', icon='ERROR')
            else:
                row.operator(SUB_OP_anim_export.bl_idname, icon='EXPORT', text='Export .NUANMB')
        else:
            row.label(text=f'The selected {obj.type.lower()} is not an armature or a camera.')

class SUB_OP_anim_export(Operator):
    bl_idname = 'sub.anim_export'
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
    use_debug_timer: BoolProperty(
        name='Debug timing stats',
        description='Print advance import timing info to the console',
        default=False,
    )

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        obj: bpy.types.Object = context.object
        if obj is None:
            return False
        elif obj.type != 'ARMATURE' and obj.type != 'CAMERA':
            return False
        elif obj.animation_data is None:
            return False
        elif obj.animation_data.action is None:
            return False
        return True

    def invoke(self, context: Context, _event):
        obj: bpy.types.Object = context.object
        self.first_blender_frame = context.scene.frame_start
        self.last_blender_frame = context.scene.frame_end

        ssp: SubSceneProperties = context.scene.sub_scene_properties
        if ssp.last_anim_export_dir != "":
            self.filepath = f'{ssp.last_anim_export_dir}/{obj.animation_data.action.name}'
        elif ssp.last_anim_import_dir != "":
            self.filepath = f'{ssp.last_anim_import_dir}/{obj.animation_data.action.name}'
        else:
            self.filepath = f'{obj.animation_data.action.name}'

        if not self.filepath.endswith('.nuanmb'):
            self.filepath += '.nuanmb'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        ssp.last_anim_export_dir = str(Path(self.filepath).parent)
        print("Starting Animation Export...")
        start = time.perf_counter()

        obj: bpy.types.Object = context.object

        if not self.filepath.endswith('.nuanmb'):
            self.filepath += '.nuanmb'

        with cProfile.Profile() as pr:
            if obj.type == 'ARMATURE':
                export_model_anim_fast(
                    context, self, obj, self.filepath,
                    self.include_transform_track, self.include_material_track,
                    self.include_visibility_track, self.first_blender_frame,
                    self.last_blender_frame)
            else:
                # TODO: Make "fast" camera export using same technique (currently fighter camera animations take less than a second to export, so theres not much priority)
                export_camera_anim(context, self, obj, self.filepath,
                    self.first_blender_frame, self.last_blender_frame)  
        if self.use_debug_timer:
            stats = pstats.Stats(pr)
            stats.sort_stats(pstats.SortKey.TIME)
            stats.print_stats()

        end = time.perf_counter()
        print(f"Animation Export finished in {end - start} seconds!")
        return {'FINISHED'}
           
class Location():
    def __init__(self, x, y, z):
        self.x: float = x
        self.y: float = y
        self.z: float = z
    def __repr__(self) -> str:
        return f'[{self.x=}, {self.y=}, {self.z=}]'

class Rotation():
    def __init__(self, w, x, y, z):
        self.w: float = w
        self.x: float = x
        self.y: float = y
        self.z: float = z
    def __repr__(self) -> str:
        return f'[{self.w=}, {self.x=}, {self.y=}, {self.z=}]'

class Scale():
    def __init__(self, x, y, z):
        self.x: float = x
        self.y: float = y
        self.z: float = z
    def __repr__(self) -> str:
        return f'[{self.x=}, {self.y=}, {self.z=}]'

def get_smash_transform(m) -> Matrix:
    # This is the inverse of the get_blender_transform permutation matrix.
    # https://en.wikipedia.org/wiki/Matrix_similarity
    p = Matrix([
        [0, 1, 0, 0],
        [-1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])
    # Perform the transformation m in Blender's basis and convert back to Ultimate.
    return p @ m @ p.inverted()

def transform_group_fix_floating_point_inaccuracies(trans_group: ssbh_data_py.anim_data.GroupData):
    from math import isclose
    for node in trans_group.nodes:
        track = node.tracks[0]
        if len(track.values) <= 1:
            continue
        first_transform = track.values[0]
        for index, val in enumerate(first_transform.scale):
            if isclose(val, 1, abs_tol=.00001):
                first_transform.scale[index] = 1
        for current_transform_index, current_transform in enumerate(track.values[1:], start=1):
            # To avoid quaternion math issues, have to check if every value is close and replace the entire quaternion,
            #  not just the 'x' or 'y' or 'z' or 'w'
            all_rot_vals_close = True
            for i in (0,1,2,3):
                if not isclose(current_transform.rotation[i], first_transform.rotation[i], abs_tol=.00001):
                    all_rot_vals_close = False
            if all_rot_vals_close is True:
                track.values[current_transform_index].rotation = first_transform.rotation
            
            for i in (0,1,2):
                if isclose(current_transform.scale[i], first_transform.scale[i], abs_tol=.00001):
                    track.values[current_transform_index].scale[i] = first_transform.scale[i]
            
            for i in (0,1,2):
                if isclose(current_transform.translation[i], first_transform.translation[i], abs_tol=.00001):
                    track.values[current_transform_index].translation[i] = first_transform.translation[i]

def uv_transform_equality(a: ssbh_data_py.anim_data.UvTransform, b: ssbh_data_py.anim_data.UvTransform) -> bool:
    if a.rotation != b.rotation:
        return False
    if a.scale_u != b.scale_u:
        return False
    if a.scale_v != b.scale_v:
        return False
    if a.translate_u != b.translate_u:
        return False
    if a.translate_v != b.translate_v:
        return False
    return True

def does_armature_data_have_fcurves(arma: bpy.types.Object) -> bool:
    if arma.data.animation_data is None:
        return False
    if arma.data.animation_data.action is None:
        return False
    if arma.data.animation_data.action.fcurves is None:
        return False
    return True

def export_model_anim_fast(context, operator: bpy.types.Operator, arma: bpy.types.Object, filepath, include_transform_track, include_material_track, include_visibility_track, first_blender_frame, last_blender_frame):
    # SSBH Anim Setup
    ssbh_anim_data =  ssbh_data_py.anim_data.AnimData()
    final_frame_index = last_blender_frame - first_blender_frame
    ssbh_anim_data.final_frame_index = final_frame_index

    # Gather Groups
    if include_transform_track:
        # First gather the blender animation data, then create the ssbh data
        # Create value dicts ahead of time
        bone_name_to_location_values: dict[str, list[Location]] = {}
        bone_name_to_rotation_values: dict[str, list[Rotation]] = {}
        bone_name_to_scale_values: dict[str, list[Scale]] = {}
        bone_to_rel_matrix_local = {}
        reordered_pose_bones = get_heirarchy_order(list(arma.pose.bones))

        # Fill value dicts with default values. Not every bone will be animated, so for these the default values of a matrix basis will be needed
        for pose_bone in reordered_pose_bones:
            bone_name_to_location_values[pose_bone.name] = [Location(0.0, 0.0, 0.0) for _ in range(first_blender_frame, last_blender_frame + 1)]
            bone_name_to_rotation_values[pose_bone.name] = [Rotation(1.0, 0.0, 0.0, 0.0) for _ in range(first_blender_frame, last_blender_frame + 1)]
            bone_name_to_scale_values[pose_bone.name] = [Scale(1.0, 1.0, 1.0) for _ in range(first_blender_frame, last_blender_frame + 1)]
            if pose_bone.parent: # non-root bones
                bone_to_rel_matrix_local[pose_bone] = pose_bone.parent.bone.matrix_local.inverted() @ pose_bone.bone.matrix_local
            else: # root bones
                bone_to_rel_matrix_local[pose_bone] = pose_bone.bone.matrix_local

        # Go through the pose bones' fcurves and store all the values at each frame.
        animated_pose_bones: set[bpy.types.PoseBone] = set()
        
        object_level_transform_reported = False
        for fcurve in arma.animation_data.action.fcurves:
            regex = r'pose\.bones\[\"(.*)\"\]\.(.*)'
            matches = re.match(regex, fcurve.data_path)
            if matches is None: # A fcurve in the action that isn't a bone transform, such as the user keyframing the Armature Object itself.
                object_level_transfrom_data_path_regex = r'^location$|^scale$|^rotation_quaternion$|^rotation_euler$'
                if re.match(object_level_transfrom_data_path_regex, fcurve.data_path):
                    if object_level_transform_reported == False:
                        operator.report(type={'WARNING'}, message=f"The Armature's \"Object Mode\" location/rotation/scale was keyframed, this will not be exported! Make sure to enter Pose Mode, and keyframe a bone's location/rotation/scale instead!")
                        object_level_transform_reported = True
                    continue
                operator.report(type={'WARNING'}, message=f"The fcurve with data path {fcurve.data_path} will not be exported, since it didn't match the pattern of a bone fcurve.")
                continue
            if len(matches.groups()) != 2: # TODO: Is this possible?
                operator.report(type={'WARNING'}, message=f"The fcurve with data path {fcurve.data_path} will not be exported, its format only partially matched the expected pattern of a bone fcurve.")
                continue
            bone_name = matches.groups()[0]
            transform_subtype = matches.groups()[1]
            if transform_subtype == 'location':
                for index, frame in enumerate(range(first_blender_frame, last_blender_frame+1)):
                    if fcurve.array_index == 0:
                        bone_name_to_location_values[bone_name][index].x = fcurve.evaluate(frame)
                    elif fcurve.array_index == 1:
                        bone_name_to_location_values[bone_name][index].y = fcurve.evaluate(frame)
                    elif fcurve.array_index == 2:
                        bone_name_to_location_values[bone_name][index].z = fcurve.evaluate(frame)
            elif transform_subtype == 'rotation_quaternion':
                for index, frame in enumerate(range(first_blender_frame, last_blender_frame+1)):
                    if fcurve.array_index == 0:
                        bone_name_to_rotation_values[bone_name][index].w = fcurve.evaluate(frame)
                    elif fcurve.array_index == 1:
                        bone_name_to_rotation_values[bone_name][index].x = fcurve.evaluate(frame)
                    elif fcurve.array_index == 2:
                        bone_name_to_rotation_values[bone_name][index].y = fcurve.evaluate(frame)
                    elif fcurve.array_index == 3:
                        bone_name_to_rotation_values[bone_name][index].z = fcurve.evaluate(frame)
            elif transform_subtype == 'scale':
                for index, frame in enumerate(range(first_blender_frame, last_blender_frame+1)):
                    if fcurve.array_index == 0:
                        bone_name_to_scale_values[bone_name][index].x = fcurve.evaluate(frame)
                    elif fcurve.array_index == 1:
                        bone_name_to_scale_values[bone_name][index].y = fcurve.evaluate(frame)
                    elif fcurve.array_index == 2:
                        bone_name_to_scale_values[bone_name][index].z = fcurve.evaluate(frame)
            animated_pose_bone = arma.pose.bones.get(bone_name)
            if animated_pose_bone is not None:
                animated_pose_bones.add(animated_pose_bone)

        # Detect Negative Scale, Fix Zero Scale
        zero_scale_reported = False
        for bone_name, scale_values_list in bone_name_to_scale_values.items():
            for index, frame in enumerate(range(first_blender_frame, last_blender_frame+1)):
                scale = scale_values_list[index]
                negative_axis: set[str] = set()
                if scale.x < 0.0:
                    negative_axis.add('X')
                if scale.y < 0.0:
                    negative_axis.add('Y')
                if scale.z < 0.0:
                    negative_axis.add('Z')
                if negative_axis:
                    operator.report(type={'ERROR'}, message=f"Negative Scale Detected! Negative scale is not supported, and so the export was cancelled! The first instance was on bone {bone_name} on blender frame {frame} in the {negative_axis} axis.")
                    return
                zero_axis: set[str] = set()
                if math.isclose(scale.x, 0.0, abs_tol= 0.0001):
                    zero_axis.add('X')
                    scale.x = 0.0001
                if math.isclose(scale.y, 0.0, abs_tol= 0.0001):
                    zero_axis.add('Y')
                    scale.y = 0.0001
                if math.isclose(scale.z, 0.0, abs_tol= 0.0001):
                    zero_axis.add('Z')
                    scale.z = 0.0001
                if zero_axis:
                    if not zero_scale_reported:
                        operator.report(type={'INFO'}, message=f"Clamped scale values of `0` to `0.0001` for export. The first instance was on bone {bone_name} on blender frame {frame} in the {zero_axis} axis.")
                        zero_scale_reported = True
                        
        # Create SSBH Transform Group
        trans_group = ssbh_data_py.anim_data.GroupData(ssbh_data_py.anim_data.GroupType.Transform)
        ssbh_anim_data.groups.append(trans_group)

        # Create ssbh nodes for the animated bones, no values just yet tho. Also, its normal for smash anims to skip some un-animated bones.
        for bone in animated_pose_bones:
            node = ssbh_data_py.anim_data.NodeData(bone.name)
            track = ssbh_data_py.anim_data.TrackData('Transform')
            track.compensate_scale = False
            node.tracks.append(track)
            trans_group.nodes.append(node)

        # Convenience dict for later node access
        node_name_to_node = {node.name:node for node in trans_group.nodes}

        # Blender stores the 'matrix basis' values in the fcurves
        # Smash stores a 'relative matrix', such that bone.parent.final_matrix @ bone.relative_matrix = bone.final_matrix
        # Need to calculate the final_matrix of each bone at each frame, even the un-animated ones, so that the child bones can be properly calculated.
        bone_to_world_matrix = {}
        for bone in reordered_pose_bones:
            for index, _ in enumerate(range(first_blender_frame, last_blender_frame+1)):
                # Get the matrix basis from the stored values of this frame.
                trans_basis_vec = bone_name_to_location_values[bone.name][index]
                trans_basis_mat = Matrix.Translation([trans_basis_vec.x, trans_basis_vec.y, trans_basis_vec.z])
                rot_basis_vec = bone_name_to_rotation_values[bone.name][index]
                rot_basis_quat = Quaternion([rot_basis_vec.w, rot_basis_vec.x, rot_basis_vec.y, rot_basis_vec.z])
                rot_basis_mat = Matrix.Rotation(rot_basis_quat.angle, 4, rot_basis_quat.axis)
                scale_basis_vec = bone_name_to_scale_values[bone.name][index]
                scale_basis_mat = Matrix.Diagonal((scale_basis_vec.x, scale_basis_vec.y, scale_basis_vec.z, 1.0))
                matrix_basis = Matrix(trans_basis_mat @ rot_basis_mat @ scale_basis_mat)

                # Now we can calculate and update the world matrix.
                if bone.parent is None: # Root bones
                    bone_to_world_matrix[bone] = matrix_basis
                else: # Non-root bones
                    bone_to_world_matrix[bone] = bone_to_world_matrix[bone.parent] @ bone_to_rel_matrix_local[bone] @ matrix_basis

                # Now if theres a matching node, we can update the values for that node.
                node = node_name_to_node.get(bone.name)
                if node is not None:
                    # Have to get the relative matrix from the stored matrixes, then transform that to smash orientation.
                    if bone.parent is None:
                        raw_rel_matrix = bone_to_world_matrix[bone]
                    else:
                        raw_rel_matrix = bone_to_world_matrix[bone.parent].inverted() @ bone_to_world_matrix[bone]
                    smash_rel_matrix = get_smash_transform(raw_rel_matrix)
                    t,q,s = smash_rel_matrix.decompose()
                    transform = ssbh_data_py.anim_data.Transform(
                        [s.x, s.y, s.z],
                        [q.x, q.y, q.z, q.w],
                        [t.x, t.y, t.z]
                    )
                    node.tracks[0].values.append(transform)
                    # Check for quaternion interpolation issues
                    if index > 0:
                        pq = mathutils.Quaternion(node.tracks[0].values[index-1].rotation)
                        cq = mathutils.Quaternion(node.tracks[0].values[index].rotation)
                        if pq.dot(cq) < 0:
                            node.tracks[0].values[index].rotation = [-c for c in node.tracks[0].values[index].rotation]
        # Pre-Saving Optimizations
        transform_group_fix_floating_point_inaccuracies(trans_group)
        # Vanilla anims sort the nodes alphabetically. 
        # Without this, certain anims will behave incorrectly, such as the Trans bone motion not working in-game.
        trans_group.nodes.sort(key=lambda node: node.name)

    if include_visibility_track and does_armature_data_have_fcurves(arma):
        # Convenience variable for the sub_anim_properties
        sap: SUB_PG_sub_anim_data = arma.data.sub_anim_properties
        
        # First gather the values
        vis_track_index_to_name: dict[int, str] = {}
        vis_track_index_to_values: dict[int, list[bool]] = {}
        fcurve: bpy.types.FCurve
        for fcurve in arma.data.animation_data.action.fcurves:
            regex = r'.*\[(\d*)\]\.value'
            matches = re.match(regex, fcurve.data_path)
            if matches is None: # Not a visibility fcurve, its probably a material track fcurve
                continue
            vis_track_index = int(matches.groups()[0])
            if vis_track_index >= len(sap.vis_track_entries): # this can happen if the user removes entries manually but not the fcurves
                operator.report(type={'WARNING'}, message=f'The fcurve with data path {fcurve.data_path} will be skipped, its index was out of bounds.')
                continue
            vis_track_index_to_name[vis_track_index] = sap.vis_track_entries[vis_track_index].name
            vis_track_index_to_values[vis_track_index] = [bool(fcurve.evaluate(frame)) for frame in range(first_blender_frame, last_blender_frame+1)]

        # Create Vis Group
        vis_group = ssbh_data_py.anim_data.GroupData(ssbh_data_py.anim_data.GroupType.Visibility)
        ssbh_anim_data.groups.append(vis_group)

        # Create nodes
        for vis_track_index, values in vis_track_index_to_values.items():
            node = ssbh_data_py.anim_data.NodeData(vis_track_index_to_name[vis_track_index])
            track = ssbh_data_py.anim_data.TrackData('Visibility')
            track.values = values.copy()
            node.tracks.append(track)
            vis_group.nodes.append(node)
        
        # Sort Nodes
        vis_group.nodes.sort(key= lambda x: sap.vis_track_entries.find(x.name))

    if include_material_track and does_armature_data_have_fcurves(arma):
        # Convenience variable for the sub_anim_properties
        sap: SUB_PG_sub_anim_data = arma.data.sub_anim_properties

        # Gather the Values
        # Not every CustomVector, CustomBool, etc will be animated, so only the animated ones should be exported.
        # In addition, fcurves may only exist for a few indices of a CustomVector or TextureTransform, since the user may not have animated them all
        # Example: mat_name_prop_name_to_values['EyeL']['CustomVector31'] -> [[1.0,1.0,1.0,1.0], ...]
        mat_name_prop_name_to_values: dict[str, dict[str, list[CustomVector|CustomFloat|CustomBool|PatternIndex|TextureTransform]]] = {}
        for fcurve in arma.data.animation_data.action.fcurves:
            regex = r"sub_anim_properties\.mat_tracks\[(\d+)\]\.properties\[(\d+)\](\.\w+)"
            matches = re.match(regex, fcurve.data_path)
            if matches is None: # The vis and mat track fcurves are in the same action, so its normal to not match every fcurve
                continue
            if len(matches.groups()) != 3: # TODO: Is this possible?
                operator.report(type={'WARNING'}, message=f"The fcurve with data path {fcurve.data_path} will not be exported, its format only partially matched the expected pattern of a mat track.")
                continue
            # The material index may be out of bounds, this can happen due to improper removal of the MatTrack from the sub_anim_properties.
            # This should however not happen when removed properly through the implemented operators
            material_index = int(matches.groups()[0])
            if material_index >= len(sap.mat_tracks):
                operator.report(type={'WARNING'}, message=f'The fcurve with data path {fcurve.data_path} will be skipped, its material index was out of bounds.')
                continue
            # Now that the material index is validated, can grab the coresponding MatTrack
            mat_track: SUB_PG_mat_track = sap.mat_tracks[material_index]
            material_name = mat_track.name
            # This dict won't exist yet for the first fcurve belonging to a material, so we add it now.
            if mat_name_prop_name_to_values.get(material_name) is None: 
                mat_name_prop_name_to_values[material_name] = {}
            # The property index may be out of bounds, this can happen due to improper removal of the MatTrackProperty from the MatTrack.
            # This should however not happen when removed properly through the implemented operators
            property_index = int(matches.groups()[1])
            if property_index >= len(mat_track.properties):
                operator.report(type={'WARNING'}, message=f'The fcurve with data path {fcurve.data_path} will be skipped, its property index was out of bounds.')
                continue
            # Now that the property index is validated, can grab the coresponding MatTrackProperty
            mat_track_property: SUB_PG_mat_track_property = mat_track.properties[property_index]
            property_name = mat_track_property.name
            # This dict won't exist yet for the first fcurve belonging to a material's property, so we add it now.
            # If it didn't exist, then the default values also didn't exist yet so nows a good time to add them.
            # The default values need to be filled out because an fcurve for each array_index may not exist.
            # This only applies to the CustomVector and TextureTransforms, all others only have one fcurve for the property.  
            if mat_name_prop_name_to_values.get(material_name).get(property_name) is None:
                if mat_track_property.sub_type == 'VECTOR':
                    cv = mat_track_property.custom_vector
                    # Use numpy as this one line takes way to long
                    #mat_name_prop_name_to_values[material_name][property_name] = [[cv[0], cv[1], cv[2], cv[3]] for _ in range(0, final_frame_index+1)]
                    #mat_name_prop_name_to_values[material_name][property_name] = np.full((final_frame_index+1, 4), [cv[0], cv[1], cv[2], cv[3]]).tolist()
                    # Nevermind it seems like the numpy array needs to be converted back into a list before being saved
                    mat_name_prop_name_to_values[material_name][property_name] = [[cv[0], cv[1], cv[2], cv[3]] for _ in range(0, final_frame_index+1)]
                elif mat_track_property.sub_type == 'TEXTURE':
                    tt = mat_track_property.texture_transform
                    mat_name_prop_name_to_values[material_name][property_name] = [ssbh_data_py.anim_data.UvTransform(tt[0], tt[1], tt[2], tt[3], tt[4]) for _ in range(0, final_frame_index+1)]
                else: # Bools, Floats, PatternIndex have only one fcurve, so any default value filled here would get replaced anyways
                    mat_name_prop_name_to_values[material_name][property_name] = []
            # Finally can add the values at each frame
            for index, frame in enumerate(range(first_blender_frame, last_blender_frame+1)):
                if mat_track_property.sub_type == 'VECTOR':
                    mat_name_prop_name_to_values[material_name][property_name][index][fcurve.array_index] = fcurve.evaluate(frame)
                elif mat_track_property.sub_type == 'BOOL':
                    mat_name_prop_name_to_values[material_name][property_name].append(bool(fcurve.evaluate(frame)))
                elif mat_track_property.sub_type == 'TEXTURE':
                    if fcurve.array_index == 0:
                        mat_name_prop_name_to_values[material_name][property_name][index].scale_u = fcurve.evaluate(frame)
                    elif fcurve.array_index == 1:
                        mat_name_prop_name_to_values[material_name][property_name][index].scale_v = fcurve.evaluate(frame)
                    elif fcurve.array_index == 2:
                        mat_name_prop_name_to_values[material_name][property_name][index].rotation = fcurve.evaluate(frame)
                    elif fcurve.array_index == 3:
                        mat_name_prop_name_to_values[material_name][property_name][index].translate_u = fcurve.evaluate(frame)
                    elif fcurve.array_index == 4:
                        mat_name_prop_name_to_values[material_name][property_name][index].translate_v = fcurve.evaluate(frame)
                else:
                    mat_name_prop_name_to_values[material_name][property_name].append(fcurve.evaluate(frame))
                
        # Now we can finally process the data
        # Create the material group
        mat_group = ssbh_data_py.anim_data.GroupData(ssbh_data_py.anim_data.GroupType.Material)
        ssbh_anim_data.groups.append(mat_group)
        # Create the nodes and tracks
        for mat_name in mat_name_prop_name_to_values:
            node = ssbh_data_py.anim_data.NodeData(mat_name)
            mat_group.nodes.append(node)
            for prop_name in mat_name_prop_name_to_values[mat_name]:
                track = ssbh_data_py.anim_data.TrackData(prop_name)
                node.tracks.append(track)
                track.values.extend(mat_name_prop_name_to_values[mat_name][prop_name])
        # Sort the nodes and tracks by their user-defined position
        mat_group.nodes.sort(key= lambda x: sap.mat_tracks.find(x.name))
        for node in mat_group.nodes:
            node.tracks.sort(key= lambda x: sap.mat_tracks[node.name].properties.find(x.name))

    # Pre-Saving Optimizations
    for group in ssbh_anim_data.groups:
        for node in group.nodes:
            for track in node.tracks:
                if type(track.values[0]) == ssbh_data_py.anim_data.UvTransform:
                    if all(uv_transform_equality(value, track.values[0]) for value in track.values):
                        track.values = [track.values[0]]
                elif all(value == track.values[0] for value in track.values):
                    track.values = [track.values[0]]
    
    # Done!
    ssbh_anim_data.save(filepath)        
                
def export_camera_anim(context, operator, camera: bpy.types.Object, filepath, first_blender_frame, last_blender_frame):
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
        context.scene.frame_set(frame)
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
