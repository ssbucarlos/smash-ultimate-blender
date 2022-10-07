import bpy
from properties import SubSceneProperties

from .. import pyprc

from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import CollectionProperty

class SUB_PT_swing_io(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Ultimate'
    bl_label = 'Swing'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ssp: SubSceneProperties = context.scene.sub_scene_properties
        layout = self.layout
        layout.use_property_split = False

        if not context.object:
            row = layout.row(align=True)
            row.label('Please select an armature in the 3D viewport')
            return
        if context.object.type != 'ARMATURE':
            row = layout.row(align=True)
            row.label('Please select an armature in the 3D viewport')
            return

        row = layout.row(align=True)
        row.operator('sub.swing_import', icon='IMPORT')  
        row = layout.row(align=True)
        row.operator('sub.swing_export', icon='EXPORT')

class SUB_OP_swing_import(Operator):
    bl_idname = 'sub.swing_import'
    bl_label = 'Import swing.prc'

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_export(Operator):
    bl_idname = 'sub.swing_import'
    bl_label = 'Import swing.prc'

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

class SwingBone(PropertyGroup):
    pass

class Sphere(PropertyGroup):
    pass

class Oval(PropertyGroup):
    pass

class Ellipsoid(PropertyGroup):
    pass

class Capsule(PropertyGroup):
    pass

class Plane(PropertyGroup):
    pass

class Connection(PropertyGroup):
    pass

class SubSwingData(PropertyGroup):
    swing_bones: CollectionProperty(type=SwingBone)
    spheres: CollectionProperty(type=Sphere)
    ovals: CollectionProperty(type=Oval)
    ellipsoids: CollectionProperty(type=Ellipsoid)
    capsules: CollectionProperty(type=Capsule)
    planes: CollectionProperty(type=Plane)
    connections: CollectionProperty(type=Connection)