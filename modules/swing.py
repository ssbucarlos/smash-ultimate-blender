import bpy

from .. import pyprc

from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty, FloatVectorProperty

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..properties import SubSceneProperties

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
            row.label(text='Please select an armature in the 3D viewport')
            return
        if context.object.type != 'ARMATURE' or \
           context.object.name not in context.view_layer.objects.selected:
            row = layout.row(align=True)
            row.label(text='Please select an armature in the 3D viewport')
            return

        row = layout.row(align=True)
        row.operator('sub.swing_import', icon='IMPORT')  
        row = layout.row(align=True)
        row.operator('sub.swing_export', icon='EXPORT')

class SUB_PT_swing_data_master(Panel):
    bl_label = "Ultimate Swing Data"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        arma = context.object

class SUB_PT_swing_data_swing_bones(Panel):
    bl_label = "Swing Bone Chains"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_swing_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
    
    def draw(self, context):
        return

class SUB_PT_swing_data_spheres(Panel):
    bl_label = "Spheres"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_swing_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
    
    def draw(self, context):
        return

class SUB_PT_swing_data_ovals(Panel):
    bl_label = "Ovals"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_swing_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
    
    def draw(self, context):
        return

class SUB_PT_swing_data_ellipsoids(Panel):
    bl_label = "Ellipsoids"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_swing_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
    
    def draw(self, context):
        return

class SUB_PT_swing_data_capsules(Panel):
    bl_label = "Capsules"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_swing_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
    
    def draw(self, context):
        return

class SUB_PT_swing_data_planes(Panel):
    bl_label = "Planes"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_swing_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
    
    def draw(self, context):
        return 

class SUB_PT_swing_data_connections(Panel):
    bl_label = "Connections"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_swing_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
    
    def draw(self, context):
        return 

class SUB_OP_swing_import(Operator):
    bl_idname = 'sub.swing_import'
    bl_label = 'Import swing.prc'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_export(Operator):
    bl_idname = 'sub.swing_export'
    bl_label = 'Export swing.prc'

    @classmethod
    def poll(cls, context):
        arma: bpy.types.Object = context.object
        if not arma:
            return False
        if arma.type != 'ARMATURE':
            return False
        ssd: SubSwingData = arma.data.sub_swing_data
        return len(ssd.swing_bone_chains) > 0

    def execute(self, context):
        return {'FINISHED'}

class Hash40(PropertyGroup):
    value: StringProperty(name='The cracked hash, or the raw hash in hex')

class SwingBoneParameters(PropertyGroup):
    air_resistance: FloatProperty(name='Air Resistance')
    water_resistance: FloatProperty(name='Water Resistance')
    min_angle_z: FloatProperty(name='Min Angle Z')
    max_angle_z: FloatProperty(name='Max Angle Z')
    min_angle_y: FloatProperty(name='Min Angle Y')
    max_angle_y: FloatProperty(name='Max Angle Y')
    collision_size_tip: FloatProperty(name='Collision Size Tip')
    collision_size_root: FloatProperty(name='Collision Size Root')
    friction_rate: FloatProperty(name='Friction Rate')
    goal_strength: FloatProperty(name='Goal Strength')
    unk_11: FloatProperty(name='0x0cc10e5d3a')
    local_gravity: FloatProperty(name='Local Gravity')
    fall_speed_scale: FloatProperty(name='Fall Speed Scale')
    ground_hit: BoolProperty(name='Ground Hit')
    wind_affect: FloatProperty(name='Wind Affect')
    collisions: CollectionProperty(type=Hash40)

class SwingBoneChain(PropertyGroup):
    name: StringProperty(name='SwingBoneChain Name Hash40')
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    swing_bones_parameters: CollectionProperty(type=SwingBoneParameters)
    is_skirt: BoolProperty(name='Is Skirt')
    rotate_order: IntProperty(name='Rotate Order')
    curve_rotate_x: BoolProperty(name='Curve Rotate X')
    unk_8: BoolProperty(name='0x0f7316a113')

class Sphere(PropertyGroup):
    name: StringProperty(name='Sphere Name Hash40')
    bone_name: StringProperty(name='Bone Name Hash40')
    offset: FloatVectorProperty(name='Offset', subtype='XYZ', size=3)
    radius: FloatProperty(name='Radius')

class Oval(PropertyGroup):
    name: StringProperty(name='Oval Name Hash40')
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    radius: FloatProperty(name='Radius')
    start_offset: FloatVectorProperty(name='Start Offset', subtype='XYZ', size=3)
    end_offset: FloatVectorProperty(name='End Offset', subtype='XYZ', size=3)

class Ellipsoid(PropertyGroup):
    name: StringProperty(name='Ellipoid Name Hash40')
    bone_name: StringProperty(name='BoneName Hash40')
    offset: FloatVectorProperty(name='Offset', subtype='XYZ', size=3)
    rotation: FloatVectorProperty(name='Rotation', subtype='XYZ', size=3)
    scale: FloatVectorProperty(name='Scale', subtype='XYZ', size=3)

class Capsule(PropertyGroup):
    name: StringProperty(name='Capsule Name Hash40')
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    start_offset: FloatVectorProperty(name='Start Offset', subtype='XYZ', size=3)
    end_offset: FloatVectorProperty(name='End Offset', subtype='XYZ', size=3)
    start_radius: FloatProperty(name='Start Radius')
    end_radius: FloatProperty(name='End Radius')

class Plane(PropertyGroup):
    name: StringProperty(name='Plane Name Hash40')
    bone_name: StringProperty(name='Bone Name Hash40')
    nx: FloatProperty(name='nx')
    ny: FloatProperty(name='ny')
    nz: FloatProperty(name='nz')
    distance: FloatProperty(name='d')

class Connection(PropertyGroup):
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    radius: FloatProperty(name='Radius')
    length: FloatProperty(name='Length')

class SubSwingData(PropertyGroup):
    swing_bone_chains: CollectionProperty(type=SwingBoneChain)
    spheres: CollectionProperty(type=Sphere)
    ovals: CollectionProperty(type=Oval)
    ellipsoids: CollectionProperty(type=Ellipsoid)
    capsules: CollectionProperty(type=Capsule)
    planes: CollectionProperty(type=Plane)
    connections: CollectionProperty(type=Connection)