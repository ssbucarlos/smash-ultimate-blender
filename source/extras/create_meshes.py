import bpy
import bmesh
import math
import numpy
from math import sqrt, cos, sin, pi, radians
from mathutils import Vector, Matrix, Quaternion
from bpy.types import Context, Operator, Object, Bone, Mesh
from bpy.props import FloatProperty, StringProperty

def verts_from_circle(radius, samples, y):
    # x**2 + z**2 = radius**2
    # need to make the object using 'Y' up since bones in blender use 'Y' as primary axis
    verts: list[tuple[float, float, float]] = []
    theta = 2.0 * pi / samples
    for i in range(1, samples+1):
        x = radius * cos(theta * i)
        z = radius * sin(theta * i)
        verts.append((x,y,z))
    return verts
    
"""def make_capsule(object:bpy.types.Object, start_radius, end_radius, length, start_offset=Vector([0.0,0.0,0.0]), end_offset=Vector([0.0,0.0,0.0])):
    # TODO: Figure out offset
    start_verts = verts_from_circle(start_radius, 32, 0.0)
    end_verts = verts_from_circle(end_radius, 32, length)

    verts = start_verts + end_verts
    offset = len(start_verts)
    edges = [(i,i+1) for i in range(offset-1)]
    edges += [(0, len(start_verts) - 1)]
    edges += [(i, i+len(start_verts)) for i in range(offset)]
    edges += [(i, i+1) for i in range(offset, offset+len(end_verts)-1)]
    edges += [(offset, len(verts)-1)]
    faces = [[i for i in range(offset)]]
    faces += [[i + offset for i in range(offset)]]
    faces += [[i, i+1, i+offset+1, i+offset] for i in range(offset-1)]
    faces += [[offset-1, 0, offset, len(verts)-1]]
    
    object.data.from_pydata(verts, edges, faces)"""

def get_quat_to_point_source_to_target(source_bone: Bone, target_bone: Bone) -> Quaternion:
    distance_vec: Vector = target_bone.matrix_local.translation - source_bone.matrix_local.translation
    up_vec = Vector([0,1,0])
    cross = up_vec.cross(distance_vec)
    dot = up_vec.dot(distance_vec)
    w = up_vec.length * distance_vec.length + dot
    distance_vec_as_rotation_quat = Quaternion([w] + list(cross))
    distance_vec_as_rotation_quat.normalize()
    return distance_vec_as_rotation_quat

def make_capsule_mesh(obj: Object, start_radius, end_radius, start_offset, end_offset, start_bone: Bone, end_bone: Bone, skin_to_start_only=False):
    # Handle vertex groups
    if start_bone == end_bone:
        skin_to_start_only = True
    obj.vertex_groups.clear()
    obj.vertex_groups.new(name=start_bone.name)
    if not skin_to_start_only:
        obj.vertex_groups.new(name=end_bone.name)
    
    # Init bmesh
    bm = bmesh.new()
    deform_layer = bm.verts.layers.deform.verify()

    # Handle starting side
    start_verts = bmesh.ops.create_circle(bm, segments=16, radius=start_radius)
    # Rotate start verts so they face the end_bone so capsule can connect properly
    align_with_end_bone_quat = get_quat_to_point_source_to_target(start_bone, end_bone)
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(radians(90),4,'X'), verts=start_verts['verts'])
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(align_with_end_bone_quat.angle, 4, align_with_end_bone_quat.axis), verts=start_verts['verts'])
    bmesh.ops.translate(bm, vec=start_bone.matrix_local.translation, verts=start_verts['verts'])
    bmesh.ops.translate(bm, vec=start_offset, space=start_bone.matrix_local.inverted(), verts=start_verts['verts'])
    for v in start_verts['verts']:
        g = v[deform_layer]
        g[0] = 1.0

    # Handle ending side
    end_verts = bmesh.ops.create_circle(bm, segments=16, radius=end_radius)
    # Rotate end verts so they face the start_bone so capsule can connect properly
    align_with_start_bone_quat = get_quat_to_point_source_to_target(end_bone, start_bone)
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(radians(90),4,'X'), verts=end_verts['verts'])
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(align_with_start_bone_quat.angle, 4, align_with_start_bone_quat.axis), verts=end_verts['verts'])
    bmesh.ops.translate(bm, vec=end_bone.matrix_local.translation, verts=end_verts['verts'])
    bmesh.ops.translate(bm, vec=end_offset, space=end_bone.matrix_local.inverted(), verts=end_verts['verts'])

    for v in end_verts['verts']:
        g = v[deform_layer]
        if skin_to_start_only:
            g[0] = 1.0
        else:
            g[1] = 1.0
    bmesh.ops.bridge_loops(bm, edges=bm.edges[:])
    bm.to_mesh(obj.data)
    bm.free()

def make_connection_mesh(obj: Object, radius: float, start_bone: Bone, end_bone: Bone):
    # Handle vertex groups
    obj.vertex_groups.clear()
    obj.vertex_groups.new(name=start_bone.name)
    obj.vertex_groups.new(name=end_bone.name)

    # Connections seem to go from the end of the bone
    # By this point, the bone chains should be properly aligned
    start_bone_child = start_bone.children[0]
    end_bone_child = end_bone.children[0]

    # Init bmesh
    bm = bmesh.new()
    deform_layer = bm.verts.layers.deform.verify()

    # Handle starting side
    start_verts = bmesh.ops.create_circle(bm, segments=16, radius=radius)
    # Rotate start verts so they face the end_bone so capsule can connect properly
    align_with_end_bone_quat = get_quat_to_point_source_to_target(start_bone_child, end_bone_child)
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(radians(90),4,'X'), verts=start_verts['verts'])
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(align_with_end_bone_quat.angle, 4, align_with_end_bone_quat.axis), verts=start_verts['verts'])
    bmesh.ops.translate(bm, vec=start_bone_child.matrix_local.translation, verts=start_verts['verts'])
    
    # Handle ending side
    end_verts = bmesh.ops.create_circle(bm, segments=16, radius=radius)
    # Rotate end verts so they face the start_bone so capsule can connect properly
    align_with_start_bone_quat = get_quat_to_point_source_to_target(end_bone_child, start_bone_child)
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(radians(90),4,'X'), verts=end_verts['verts'])
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(align_with_start_bone_quat.angle, 4, align_with_start_bone_quat.axis), verts=end_verts['verts'])
    bmesh.ops.translate(bm, vec=end_bone_child.matrix_local.translation, verts=end_verts['verts'])
    
    # Assign weights
    for v in start_verts['verts']:
        g = v[deform_layer]
        g[0] = 1.0
    for v in end_verts['verts']:
        g = v[deform_layer]
        g[1] = 1.0

    # Connect Ends
    bmesh.ops.bridge_loops(bm, edges=bm.edges[:])

    # Finalize
    bm.to_mesh(obj.data)
    bm.free()

def make_connection_obj(connection_name, radius, start_bone, end_bone):
    mesh: bpy.types.Mesh = bpy.data.meshes.new(connection_name)
    obj: bpy.types.Object = bpy.data.objects.new(mesh.name, mesh)
    make_connection_mesh(obj, radius, start_bone, end_bone)
    return obj

def make_capsule_object(name, start_radius, end_radius, start_offset, end_offset, start_bone, end_bone, skin_to_start_only=False):
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    obj: bpy.types.Object = bpy.data.objects.new(mesh.name, mesh)
    obj.vertex_groups.new(name=end_bone.name)
    make_capsule_mesh(obj, start_radius, end_radius, start_offset, end_offset, start_bone, end_bone, skin_to_start_only)
    return obj

def make_sphere_2(obj: bpy.types.Object, radius, offset, bone: bpy.types.Bone):
    mesh = obj.data
    obj.vertex_groups.clear()
    obj.vertex_groups.new(name=bone.name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=radius)
    bm.transform(Matrix.Translation(offset))
    bm.transform(bone.matrix_local)
    deform_layer = bm.verts.layers.deform.verify()
    for v in bm.verts:
        g = v[deform_layer]
        g[0] = 1.0
    bm.to_mesh(mesh)
    bm.free()

def make_sphere_object_2(name:str, radius: float, offset: tuple[float, float, float], bone: bpy.types.Bone):
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    obj: bpy.types.Object = bpy.data.objects.new(mesh.name, mesh)
    make_sphere_2(obj, radius, offset, bone)
    return obj

def make_sphere(object:bpy.types.Object, radius, offset):
    start_theta = radians(270)
    theta_step = pi / 16
    verts = [(0, -radius, 0)] # Bottom Pole
    for iteration in range(1,16): # Dont make the top or bottom or sphere
        theta = start_theta + theta_step * iteration
        circle_radius = radius * cos(theta)
        circle_y_offset = radius * sin(theta)
        verts += verts_from_circle(circle_radius, 32, circle_y_offset)
    verts += [(0, radius, 0)] # Top Pole
    for index, v in enumerate(verts):
        x,y,z = v
        x += offset[0]
        y += offset[1]
        z += offset[2]
        verts[index] = (x,y,z)
    edges = []
    for circle_index in range (0,15):
        edges+= [(1 + (circle_index*32) + vi, 1 + (circle_index*32) + vi + 1) for vi in range(0,31)]
        edges+= [(1 + (circle_index*32), 1 + (circle_index*32) + 31)]
    faces = []
    for circle_index in range (0,14):
        faces+= [(1 + (circle_index*32) + vi, 1 + (circle_index*32) + vi + 32,
                  1 + (circle_index*32) + vi + 33, 1 + (circle_index*32) + vi + 1)
                  for vi in range(0,31)]
        faces+= [(1 + (circle_index*32) + 0, 1 + (circle_index*32) + 31, 
                  1 + (circle_index*32) + 32 + 31, 1 + (circle_index*32) + 32, )]
    faces += [(0, 1 + vi, 1 + vi + 1) for vi in range (0,31)] # Faces for bottom fan
    faces += [(0, 32, 1)]
    final = len(verts) - 1
    faces += [(final, final - 32 + vi + 1, final - 32 + vi) for vi in range(0,31)] # Faces for top fan
    faces += [(final, final - 32, final - 1)]    
    object.data.from_pydata(verts, edges, faces)

def make_sphere_object(name, radius, offset=[0,0,0]):
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    obj: bpy.types.Object = bpy.data.objects.new(mesh.name, mesh)
    make_sphere(obj, radius, offset)
    return obj

"""def make_ellipsoid_object(name, radius=1.0, offset=Vector([0.0,0.0,0.0]), rotation=Vector([0.0,0.0,0.0]), scale=Vector([1.0,1.0,1.0])):
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    obj: bpy.types.Object = bpy.data.objects.new(mesh.name, mesh)
    make_sphere(obj, radius, Vector([0.0, 0.0, 0.0]))
    obj_data: bpy.types.Mesh = obj.data
    vert: bpy.types.MeshVertex
    for vert in obj_data.vertices:
        co: Vector = vert.co.copy()
        vert.co = ((co.x*scale.x , co.y*scale.y, co.z*scale.z))
    rmx = Matrix.Rotation(radians(rotation.x), 3, 'X')
    rmy = Matrix.Rotation(radians(rotation.y), 3, 'Y')
    rmz = Matrix.Rotation(radians(rotation.z), 3, 'Z')
    # TODO Is this the right order?
    rm  = rmy @ rmx @ rmz  # Assuming that smash uses 'XYZ' rotation order, that corresponds to blender 'YXZ' order
    for vert in obj_data.vertices:
        co: Vector = vert.co.copy()
        vert.co = rm @ co
    for vert in obj_data.vertices:
        co: Vector = vert.co.copy()
        vert.co = ((co.x+offset.x, co.y+offset.y, co.z+offset.z))
    return obj"""

def make_ellipsoid_mesh(obj, offset, rotation, scale, bone):
    mesh = obj.data
    obj.vertex_groups.clear()
    obj.vertex_groups.new(name=bone.name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    tm = Matrix.Translation(offset)
    rq = Quaternion([radians(angle) for angle in rotation])
    rm = Matrix.Rotation(rq.angle, 4, rq.axis)
    sm = Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
    mat = Matrix(tm @ rm @ sm) 
    bm.transform(mat)
    bm.transform(bone.matrix_local)
    deform_layer = bm.verts.layers.deform.verify()
    for v in bm.verts:
        g = v[deform_layer]
        g[0] = 1.0
    bm.to_mesh(mesh)
    bm.free()

def make_ellipsoid_object(name, offset, rotation, scale, bone):
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    obj: bpy.types.Object = bpy.data.objects.new(mesh.name, mesh)
    make_ellipsoid_mesh(obj, offset, rotation, scale, bone)
    return obj

def make_plane_mesh(obj: Object, bone: Bone, nx: float, ny: float, nz: float, d: float):
    # Handle vertex groups
    obj.vertex_groups.clear()
    obj.vertex_groups.new(name=bone.name)

    # Init bmesh
    bm = bmesh.new()
    deform_layer = bm.verts.layers.deform.verify()

    # Create Plane
    geom = bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=4)
    
    # Calculate needed rotation
    up_vec = Vector([0,1,0])
    goal_normal = Vector([nx, ny, nz])
    goal_normal.normalize()
    cross = up_vec.cross(goal_normal)
    dot = up_vec.dot(goal_normal)
    w = up_vec.length * goal_normal.length + dot
    rotation = Quaternion([w] + list(cross))
    rotation.normalize()
    
    # The plane normal is from the bone's space
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(radians(90),4,'X'), verts=geom['verts'])
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(rotation.angle, 4, rotation.axis), verts=geom['verts'])
    bmesh.ops.transform(bm, matrix=bone.matrix_local, verts=geom['verts'])
    bmesh.ops.translate(bm, vec=d*goal_normal, space=bone.matrix_local.inverted(), verts=geom['verts'])
    
    # Assign weights
    for v in geom['verts']:
        g = v[deform_layer]
        g[0] = 1.0

    # Finalize
    bm.to_mesh(obj.data)
    bm.free()

def make_plane_object(name: str, bone: Bone, nx: float, ny: float, nz: float, d: float):
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    obj: bpy.types.Object = bpy.data.objects.new(mesh.name, mesh)

    make_plane_mesh(obj, bone, nx, ny, nz, d)
    return obj
"""
class SUB_OP_make_capsule(Operator):
    bl_idname = 'sub.make_capsule'
    bl_label = 'Add Capsule'

    start_radius: FloatProperty(
        name='Start Radius',
        default=1.0,
        unit='LENGTH',
    )

    end_radius: FloatProperty(
        name='End Radius',
        default=1.0,
        unit='LENGTH',
    )

    length: FloatProperty(
        name='Length',
        default=1.0,
        unit='LENGTH',
    )

    name: StringProperty(
        name='Capsule Name',
    )

    def execute(self, context: Context):
        mesh: bpy.types.Mesh = bpy.data.meshes.new(self.name)
        obj: bpy.types.Object = bpy.data.objects.new(mesh.name, mesh)
        context.collection.objects.link(obj)
        make_capsule(obj, self.start_radius, self.end_radius, self.length)
        return {'FINISHED'}
"""