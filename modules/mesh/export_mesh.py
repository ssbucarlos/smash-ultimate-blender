import bpy
import numpy as np
import math
import sys

from bpy.types import Operator, Mesh, MeshLoopTriangle, Material, MeshLoop, Object, MeshVertex, Armature
from mathutils import Matrix

if __name__ == "__main__":
    import ssbh_data_py
else:
    from ... import ssbh_data_py

# TODO: Is there a better way to account for the change of coordinates?
AXIS_CORRECTION = np.array(Matrix.Rotation(math.radians(90), 3, 'X'), dtype=np.float32)
WARNING = {"WARNING"}
ERROR = {"ERROR"}
SMASH_UV_NAMES = ('map1', 'bake1', 'uvSet', 'uvSet1', 'uvSet2')
SMASH_COLOR_NAMES = ('colorSet1', 'colorSet2', 'colorSet2_1', 'colorSet2_2', 'colorSet2_3', 'colorSet3', 'colorSet4', 'colorSet5', 'colorSet6', 'colorSet7')
class MeshExportError(Exception):
    pass

def get_tris_per_material(mesh: Mesh) -> dict[Material, set[MeshLoopTriangle]]:
    tris: list[MeshLoopTriangle] = mesh.loop_triangles
    material_to_tris: dict[Material, set[MeshLoopTriangle]] = {material : set() for material in mesh.materials}
    for tri in tris:
        face_material = mesh.materials[tri.material_index]
        material_to_tris[face_material].add(tri)
    return material_to_tris

def nested_to_tuple(lst):
    return tuple(nested_to_tuple(i) if isinstance(i, list) or isinstance(i, np.ndarray) else i for i in lst)

def hash_ssbh_vert(ssbh_mesh: ssbh_data_py.mesh_data.MeshObjectData, index: int) -> int:
    """values_to_hash = []
    values_to_hash.append(ssbh_mesh.positions[0].data[index])
    values_to_hash.append(ssbh_mesh.normals[0].data[index])
    values_to_hash.append(ssbh_mesh.tangents[0].data[index])
    for uv_layer in ssbh_mesh.texture_coordinates:
        values_to_hash.append(uv_layer.data[index])
    for color_set in ssbh_mesh.color_sets:
        values_to_hash.append(color_set.data[index])"""

    """values_to_hash = (
        tuple(ssbh_mesh.positions[0].data[index]),
        tuple(ssbh_mesh.normals[0].data[index]),
        tuple(ssbh_mesh.tangents[0].data[index]),
        tuple(tuple(uv_layer.data[index]) for uv_layer in ssbh_mesh.texture_coordinates),
        tuple(tuple(color_set.data[index]) for color_set in ssbh_mesh.color_sets),
    )"""
    all_data_layers = (
        ssbh_mesh.positions,
        ssbh_mesh.normals,
        ssbh_mesh.tangents,
        ssbh_mesh.texture_coordinates,
        ssbh_mesh.color_sets
    )

    all_data_layer_data: tuple[np.ndarray] = (data_layer.data for data_layers in all_data_layers for data_layer in data_layers)

    concatenated_vertex_data_bytes = bytes()
    for data_layer_data in all_data_layer_data:
        vertex_data: np.ndarray = data_layer_data[index]
        concatenated_vertex_data_bytes += vertex_data.data.tobytes()

    """values_to_hash = ssbh_mesh.positions[0].data[index].data.tobytes() +\
        ssbh_mesh.normals[0].data[index].data.tobytes() +\
        ssbh_mesh.tangents[0].data[index].data.tobytes()"""
    return hash(concatenated_vertex_data_bytes)

"""def hash_ssbh_verts(ssbh_mesh: ssbh_data_py.mesh_data.MeshObjectData) -> list[int]:
    hashes = []
    for index,_ in enumerate(ssbh_mesh.positions[0].data):
        hashes.append(hash_ssbh_vert(ssbh_mesh, index))
    return hashes"""

def consolidate_duplicate_verts(ssbh_mesh: ssbh_data_py.mesh_data.MeshObjectData) -> ssbh_data_py.mesh_data.MeshObjectData:
    """
    Exporting loops creates many duplicate verts.
    Also the other function exported loops even if unused (my bad)
    """
    """
    old_positions = ssbh_mesh.positions[0].data
    old_tangents = ssbh_mesh.tangents[0].data
    old_normals = ssbh_mesh.normals[0].data

    old_positions = [tuple(v) for v in old_positions]
    old_normals = [tuple(v) for v in old_normals]
    old_tangents = [tuple(v) for v in old_tangents]

    data_to_vertices: dict[tuple, list[int]] = {}
    for index, _ in enumerate(old_positions):
        data = (old_positions[index], old_normals[index], old_tangents[index])
        if data_to_vertices.get(data):
            #print(f"Duplicate vertex found! index={index}")
            data_to_vertices[data].append(index)
        else:
            data_to_vertices[data] = []
            data_to_vertices[data].append(index)
    """
    #print(data_to_vertices)

    #used_vertex_indexes = {vertex_index for vertex_index in ssbh_mesh.vertex_indices}
    used_vertex_indexes = set(ssbh_mesh.vertex_indices)

    hash_to_verts: dict[int, list[int]] = {}
    hashed_verts = np.zeros(len(used_vertex_indexes), dtype=np.int64)
    for index,_ in enumerate(ssbh_mesh.positions[0].data):
        if index not in used_vertex_indexes:
            continue
        hashed_vert = hash_ssbh_vert(ssbh_mesh, index)
        hashed_verts[index] = hashed_vert
        if hash_to_verts.get(hashed_vert):
            hash_to_verts[hashed_vert].append(index)
        else:
            hash_to_verts[hashed_vert] = []
            hash_to_verts[hashed_vert].append(index)

    

    old_index_to_new_index: dict[int, int] = {}
    new_index = 0
    new_positions = []
    new_normals = []
    new_tangents = []
    new_colorset_data = [[] for color_set in ssbh_mesh.color_sets]
    new_uv_data = [[] for uv_layer in ssbh_mesh.texture_coordinates]
    """
    for old_index, _ in enumerate(old_positions):
        if old_index not in used_vertex_indexes:
            continue
        data = (old_positions[old_index], old_normals[old_index], old_tangents[old_index])
        if len(data_to_vertices[data]) > 1:
            # Potential duplicate vert found
            if data_to_vertices[data][0] == old_index:
                # This is the first of the series of duplicate verts so still include it
                new_positions.append(old_positions[old_index])
                new_tangents.append(old_tangents[old_index])
                new_normals.append(old_normals[old_index])
                old_index_to_new_index[old_index] = new_index
                new_index += 1
            else:
                first_vert_old_index = data_to_vertices[data][0]
                old_index_to_new_index[old_index] = old_index_to_new_index[first_vert_old_index]
        else:
            new_positions.append(old_positions[old_index])
            new_tangents.append(old_tangents[old_index])
            new_normals.append(old_normals[old_index])
            old_index_to_new_index[old_index] = new_index
            new_index += 1
    """
    
    for old_index, _ in enumerate(ssbh_mesh.positions[0].data):
        if old_index not in used_vertex_indexes:
            # discarding unused vertices
            continue
        #hashed_vert = hash_ssbh_vert(ssbh_mesh, old_index)
        hashed_vert = hashed_verts[old_index]
        if len(hash_to_verts[hashed_vert]) > 1:
            # A vert with duplicates was found
            if hash_to_verts[hashed_vert][0] == old_index:
                # This is the first of the series of duplicate verts so still include it
                new_positions.append(ssbh_mesh.positions[0].data[old_index])
                new_tangents.append(ssbh_mesh.tangents[0].data[old_index])
                new_normals.append(ssbh_mesh.normals[0].data[old_index])
                for old_color_set, new_color_set in zip(ssbh_mesh.color_sets, new_colorset_data):
                    new_color_set.append(old_color_set.data[old_index])
                for old_uv_set, new_uv_set in zip(ssbh_mesh.texture_coordinates, new_uv_data):
                    new_uv_set.append(old_uv_set.data[old_index])
                old_index_to_new_index[old_index] = new_index
                new_index += 1
            else:
                first_vert_old_index = hash_to_verts[hashed_vert][0]
                old_index_to_new_index[old_index] = old_index_to_new_index[first_vert_old_index]
        else:
            new_positions.append(ssbh_mesh.positions[0].data[old_index])
            new_tangents.append(ssbh_mesh.tangents[0].data[old_index])
            new_normals.append(ssbh_mesh.normals[0].data[old_index])
            for old_color_set, new_color_set in zip(ssbh_mesh.color_sets, new_colorset_data):
                new_color_set.append(old_color_set.data[old_index])
            for old_uv_set, new_uv_set in zip(ssbh_mesh.texture_coordinates, new_uv_data):
                new_uv_set.append(old_uv_set.data[old_index])
            old_index_to_new_index[old_index] = new_index
            new_index += 1
    
    """ 
    new_vert_count = sum(1 for values in hash_to_verts.values())
    new_positions = np.zeros((new_vert_count,3), dtype=np.float32)
    new_normals = np.zeros((new_vert_count,4), dtype=np.float32)
    new_tangents = np.zeros((new_vert_count,4), dtype=np.float32)
    new_index = 0
    for old_index, _ in enumerate(ssbh_mesh.positions[0].data):
        if old_index not in used_vertex_indexes:
            # discarding unused vertices
            continue
        hashed_vert = hashed_verts[old_index]
        if len(hash_to_verts[hashed_vert]) > 1:
            # A vert with duplicates was found
            if hash_to_verts[hashed_vert][0] == old_index:
                # This is the first of the series of duplicate verts so still include it
                new_positions[new_index] = ssbh_mesh.positions[0].data[old_index]
                new_tangents[new_index] = ssbh_mesh.tangents[0].data[old_index]
                new_normals[new_index] = ssbh_mesh.normals[0].data[old_index]
                for old_color_set, new_color_set in zip(ssbh_mesh.color_sets, new_colorset_data):
                    new_color_set.append(old_color_set.data[old_index])
                for old_uv_set, new_uv_set in zip(ssbh_mesh.texture_coordinates, new_uv_data):
                    new_uv_set.append(old_uv_set.data[old_index])
                old_index_to_new_index[old_index] = new_index
                new_index += 1
            else:
                first_vert_old_index = hash_to_verts[hashed_vert][0]
                old_index_to_new_index[old_index] = old_index_to_new_index[first_vert_old_index]
        else:
            new_positions[new_index] = ssbh_mesh.positions[0].data[old_index]
            new_tangents[new_index] = ssbh_mesh.tangents[0].data[old_index]
            new_normals[new_index] = ssbh_mesh.normals[0].data[old_index]
            old_index_to_new_index[old_index] = new_index
            new_index += 1
    """

    new_vertex_indices = [old_index_to_new_index[vertex_index] for vertex_index in ssbh_mesh.vertex_indices]
    new_position0 = ssbh_data_py.mesh_data.AttributeData('Position0', new_positions)
    #print(f"{new_vert_count=}, {len(new_positions)=}, {len(new_vertex_indices)=}")
    new_normal0 = ssbh_data_py.mesh_data.AttributeData('Normal0', new_normals)
    new_tangent0 = ssbh_data_py.mesh_data.AttributeData('Tangent0', new_tangents)
    new_colorsets = []
    for index, color_set in enumerate(ssbh_mesh.color_sets):
        new_colorsets.append(ssbh_data_py.mesh_data.AttributeData(color_set.name, new_colorset_data[index]))
    new_uvs = []
    for index, uv_layer in enumerate(ssbh_mesh.texture_coordinates):
        new_uvs.append(ssbh_data_py.mesh_data.AttributeData(uv_layer.name, new_uv_data[index]))
    if new_colorsets:
        print(f'\n\n{ssbh_mesh.color_sets=}{new_colorsets=}{len(ssbh_mesh.color_sets)=}, \n{ssbh_mesh.texture_coordinates=}{new_uvs=}')
    return ssbh_data_py.mesh_data.MeshObjectData(
        name=ssbh_mesh.name,
        subindex=ssbh_mesh.subindex,
        parent_bone_name=ssbh_mesh.parent_bone_name,
        disable_depth_test=ssbh_mesh.disable_depth_test,
        disable_depth_write=ssbh_mesh.disable_depth_write,
        sort_bias=ssbh_mesh.sort_bias,
        vertex_indices=new_vertex_indices,
        positions=[new_position0],
        normals=[new_normal0],
        tangents=[new_tangent0],
        color_sets=new_colorsets,
        texture_coordinates=new_uvs,
    )

def get_optimized_ssbh_mesh_data(mesh: Mesh, export_mesh_name:str):
    material_to_tris = get_tris_per_material(mesh)
    
    loop_positions, loop_normals, loop_tangents, loop_texture_coordinate_layers, loop_colorset_layers = get_ssbh_data_from_mesh_loops(mesh)
    for material, tris in material_to_tris.items():
        if tris:
            vertex_indices = [loop_index for tri in tris for loop_index in tri.loops]

def get_per_loop_data_from_mesh_test(mesh: Mesh, operator: Operator):
    # Normals
    loop_normals_flattened = np.zeros(len(mesh.loops)*3, dtype=np.float32)
    mesh.loops.foreach_get('normal', loop_normals_flattened)
    loop_normals_unpadded = loop_normals_flattened.reshape((-1,3)) @ AXIS_CORRECTION
    # Pad normals to 4 components instead of 3 components.
    # This actually results in smaller file sizes since HalfFloat4 is smaller than Float3.
    loop_normals = np.append(loop_normals_unpadded, np.zeros((loop_normals_unpadded.shape[0],1), dtype=np.float32), axis=1)

    # Tangents
    loop_tangents_flattened = np.zeros(len(mesh.loops)*3, dtype=np.float32)
    mesh.loops.foreach_get('tangent', loop_tangents_flattened)
    loop_tangents = loop_tangents_flattened.reshape((-1,3)) @ AXIS_CORRECTION
    # Bitangent signs
    bitangent_signs_flattened = np.zeros(len(mesh.loops)*1, dtype=np.float32) # *1 because type hinting breaks otherwise, remove once fixed
    mesh.loops.foreach_get('bitangent_sign', bitangent_signs_flattened)
    bitangent_signs = bitangent_signs_flattened.reshape((-1,1))
    # Tangents w/ Bitangent signs
    loop_tangents_with_bitangents = np.append(loop_tangents, bitangent_signs * -1.0, axis=1) # Smash needs the flipped bitangent sign

    # UVs
    loop_texture_coordinate_layers: dict[str, np.ndarray[np.float32]] = {}
    for uv_layer in mesh.uv_layers:
        if uv_layer.name not in SMASH_UV_NAMES:
            # If there's only one UV layer, assume its meant to be 'map1'.
            if len(mesh.uv_layers) == 1:
                smash_uv_layer_name = 'map1'
                operator.report(WARNING, f"Automatically Renamed UV Layer `{uv_layer.name}` to `map1` for mesh `{mesh.name}`, but please use the `Attribute Renamer` (in a panel included with this plugin) to rename it to a correct Smash UV Layer Name. Or rename it manually.")
            else:
                raise MeshExportError(f"Incorrect UV Layer Names for mesh `{mesh.name}`! Please use the `Attribute Renamer` (in a panel included with this plugin) to rename them to correct Smash UV Layer Names. Or rename them manually.")
        else:
            smash_uv_layer_name = uv_layer.name
        loop_uvs_flattened = np.zeros(len(mesh.loops) * 2, dtype=np.float32)
        uv_layer.data.foreach_get("uv", loop_uvs_flattened)
        loop_uvs = loop_uvs_flattened.reshape((-1, 2))
        loop_uvs[:,1] = 1.0 - loop_uvs[:,1] # Smash needs the inverted V value
        loop_texture_coordinate_layers.update({uv_layer.name : loop_uvs})

    # Colorsets
    loop_colorset_layers: dict[str, np.ndarray[np.float32]] = {}
    for color_attribute in mesh.color_attributes:
        if color_attribute.domain != "CORNER":
            continue
        smash_color_set_name: str
        if color_attribute.name in SMASH_COLOR_NAMES:
            smash_color_set_name = color_attribute.name
        else:
            # If there's only one color layer, assume its meant to be 'colorSet1'
            if len(mesh.color_attributes) == 1:
                smash_color_set_name = 'colorSet1'
                operator.report(WARNING, f"Automatically Renamed Color Set Layer `{color_attribute.name}` to `colorSet1` for mesh `{mesh.name}`, but please use the `Attribute Renamer` (in a panel included with this plugin) to rename it to a correct Smash Color Set Layer Name. Or rename it manually.")
            else:
                raise MeshExportError(f"Incorrect 'Color Attribute' names for mesh `{mesh.name}`! Please use the `Attribute Renamer` (in a panel included with this plugin) to rename them to correct Smash UV Layer Names. Or rename them manually.")

        loop_colors_flattened = np.zeros(len(mesh.loops) * 4, dtype=np.float32)
        color_attribute.data.foreach_get('color', loop_colors_flattened)
        loop_colors = loop_colors.reshape((-1,4))
        loop_colorset_layers.update({smash_color_set_name:loop_colors})

    return loop_normals, loop_tangents_with_bitangents, loop_texture_coordinate_layers, loop_colorset_layers

def get_vertex_weights_from_mesh(mesh: Mesh, arma: Armature, operator: Operator):
    '''
    Vertex groups can either be 'Deform' groups used for actual mesh deformation, or 'Other'
    Only want the 'Deform' groups exported.
    Except in the edge-case of some vanilla models that come with weights for bones not in the model.  
    '''
    # Export Weights
    reported_unweighted_vertices = False
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

def get_per_vertex_data_from_mesh_test(mesh: Mesh, operator: Operator):
    # Positions
    vertex_positions_flattened = np.zeros(len(mesh.vertices)*3, dtype=np.float32)
    mesh.vertices.foreach_get('co', vertex_positions_flattened) 
    vertex_positions = vertex_positions_flattened.reshape((-1,3)) @ AXIS_CORRECTION
    
    # Bone Influences
    
    

def get_per_triangle_data_from_mesh_test(mesh: Mesh, operator: Operator):
    pass

def get_data_from_mesh_test(mesh: Mesh, operator: Operator):
    '''
    For accurate export, the export of 'per-loop' (vertex-per-face) data is required.
    Even though smash doesn't support 'loops', each loop can be exported as a new vert.
    Doing so is extremely inefficient however, as many loops are just duplicates and could have
    just been consolidated into one vert.
    So, for efficiency, we need to figure out which verts we can get away with just exporting
    one vert that all loops belonging to that vert will re-use, or when we need to "split" the vert into per loop data.
    For example, a vert with split custom normals, or a vert where different materials use the same vert.
    For fast export, only numpy and blender's "foreach_get" should be used.
    '''
    
    vertex_positions, vertex_bone_weights, vertex_colorset_layers = get_per_vertex_data_from_mesh_test(mesh, operator)
    loop_normals, loop_tangents_with_bitangents, loop_texture_coordinate_layers, loop_colorset_layers = get_per_loop_data_from_mesh_test(mesh, operator)
    triangle_loop_indices, triangle_material_indices = get_per_triangle_data_from_mesh_test(mesh, operator)



def get_data_from_mesh_ex(mesh: Mesh, materials: list[Material]):
    # Using numpy and blender's foreach_get is much faster
    # TODO: Is there a better way to account for the change of coordinates?
    axis_correction = np.array(Matrix.Rotation(math.radians(90), 3, 'X'), dtype=np.float32)

    # Positions
    # position data is per-vertex, not per loop
    # positions = [mesh.vertices[loop.vertex_index].co for loop in mesh.loops]
    vertex_positions = np.zeros(len(mesh.vertices)*3, dtype=np.float32)
    mesh.vertices.foreach_get('co', vertex_positions)
    # foreach_get returns 'flattened' aka '1D', so reshape it to a N-by-3 array
    vertex_positions = vertex_positions.reshape((-1,3))
    vertex_positions = vertex_positions @ axis_correction

    # Normals
    # normals = [loop.normal for loop in mesh.loops]
    loop_normals = np.zeros(len(mesh.loops)*3, dtype=np.float32)
    mesh.loops.foreach_get('normal', loop_normals)
    loop_normals = loop_normals.reshape((-1,3))
    loop_normals = loop_normals @ axis_correction
    # Pad normals to 4 components instead of 3 components.
    # This actually results in smaller file sizes since HalFloat4 is smaller than Float3.
    loop_normals = np.append(loop_normals, np.zeros((loop_normals.shape[0],1), dtype=np.float32), axis=1)

    # Tangents
    # tangents = [loop.tangent for loop in mesh.loops]
    loop_tangents = np.zeros(len(mesh.loops)*3, dtype=np.float32)
    mesh.loops.foreach_get('tangent', loop_tangents)
    loop_tangents = loop_tangents.reshape((-1,3))
    # Bitangent signs
    bitangent_signs = np.zeros(len(mesh.loops)*1, dtype=np.float32) # *1 because type hinting breaks otherwise, remove once fixed
    mesh.loops.foreach_get('bitangent_sign', bitangent_signs)
    bitangent_signs = bitangent_signs.reshape((-1,1))
    # Tangents w/ Bitangent signs
    loop_tangents = np.append(loop_tangents @ axis_correction, bitangent_signs * -1.0, axis=1)

    # UVs
    # uvs = [[uv_data.uv[0], 1.0 - uv_data.uv[1]] for uv_data in uv_layer.data]
    smash_uv_names = ['map1', 'bake1', 'uvSet', 'uvSet1', 'uvSet2']
    loop_texture_coordinate_layers: dict[str, np.ndarray[np.float32]] = {}
    for uv_layer in mesh.uv_layers:
        uv_layer: bpy.types.MeshUVLoopLayer
        if uv_layer.name not in smash_uv_names:
            # TODO: Actual exception
            continue
        loop_uvs = np.zeros(len(mesh.loops) * 2, dtype=np.float32)
        uv_layer.data.foreach_get("uv", loop_uvs)
        loop_uvs = loop_uvs.reshape((-1, 2))
        loop_uvs[:,1] = 1.0 - loop_uvs[:,1]
        loop_texture_coordinate_layers[uv_layer.name] = loop_uvs

    # Colorsets
    smash_color_names = ['colorSet1', 'colorSet2', 'colorSet2_1', 'colorSet2_2', 'colorSet2_3', 'colorSet3', 'colorSet4', 'colorSet5', 'colorSet6', 'colorSet7']
    loop_colorset_layers: dict[str, np.ndarray[np.float32]] = {}
    for attribute in mesh.color_attributes:
        if attribute.name not in smash_color_names:
            # TODO: Use more specific exception classes?
            # TODO: Actual exception
            continue
        
        if attribute.data_type != 'FLOAT_COLOR' and attribute.data_type != 'BYTE_COLOR':
            message = f'Color attribute {attribute.name} has unsupported data type {attribute.data_type}!'
            raise RuntimeError(message)
        
        loop_colors = np.zeros(len(mesh.loops) * 4, dtype=np.float32)
        match attribute.domain:
            case 'POINT': # per-vertex
                loop_colors = loop_colors.reshape((-1,4))
                for loop_index, loop in enumerate(mesh.loops):
                    loop_colors[loop_index] = attribute.data[loop.vertex_index].color
            case 'CORNER': # per-loop
                attribute.data.foreach_get('color', loop_colors)
                loop_colors = loop_colors.reshape((-1,4))
            case _:
                raise RuntimeError(f"Unsupported domain {attribute.domain}.")
        loop_colorset_layers[attribute.name] = loop_colors

    # Triangles
    triangle_loop_indices = np.zeros(len(mesh.loop_triangles)*3, dtype=np.uint64)
    mesh.loop_triangles.foreach_get("loops", triangle_loop_indices)
    triangle_loop_indices = np.reshape(triangle_loop_indices, (-1,3))

    triangle_material_indices = np.zeros(len(mesh.loop_triangles)*1, dtype=np.uint8)
    mesh.loop_triangles.foreach_get('material_index', triangle_material_indices)

    vertex_indices_of_loops = np.zeros(len(mesh.loops)*1, dtype=np.uint64)
    mesh.loops.foreach_get("vertex_index", vertex_indices_of_loops)

    from ...dependencies import ssbh_mesh_optimizer
    return ssbh_mesh_optimizer.BlenderMeshData(
        mesh.name,
        [material.name for material in materials],
        vertex_positions,
        loop_normals,
        loop_tangents,
        loop_texture_coordinate_layers,
        loop_colorset_layers,
        vertex_indices_of_loops,
        triangle_loop_indices,
        triangle_material_indices
    )

def temp():
    # Blender supports per-loop vertex attribute data
    # for export accuracy, each loop would need to be split off into a new vertex
    # for export speed/filesize efficiency, only split off into new verts when needed
    first_loop_index_per_vertex: dict[int, int] = {}
    vertex_indices_to_split: set[int] = set()
    loop_indices_to_split: set[int] = set()
    
    mesh.loops.foreach_get("vertex_index", vertex_indices_of_loops)
    for (loop_index, vertex_index) in enumerate(vertex_indices_of_loops):
        if vertex_index in vertex_indices_to_split:
            loop_indices_to_split.add(loop_index)
            continue
        first_loop_index = first_loop_index_per_vertex.get(vertex_index)
        if first_loop_index is None:
            first_loop_index_per_vertex[vertex_index] = loop_index
            continue
        if not np.allclose(loop_normals[loop_index], loop_normals[first_loop_index]):
            vertex_indices_to_split.add(vertex_index)
            loop_indices_to_split.add(loop_index)
            continue
        for loop_uv_layer in loop_texture_coordinate_layers:
            if not np.allclose(loop_uv_layer[loop_index], loop_uv_layer[first_loop_index]):
                vertex_indices_to_split.add(vertex_index)
                loop_indices_to_split.add(loop_index)
                continue
        for loop_colorset_layer in loop_colorset_layers:
            if not np.allclose(loop_colorset_layer[loop_index], loop_colorset_layer[first_loop_index]):
                vertex_indices_to_split.add(vertex_index)
                loop_indices_to_split.add(loop_index)
                continue
    
    mesh_entries = []
    subindex = 0
    for material_index, material in enumerate(mesh.materials):
        matching_triangle_indices = np.flatnonzero(triangle_material_indices == material_index)
        export_positions = []
        export_normals = []
        export_tangents = []
        export_texture_coordinates = [[] for texture_coordinate_layer in loop_texture_coordinate_layers]
        export_colorsets = [[] for color_set_layer in loop_colorset_layers]
        export_vertex_indices = []
        old_vert_index_to_new_vert_index: dict[int,int] = {}
        new_index = 0
        for matching_triangle_index in matching_triangle_indices:
            loop_indices = triangle_loop_indices[matching_triangle_index]
            for loop_index in loop_indices:
                vert_index = vertex_indices_of_loops[loop_index]
                if loop_index in loop_indices_to_split:
                    # Export the split vert data
                    export_positions.append(vertex_positions[vert_index])
                    export_vertex_indices.append(new_index)
                    new_index+=1
                    pass
                else:
                    # just place one vert for all loops on this index
                    pre_existing_index = old_vert_index_to_new_vert_index.get(vert_index)
                    if pre_existing_index:
                        export_vertex_indices.append(pre_existing_index)
                    else:
                        export_positions.append(vertex_positions[vert_index])
                        export_vertex_indices.append(new_index)
                        old_vert_index_to_new_vert_index[vert_index] = new_index
                        new_index+=1
        new_ssbh_mesh = ssbh_data_py.mesh_data.MeshObjectData(
            name=mesh.name,
            subindex=subindex,
            vertex_indices=export_vertex_indices,
            positions=ssbh_data_py.mesh_data.AttributeData(name="Position0", data=[export_positions]),

        )
        subindex+=1

  
def get_ssbh_data_from_mesh_loops(mesh: Mesh):
    '''
    This gets data per-loop, which while accurate it results
    in extremely unoptimized mesh file size data, as one vertex can have several loops, 
    but each loop may actually just contain identical data since there was no
    vertex-per-face data (aka per-loop or per-face-corner) data at all.
    In addition, blender meshes support multiple materials per mesh, so
    the whole loop data may contain loops for different materials so 
    another function is required to only grab the loops per-material.
    '''
    # Using numpy and blender's foreach_get is much faster
    # TODO: Is there a better way to account for the change of coordinates?
    axis_correction = np.array(Matrix.Rotation(math.radians(90), 3, 'X'), dtype=np.float32)

    # Positions
    # position data is per-vertex, need to convert to per-loop after its done
    # positions = [mesh.vertices[loop.vertex_index].co for loop in mesh.loops]
    vertex_positions = np.zeros(len(mesh.vertices)*3, dtype=np.float32)
    mesh.vertices.foreach_get('co', vertex_positions)
    # foreach_get returns 'flattened' aka '1D', so reshape it to a N-by-3 array
    vertex_positions = vertex_positions.reshape((-1,3))
    vertex_positions = vertex_positions @ axis_correction
    loop_positions = np.array([vertex_positions[loop.vertex_index] for loop in mesh.loops], dtype=np.float32)

    # Normals
    # normals = [loop.normal for loop in mesh.loops]
    loop_normals = np.zeros(len(mesh.loops)*3, dtype=np.float32)
    mesh.loops.foreach_get('normal', loop_normals)
    loop_normals = loop_normals.reshape((-1,3))
    loop_normals = loop_normals @ axis_correction
    # Pad normals to 4 components instead of 3 components.
    # This actually results in smaller file sizes since HalFloat4 is smaller than Float3.
    loop_normals = np.append(loop_normals, np.zeros((loop_normals.shape[0],1), dtype=np.float32), axis=1)

    # Tangents
    # tangents = [loop.tangent for loop in mesh.loops]
    loop_tangents = np.zeros(len(mesh.loops)*3, dtype=np.float32)
    mesh.loops.foreach_get('tangent', loop_tangents)
    loop_tangents = loop_tangents.reshape((-1,3))
    # Bitangent signs
    bitangent_signs = np.zeros(len(mesh.loops)*1, dtype=np.float32) # *1 because type hinting breaks otherwise, remove once fixed
    mesh.loops.foreach_get('bitangent_sign', bitangent_signs)
    bitangent_signs = bitangent_signs.reshape((-1,1))
    # Tangents w/ Bitangent signs
    loop_tangents = np.append(loop_tangents @ axis_correction, bitangent_signs * -1.0, axis=1)

    # UVs
    # uvs = [[uv_data.uv[0], 1.0 - uv_data.uv[1]] for uv_data in uv_layer.data]
    smash_uv_names = ['map1', 'bake1', 'uvSet', 'uvSet1', 'uvSet2']
    loop_texture_coordinate_layers: dict[str, np.ndarray[np.float32]] = {}
    for uv_layer in mesh.uv_layers:
        uv_layer: bpy.types.MeshUVLoopLayer
        if uv_layer.name not in smash_uv_names:
            # TODO: Actual exception
            continue
        loop_uvs = np.zeros(len(mesh.loops) * 2, dtype=np.float32)
        uv_layer.data.foreach_get("uv", loop_uvs)
        loop_uvs = loop_uvs.reshape((-1, 2))
        loop_uvs[:,1] = 1.0 - loop_uvs[:,1]
        loop_texture_coordinate_layers[uv_layer.name] = loop_uvs

    # Colorsets
    smash_color_names = ['colorSet1', 'colorSet2', 'colorSet2_1', 'colorSet2_2', 'colorSet2_3', 'colorSet3', 'colorSet4', 'colorSet5', 'colorSet6', 'colorSet7']
    loop_colorset_layers: dict[str, np.ndarray[np.float32]] = {}
    for attribute in mesh.color_attributes:
        if attribute.name not in smash_color_names:
            # TODO: Use more specific exception classes?
            # TODO: Actual exception
            continue
        
        if attribute.data_type != 'FLOAT_COLOR' and attribute.data_type != 'BYTE_COLOR':
            message = f'Color attribute {attribute.name} has unsupported data type {attribute.data_type}!'
            raise RuntimeError(message)
        
        loop_colors = np.zeros(len(mesh.loops) * 4, dtype=np.float32)
        match attribute.domain:
            case 'POINT': # per-vertex
                loop_colors = loop_colors.reshape((-1,4))
                for loop_index, loop in enumerate(mesh.loops):
                    loop_colors[loop_index] = attribute.data[loop.vertex_index].color
            case 'CORNER': # per-loop
                attribute.data.foreach_get('color', loop_colors)
                loop_colors = loop_colors.reshape((-1,4))
            case _:
                raise RuntimeError(f"Unsupported domain {attribute.domain}.")
        loop_colorset_layers[attribute.name] = loop_colors
        
    return (
        loop_positions, 
        loop_normals,
        loop_tangents,
        loop_texture_coordinate_layers,
        loop_colorset_layers,
    )

def get_ssbh_mesh_from_mesh_loop_tris(mesh: Mesh, tris: set[MeshLoopTriangle], mesh_sub_index: int, ssbh_mesh_name: str) -> ssbh_data_py.mesh_data.MeshObjectData:
    """
    each MeshLoopTriangle corresponds to three "loop vertices"
    To ensure proper export of vertex-per-face data, each "loop vertex" will be exported as
    separate vertices. 
    """
    # Not every loop in the mesh will be accessed, only the loops corresponding to the current material are needed.
    #used_loops: set[MeshLoop] = {mesh.loops[loop_index] for tri in tris for loop_index in tri.loops}
    # For now, just export every loop (even those belonging to other materials) and cleanup the unused ones later
    # has to be a list to preserve the correct order for the "vertex_indices" list later on.
    used_loops: list[MeshLoop] = [loop for loop in mesh.loops]
    # TODO: Is there a better way to account for the change of coordinates?
    axis_correction = np.array(Matrix.Rotation(math.radians(90), 3, 'X'))
    #axis_correction = Matrix.Rotation(math.radians(90), 3, 'X')

    # Each "loop" will be treated as a unique vertex for now.
    #positions = np.zeros(len(loops)*3, dtype=np.float32)
    #positions = [mesh.vertices[loop.vertex_index].co for loop in used_loops]
    vertex_positions = np.zeros(len(mesh.loops)*3, dtype=np.float32)
    mesh.vertices.foreach_get('co', vertex_positions)
    vertex_positions = vertex_positions.reshape((-1, 3))
    vertex_positions = vertex_positions @ axis_correction
    loop_positions = [vertex_positions[loop.vertex_index] for loop in used_loops]
    position0 = ssbh_data_py.mesh_data.AttributeData('Position0', np.array(loop_positions))

    # This is the part that gets the loops that belong only to the given set of faces,
    # which was the set of faces that belong to a given material.
    vertex_indices = [loop_index for tri in tris for loop_index in tri.loops]

    # normal0 stuff
    #normals = [loop.normal for loop in used_loops]
    normals = np.zeros(len(mesh.loops)*3, dtype=np.float32)
    mesh.loops.foreach_get('normal', normals)
    normals = normals.reshape((-1,3))
    normals = normals @ axis_correction
    
    # Pad normals to 4 components instead of 3 components.
    # This actually results in smaller file sizes since HalFloat4 is smaller than Float3.
    normals = np.append(normals, np.zeros((normals.shape[0],1)), axis=1)
    normal0 = ssbh_data_py.mesh_data.AttributeData('Normal0', normals)

    # Calculate tangents now that the necessary attributes are initialized.
    # Use Blender's implementation since it uses mikktspace.
    # Mikktspace is necessary to properly bake normal maps in Blender or external programs.
    # This addresses a number of consistency issues with how normals are encoded/decoded.
    # This will be similar to the in game tangents apart from different smoothing.
    # The vanilla tangents can still cause seams, so they aren't worth preserving.
    #tangents = [loop.tangent for loop in used_loops]
    #print(tangents)
    #bitangent_signs = np.array([loop.bitangent_sign for loop in used_loops], dtype=np.float32)
    #print(bitangent_signs)
    #tangent0_data = np.append(tangents, bitangent_signs * -1.0, axis=1)
    
    #tangent0 = ssbh_data_py.mesh_data.AttributeData('Tangent0', tangent0_data)
    tangents = np.zeros(len(mesh.loops)*3, dtype=np.float32)
    mesh.loops.foreach_get('tangent', tangents)
    tangents = tangents.reshape((-1,3))

    bitangent_signs = np.zeros(len(mesh.loops)*1, dtype=np.float32) # *1 because type hinting breaks otherwise
    mesh.loops.foreach_get('bitangent_sign', bitangent_signs)
    bitangent_signs = bitangent_signs.reshape((-1,1))

    tangents = np.append(tangents @ axis_correction, bitangent_signs * -1.0, axis=1)
    #test = [list(loop.tangent[:] @ axis_correction) + [loop.bitangent_sign * -1.0] for loop in used_loops]
    tangent0 = ssbh_data_py.mesh_data.AttributeData('Tangent0', tangents)

    # uv stuff
    smash_uv_names = ['map1', 'bake1', 'uvSet', 'uvSet1', 'uvSet2']
    ssbh_uvs = []
    for uv_layer in mesh.uv_layers:
        uv_layer: bpy.types.MeshUVLoopLayer
        if uv_layer.name not in smash_uv_names:
            # TODO: Actual exception
            continue
        #uvs = [[uv_data.uv[0], 1.0 - uv_data.uv[1]] for uv_data in uv_layer.data]
        uvs = np.zeros(len(mesh.loops) * 2, dtype=np.float32)
        uv_layer.data.foreach_get("uv", uvs)
        uvs = uvs.reshape((-1, 2))
        uvs[:,1] = 1.0 - uvs[:,1]
        ssbh_uvs.append(ssbh_data_py.mesh_data.AttributeData(uv_layer.name, data=uvs))    
    # colorset stuff
    smash_color_names = ['colorSet1', 'colorSet2', 'colorSet2_1', 'colorSet2_2', 'colorSet2_3', 'colorSet3', 'colorSet4', 'colorSet5', 'colorSet6', 'colorSet7']
    ssbh_colorsets = []
    for attribute in mesh.color_attributes:
        if attribute.name not in smash_color_names:
            # TODO: Use more specific exception classes?
            # TODO: Actual exception
            continue
        
        if attribute.data_type != 'FLOAT_COLOR' and attribute.data_type != 'BYTE_COLOR':
            message = f'Color attribute {attribute.name} has unsupported data type {attribute.data_type}!'
            raise RuntimeError(message)
        
        colors = np.zeros(len(mesh.loops) * 4, dtype=np.float32)
        if attribute.domain == 'POINT': # per-vertex
            colors = colors.reshape((-1,4))
            for loop_index, loop in enumerate(used_loops):
                colors[loop_index] = attribute.data[loop.vertex_index].color
            #colors = [attribute.data[loop.vertex_index].color for loop in used_loops]
        elif attribute.domain == 'CORNER': # per-loop
            attribute.data.foreach_get('color', colors)
            colors = colors.reshape((-1,4))
            #colors = [data.color for data in attribute.data]
            print(f'{colors=}')
        ssbh_colorsets.append(ssbh_data_py.mesh_data.AttributeData(attribute.name, data=colors))
            
    return ssbh_data_py.mesh_data.MeshObjectData(
        ssbh_mesh_name,
        mesh_sub_index, 
        positions=[position0], 
        vertex_indices=vertex_indices,
        normals=[normal0],
        tangents=[tangent0],
        texture_coordinates=ssbh_uvs,
        color_sets=ssbh_colorsets
        )

def create_ssbh_mesh_modl_entries_from_blender_mesh_with_shapekeys(context: bpy.types.Context, mesh_object: Object, mesh: Mesh) -> tuple[list[ssbh_data_py.mesh_data.MeshObjectData], list[ssbh_data_py.modl_data.ModlEntryData]]:
    ssbh_mesh_objects = []
    ssbh_modl_entries = []
    for index, shapekey in enumerate(mesh.shape_keys.key_blocks):
        shapekey: bpy.types.ShapeKey
        if "_VIS" in shapekey.name:
            mesh_object.active_shape_key_index = index
            depsgraph = context.evaluated_depsgraph_get()
            obj_eval: Object = mesh_object.evaluated_get(depsgraph)
            mesh_eval = obj_eval.data
            new_ssbh_mesh_objects, new_ssbh_modl_entries = create_ssbh_mesh_modl_entries_from_blender_mesh(mesh_eval, shapekey.name)
            ssbh_mesh_objects.extend(new_ssbh_mesh_objects)
            ssbh_modl_entries.extend(new_ssbh_modl_entries)
    
    return ssbh_mesh_objects, ssbh_modl_entries

def create_ssbh_mesh_modl_entries_from_blender_mesh(mesh: Mesh, ssbh_mesh_name: str) -> tuple[list[ssbh_data_py.mesh_data.MeshObjectData], list[ssbh_data_py.modl_data.ModlEntryData]]:
    """
    Since a smash mesh has one material applied to the whole mesh, blender meshes with multiple materials will result in
    multiple ssbh_meshes being created. In addition a blender mesh may have shapekeys which also need to be evaluated.
    """
    mesh.calc_loop_triangles()
    mesh.calc_normals_split()
    mesh.calc_tangents(uvmap="map1" if mesh.uv_layers.get("map1") else mesh.uv_layers[0].name)

    material_to_tris = get_tris_per_material(mesh)

    ssbh_meshes: list[ssbh_data_py.mesh_data.MeshObjectData] = []
    ssbh_modl_entries: list[ssbh_data_py.modl_data.ModlEntryData] = []
    subindex = 0
    for material, tris in material_to_tris.items():
        if tris: # Skips materials with no faces
            unoptimized_mesh = get_ssbh_mesh_from_mesh_loop_tris(mesh, tris, subindex, ssbh_mesh_name)
            optimized_mesh = consolidate_duplicate_verts(unoptimized_mesh)
            ssbh_meshes.append(optimized_mesh)
            ssbh_modl_entries.append(ssbh_data_py.modl_data.ModlEntryData(ssbh_mesh_name, subindex, material.name))
            subindex += 1

    return ssbh_meshes, ssbh_modl_entries

# For testing, i copy paste this whole file into blender's scripting page then i hit run
# ssbh_data_py must be pip installed into blender's python before trying this.
def main():
    test_object: Object = bpy.data.objects['Cube']
    test_mesh: Mesh = test_object.data

    if test_mesh.shape_keys:
        ssbh_meshes, ssbh_modl_entries = create_ssbh_mesh_modl_entries_from_blender_mesh_with_shapekeys(bpy.context, test_object, test_mesh)
    else:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval: Object = test_object.evaluated_get(depsgraph)
        mesh_eval = obj_eval.data
        ssbh_meshes, ssbh_modl_entries = create_ssbh_mesh_modl_entries_from_blender_mesh(mesh_eval, mesh_eval.name)

    ssbh_modl_data = ssbh_data_py.modl_data.ModlData()

    ssbh_modl_data.model_name = 'model'
    ssbh_modl_data.skeleton_file_name = 'model.nusktb'
    ssbh_modl_data.material_file_names = ['model.numatb']
    ssbh_modl_data.animation_file_name = None
    ssbh_modl_data.mesh_file_name = 'model.numshb'

    ssbh_modl_data.entries = ssbh_modl_entries

    ssbh_mesh_data = ssbh_data_py.mesh_data.MeshData()
    ssbh_mesh_data.objects = ssbh_meshes

    from pathlib import Path
    out = Path(r"C:\Users\Carlos\Downloads\blah")
    ssbh_modl_data.save(str(out / "model.numdlb"))
    ssbh_mesh_data.save(str(out / "model.numshb"))

if __name__ == '__main__':
    main()

