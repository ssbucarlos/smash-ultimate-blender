import bpy
import bmesh
import math
import numpy
from math import sqrt, cos, sin, pi
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


