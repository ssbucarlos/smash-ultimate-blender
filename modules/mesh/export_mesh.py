import bpy
import numpy as np
import math

from bpy.types import Operator, Mesh, MeshLoopTriangle, Material, MeshLoop
from mathutils import Matrix

if __name__ == "__main__":
    import ssbh_data_py
else:
    from ... import ssbh_data_py

def export_mesh_ex(operator: Operator, mesh: Mesh) -> ssbh_data_py.mesh_data.MeshObjectData:
    """
    This mesh exporter will be reworked to not create any temporary meshes.
    Attempt to avoid using bmesh, as that has additional overhead.
    mesh.loop_triangles should have the data needed.
    blender has vertex-per-face normals that the user edits, so
    each vertex-per-face normal has to be split into 3 separate vertices,
    the 3 verts only differing in which normal they have.
    In addition, meshes in smash can only have one material that gets applied to the whole object, so 
    one blender mesh may result in several exported meshes.

    Blender stores its vertex-per-face data in "loops".
    smash only has support for vertex data, so in the case where one vertex corresponds to multiple "loops" with differing
    uvs or custom normals, multiple output verts need to be created.

    The plan is to go through each "loop triangle", which is the result of triangulating those "loops",
    since thats what we need to export since smash doesn't support non-tris.

    However, there are significantly more loops than vertices in a model, and
    as a result the final mesh will need to be optimized since outside of UV seams and split normals,
    most verts should have the same normals and same UV coords and so they can re-use the same vert.
    """

    return ssbh_data_py.mesh_data.MeshObjectData(
        name,
        sub_index
    )


def get_tris_per_material(mesh: Mesh) -> dict[Material, set[MeshLoopTriangle]]:
    tris: list[MeshLoopTriangle] = mesh.loop_triangles
    material_to_tris: dict[Material, set[MeshLoopTriangle]] = {material : set() for material in mesh.materials}
    for tri in tris:
        face_material = mesh.materials[tri.material_index]
        material_to_tris[face_material].add(tri)
    return material_to_tris

def get_verts_to_split(mesh: Mesh, tris: set[MeshLoopTriangle]) -> set[bpy.types.MeshVertex]:
    """
    Verts that need to be split due to multiple uv-coords or
    """
    for tri in tris:
        tri

def get_ssbh_mesh_from_mesh_loop_tris(mesh: Mesh, tris: set[MeshLoopTriangle], mesh_sub_index: int) -> ssbh_data_py.mesh_data.MeshObjectData:
    """
    each MeshLoopTriangle corresponds to three "loop vertices"
    To ensure proper export of vertex-per-face data, each "loop vertex" will be exported as
    separate vertices. 
    """
    # Not every loop in the mesh will be accessed, only the loops corresponding to the current material are needed.
    #used_loops: set[MeshLoop] = {mesh.loops[loop_index] for tri in tris for loop_index in tri.loops}
    # For now, just export every loop and cleanup the unused ones later
    used_loops = [loop for loop in mesh.loops]
    # TODO: Is there a better way to account for the change of coordinates?
    axis_correction = np.array(Matrix.Rotation(math.radians(90), 3, 'X'))
    
    # Each "loop" will be treated as a unique vertex for now.
    #positions = np.zeros(len(loops)*3, dtype=np.float32)
    positions = [mesh.vertices[loop.vertex_index].co for loop in used_loops]
    position0 = ssbh_data_py.mesh_data.AttributeData('Position0', positions @ axis_correction)

    # Since each loop was treated as a unique vertex
    vertex_indices = [loop_index for tri in tris for loop_index in tri.loops]

    # normal0 stuff
    normals = [loop.normal for loop in used_loops]
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
    test = [loop.tangent[:] @ axis_correction + [loop.bitangent_sign * -1.0] for loop in used_loops]
    tangent0 = ssbh_data_py.mesh_data.AttributeData('Tangent0', test)
    return ssbh_data_py.mesh_data.MeshObjectData(
        mesh.name,
        mesh_sub_index, 
        positions=[position0], 
        vertex_indices=vertex_indices,
        normals=[normal0],
        tangents=[tangent0])

def create_ssbh_mesh_modl_data_from_blender_mesh(mesh: Mesh) -> tuple[list[ssbh_data_py.mesh_data.MeshObjectData], list[ssbh_data_py.modl_data.ModlEntryData]]:
    """
    Since a smash mesh has one material applied to the whole mesh, blender meshes with multiple materials will result in
    multiple ssbh_meshes being created.
    """
    mesh.calc_loop_triangles()
    mesh.calc_normals_split()
    mesh.calc_tangents(uvmap="map1" if mesh.uv_layers.get("map1") else "")

    material_to_tris = get_tris_per_material(mesh)

    ssbh_meshes: list[ssbh_data_py.mesh_data.MeshObjectData] = []
    ssbh_modl_entries: list[ssbh_data_py.modl_data.ModlEntryData] = []
    subindex = 0
    for material, tris in material_to_tris.items():
        if tris: # Skips materials with no faces
            ssbh_meshes.append(get_ssbh_mesh_from_mesh_loop_tris(mesh, tris, subindex))
            ssbh_modl_entries.append(ssbh_data_py.modl_data.ModlEntryData(mesh.name, subindex, material.name))
            subindex += 1

    return ssbh_meshes, ssbh_modl_entries
        
# For testing, i copy paste this whole file into blender's scripting page then i hit run
# ssbh_data_py must be pip installed into blender's python before trying this.
# the line
def main():
    test_mesh = bpy.data.meshes['Cube']
    ssbh_meshes, ssbh_modl_entries = create_ssbh_mesh_modl_data_from_blender_mesh(test_mesh)

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

