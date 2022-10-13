import bpy
import bmesh
import math
import numpy
from math import sqrt, cos, sin, pi, radians
from bpy.types import Context, Operator
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
    
def make_capsule(object:bpy.types.Object, start_radius, end_radius, length):
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
    
    object.data.from_pydata(verts, edges, faces)

def make_capsule_object(context, name, start_radius, end_radius, length):
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    obj: bpy.types.Object = bpy.data.objects.new(mesh.name, mesh)
    make_capsule(obj, start_radius, end_radius, length)
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


