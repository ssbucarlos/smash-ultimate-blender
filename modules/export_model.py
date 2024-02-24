import os
import time
import bpy
import os.path
import numpy as np
import math
import bmesh
import re
import traceback
import cProfile
import pstats

from pathlib import Path
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, Panel, EditBone, Object, Context, EditBone, Mesh, MeshVertex, ShapeKey
from mathutils import Vector, Matrix

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from .helper_bone_data import SubHelperBoneData, AimConstraint, OrientConstraint
    from ..properties import SubSceneProperties

from .. import ssbh_data_py
from .. import pyprc
from ..operators import material_inputs


class SUB_PT_export_model(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Ultimate'
    bl_label = 'Model Exporter'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        layout = self.layout
        layout.use_property_split = False

        layout.row().label(text='Select an armature. The armature + its meshes will be exported')
        layout.row().prop(ssp, 'model_export_arma', icon='ARMATURE_DATA')
        if not ssp.model_export_arma:
            return
        if ssp.model_export_arma.name not in context.view_layer.objects.keys():
            layout.row().label(text='Armature not in view layer!', icon='ERROR')
            return
        if '' == ssp.vanilla_nusktb:
            layout.row().label(text='Select the vanilla .nusktb for the exporter to reference!')
            row = layout.row()
            row.alert = True
            row.label(text='Character Mods need to do this!')
            layout.row().label(text="If you know you don't need it then export anyways.")
            layout.row().operator('sub.vanilla_nusktb_selector', icon='FILE', text='Select Vanilla Nusktb')
            layout.row().operator('sub.model_exporter', icon='EXPORT', text='Export Model Files Anyways...')
            return
        
        new_bones, missing_bones = get_standard_bone_changes(ssp.model_export_arma, ssp.vanilla_nusktb)
        if any(len(s) > 0 for s in (new_bones, missing_bones)):
            layout.row().label(text='Change in "Standard Bones" detected!')
            if len(new_bones) > 0:
                row = layout.row()
                row.label(text='New Bones')
                if len(new_bones) > 5:
                    row.prop(ssp, 'model_export_show_all_new_bones')
                box = layout.row().box()
                for index, new_bone in enumerate(new_bones):
                    if index > 4 and not ssp.model_export_show_all_new_bones:
                        box.row().label(text=f'Only showed 5. Total = {len(new_bones)}')
                        break
                    box.row().label(text=f'{new_bone}', icon='BONE_DATA')

            if len(missing_bones) > 0:
                row = layout.row()
                row.label(text='Missing Bones')
                if len(missing_bones) > 5:
                    row.prop(ssp, 'model_export_show_all_missing_bones')
                box = layout.row().box()
                for index, missing_bone in enumerate(missing_bones):
                    if index > 4 and not ssp.model_export_show_all_missing_bones:
                        box.row().label(text=f'Only showed 5. Total = {len(missing_bones)}')
                        break
                    box.row().label(text=f'{missing_bone}', icon='BONE_DATA')
            layout.row().label(text='A new "update.prc" file is needed or the skeleton will glitch in game!')
            layout.row().label(text='The new "update.prc" file does NOT go with the rest of the model files!')
            layout.row().label(text='The new "update.prc" file goes in the motion folder!')
            layout.row().label(text='example: fighter/demon/motion/body/c00/update.prc')
            if '' == ssp.vanilla_update_prc:
                layout.row().label(text='Please select the vanilla "update.prc" file to properly generate the new one.')
                layout.row().operator('sub.vanilla_update_prc_selector', icon='FILE', text='Select Vanilla update.prc')
            else:
                layout.row().label(text=f'Selected reference update.prc: {ssp.vanilla_update_prc}')
                layout.row().operator('sub.vanilla_update_prc_selector', icon='FILE', text='Re-Select Vanilla update.prc')
        layout.row().label(text='Selected reference .nusktb: ' + ssp.vanilla_nusktb)
        layout.row().operator('sub.vanilla_nusktb_selector', icon='FILE', text='Re-Select Vanilla Nusktb')

        layout.row().operator('sub.model_exporter', icon='EXPORT', text='Export Model Files to a Folder')
    
class SUB_OP_vanilla_update_prc_selector(Operator, ImportHelper):
    bl_idname = 'sub.vanilla_update_prc_selector'
    bl_label = 'Vanilla update.prc Selector'

    filter_glob: StringProperty(
        default='*.prc',
        options={'HIDDEN'}
    )
    def execute(self, context):
        context.scene.sub_scene_properties.vanilla_update_prc = self.filepath
        return {'FINISHED'}

class SUB_OP_vanilla_nusktb_selector(Operator, ImportHelper):
    bl_idname = 'sub.vanilla_nusktb_selector'
    bl_label = 'Vanilla Nusktb Selector'

    filter_glob: StringProperty(
        default='*.nusktb',
        options={'HIDDEN'}
    )
    def execute(self, context):
        context.scene.sub_scene_properties.vanilla_nusktb = self.filepath
        return {'FINISHED'}      

class SUB_OP_model_exporter(Operator):
    bl_idname = 'sub.model_exporter'
    bl_label = 'Export To This Folder'

    filter_glob: StringProperty(
        default='*.numdlb;*.nusktb;*.numshb;*.numatb;*.nuhlpb',
        options={'HIDDEN'},
        #maxlen=255,  # Max internal buffer length, longer would be clamped. Also blender has this in the example but tbh idk what it does yet
    )
    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    include_numdlb: BoolProperty(
        name="Export .NUMDLB",
        description="Export .NUMDLB",
        default=True,
    )
    include_numshb: BoolProperty(
        name="Export .NUMSHB",
        description="Export .NUMSHB",
        default=True,
    )
    include_numshexb: BoolProperty(
        name="Export .NUMSHEXB",
        description="Export .NUMSHEXB",
        default=True,
    )
    include_nusktb: BoolProperty(
        name="Export .NUSKTB",
        description="Export .NUSKTB",
        default=True,
    )
    include_numatb: BoolProperty(
        name="Export .NUMATB",
        description="Export .NUMATB",
        default=True,
    )
    include_nuhlpb: BoolProperty(
        name="Export .NUHLPB",
        description="Export .NUHLPB",
        default=True,
    )
    include_nutexb: BoolProperty(
        name="Export .NUTEXB",
        description="Export .NUTEXB",
        default=True,
    )

    linked_nusktb_settings: EnumProperty(
        name="Bone Linkage",
        description="Pick 'Order & Values' unless you intentionally edited the vanilla bones.",
        items=(
            ('ORDER_AND_VALUES', "Order & Values", "Preserve the order and transforms of vanilla bones (recommended)"),
            ('ORDER_ONLY', "Order Only", "Preserve the order of vanilla bones but use bone transforms from Blender."),
            ('NO_LINK', "No Link", "Recreate the bone order and transforms from Blender (not recommended)."),
        ),
        default='ORDER_AND_VALUES',
    )

    optimize_mesh_weights_to_parent_bone: EnumProperty(
        name="Mesh Weights",
        description="If a mesh is weighted to only one bone, this optimization improves performance. (Can cause issues if the mesh deforms!)",
        items=(
            ('ENABLED', "Optimize mesh weights by parenting to a bone where possible.", "This will improve performance, recommended for meshes that don't deform."),
            ('DISABLED', "Don't optimize mesh weights", "Mesh Weights will be exported as-is. (Recommended on meshes that deform.)"),
        ),
        default='DISABLED',
    )

    armature_position: EnumProperty(
        name='Armature Pos.',
        description="Select 'Rest' to use the Rest (T-Pose, A-Pose, etc...) Position.",
        items=(
            ('REST', 'Rest Position', 'Recommended, this is the expected behavior, select this unless you really intend to export the posed position.'),
            ('POSE', 'Pose Position', 'Not Recommended, as this is probably not what you want, as any minor error with helper bones or other bone constraints will cause export issues'),
        ),
        default='REST',
    )
    apply_modifiers: EnumProperty(
        name='Mesh Modifiers',
        description='Ignore or Apply the Mesh Modifiers',
        items=(
            ('APPLY', 'Apply Modifiers', 'Applies any mesh modifiers. Remember that some modifiers work strangely with un-applied transforms, if you notice export issues please apply transforms before exporting.'),
            ('IGNORE', 'Ignore Modifiers', 'Ignores the mesh modifiers.'),
        ),
        default='APPLY',
    )
    split_shape_keys: EnumProperty(
        name='Shape Keys',
        description="Ultimate doesn't support shape keys, so specify how to deal with blender shape keys.",
        items=(
            ('EXPORT_INCLUDE_ORIGINAL', 'Convert "VIS" Keys to New Meshes, and still export the base mesh', 'Keys whose name contain `_VIS` (e.g "Happy_VIS") will become a new mesh, AND the base mesh will ALSO be exported'),
            ('EXPORT_EXCULDE_ORIGINAL', 'Convert "VIS" Keys to New Meshes, but no longer export the base mesh', 'Keys whose name contain `_VIS` (e.g "Happy_VIS") will become a new mesh, BUT the base mesh will NOT be exported.'),
            ('IGNORE_SHAPEKEYS', 'Ignore Shapekeys','Shapekeys will be completely ignored. The current Mix will be ignored. Same as clearing the keys. '),
        ),
        default='IGNORE_SHAPEKEYS',
    )

    ignore_underscore_meshes: EnumProperty(
        name='Ignore Meshes',
        description="You can choose to not export some meshes on the model",
        items=(
            ('IGNORE_STARTING_UNDERSCORE', 'Ignore Meshes whose name starts with an Underscore "_"', 'For example, a mesh whose name is "_test" will not be exported.'),
            ('NONE', "Don't Ignore Any Meshes", "Won't ignore any meshes"),
        ),
        default='NONE',
    )
    use_debug_timer: BoolProperty(
        name='Print debug timing stats',
        description='Prints advance import timing info to the console, useful for development of this plugin.',
        default=False,
    )

    @classmethod
    def poll(cls, context):
        if not context.scene.sub_scene_properties.model_export_arma:
            return False
        return True

    # Initially set the filename field to be nothing
    def invoke(self, context, _event):
        if context.scene.sub_scene_properties.vanilla_nusktb == '':
            self.linked_nusktb_settings = 'NO_LINK'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        start = time.perf_counter()
        with cProfile.Profile() as pr:
            """
            export_model(self, context, self.directory, self.include_numdlb, self.include_numshb, self.include_numshexb,
                    self.include_nusktb, self.include_numatb, self.include_nuhlpb, self.include_nutexb, self.linked_nusktb_settings,
                    self.optimize_mesh_weights_to_parent_bone, self.armature_position, self.apply_modifiers,
                    self.split_shape_keys, self.ignore_underscore_meshes)
            """
            arma = context.scene.sub_scene_properties.model_export_arma
            export_model_ex_windows(self, context, arma, self.directory, self.include_numdlb, self.include_numshb, self.include_numshexb,
                    self.include_nusktb, self.include_numatb, self.include_nuhlpb, self.include_nutexb, self.linked_nusktb_settings,
                    self.optimize_mesh_weights_to_parent_bone, self.armature_position, self.apply_modifiers,
                    self.split_shape_keys, self.ignore_underscore_meshes)
        if self.use_debug_timer:
            stats = pstats.Stats(pr)
            stats.sort_stats(pstats.SortKey.TIME)
            #stats.print_stats()
            stats.dump_stats(str(Path(self.directory) / "timing_debug.prof"))
        end = time.perf_counter()
        print(f"Model Export finished in {end - start} seconds!")
        return {'FINISHED'}

def model_export_arma_update(self, context):
    ssp: SubSceneProperties = context.scene.sub_scene_properties
    ssp.vanilla_nusktb = ''
    ssp.vanilla_update_prc = ''

def trim_name(name: str) -> str:
    trimmed_name = re.split(r'\.\d\d\d$', name)[0]
    return trimmed_name

def would_trimmed_names_be_unique(names_to_check: set[str]) -> bool:
    trimmed_names = {trim_name(name) for name in names_to_check}
    return len(trimmed_names) == len(names_to_check)

def get_problematic_names(names_to_check: set[str]) -> set[str]:
    trimmed_name_to_og_names: dict[str, list[str]] = {trim_name(name) : [] for name in names_to_check}

    for name in names_to_check:
        trimmed_name_to_og_names[trim_name(name)].append(name)
    
    problematic_names = []
    for og_names in trimmed_name_to_og_names.values():
        if len(og_names) > 1:
            problematic_names.extend(og_names)
    
    return problematic_names
    
def trim_matl_texture_names(operator: Operator, ssbh_matl_data: ssbh_data_py.matl_data.MatlData):
    texture_names: set[str]  = {texture.data for entry in ssbh_matl_data.entries for texture in entry.textures}
    if would_trimmed_names_be_unique(texture_names) is not True:
        message = f'Texture names are not unique after trimming! So the texture names will be exported as-is, without trimming!'
        operator.report({'WARNING'}, message)
        problematic_names = get_problematic_names(texture_names)
        for problematic_name in problematic_names:
            message = f'The texture name of "{problematic_name}" is not a unique name after trimming! (Trimmed name is "{trim_name(problematic_name)}")'
            operator.report({'WARNING'}, message)
        return
    
    for entry in ssbh_matl_data.entries:
        for texture in entry.textures:
            texture.data = trim_name(texture.data)

def trim_material_labels(operator: Operator, ssbh_modl_data: ssbh_data_py.modl_data.ModlData, ssbh_matl_data: ssbh_data_py.matl_data.MatlData):
    material_names: set[str] = {entry.material_label for entry in ssbh_matl_data.entries}
    
    if would_trimmed_names_be_unique(material_names) is not True:
        message = f'Material names are not unique after trimming! So the material names will be exported as-is, without trimming!'
        operator.report({'WARNING'}, message)
        problematic_names = get_problematic_names(material_names)
        for problematic_name in problematic_names:
            message = f'The material name of "{problematic_name}" is not a unique name after trimming! (Trimmed name is "{trim_name(problematic_name)}")'
            operator.report({'WARNING'}, message)
        return
    
    for entry in ssbh_matl_data.entries:
        entry.material_label = trim_name(entry.material_label)
    
    for entry in ssbh_modl_data.entries:
        entry.material_label = trim_name(entry.material_label)

def weights_to_parent_bones(ssbh_mesh_data: ssbh_data_py.mesh_data.MeshData, ssbh_skel_data: ssbh_data_py.skel_data.SkelData):
    # https://github.com/ScanMountGoat/ssbh_data_py/blob/main/examples/parent_bone_to_weights.py
    bones: dict[str, ssbh_data_py.skel_data.BoneData] = {bone.name : bone for bone in ssbh_skel_data.bones}
    for mesh_object in ssbh_mesh_data.objects:
        if len(mesh_object.bone_influences) != 1:
            continue
        bone_name = mesh_object.bone_influences[0].bone_name
        bone_data = bones.get(bone_name)
        bone_matrix = ssbh_skel_data.calculate_world_transform(bone_data)
        inverted_bone_matrix = np.linalg.inv(bone_matrix)
        for position in mesh_object.positions:
            position.data = ssbh_data_py.mesh_data.transform_points(position.data, inverted_bone_matrix)
        
        for normal in mesh_object.normals:
            normal.data = ssbh_data_py.mesh_data.transform_vectors(normal.data, inverted_bone_matrix)

        for tangent in mesh_object.tangents:
            tangent.data = ssbh_data_py.mesh_data.transform_vectors(tangent.data, inverted_bone_matrix)

        for binormal in mesh_object.binormals:
            binormal.data = ssbh_data_py.mesh_data.transform_vectors(binormal.data, inverted_bone_matrix)
        
        mesh_object.parent_bone_name = bone_name
        mesh_object.bone_influences.clear()

def calc_loop_triangles(mesh: Mesh):
    mesh.calc_loop_triangles()

def calc_normals_split(mesh: Mesh):
    mesh.calc_normals_split()

def calc_tangents(mesh: Mesh):
    mesh.calc_tangents(uvmap="map1" if mesh.uv_layers.get("map1") else mesh.uv_layers[0].name)

def validate_material_indices(mesh: Mesh):
    mesh.validate_material_indices()

def validate_mesh(mesh: Mesh):
    calc_loop_triangles(mesh)
    #calc_normals_split(mesh) #Not necessary since calc_tangents also calculates normals anyways
    calc_tangents(mesh)
    validate_material_indices(mesh)

def export_model_ex_windows(operator: Operator, context: Context, arma: bpy.types.Object, output_dir: str, include_numdlb, include_numshb, include_numshexb, include_nusktb,
                include_numatb, include_nuhlpb, include_nutexb, linked_nusktb_settings, optimize_mesh_weights:str, armature_position: str,
                apply_modifiers: str, split_shape_keys: str, ignore_underscore_meshes:str):
    from .mesh.export_mesh import create_ssbh_mesh_modl_entries_from_blender_mesh, create_ssbh_mesh_modl_entries_from_blender_mesh_with_shapekeys
    from .mesh.export_mesh import get_tris_per_material, get_ssbh_data_from_mesh_loops, get_data_from_mesh_ex

    mesh_objects: list[bpy.types.Object] = [child for child in arma.children if child.type == 'MESH']

    ssbh_modl_data = ssbh_data_py.modl_data.ModlData()
    depsgraph = context.evaluated_depsgraph_get()
    meshes_eval = [mesh_object.evaluated_get(depsgraph).data for mesh_object in mesh_objects]
    # TODO: Shape key export lol
    mesh_data_to_export = []
    for mesh_eval in meshes_eval:
        mesh_eval: Mesh
        validate_mesh(mesh_eval)
        mesh_data = get_data_from_mesh_ex(mesh_eval, mesh_eval.materials)
        mesh_data_to_export.append(mesh_data)

    from .material.create_matl_from_blender_materials import create_matl_from_blender_materials
    materials = {material for mesh in mesh_objects for material in mesh.data.materials}
    ssbh_matl_data = create_matl_from_blender_materials(operator, materials)

    ssbh_skel_data, prc = make_skel(operator, context, linked_nusktb_settings)

    # Modl
    ssbh_modl_data.model_name = 'model'
    ssbh_modl_data.skeleton_file_name = 'model.nusktb'
    ssbh_modl_data.material_file_names = ['model.numatb']
    ssbh_modl_data.animation_file_name = None
    ssbh_modl_data.mesh_file_name = 'model.numshb'

    if ssbh_matl_data is not None:
        trim_matl_texture_names(operator, ssbh_matl_data)
    if ssbh_modl_data is not None and ssbh_matl_data is not None:
        trim_material_labels(operator, ssbh_modl_data, ssbh_matl_data)

    output_dir = Path(output_dir)
    #ssbh_modl_data.save(str(output_dir / "model.numdlb"))
    from ..dependencies import ssbh_mesh_optimizer
    ssbh_mesh_optimizer.write_blender_meshes_to_file(mesh_data_to_export, Path(output_dir))
    #ssbh_matl_data.save(str(output_dir / "model.numatb"))
    ssbh_skel_data.save(str(output_dir / "model.nusktb"))

    from .texture.export_nutexb import export_nutexb_from_blender_materials
    
    if include_nutexb:
        export_nutexb_from_blender_materials(operator, materials, output_dir)    

def export_model_ex(operator: Operator, context: Context, arma: bpy.types.Object, output_dir: str, include_numdlb, include_numshb, include_numshexb, include_nusktb,
                include_numatb, include_nuhlpb, include_nutexb, linked_nusktb_settings, optimize_mesh_weights:str, armature_position: str,
                apply_modifiers: str, split_shape_keys: str, ignore_underscore_meshes:str, pr):
    from .mesh.export_mesh import create_ssbh_mesh_modl_entries_from_blender_mesh, create_ssbh_mesh_modl_entries_from_blender_mesh_with_shapekeys

    mesh_objects: list[bpy.types.Object] = [child for child in arma.children if child.type == 'MESH']

    ssbh_mesh_data = ssbh_data_py.mesh_data.MeshData()
    ssbh_modl_data = ssbh_data_py.modl_data.ModlData()

    for mesh_object in mesh_objects:
        if mesh_object.data.shape_keys:
            new_ssbh_mesh_objects, new_ssbh_modl_entries = create_ssbh_mesh_modl_entries_from_blender_mesh_with_shapekeys(context, mesh_object, mesh_object.data)
        else:
            depsgraph = context.evaluated_depsgraph_get()
            obj_eval: Object = mesh_object.evaluated_get(depsgraph)
            mesh_eval = obj_eval.data
            new_ssbh_mesh_objects, new_ssbh_modl_entries = create_ssbh_mesh_modl_entries_from_blender_mesh(mesh_eval, mesh_eval.name)
        ssbh_mesh_data.objects.extend(new_ssbh_mesh_objects)
        ssbh_modl_data.entries.extend(new_ssbh_modl_entries)
    
    from .material.create_matl_from_blender_materials import create_matl_from_blender_materials
    materials = {material for mesh in mesh_objects for material in mesh.data.materials}
    ssbh_matl_data = create_matl_from_blender_materials(operator, materials)

    ssbh_skel_data, prc = make_skel(operator, context, linked_nusktb_settings)

    # Modl
    ssbh_modl_data.model_name = 'model'
    ssbh_modl_data.skeleton_file_name = 'model.nusktb'
    ssbh_modl_data.material_file_names = ['model.numatb']
    ssbh_modl_data.animation_file_name = None
    ssbh_modl_data.mesh_file_name = 'model.numshb'

    if ssbh_matl_data is not None:
        trim_matl_texture_names(operator, ssbh_matl_data)
    if ssbh_modl_data is not None and ssbh_matl_data is not None:
        trim_material_labels(operator, ssbh_modl_data, ssbh_matl_data)

    output_dir = Path(output_dir)
    ssbh_modl_data.save(str(output_dir / "model.numdlb"))
    ssbh_mesh_data.save(str(output_dir / "model.numshb"))
    ssbh_matl_data.save(str(output_dir / "model.numatb"))
    ssbh_skel_data.save(str(output_dir / "model.nusktb"))

    from .texture.export_nutexb import export_nutexb_from_blender_materials
    
    if include_nutexb:
        export_nutexb_from_blender_materials(operator, materials, output_dir)    
    

def export_model(operator: bpy.types.Operator, context, directory, include_numdlb, include_numshb, include_numshexb, include_nusktb,
                include_numatb, include_nuhlpb, include_nutexb, linked_nusktb_settings, optimize_mesh_weights:str, armature_position: str,
                apply_modifiers: str, split_shape_keys: str, ignore_underscore_meshes:str):
    # Prepare the scene for export and find the meshes to export.
    arma: bpy.types.Object = context.scene.sub_scene_properties.model_export_arma
    context.view_layer.objects.active = arma

    # Track old_pose_position to return armature to whatever setting the user had
    old_pose_position = arma.data.pose_position
    if armature_position == 'REST':
        arma.data.pose_position = 'REST'
    elif armature_position == 'POSE':
        arma.data.pose_position = 'POSE'

    # Temporarily remove mesh vis drivers and un-hide them for export
    if arma.animation_data is not None:
        bpy.ops.sub.vis_drivers_remove()
    for child in arma.children:
        child.hide_viewport = False
        child.hide_render = False
    
    # Unselect objects so they don't interfere with ops
    for selected_object in context.selected_objects:
        selected_object.select_set(False)

    folder = Path(directory)
    # Create and save files individually to make this step more robust.
    # Users can avoid errors in generating a file by disabling export for that file.
    if include_numshb or include_numshexb or include_numatb or include_numdlb:
        # Only Mesh Objects, Skip Empty Objects
        if ignore_underscore_meshes == 'IGNORE_STARTING_UNDERSCORE':
            unprocessed_meshes: list[Object] = [child for child in arma.children if child.type == 'MESH' and len(child.data.vertices) > 0 and not child.name.startswith("_")] 
        else:
            unprocessed_meshes: list[Object] = [child for child in arma.children if child.type == 'MESH' and len(child.data.vertices) > 0] 
        
        # Remove swing meshes
        unprocessed_meshes = [mesh for mesh in unprocessed_meshes if mesh.data.sub_swing_data_linked_mesh.is_swing_mesh == False]
        
        # TODO: Is it possible to keep the correct order for non imported meshes?
        # TODO: Should users just re-order meshes in ssbh_editor instead?
        unprocessed_meshes.sort(key=lambda mesh: mesh.get("numshb order", 10000))

        if len(unprocessed_meshes) == 0:
            message = f'No meshes are parented to the armature {arma.name}. Exported .NUMDLB, .NUMSHB, .NUMATB, and .NUMSHEXB files will have no entries.'
            operator.report({'WARNING'}, message)

        # Smash Ultimate groups mesh objects with the same name like 'c00BodyShape'.
        # Blender appends numbers like '.001' to prevent duplicates, so we need to remove those before grouping.
        # Use a dictionary since we can't assume meshes with the same name are contiguous.
        group_name_to_unprocessed_meshes: dict[str, set[bpy.types.Object]] = {trim_name(mesh.name) : set() for mesh in unprocessed_meshes}
        for mesh in unprocessed_meshes:
            group_name_to_unprocessed_meshes[trim_name(mesh.name)].add(mesh)
        
        ssbh_mesh_data = None
        ssbh_modl_data = None
        ssbh_matl_data = None
        group_name_to_unprocessed_meshes_to_export_meshes, new_shape_key_meshes = get_processed_meshes(operator, context, group_name_to_unprocessed_meshes, apply_modifiers, split_shape_keys, armature_position)
        try:
            if include_numshb:
                try:
                    ssbh_mesh_data = make_ssbh_mesh_data(operator, context, group_name_to_unprocessed_meshes_to_export_meshes)
                except Exception as e:
                    operator.report({'ERROR'}, f'Failed to make ssbh mesh data, but will try to make the rest. Error="{e}" ; Traceback=\n{traceback.format_exc()}')

            if include_numdlb:
                try:
                    ssbh_modl_data = make_ssbh_modl_data(operator, context, group_name_to_unprocessed_meshes_to_export_meshes)
                except Exception as e:
                    operator.report({'ERROR'}, f'Failed to make modl_data (.NUMDLB), but will try to make the rest. Error="{e}" ; Traceback=\n{traceback.format_exc()}')
            
            if include_numatb:
                just_export_meshes = set()
                for unprocessed_meshes_to_export_meshes in group_name_to_unprocessed_meshes_to_export_meshes.values():
                    for export_meshes in unprocessed_meshes_to_export_meshes.values():
                        for export_mesh in export_meshes:
                            just_export_meshes.add(export_mesh)
                
                ssbh_matl_data = create_matl(operator, just_export_meshes)
                if ssbh_matl_data is not None:
                    trim_matl_texture_names(operator, ssbh_matl_data)
                if ssbh_modl_data is not None and ssbh_matl_data is not None:
                    trim_material_labels(operator, ssbh_modl_data, ssbh_matl_data)
                if include_nutexb:
                    try:
                        materials = get_mesh_materials(operator, just_export_meshes)
                        from .texture.export_nutexb import export_nutexb_from_blender_materials
                        export_nutexb_from_blender_materials(operator, materials, folder)
                    except Exception as e:
                        operator.report({'ERROR'}, f'Texture exporting stopped early, error = {e} ; Traceback=\n{traceback.format_exc()}')
            if include_numshexb:
                if ssbh_mesh_data is not None:
                    try:
                        create_and_save_meshex(operator, folder, ssbh_mesh_data)
                    except Exception as e:
                        operator.report({'ERROR'}, f'Failed to make mesh ex data (.NUMSHEXB), but will try to make the rest. Error="{e}" ; Traceback=\n{traceback.format_exc()}')
        finally:
            for group_name, unprocessed_meshes_to_export_meshes in group_name_to_unprocessed_meshes_to_export_meshes.items():
                for unprocessed_mesh, export_meshes in unprocessed_meshes_to_export_meshes.items():
                    for export_mesh in export_meshes:
                        bpy.data.meshes.remove(export_mesh.data)
            for new_shape_key_mesh in new_shape_key_meshes:
                bpy.data.meshes.remove(new_shape_key_mesh.data)

    if include_nusktb:
        ssbh_skel_data, prc = create_skel_and_prc(operator, context, linked_nusktb_settings, folder)

    if include_numshb and include_nusktb:
        if ssbh_mesh_data is not None and ssbh_skel_data is not None:
            if optimize_mesh_weights == 'ENABLED':
                weights_to_parent_bones(ssbh_mesh_data, ssbh_skel_data)

    if include_numshb:
        if ssbh_mesh_data is not None:
            path = str(folder.joinpath('model.numshb'))
            try:
                ssbh_mesh_data.save(path)
            except Exception as e:
                operator.report({'ERROR'}, f'Failed to save {path}: {e}')

    if include_nusktb:
        if ssbh_skel_data is not None:
            path = str(folder.joinpath('model.nusktb'))
            try:
                ssbh_skel_data.save(path)
            except Exception as e:
                operator.report({'ERROR'}, f'Failed to save .nusktb, Error="{e}" ; Traceback=\n{traceback.format_exc()}')
        prc_path = str(folder.joinpath('update.prc'))
        if prc is not None:
            try:
                prc.save(prc_path)
            except Exception as e:
                operator.report({'ERROR'}, f'Failed to save update.prc, Error="{e}" ; Traceback=\n{traceback.format_exc()}')

    if include_nuhlpb:
        try:
            create_and_save_nuhlpb(folder.joinpath('model.nuhlpb'), arma)
        except Exception as e:
            operator.report({'ERROR'}, f'Failed to create .nuhlpb, Error="{e}" ; Traceback=\n{traceback.format_exc()}')

    if include_numdlb:
        if ssbh_modl_data is not None:
            path = str(folder.joinpath('model.numdlb'))
            try:
                ssbh_modl_data.save(path)
            except Exception as e:
                operator.report({'ERROR'}, f'Failed to save {path}: {e}')

    if include_numatb:
        if ssbh_matl_data is not None:
            path = str(folder.joinpath('model.numatb'))
            try:
                ssbh_matl_data.save(path)
            except Exception as e:
                operator.report({'ERROR'}, f'Failed to save .numatb, Error="{e}" ; Traceback=\n{traceback.format_exc()}')
    
    # Create adjb, if needed
    if include_numdlb and include_numshb and include_numatb:
        if all(data is not None for data in (ssbh_matl_data, ssbh_modl_data, ssbh_mesh_data)):
            renormal_meshes: list[tuple[str, int]] = [(entry.mesh_object_name, entry.mesh_object_subindex) for entry in ssbh_modl_data.entries if entry.material_label.startswith("RENORMAL")]
            if len(renormal_meshes) > 0:
                ssbh_adj_data = ssbh_data_py.adj_data.AdjData()
                for mesh_object_index, mesh_object in enumerate(ssbh_mesh_data.objects):
                    if (mesh_object.name, mesh_object.subindex) in renormal_meshes:
                        ssbh_adj_data.entries.append(ssbh_data_py.adj_data.AdjEntryData.from_mesh_object(mesh_object_index, mesh_object))
                path = str(folder.joinpath('model.adjb'))
                try:
                    ssbh_adj_data.save(path)
                except Exception as e:
                    operator.report({'ERROR'}, f'Failed to save .adjb, Error="{e}" ; Traceback=\n{traceback.format_exc()}')
                    
    if arma.animation_data is not None:
        from .import_anim import setup_visibility_drivers
        setup_visibility_drivers(arma)

    arma.data.pose_position = old_pose_position

def create_skel_and_prc(operator, context, linked_nusktb_settings, folder) -> tuple[ssbh_data_py.skel_data.SkelData, Any]:
    try:
        ssbh_skel_data, prc = make_skel(operator, context, linked_nusktb_settings)
    except RuntimeError as e:
        operator.report({'ERROR'},  f'Failed to make skel for export, Error="{e}" ; Traceback=\n{traceback.format_exc()}')
        return

    # The uniform buffer for bone transformations in the skinning shader has a fixed size.
    # Limit exports to 511 bones to prevent rendering issues and crashes in game.
    if len(ssbh_skel_data.bones) > 511:
        operator.report({'ERROR'}, f'{len(ssbh_skel_data.bones)} bones exceeds the maximum supported count of 511.')
        return

    """path = str(folder.joinpath('model.nusktb'))
    try:
        ssbh_skel_data.save(path)
    except Exception as e:
        operator.report({'ERROR'}, f'Failed to save .nusktb, Error="{e}" ; Traceback=\n{traceback.format_exc()}')

    prc_path = str(folder.joinpath('update.prc'))
    if prc:
        try:
            prc.save(prc_path)
        except Exception as e:
            operator.report({'ERROR'}, f'Failed to save update.prc, Error="{e}" ; Traceback=\n{traceback.format_exc()}')"""
    
    return (ssbh_skel_data, prc)


def create_and_save_meshex(operator, folder, ssbh_mesh_data):
    meshex = ssbh_data_py.meshex_data.MeshExData.from_mesh_objects(ssbh_mesh_data.objects)

    path = str(folder.joinpath('model.numshexb'))
    try:
        meshex.save(path)
    except Exception as e:
        operator.report({'ERROR'}, f'Failed to save {path}: {e}')


def get_mesh_materials(operator, export_meshes) -> set[bpy.types.Material]:
    #  Gather Material Info
    materials = set()
    for mesh in export_meshes:
        if len(mesh.data.materials) > 0:
            if mesh.data.materials[0] is not None:
                if len(mesh.data.materials) > 1:
                    message = f'The mesh {mesh.name} has more than one material slot. Only the first material will be exported.'
                    operator.report({'WARNING'}, message)

                materials.add(mesh.data.materials[0])
            else:
                message = f'The mesh {mesh.name} has no material created for the first material slot.' 
                message += ' Cannot create model.numatb. Create a material or disable .NUMATB export.'
                raise RuntimeError(message)

    return materials


def create_matl(operator, export_meshes) -> ssbh_data_py.matl_data.MatlData | None:
    from .material.create_matl_from_blender_materials import create_matl_from_blender_materials
    try:
        materials = get_mesh_materials(operator, export_meshes)
        ssbh_matl = create_matl_from_blender_materials(operator, materials)
    except RuntimeError as e:
        operator.report({'ERROR'}, f'Failed to prepare .numatb, Error="{e}" ; Traceback=\n{traceback.format_exc()}')
        return None
    else:
        return ssbh_matl

def create_and_save_matl(operator, folder, export_meshes):
    try:
        materials = get_mesh_materials(operator, export_meshes)
        #ssbh_matl = make_matl(operator, materials)
        from .material.create_matl_from_blender_materials import create_matl_from_blender_materials
        ssbh_matl = create_matl_from_blender_materials(operator, materials)
    except RuntimeError as e:
        operator.report({'ERROR'}, f'Failed to prepare .numatb, Error="{e}" ; Traceback=\n{traceback.format_exc()}')
        return

    path = str(folder.joinpath('model.numatb'))
    try:
        ssbh_matl.save(path)
    except Exception as e:
        operator.report({'ERROR'}, f'Failed to save .numatb, Error="{e}" ; Traceback=\n{traceback.format_exc()}')


def get_material_label_from_mesh(operator, mesh):
    if len(mesh.material_slots) == 0:
        message = f'No material assigned for {mesh.name}. Cannot create model.numdlb. Assign a material or disable .NUMDLB export.'
        raise RuntimeError(message)

    material = mesh.material_slots[0].material

    if material is None:
        message = f'The mesh {mesh.name} has no material created for the first material slot.' 
        message += ' Cannot create model.numdlb. Create a material or disable .NUMDLB export.'
        raise RuntimeError(message)

    """mat_label = None
    try:
        ultimate_node = find_ultimate_node(material)
        mat_label = ultimate_node.inputs['Material Name'].default_value
    except:
        # Use the Blender material name as a fallback.
        mat_label = material.name
        message = f'Missing Smash Ultimate node group for the mesh {mesh.name}. Assigning {mat_label} by material name.'
        operator.report({'WARNING'}, message)"""

    return material.name


def find_bone_index(bones, name):
    for i, bone in enumerate(bones):
        if bone.name == name:
            return i

    return None


def default_ssbh_material(material_label:str) -> ssbh_data_py.matl_data.MatlEntryData:
    # Mario's phong0_sfx_0x9a011063_____VTC___TANGENT___BINORMAL_101 material.
    # This is a good default for fighters since the user can just assign textures in another application.
    entry = ssbh_data_py.matl_data.MatlEntryData(material_label, 'SFX_PBS_0100000008008269_opaque')
    entry.blend_states = [ssbh_data_py.matl_data.BlendStateParam(
        ssbh_data_py.matl_data.ParamId.BlendState0,
        ssbh_data_py.matl_data.BlendStateData()
    )]
    entry.floats = [ssbh_data_py.matl_data.FloatParam(ssbh_data_py.matl_data.ParamId.CustomFloat0, 0.8)]
    entry.booleans = [
        ssbh_data_py.matl_data.BooleanParam(ssbh_data_py.matl_data.ParamId.CustomBoolean1, True),
        ssbh_data_py.matl_data.BooleanParam(ssbh_data_py.matl_data.ParamId.CustomBoolean3, True),
        ssbh_data_py.matl_data.BooleanParam(ssbh_data_py.matl_data.ParamId.CustomBoolean4, True),
    ]
    entry.vectors = [
        ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.CustomVector0, [1.0, 0.0, 0.0, 0.0]),
        ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.CustomVector13, [1.0, 1.0, 1.0, 1.0]),
        ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.CustomVector14, [1.0, 1.0, 1.0, 1.0]),
        ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.CustomVector8, [1.0, 1.0, 1.0, 1.0]),
    ]
    entry.rasterizer_states = [ssbh_data_py.matl_data.RasterizerStateParam(
        ssbh_data_py.matl_data.ParamId.RasterizerState0,
        ssbh_data_py.matl_data.RasterizerStateData()
    )]
    entry.samplers = [
        ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.Sampler0, ssbh_data_py.matl_data.SamplerData()),
        ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.Sampler4, ssbh_data_py.matl_data.SamplerData()),
        ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.Sampler6, ssbh_data_py.matl_data.SamplerData()),
        ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.Sampler7, ssbh_data_py.matl_data.SamplerData()),
    ]
    # Use magenta for the albedo/base color to avoid confusion with existing error colors like white, yellow, or red.
    # Magenta is commonly used to indicate missing/invalid textures in applications and game engines.
    entry.textures = [
        ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.Texture0, '/common/shader/sfxpbs/default_params_r100_g025_b100'),
        ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.Texture4, '/common/shader/sfxpbs/fighter/default_normal'),
        ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.Texture6, '/common/shader/sfxpbs/fighter/default_params'),
        ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.Texture7, '#replace_cubemap'),
    ]
    return entry


def default_texture(param_name):
    # Select defaults that have as close to no effect as possible.
    # This is white (1,1,1) for multiplication and black (0,0,0) for addition.
    defaults = {
        'Texture0': '/common/shader/sfxpbs/default_white',
        'Texture1': '/common/shader/sfxpbs/default_white',
        'Texture2': '#replace_cubemap',
        'Texture3': '/common/shader/sfxpbs/default_white',
        'Texture4': '/common/shader/sfxpbs/fighter/default_normal',
        'Texture5': '/common/shader/sfxpbs/default_black',
        'Texture6': '/common/shader/sfxpbs/fighter/default_params',
        'Texture7': '#replace_cubemap',
        'Texture8': '#replace_cubemap',
        'Texture9': '/common/shader/sfxpbs/default_black',
        'Texture10': '/common/shader/sfxpbs/default_white',
        'Texture11': '/common/shader/sfxpbs/default_white',
        'Texture12': '/common/shader/sfxpbs/default_white',
        'Texture13': '/common/shader/sfxpbs/default_white',
        'Texture14': '/common/shader/sfxpbs/default_black',
        'Texture15': '/common/shader/sfxpbs/default_white',
        'Texture16': '/common/shader/sfxpbs/default_white',
        'Texture17': '/common/shader/sfxpbs/default_white',
        'Texture18': '/common/shader/sfxpbs/default_white',
        'Texture19': '/common/shader/sfxpbs/default_white',
    }

    if param_name in defaults:
        return defaults[param_name]
    else:
        return '/common/shader/sfxpbs/default_white'


def find_output_node(material):
    try:
        for node in material.node_tree.nodes:
            if node.bl_idname == 'ShaderNodeOutputMaterial':
                return node

        return None
    except:
        return None


def find_ultimate_node(material):
    output_node = find_output_node(material)
    if output_node is None:
        return None

    # We can't differentiate the ultimate node group from other node groups.
    # Just assume all node groups are correct and handle errors on export.
    node = output_node.inputs['Surface'].links[0].from_node
    if node is not None and node.bl_idname == 'ShaderNodeGroup':
        return node
    else:
        return None


def find_principled_node(material):
    output_node = find_output_node(material)
    if output_node is None:
        return None

    # We can't differentiate the ultimate node group from other node groups.
    # Just assume all node groups are correct and handle errors on export.
    node = output_node.inputs['Surface'].links[0].from_node
    if node is not None and node.bl_idname == 'ShaderNodeBsdfPrincipled':
        return node
    else:
        return None


"""def make_matl(operator, materials):
    matl = ssbh_data_py.matl_data.MatlData()

    for material in materials:
        try:
            ultimate_node = find_ultimate_node(material)
            entry = create_material_entry_from_node_group(operator, ultimate_node)
        except:
            # Materials are often edited in external applications.
            # Use a default for missing node groups to allow exporting to proceed.    
            entry = default_ssbh_material(material.name)
            principled_node = find_principled_node(material)
            if principled_node is not None:
                operator.report({'WARNING'}, f'Missing Smash Ultimate node group for {material.name}. Creating material from Principled BSDF.')
                texture, sampler = create_texture_sampler(operator, principled_node.inputs['Base Color'], material.name, 'Texture0')
                entry.textures[0] = texture
                entry.samplers[0] = sampler
            else:
                operator.report({'WARNING'}, f'Missing Smash Ultimate node group for {material.name}. Creating default material.')
        

        matl.entries.append(entry)

    return matl"""

"""
def create_material_entry_from_node_group(operator, node: bpy.types.Node):
    material_label = node.inputs['Material Name'].default_value
    entry = ssbh_data_py.matl_data.MatlEntryData(material_label, node.inputs['Shader Label'].default_value)

    # The ultimate node group has inputs for each material parameter.
    # Hidden inputs aren't used by the in game shader and should be skipped.
    inputs: list[bpy.types.NodeSocket] = [input for input in node.inputs if input.hide == False]

    # Multiple inputs may correspond to a single parameter.
    # Avoid exporting the same parameter more than once.
    exported_params = set()

    for input in inputs:
        name = input.name
        param_name = name.split(' ')[0]

        if param_name in exported_params:
            continue

        elif name == 'BlendState0 Field1 (Source Color)':
            attribute = create_blend_state(node)
            entry.blend_states.append(attribute)
        elif name == 'RasterizerState0 Field1 (Polygon Fill)':
            attribute = create_rasterizer_state(node)
            entry.rasterizer_states.append(attribute)
        elif 'Texture' in param_name and 'RGB' in name.split(' ')[1]:
            # Samplers are connected to their corresponding texture nodes instead of the ultimate node group.
            texture_attribute, sampler_attribute = create_texture_sampler(operator, input, material_label, param_name)
            entry.textures.append(texture_attribute)
            entry.samplers.append(sampler_attribute)
        elif 'Boolean' in param_name:
            attribute = ssbh_data_py.matl_data.BooleanParam(ssbh_data_py.matl_data.ParamId.from_str(param_name), input.default_value)
            entry.booleans.append(attribute)
        elif 'Float' in param_name:
            attribute = ssbh_data_py.matl_data.FloatParam(ssbh_data_py.matl_data.ParamId.from_str(param_name), input.default_value)
            entry.floats.append(attribute)
        elif 'Vector' in param_name:
            if param_name in material_inputs.vec4_param_to_inputs:
                attribute = ssbh_data_py.matl_data.Vector4Param(ssbh_data_py.matl_data.ParamId.from_str(param_name), [0.0, 0.0, 0.0, 0.0])        

                inputs = [node.inputs.get(name) for _, name, _ in material_inputs.vec4_param_to_inputs[param_name]]
                    
                # Assume inputs are RGBA, RGB/A, or X/Y/Z/W.
                if len(inputs) == 1:
                    attribute.data = list(inputs[0].default_value)
                elif len(inputs) == 2:
                    # Discard the 4th RGB component and use the explicit alpha instead.
                    attribute.data[:3] = list(inputs[0].default_value)[:3]
                    attribute.data[3] = inputs[1].default_value
                elif len(inputs) == 4:
                    attribute.data[0] = inputs[0].default_value
                    attribute.data[1] = inputs[1].default_value
                    attribute.data[2] = inputs[2].default_value
                    attribute.data[3] = inputs[3].default_value

                entry.vectors.append(attribute)
        else:
            continue

        exported_params.add(param_name)
    return entry

"""

def create_blend_state(node):
    data = ssbh_data_py.matl_data.BlendStateData()

    try:
        data.source_color = ssbh_data_py.matl_data.BlendFactor.from_str(node.inputs['BlendState0 Field1 (Source Color)'].default_value)
        data.destination_color = ssbh_data_py.matl_data.BlendFactor.from_str(node.inputs['BlendState0 Field3 (Destination Color)'].default_value)
        data.alpha_sample_to_coverage = node.inputs['BlendState0 Field7 (Alpha to Coverage)'].default_value
    except:
        # TODO: Report errors?
        data = ssbh_data_py.matl_data.BlendStateData()

    attribute = ssbh_data_py.matl_data.BlendStateParam(ssbh_data_py.matl_data.ParamId.BlendState0, data)
    return attribute


def create_rasterizer_state(node):
    data = ssbh_data_py.matl_data.RasterizerStateData()

    try:
        data.fill_mode = ssbh_data_py.matl_data.FillMode.from_str(node.inputs['RasterizerState0 Field1 (Polygon Fill)'].default_value)
        data.cull_mode = ssbh_data_py.matl_data.CullMode.from_str(node.inputs['RasterizerState0 Field2 (Cull Mode)'].default_value)
        data.depth_bias = node.inputs['RasterizerState0 Field3 (Depth Bias)'].default_value
    except:
        # TODO: Report errors?
        data = ssbh_data_py.matl_data.RasterizerStateData()

    attribute = ssbh_data_py.matl_data.RasterizerStateParam(ssbh_data_py.matl_data.ParamId.RasterizerState0, data)
    return attribute


def create_texture_sampler(operator, input, material_label, param_name):
    # Texture Data
    try:
        texture_node = input.links[0].from_node
        texture_name = texture_node.label
    except:
        operator.report({'WARNING'}, f'Missing texture {param_name} for material {material_label}. Applying defaults.')
        texture_name = default_texture(param_name)

    texture_attribute = ssbh_data_py.matl_data.TextureParam(ssbh_data_py.matl_data.ParamId.from_str(param_name), texture_name)

    # Sampler Data
    sampler_number = param_name.split('Texture')[1]
    sampler_param_id_text = f'Sampler{sampler_number}'

    sampler_data = ssbh_data_py.matl_data.SamplerData()

    try:
        sampler_node = texture_node.inputs[0].links[0].from_node
        # TODO: These conversions may return None on error.
        sampler_data.wraps = ssbh_data_py.matl_data.WrapMode.from_str(sampler_node.wrap_s)
        sampler_data.wrapt = ssbh_data_py.matl_data.WrapMode.from_str(sampler_node.wrap_t)
        sampler_data.wrapr = ssbh_data_py.matl_data.WrapMode.from_str(sampler_node.wrap_r)
        sampler_data.min_filter = ssbh_data_py.matl_data.MinFilter.from_str(sampler_node.min_filter)
        sampler_data.mag_filter = ssbh_data_py.matl_data.MagFilter.from_str(sampler_node.mag_filter)
        sampler_data.border_color = list(sampler_node.border_color)
        sampler_data.lod_bias = sampler_node.lod_bias
        sampler_data.max_anisotropy = ssbh_data_py.matl_data.MaxAnisotropy.from_str(sampler_node.max_anisotropy) if sampler_node.anisotropic_filtering else None
    except:
        operator.report({'WARNING'}, f'Missing sampler {sampler_param_id_text} for material {material_label}. Applying defaults.')
        sampler_data = ssbh_data_py.matl_data.SamplerData()

    sampler_attribute = ssbh_data_py.matl_data.SamplerParam(ssbh_data_py.matl_data.ParamId.from_str(sampler_param_id_text), sampler_data)

    return texture_attribute, sampler_attribute


def per_loop_to_per_vertex(per_loop, vertex_indices, dim):
    # Consider the following per loop data.
    # index, value
    # 0, 1
    # 1, 3
    # 0, 1
    
    # This generates the following per vertex data.
    # vertex, value
    # 0, 1
    # 1, 3

    # Convert from 1D per loop to 2D per vertex using numpy indexing magic.
    _, cols = dim
    per_vertex = np.zeros(dim, dtype=np.float32)
    per_vertex[vertex_indices] = per_loop.reshape((-1, cols))
    return per_vertex

def split_mesh_shape_keys_to_new_meshes(operator: Operator, context: Context, mesh_object: Object) -> set[Object]:
    if mesh_object.data.shape_keys is None:
        return set()
    if mesh_object.data.shape_keys.key_blocks is None:
        return set()
    shape_keys_to_split: set[ShapeKey] = {sk for sk in mesh_object.data.shape_keys.key_blocks if "_VIS" in sk.name}
    if len(shape_keys_to_split) == 0:
        return set()
    
    new_meshes: set[Object] = set()
    for shape_key_to_split in shape_keys_to_split:
        shape_key_mesh_copy: Object = mesh_object.copy()
        shape_key_mesh_copy.data: Mesh = mesh_object.data.copy()
        shape_key_mesh_copy.name = shape_key_to_split.name
        shape_key_mesh_copy.show_only_shape_key = True
        shape_key_mesh_copy.active_shape_key_index = shape_key_mesh_copy.data.shape_keys.key_blocks.find(shape_key_to_split.name)
        shape_key_mesh_copy.shape_key_add(name="_smush_blender_combined_key", from_mix=True)
        for sk in shape_key_mesh_copy.data.shape_keys.key_blocks:
            shape_key_mesh_copy.shape_key_remove(sk)
        context.collection.objects.link(shape_key_mesh_copy)
        
        new_meshes.add(shape_key_mesh_copy)
    print(f'{new_meshes=}')
    return new_meshes

def process_mesh(operator: Operator, context: Context, mesh_object_copy: Object, mesh_name_in_errors: str,
                apply_modifiers: str, armature_position: str) -> set[Object]:
    """
    Always returns at least one mesh, but since processing a mesh may split it by material, more than one mesh could be returned. 
    """

    # Apply any transforms before exporting to preserve vertex positions.
    # Assume the meshes have no children that would inherit their transforms.
    mesh_object_copy.data.transform(mesh_object_copy.matrix_basis)
    mesh_object_copy.matrix_basis.identity()

    # Remove shapekeys 
    mesh_object_copy.shape_key_clear()
    
    # Apply Modifiers
    if apply_modifiers == 'APPLY':
        override = context.copy()
        override['object'] = mesh_object_copy
        override['active_object'] = mesh_object_copy
        override['selected_objects'] = [mesh_object_copy]
        with context.temp_override(**override):
            for modifier in mesh_object_copy.modifiers:
                if armature_position == 'REST': # Optimization to speed up export when the user doesn't want to export armature changes anyways
                    if modifier.type != 'ARMATURE':
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                else:
                    bpy.ops.object.modifier_apply(modifier=modifier.name)

    # Cleanup and dissolve degen
    # https://blender.stackexchange.com/questions/139615/bmesh-ops-method-to-get-loose-vertices-edges-and-delete-from-that-list
    # https://blender.stackexchange.com/questions/206751/set-the-context-to-run-dissolve-degenerate-from-the-python-shell
    bm = bmesh.new()
    bm.from_mesh(mesh_object_copy.data)
    bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges)
    unlinked_verts = [v for v in bm.verts if len(v.link_faces) == 0]
    bmesh.ops.delete(bm, geom=unlinked_verts, context='VERTS')
    bm.to_mesh(mesh_object_copy.data)
    mesh_object_copy.data.update()
    bm.clear()
    
    # Get the custom normals from the original mesh.
    # We use the copy here since applying transforms alters the normals.
    mesh_object_copy.data.calc_normals_split()
    loop_normals = np.zeros(len(mesh_object_copy.data.loops) * 3, dtype=np.float32)
    mesh_object_copy.data.loops.foreach_get('normal', loop_normals)

    # Pad to 4 components for fitting in the color attribute.
    loop_normals = loop_normals.reshape((-1, 3))
    loop_normals = np.append(loop_normals, np.zeros((loop_normals.shape[0],1)), axis=1)
    loop_normals = loop_normals.flatten()

    # Transfer the original normals to a custom attribute.
    # This allows us to edit the mesh without affecting custom normals.
    # Use FLOAT_COLOR since FLOAT_VECTOR doesn't add a key for some reason.
    # TODO: Is it ok to always assume FLOAT_COLOR will allow signed values?
    normals_color = mesh_object_copy.data.color_attributes.new(name='_smush_blender_custom_normals', type='FLOAT_COLOR', domain='CORNER')
    normals_color.data.foreach_set('color', loop_normals)

    # Check if any of the faces are not tris, and converts them into tris
    if any(len(f.vertices) != 3 for f in mesh_object_copy.data.polygons):
        operator.report({'WARNING'}, f'Mesh {mesh_name_in_errors} has non triangular faces. Triangulating a temporary mesh for export.')

        # https://blender.stackexchange.com/questions/45698
        me = mesh_object_copy.data
        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)

        bmesh.ops.triangulate(bm, faces=bm.faces[:])

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        bm.free()

    # Blender stores normals and UVs per loop rather than per vertex.
    # Edges with more than one value per vertex need to be split.
    split_duplicate_loop_attributes(mesh_object_copy)
    # Rarely this will create some loose verts
    bm = bmesh.new()
    bm.from_mesh(mesh_object_copy.data)
    unlinked_verts = [v for v in bm.verts if len(v.link_faces) == 0]
    bmesh.ops.delete(bm, geom=unlinked_verts, context='VERTS')
    bm.to_mesh(mesh_object_copy.data)
    mesh_object_copy.data.update()
    bm.clear()

    # Split mesh by material
    bm = bmesh.new()
    bm.from_mesh(mesh_object_copy.data)
    material_indices: set[int] = {f.material_index for f in bm.faces}
    #bm.to_mesh(mesh_object_copy.data)
    #mesh_object_copy.data.update()
    bm.clear()
    split_meshes: set[Object] = set()
    for material_index in material_indices:
        dest_obj: bpy.types.Object = mesh_object_copy.copy()
        dest_obj.data: bpy.types.Mesh = mesh_object_copy.data.copy()
        dest_bm = bmesh.new()
        dest_bm.from_mesh(dest_obj.data)
        dest_faces_to_split = [f for f in dest_bm.faces if f.material_index != material_index]
        if len(dest_faces_to_split) > 0:
            bmesh.ops.delete(dest_bm, geom=dest_faces_to_split, context='FACES')
            dest_bm.to_mesh(dest_obj.data)
        dest_bm.clear()
        dest_obj.data.update()
        mat = dest_obj.material_slots[material_index].material
        dest_obj.data.materials.clear()
        dest_obj.data.materials.append(mat)
        split_meshes.add(dest_obj)
    
    for split_mesh in split_meshes:
        # Extract the custom normals preserved in the color attribute.
        # Color attributes should not be affected by splitting or triangulating.
        # This avoids the datatransfer modifier not handling vertices at the same position.
        loop_normals = np.zeros(len(split_mesh.data.loops) * 4, dtype=np.float32)
        normals_color = split_mesh.data.color_attributes['_smush_blender_custom_normals']
        normals_color.data.foreach_get('color', loop_normals)

        # Remove the dummy fourth component.
        loop_normals = loop_normals.reshape((-1, 4))[:,:3]

        # Assign the preserved custom normals to the temp mesh.
        split_mesh.data.normals_split_custom_set(loop_normals)
        split_mesh.data.use_auto_smooth = True
        split_mesh.data.calc_normals_split()
        split_mesh.data.update()

    return split_meshes

def get_processed_meshes(operator: bpy.types.Operator, context: bpy.types.Context,
                    group_name_to_unprocessed_meshes: dict[str, set[bpy.types.Object]],
                    apply_modifiers: str, split_shape_keys: str, armature_position: str) -> tuple[dict[str, dict[Object, set[Object]]], set[object]]:
    '''
    Splitting by shape key and by material may add more meshes to export, so need to track the new meshes.
    In addition the new shapekeys could be named completely differently
    Example:
    group_name_to_export_meshes_to_temp_meshes: dict[str, dict[Mesh, set[Mesh]]]
    |-> Cube             "Group Name"       # This is the trimmed name that will show up in the numshb
        |-> Cube.001     "Unprocessed Mesh" # This is the mesh in blender un-modified with its un-trimmed name and shape keys that the user wants to export.
            |-> Cube.003 "Export Mesh"      # Every blender mesh will make at least one temporary "Export Mesh". This is the mesh that has been modified and cleaned up.
            |-> Cube.004 "Export Mesh"      # Maybe this one has two export meshes because it had more than one material
            |-> Cube.005 "Export Mesh"      # Or maybe it had shape keys
        |-> Cube.002     "Unprocessed Mesh" # For proper error reporting, unprocessed meshes need to be tracked as well
            |-> Cube.006 "Export Mesh"      # Since saying "Cube.006 Failed" would not be helpful when "Cube.006" is not a mesh the user made
        |-> Cube.003
            |-> Cube.007 "Export Mesh"
    |-> Sphere           "Group Name"
        |-> ....
    |-> C_VIS            "Group Name"        # New group name for new shape key mesh name
        |-> C_VIS        "Unprocessed Mesh"  # This is the shape key mesh, split off from its original mesh, but it still has modifiers
            |-> C_VIS.001"Export Mesh"       # This is the shape key mesh after processing, applied modifiers, split materials, etc.
            |-> C_VIS.002"Export Mesh"
    '''
    # Meshes with shape keys will make more "groups" with more "unprocessed meshes"
    new_shape_key_meshes: set[Object] = set()
    # If a mesh was succesfully split into multiple shapekey
    meshes_that_split_into_shapekeys: set[Object] = set()
    if split_shape_keys in ('EXPORT_INCLUDE_ORIGINAL', 'EXPORT_EXCULDE_ORIGINAL'):
        for group_name, unprocessed_meshes in group_name_to_unprocessed_meshes.items():
            for unprocessed_mesh in unprocessed_meshes:
                meshes = split_mesh_shape_keys_to_new_meshes(operator, context, unprocessed_mesh)
                if len(meshes) > 0:
                    new_shape_key_meshes |= meshes
                    meshes_that_split_into_shapekeys.add(unprocessed_mesh)
    
        # Remove the split shapekey meshes if needed
        if split_shape_keys == 'EXPORT_EXCULDE_ORIGINAL':
            group_names = group_name_to_unprocessed_meshes.keys()
            for group_name in group_names:
                unprocessed_meshes = group_name_to_unprocessed_meshes[group_name]
                group_name_to_unprocessed_meshes[group_name] = unprocessed_meshes - meshes_that_split_into_shapekeys
    
        group_names = group_name_to_unprocessed_meshes.keys()
        new_group_names = {trim_name(new_shape_key_mesh.name) for new_shape_key_mesh in new_shape_key_meshes}
        for missing_name in new_group_names - group_names:
            group_name_to_unprocessed_meshes[missing_name] = set()
        
        for new_shape_key_mesh in new_shape_key_meshes:
            group_name = trim_name(new_shape_key_mesh.name)
            group_name_to_unprocessed_meshes[group_name].add(new_shape_key_mesh)
    

    # Return Dictionary initialization
    group_name_to_unprocessed_meshes_to_export_meshes: dict[str, dict[Object, set[Object]]] = {}
    for group_name, unprocessed_meshes in group_name_to_unprocessed_meshes.items():
        group_name_to_unprocessed_meshes_to_export_meshes[group_name] = {}
        for unprocessed_mesh in unprocessed_meshes:
            group_name_to_unprocessed_meshes_to_export_meshes[group_name][unprocessed_mesh] = set() 

    # Process meshes
    for group_name, unprocessed_meshes in group_name_to_unprocessed_meshes.items():
        for unprocessed_mesh in unprocessed_meshes:
            # Make a copy of the mesh so that the original remains unmodified.
            # The copy is out here so that is deleted regardless of error
            unprocessed_mesh_copy: bpy.types.Object = unprocessed_mesh.copy()
            unprocessed_mesh_copy.data: bpy.types.Mesh = unprocessed_mesh.data.copy()
            # This is needed for split_duplicate_loop_attributes()
            context.collection.objects.link(unprocessed_mesh_copy)
            try:
                group_name_to_unprocessed_meshes_to_export_meshes[group_name][unprocessed_mesh] |= process_mesh(operator, context, unprocessed_mesh_copy, unprocessed_mesh.name, apply_modifiers, armature_position)
            finally:
                bpy.data.meshes.remove(unprocessed_mesh_copy.data)


    return group_name_to_unprocessed_meshes_to_export_meshes, new_shape_key_meshes
    
def make_ssbh_mesh_data(operator: Operator, context: Context, group_name_to_unprocessed_meshes_to_export_meshes: dict[str, dict[Object, set[Object]]]) -> ssbh_data_py.mesh_data.MeshData:
    ssbh_mesh_data = ssbh_data_py.mesh_data.MeshData()
    for group_name, unprocessed_meshes_to_export_meshes in group_name_to_unprocessed_meshes_to_export_meshes.items():
        subindex = 0
        for unprocessed_mesh, export_meshes in unprocessed_meshes_to_export_meshes.items():
            for export_mesh in export_meshes:
                ssbh_mesh_object = make_mesh_object(operator, context, export_mesh, group_name, subindex, unprocessed_mesh.name)
                ssbh_mesh_data.objects.append(ssbh_mesh_object)
                subindex += 1
    return ssbh_mesh_data

def make_mesh_object(operator, context, mesh: bpy.types.Object, group_name, i, mesh_name):
    # ssbh_data_py accepts lists, tuples, or numpy arrays for AttributeData.data.
    # foreach_get and foreach_set provide substantially faster access to property collections in Blender.
    # https://devtalk.blender.org/t/alternative-in-2-80-to-create-meshes-from-python-using-the-tessfaces-api/7445/3
    mesh_data: bpy.types.Mesh = mesh.data
    ssbh_mesh_object = ssbh_data_py.mesh_data.MeshObjectData(group_name, i)
    position0 = ssbh_data_py.mesh_data.AttributeData('Position0')

    # TODO: Is there a better way to account for the change of coordinates?
    axis_correction = np.array(Matrix.Rotation(math.radians(90), 3, 'X'))

    # For example, vertices is a bpy_prop_collection of MeshVertex, which has a "co" attribute for position.
    positions = np.zeros(len(mesh_data.vertices) * 3, dtype=np.float32)
    mesh_data.vertices.foreach_get('co', positions)
    # The output data is flattened, so we need to reshape it into the appropriate number of rows and columns.
    position0.data = positions.reshape((-1, 3)) @ axis_correction
    ssbh_mesh_object.positions = [position0]

    # Store vertex indices as a numpy array for faster indexing later.
    vertex_indices = np.zeros(len(mesh_data.loops), dtype=np.uint32)
    mesh_data.loops.foreach_get('vertex_index', vertex_indices)
    ssbh_mesh_object.vertex_indices = vertex_indices

    # Export Normals
    normal0 = ssbh_data_py.mesh_data.AttributeData('Normal0')
    loop_normals = np.zeros(len(mesh_data.loops) * 3, dtype=np.float32)
    mesh_data.loops.foreach_get('normal', loop_normals)
    normals = per_loop_to_per_vertex(loop_normals, vertex_indices, (len(mesh_data.vertices), 3))
    normals = normals @ axis_correction

    # Pad normals to 4 components instead of 3 components.
    # This actually results in smaller file sizes since HalFloat4 is smaller than Float3.
    normals = np.append(normals, np.zeros((normals.shape[0],1)), axis=1)
            
    normal0.data = normals
    ssbh_mesh_object.normals = [normal0]

    # Export Weights
    # TODO: Reversing a vertex -> group lookup to a group -> vertex lookup is expensive.
    # TODO: Does Blender not expose this directly?
    group_to_weights = { vg.index : (vg.name, []) for vg in mesh.vertex_groups }
    has_unweighted_vertices = False
    # TODO: Skip this for performance reasons if there are no vertex groups?
    '''
    Vertex groups can either be 'Deform' groups used for actual mesh deformation, or 'Other'
    Only want the 'Deform' groups exported.
    '''
    ssp: SubSceneProperties = context.scene.sub_scene_properties
    arma = ssp.model_export_arma
    deform_vertex_group_indices = {vg.index for vg in mesh.vertex_groups if vg.name in arma.data.bones}
    for vertex in mesh_data.vertices:
        vertex: MeshVertex 
        deform_groups = [g for g in vertex.groups if g.group in deform_vertex_group_indices]
        if len(deform_groups) > 4:
            # We won't fix this automatically since removing influences may break animations.
            message = f'Vertex with more than 4 weights detected for mesh {mesh_name}.'
            message += ' Select all in Edit Mode and click Mesh > Weights > Limit Total with the limit set to 4.'
            message += ' Weights may need to be reassigned after limiting totals.'
            raise RuntimeError(message)

        # Only report this warning once.
        if len(deform_groups) == 0 or all([g.weight == 0.0 for g in deform_groups]):
            has_unweighted_vertices = True

        # Blender doesn't enforce normalization, since it normalizes while animating.
        # Normalize on export to ensure the weights work correctly in game.
        weight_sum = sum([g.weight for g in deform_groups])
        for group in deform_groups:
            # Remove unused weights on export.
            if group.weight > 0.0:
                ssbh_weight = ssbh_data_py.mesh_data.VertexWeight(vertex.index, group.weight / weight_sum)
                group_to_weights[group.group][1].append(ssbh_weight)

    if has_unweighted_vertices:
        message = f'Mesh {mesh_name} has unweighted vertices or vertices with only 0.0 weights.'
        operator.report({'WARNING'}, message)

    # Avoid adding unused influences if there are no weights.
    # Some meshes are parented to a bone instead of using vertex skinning.
    # This requires the influence list to be empty to save properly.
    ssbh_mesh_object.bone_influences = []
    for name, weights in group_to_weights.values():
        # Assume all influence names are valid since some in game models have influences not in the skel.
        # For example, fighter/miifighter/model/b_deacon_m weights vertices to effect bones.
        if len(weights) > 0:
            ssbh_mesh_object.bone_influences.append(ssbh_data_py.mesh_data.BoneInfluence(name, weights))

    # Mesh version 1.10 only has 16-bit unsigned vertex indices for skin weights.
    # Meshes without vertex skinning can use the full range of 32-bit unsigned vertex indices.
    vertex_index = vertex_indices.max()
    if len(ssbh_mesh_object.bone_influences) > 0 and vertex_index > 65535:
        message = f'Vertex index {vertex_index} exceeds the limit of 65535 for mesh {mesh_name}.'
        message += ' Reduce the number of vertices or split the mesh into smaller meshes.'
        message += ' Note that splitting duplicate UVs will increase the vertex count.'
        raise RuntimeError(message)

    smash_uv_names = ['map1', 'bake1', 'uvSet', 'uvSet1', 'uvSet2']
    for uv_layer in mesh.data.uv_layers:
        if uv_layer.name not in smash_uv_names:
            # TODO: Use more specific exception classes?
            valid_attribute_list = ', '.join(smash_uv_names)
            message = f'Mesh {mesh_name} has invalid UV map name {uv_layer.name}.'
            message += ' Use the Attribute Renamer or change the name in Object Data Properties > UV Maps.'
            message += f' Valid names are {valid_attribute_list}.'
            raise RuntimeError(message)

        ssbh_uv_layer = ssbh_data_py.mesh_data.AttributeData(uv_layer.name)
        loop_uvs = np.zeros(len(mesh.data.loops) * 2, dtype=np.float32)
        uv_layer.data.foreach_get("uv", loop_uvs)

        uvs = per_loop_to_per_vertex(loop_uvs, vertex_indices, (len(mesh.data.vertices), 2))
        # Flip vertical.
        uvs[:,1] = 1.0 - uvs[:,1]
        ssbh_uv_layer.data = uvs

        ssbh_mesh_object.texture_coordinates.append(ssbh_uv_layer)

    # Export Color Set
    smash_color_names = ['colorSet1', 'colorSet2', 'colorSet2_1', 'colorSet2_2', 'colorSet2_3', 'colorSet3', 'colorSet4', 'colorSet5', 'colorSet6', 'colorSet7']
    for attribute in mesh.data.color_attributes:
        if attribute.name == '_smush_blender_custom_normals':
            continue

        if attribute.name not in smash_color_names:
            # TODO: Use more specific exception classes?
            valid_attribute_list = ', '.join(smash_color_names)
            message = f'Mesh {mesh_name} has invalid vertex color name {attribute.name}.'
            message += ' Use the Attribute Renamer or change the name in Object Data Properties > Color Attributes.'
            message += f' Valid names are {valid_attribute_list}.'
            raise RuntimeError(message)

        ssbh_color_layer = ssbh_data_py.mesh_data.AttributeData(attribute.name)

        # ssbh_data expects all colors to be 32 bit floats in the range 0.0 to 1.0.
        # Blender currently supports 'POINT' or 'CORNER' and 'FLOAT_COLOR' or 'BYTE_COLOR'.
        # Raise an error if we encounter an unexpected data type or domain.
        if attribute.domain == 'CORNER':
            colors = np.zeros(len(mesh.data.loops) * 4, dtype=np.float32)
        elif attribute.domain == 'POINT':
            colors = np.zeros(len(mesh.data.vertices) * 4, dtype=np.float32)
        else:
            message = f'Color attribute {attribute.name} has unsupported domain {attribute.domain}.'
            raise RuntimeError(message)

        # 'BYTE_COLOR' also uses an array of 4 floats.
        # https://docs.blender.org/api/current/bpy_types_enum_items/attribute_type_items.html#rna-enum-attribute-type-items
        if attribute.data_type == 'FLOAT_COLOR' or attribute.data_type == 'BYTE_COLOR':
            attribute.data.foreach_get('color', colors)
        else:
            message = f'Color attribute {attribute.name} has unsupported data type {attribute.data_type}.'
            raise RuntimeError(message)

        # Only face corner data is stored per loop.
        # Unsupported domains are already checked above.
        if attribute.domain == 'CORNER':
            colors = per_loop_to_per_vertex(colors, vertex_indices, (len(mesh.data.vertices), 4))
        
        colors = colors.reshape((len(mesh.data.vertices), 4))
        ssbh_color_layer.data = colors

        ssbh_mesh_object.color_sets.append(ssbh_color_layer)

    # Calculate tangents now that the necessary attributes are initialized.
    # Use Blender's implementation since it uses mikktspace.
    # Mikktspace is necessary to properly bake normal maps in Blender or external programs.
    # This addresses a number of consistency issues with how normals are encoded/decoded.
    # This will be similar to the in game tangents apart from different smoothing.
    # The vanilla tangents can still cause seams, so they aren't worth preserving.
    mesh.data.calc_tangents()

    tangent0 = ssbh_data_py.mesh_data.AttributeData('Tangent0')

    loop_tangents = np.zeros(len(mesh.data.loops) * 3, dtype=np.float32)
    mesh.data.loops.foreach_get('tangent', loop_tangents)

    loop_bitangent_signs = np.zeros(len(mesh.data.loops), dtype=np.float32)
    mesh.data.loops.foreach_get('bitangent_sign', loop_bitangent_signs)

    tangents = per_loop_to_per_vertex(loop_tangents, vertex_indices, (len(mesh.data.vertices), 3))
    bitangent_signs = per_loop_to_per_vertex(loop_bitangent_signs, vertex_indices, (len(mesh.data.vertices), 1))
    tangent0.data = np.append(tangents @ axis_correction, bitangent_signs * -1.0, axis=1)

    ssbh_mesh_object.tangents = [tangent0]
            
    return ssbh_mesh_object


def add_duplicate_uv_edges(edges_to_split, bm, uv_layer):
    # Blender stores uvs per loop rather than per vertex.
    # Find edges connected to vertices with more than one uv coord.
    # This allows converting to per vertex later by splitting edges.
    index_to_uv = {}
    for face in bm.faces:
        for loop in face.loops:
            vertex_index = loop.vert.index
            uv = loop[uv_layer].uv
            # Use strict equality since UVs are unlikely to change unintentionally.
            if vertex_index not in index_to_uv:
                index_to_uv[vertex_index] = uv
            elif uv != index_to_uv[vertex_index]:
                edges_to_split.extend(loop.vert.link_edges)


def add_duplicate_normal_edges(edges_to_split, bm):
    # The original normals are preserved in a color attribute.
    normal_layer = bm.loops.layers.float_color.get('_smush_blender_custom_normals')

    # Find edges connected to vertices with more than one normal.
    # This allows converting to per vertex later by splitting edges.
    index_to_normal = {}
    for face in bm.faces:
        for loop in face.loops:
            vertex_index = loop.vert.index
            normal = loop[normal_layer]
            # Small fluctuations in normal vectors are expected during processing.
            # Check if the angle between normals is sufficiently large.
            # Assume normal vectors are normalized to have length 1.0.
            if vertex_index not in index_to_normal:
                index_to_normal[vertex_index] = normal
            elif not math.isclose(normal.dot(index_to_normal[vertex_index]), 1.0, abs_tol=0.001, rel_tol=0.001):
                # Get any edges containing this vertex.
                edges_to_split.extend(loop.vert.link_edges)


def split_duplicate_loop_attributes(mesh: bpy.types.Object):
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.mode_set(mode = 'EDIT')

    me: bpy.types.Mesh = mesh.data
    bm = bmesh.from_edit_mesh(me)

    edges_to_split: list[bmesh.types.BMEdge] = []

    add_duplicate_normal_edges(edges_to_split, bm)

    for layer_name in bm.loops.layers.uv.keys():
        uv_layer = bm.loops.layers.uv.get(layer_name)
        add_duplicate_uv_edges(edges_to_split, bm, uv_layer)

    # Duplicate edges cause problems with split_edges.
    edges_to_split = list(set(edges_to_split))

    # Don't modify the mesh if no edges need to be split.
    # This check also seems to prevent a potential crash.
    if len(edges_to_split) > 0:
        bmesh.ops.split_edges(bm, edges=edges_to_split)
        bmesh.update_edit_mesh(me)

    bm.free()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = None

    # Check if any edges were split.
    return len(edges_to_split) > 0


def make_ssbh_modl_data(operator, context, group_name_to_unprocessed_meshes_to_export_meshes: dict[str, dict[Object, set[Object]]]):
    ssbh_modl_data = ssbh_data_py.modl_data.ModlData()

    ssbh_modl_data.model_name = 'model'
    ssbh_modl_data.skeleton_file_name = 'model.nusktb'
    ssbh_modl_data.material_file_names = ['model.numatb']
    ssbh_modl_data.animation_file_name = None
    ssbh_modl_data.mesh_file_name = 'model.numshb'

    for group_name, unprocessed_meshes_to_export_meshes in group_name_to_unprocessed_meshes_to_export_meshes.items():
        sub_index = 0
        for unprocessed_mesh, export_meshes in unprocessed_meshes_to_export_meshes.items():
            for export_mesh in export_meshes:
                mat_label = get_material_label_from_mesh(operator, export_mesh)
                ssbh_modl_entry = ssbh_data_py.modl_data.ModlEntryData(group_name, sub_index, mat_label)
                ssbh_modl_data.entries.append(ssbh_modl_entry)
                sub_index += 1

    return ssbh_modl_data


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
    return (p @ m @ p.inverted()).transposed()


def get_smash_root_transform(bone: bpy.types.EditBone) -> Matrix:
    bone.transform(Matrix.Rotation(math.radians(-90), 4, 'X'))
    bone.transform(Matrix.Rotation(math.radians(90), 4, 'Z'))
    unreoriented_matrix = get_smash_transform(bone.matrix)
    bone.transform(Matrix.Rotation(math.radians(-90), 4, 'Z'))
    bone.transform(Matrix.Rotation(math.radians(90), 4, 'X'))
    return unreoriented_matrix

def read_vanilla_nusktb_ex(operator: Operator, path: Path) -> ssbh_data_py.skel_data.SkelData | None:
    if not path:
        return None
    try:
        skel = ssbh_data_py.skel_data.read_skel(path)
    except Exception as e:
        operator.report(f"Failed to read vanilla .NUSKTB! The exported model won't be `Wifi-Safe`! Please ensure the vanilla .NUSKTB exists and is a valid .NUSKTB, and try again! \n Error={e}")
        return None
    return skel

def read_vanilla_nusktb(path, mode):
    if not path:
        raise RuntimeError(f'Link mode {mode} requires a vanilla .NUSKTB file to be selected.')

    try:
        skel = ssbh_data_py.skel_data.read_skel(path)
        return skel
    except Exception as e:
        message = 'Failed to read vanilla .NUSKTB. Ensure the file exists and is a valid .NUSKTB file.'
        message += f' Error reading {path}: {e}'
        raise RuntimeError(message)


def get_ssbh_bone(blender_bone: bpy.types.EditBone, parent_index):
    if blender_bone.parent:
        unreoriented_matrix = get_smash_transform(blender_bone.parent.matrix.inverted() @ blender_bone.matrix)
        m = list(list(r) for r in unreoriented_matrix)
        #return ssbh_data_py.skel_data.BoneData(blender_bone.name, unreoriented_matrix, parent_index)
        return ssbh_data_py.skel_data.BoneData(blender_bone.name, m, parent_index)
    else:
        m = list(list(r) for r in get_smash_root_transform(blender_bone))
        #return ssbh_data_py.skel_data.BoneData(blender_bone.name, get_smash_root_transform(blender_bone), None)
        return ssbh_data_py.skel_data.BoneData(blender_bone.name, m, None)
    
def get_parent_first_ordered_bones(arma: bpy.types.Object) -> list[bpy.types.EditBone]:
    ''' Edit Bones are not guaranteed to appear in such a way where the child appears after its parent
        This will make sure that parent bones always appear before their children
    '''
    edit_bones: list[EditBone] = arma.data.edit_bones
    parent_first_ordered_bones: list[EditBone] = []
    for bone in edit_bones:
        # only need to do this on the root bones, of which there could be several
        if not bone.parent:
            parent_first_ordered_bones.append(bone)
            parent_first_ordered_bones.extend(child for child in bone.children_recursive)
    return parent_first_ordered_bones

def get_standard_bone_changes(arma: bpy.types.Object, vanilla_nusktb: Path) -> tuple[set[str], set[str]]:
    vanilla_skel: ssbh_data_py.skel_data.SkelData = read_vanilla_nusktb(vanilla_nusktb, None)
    non_standard_bone_regex = r"^[SH]_"
    standard_vanilla_bones: set[str] = {bone.name for bone in vanilla_skel.bones if not re.match(non_standard_bone_regex, bone.name)}
    standard_blender_bones: set[str] = {bone.name for bone in arma.data.bones if not re.match(non_standard_bone_regex, bone.name)}

    new_bones = standard_blender_bones - standard_vanilla_bones
    missing_bones = standard_vanilla_bones - standard_blender_bones

    return new_bones, missing_bones

def make_update_prc(operator: Operator, context, bones_not_in_vanilla: list[EditBone]):
    ssp: SubSceneProperties = context.scene.sub_scene_properties
    prc_root = pyprc.param(ssp.vanilla_update_prc) # Read the .prc into 'prc_root'
    bones_fake_list = dict(prc_root).get(pyprc.hash('bones'))
    if bones_fake_list is None:
        operator.report({'ERROR'}, 'No "bones" list in update.prc! (Did you load another prc instead?)')
        return
    bones_real_list = list(bones_fake_list)
    for bone in bones_not_in_vanilla:
        if bone.name.startswith('H_') or bone.name.startswith('S_'):
            continue
        new_prc_struct = prc_root.struct([
                            (pyprc.hash('name'), prc_root.hash(pyprc.hash(bone.name.lower())))
                        ])
        bones_real_list.append(new_prc_struct)
    bones_fake_list.set_list(bones_real_list)
    return prc_root

def find_non_helper_ancestor_index(bone: EditBone, bones: list[EditBone]) -> int:
    if bone.parent is None:
        return None
    if bone.parent.name.startswith('H_'):
        return find_non_helper_ancestor_index(bone.parent, bones)
    return bones.index(bone.parent)

def make_skel_ex(operator, arma: bpy.types.Armature, reference_skel_path: Path|None):
    """
    This rework eliminates the need to enter Edit mode.
    Also, the vanilla skell values are automatically used, rather than having
    the user input which "Link" mode to use.
    """
    if reference_skel_path:
        return export_skel_with_reference(operator, arma, reference_skel_path)
    
    hierarchical_ordered_bones = []
    for blender_bone in arma.bones:
        if not blender_bone.parent:
            hierarchical_ordered_bones.append(blender_bone)
            hierarchical_ordered_bones.extend(child for child in blender_bone.children_recursive)
    
    export_skel = ssbh_data_py.skel_data.SkelData()
    for blender_bone in hierarchical_ordered_bones:
        blender_bone: bpy.types.Bone
        blender_value = blender_bone.head_local
        export_skel.bones.append(ssbh_data_py.skel_data.BoneData(
            name=blender_bone.name,
            transform=None,
        ))



def make_skel(operator, context, mode):
    ssp: SubSceneProperties = context.scene.sub_scene_properties
    arma: bpy.types.Object = ssp.model_export_arma
    arma_data: bpy.types.Armature = arma.data
    prc = None
    bpy.context.view_layer.objects.active = arma
    # The object should be selected and visible before entering edit mode.
    arma.select_set(True)
    arma.hide_set(False)
    bpy.ops.object.mode_set(mode='EDIT')

    skel = ssbh_data_py.skel_data.SkelData()

    preserve_values = mode == 'ORDER_AND_VALUES'
    preserve_order = mode == 'ORDER_AND_VALUES' or mode == 'ORDER_ONLY'

    vanilla_skel = read_vanilla_nusktb(ssp.vanilla_nusktb, mode) if preserve_values or preserve_order else None

    if vanilla_skel is None:
        message = 'Creating .NUSKTB without a vanilla .NUSKTB file.'
        message += ' Bone order will not be preserved and may cause animation issues in game.'
        operator.report({'WARNING'}, message)
    
    parent_first_ordered_bones = get_parent_first_ordered_bones(arma)

    new_bones: list[EditBone] = []
    bones_not_in_vanilla: list[EditBone] = []
    if mode == 'ORDER_AND_VALUES' or mode == 'ORDER_ONLY':
        for vanilla_bone in vanilla_skel.bones:
            blender_bone = arma_data.edit_bones.get(vanilla_bone.name)
            if blender_bone:
                new_bones.append(blender_bone)

        for blender_bone in parent_first_ordered_bones:
            if blender_bone not in new_bones:
                bones_not_in_vanilla.append(blender_bone)
                if blender_bone.name.startswith('H_') or blender_bone.name.startswith('S_'): # Need to insert new helper or swing bones at the end
                    new_bones.append(blender_bone)
                    continue
                if blender_bone.parent:
                    if blender_bone.parent.name.startswith('H_'): # Makes sure the new normal bone is not at the bottom bone section
                        non_helper_ancestor_index = find_non_helper_ancestor_index(blender_bone, new_bones)
                        if non_helper_ancestor_index is not None:
                            new_bones.insert(non_helper_ancestor_index + 1, blender_bone)
                        else:
                            new_bones.append(blender_bone)
                    else:
                        parent_index = new_bones.index(blender_bone.parent)
                        new_bones.insert(parent_index + 1, blender_bone)
                else:
                    new_bones.append(blender_bone)

        vanilla_skel_name_to_bone = {bone.name : bone for bone in vanilla_skel.bones}
        for new_bone in new_bones:
            ssbh_bone = get_ssbh_bone(new_bone, new_bones.index(new_bone.parent) if new_bone.parent else None)

            if preserve_values:
                vanilla_bone = vanilla_skel_name_to_bone.get(new_bone.name)
                if vanilla_bone:
                    ssbh_bone.transform = vanilla_bone.transform

            skel.bones.append(ssbh_bone)
    else:
        for bone in parent_first_ordered_bones:
            ssbh_bone = get_ssbh_bone(bone, parent_first_ordered_bones.index(bone.parent) if bone.parent else None)
            skel.bones.append(ssbh_bone)

    if ssp.vanilla_update_prc != '':
        prc = make_update_prc(operator, context, bones_not_in_vanilla)

    bpy.ops.object.mode_set(mode='OBJECT')
    arma.select_set(False)
    bpy.context.view_layer.objects.active = None
    return skel, prc

def create_and_save_nuhlpb(path: Path, arma: bpy.types.Object):
    ssbh_hlpb                    = ssbh_data_py.hlpb_data.HlpbData()
    ssbh_hlpb.major_version      = arma.data.sub_helper_bone_data.major_version
    ssbh_hlpb.minor_version      = arma.data.sub_helper_bone_data.minor_version
    ssbh_hlpb.aim_constraints    = [ssbh_data_py.hlpb_data.AimConstraintData(
                                        name              = ac.name,
                                        aim_bone_name1    = ac.aim_bone_name1,
                                        aim_bone_name2    = ac.aim_bone_name2,
                                        aim_type1         = ac.aim_type1,
                                        aim_type2         = ac.aim_type2,
                                        target_bone_name1 = ac.target_bone_name1,
                                        target_bone_name2 = ac.target_bone_name2,
                                        aim               = list(ac.aim),
                                        up                = list(ac.up),
                                        quat1             = [ac.quat1[1], ac.quat1[2], ac.quat1[3], ac.quat1[0]],
                                        quat2             = [ac.quat2[1], ac.quat2[2], ac.quat2[3], ac.quat2[0]],
                                    ) for ac in arma.data.sub_helper_bone_data.aim_constraints]
    ssbh_hlpb.orient_constraints = [ssbh_data_py.hlpb_data.OrientConstraintData(
                                        name              = oc.name,
                                        parent_bone_name1 = oc.parent_bone_name1,
                                        parent_bone_name2 = oc.parent_bone_name2,
                                        source_bone_name  = oc.source_bone_name,
                                        target_bone_name  = oc.target_bone_name,
                                        unk_type          = oc.unk_type,
                                        constraint_axes   = list(oc.constraint_axes),
                                        quat1             = [oc.quat1[1], oc.quat1[2], oc.quat1[3], oc.quat1[0]],
                                        quat2             = [oc.quat2[1], oc.quat2[2], oc.quat2[3], oc.quat2[0]],
                                    ) for oc in arma.data.sub_helper_bone_data.orient_constraints]
    ssbh_hlpb.save(str(path))
     