import bpy
# BPY Imports
from bpy.types import (
    PropertyGroup)
from bpy.props import (
    IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty, FloatVectorProperty)
# Core Library imports
import re
# 3rd Party Imports
# Local Project Imports


def get_unique_name_for_entry_in_collection_property(entry, collection) -> str:
    other_names: set[str] = {e.name for e in collection if e.as_pointer() != entry.as_pointer()}
    
    if entry.name not in other_names:
        return entry.name
    
    regex = r"(\w+)\.(\d{3})"
    matches = re.match(regex, entry.name)
    if matches is None:
        base_name = entry.name
        number = 1
    else:
        base_name = matches.groups()[0]
        number = int(matches.groups()[1])
    
    for number in range(number, 1000):
        new_name = f'{base_name}.{number:003d}'
        if new_name not in other_names:
            return new_name
     
    raise ValueError("Over 1000 duplicate names, this can't be right...")
    
def is_entry_name_unique_in_collection_property(entry, collection) -> bool:
    other_names: set[str] = {e.name for e in collection if e.as_pointer() != entry.as_pointer()}

    return entry.name not in other_names

def swing_bone_chain_name_update(self, context):
    sub_swing_data: SUB_PG_sub_swing_data = context.object.data.sub_swing_data

    if is_entry_name_unique_in_collection_property(self, sub_swing_data.swing_bone_chains):
       return 
    
    self.name = get_unique_name_for_entry_in_collection_property(self, sub_swing_data.swing_bone_chains)


class SUB_PG_armature_swing_bone(PropertyGroup):
    name: StringProperty('Armature Swing Bone Name')
class SUB_PG_armature_swing_bone_children(PropertyGroup):
    name: StringProperty('Armature Swing Bone Child Name')

def collision_object_name_update(self, context):
    ssd: SUB_PG_sub_swing_data = context.object.data.sub_swing_data
    collision: SUB_PG_swing_bone_collision

    # Need to make sure the name isn't used by other collision objects.
    collision_collections = [
        ssd.spheres,
        ssd.ovals,
        ssd.ellipsoids,
        ssd.capsules,
        ssd.planes,
    ]
    collision_names = [col.name for col_collection in collision_collections for col in col_collection if col.as_pointer() != self.as_pointer()]
    if self.name in collision_names:
        regex = r"(\w+\.)(\d+)"
        matches = re.match(regex, self.name)
        if matches is None:
            self.name = self.name + '.001'
        else:
            base_name = matches.groups()[0]
            number = int(matches.groups()[1])
            self.name = f'{base_name}{number+1:003d}'
         
collision_types = (
    ('SPHERE', 'Sphere', 'Sphere'),
    ('OVAL', 'Oval', 'Oval'),
    ('ELLIPSOID', 'Ellipsoid', 'Ellipsoid'),
    ('CAPSULE', 'Capsule', 'Capsule'),
    ('PLANE', 'Plane', 'Plane'),
)

class SUB_PG_swing_bone_collision(PropertyGroup):
    # target_collision_name: StringProperty(name='The cracked hash of the collision name if possible, otherwise the raw hash')
    # New idea, instead of storing the collision name, store the collision sub-type and index
    collision_type: EnumProperty(
        name='Collision Type',
        items=collision_types,
        default='SPHERE',
    )
    collision_index: IntProperty(
        name='Collision Index',
        default=0,
    )

class SUB_PG_swing_bone(PropertyGroup):
    air_resistance: FloatProperty(name='Air Resistance')
    water_resistance: FloatProperty(name='Water Resistance')
    #min_angle_z: FloatProperty(name='Min Angle Z')
    #max_angle_z: FloatProperty(name='Max Angle Z')
    angle_z: FloatVectorProperty(name='Angle Z Min/Max', size=2, unit='ROTATION')
    #min_angle_y: FloatProperty(name='Min Angle Y')
    #max_angle_y: FloatProperty(name='Max Angle Y')
    angle_y: FloatVectorProperty(name='Angle Y Min/Max', size=2, unit='ROTATION')
    #collision_size_tip: FloatProperty(name='Collision Size Tip')
    #collision_size_root: FloatProperty(name='Collision Size Root')
    collision_size: FloatVectorProperty(name='Collsion Size Head/Tail', size=2, unit='LENGTH')
    friction_rate: FloatProperty(name='Friction Rate')
    goal_strength: FloatProperty(name='Goal Strength')
    unk_11: FloatProperty(name='0x0cc10e5d3a')
    local_gravity: FloatProperty(name='Local Gravity')
    fall_speed_scale: FloatProperty(name='Fall Speed Scale')
    ground_hit: BoolProperty(name='Ground Hit')
    wind_affect: FloatProperty(name='Wind Affect')
    collisions: CollectionProperty(type=SUB_PG_swing_bone_collision)
    # Properties Below are for UI Only
    name: StringProperty(name='Swing Bone Name') # The swing.prc doesn't track individual bone names
    # Ok so it turns out bones cant be used for pointer props when made thru python
    #bone: PointerProperty(type=bpy.types.Bone) # Testing using pointer prop instead
   
    active_collision_index: IntProperty(name='Active Collision Index', default=0) 

class SUB_PG_swing_bone_chain(PropertyGroup):
    name: StringProperty(name='SwingBoneChain Name Hash40', update=swing_bone_chain_name_update)
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    is_skirt: BoolProperty(name='Is Skirt')
    rotate_order: IntProperty(name='Rotate Order')
    curve_rotate_x: BoolProperty(name='Curve Rotate X')
    has_unk_8: BoolProperty(name='Has Unk 8', default=False)
    unk_8: IntProperty(name='0x0f7316a113', default=0)
    swing_bones: CollectionProperty(type=SUB_PG_swing_bone)
    # Properties below are for UI Only
    active_swing_bone_index: IntProperty(name='Active Bone Index', default=0)
    # Ok so it turns out bones cant be used for pointer props when made thru python
    # Testing Pointer Properties Instead
    #start_bone: PointerProperty(type=bpy.types.Bone)
    #end_bone: PointerProperty(type=bpy.types.Bone)

class SUB_PG_swing_sphere(PropertyGroup):
    name: StringProperty(name='Sphere Name Hash40', update=collision_object_name_update)
    #bone_name: StringProperty(name='Bone Name Hash40')
    bone: StringProperty(
        name='Bone',
        description='The bone this sphere is attached to',
    )
    offset: FloatVectorProperty(name='Offset', subtype='XYZ', size=3)
    radius: FloatProperty(name='Radius')
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Sphere Object',
    )

class SUB_PG_swing_oval(PropertyGroup):
    name: StringProperty(name='Oval Name Hash40', update=collision_object_name_update)
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    radius: FloatProperty(name='Radius')
    start_offset: FloatVectorProperty(name='Start Offset', subtype='XYZ', size=3)
    end_offset: FloatVectorProperty(name='End Offset', subtype='XYZ', size=3)
    # Store the blender object for optimization 
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Oval Object',
    )

class SUB_PG_swing_ellipsoid(PropertyGroup):
    name: StringProperty(name='Ellipoid Name Hash40', update=collision_object_name_update)
    bone_name: StringProperty(name='BoneName Hash40')
    offset: FloatVectorProperty(name='Offset', subtype='XYZ', size=3)
    rotation: FloatVectorProperty(name='Rotation', subtype='XYZ', size=3)
    scale: FloatVectorProperty(name='Scale', subtype='XYZ', size=3)
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Ellipse Object',
    )


class SUB_PG_swing_capsule(PropertyGroup):
    name: StringProperty(name='Capsule Name Hash40', update=collision_object_name_update)
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    start_offset: FloatVectorProperty(name='Start Offset', subtype='XYZ', size=3)
    end_offset: FloatVectorProperty(name='End Offset', subtype='XYZ', size=3)
    start_radius: FloatProperty(name='Start Radius')
    end_radius: FloatProperty(name='End Radius')
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Capsule Object',
    )

class SUB_PG_swing_plane(PropertyGroup):
    name: StringProperty(name='Plane Name Hash40', update=collision_object_name_update)
    bone_name: StringProperty(name='Bone Name Hash40')
    nx: FloatProperty(name='nx')
    ny: FloatProperty(name='ny')
    nz: FloatProperty(name='nz')
    distance: FloatProperty(name='d')
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Plane Object',
    )

class SUB_PG_swing_connection(PropertyGroup):
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    radius: FloatProperty(name='Radius')
    length: FloatProperty(name='Length')
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Connection Object',
    )

class SUB_PG_sub_swing_data(PropertyGroup):
    swing_bone_chains: CollectionProperty(type=SUB_PG_swing_bone_chain)
    spheres: CollectionProperty(type=SUB_PG_swing_sphere)
    ovals: CollectionProperty(type=SUB_PG_swing_oval)
    ellipsoids: CollectionProperty(type=SUB_PG_swing_ellipsoid)
    capsules: CollectionProperty(type=SUB_PG_swing_capsule)
    planes: CollectionProperty(type=SUB_PG_swing_plane)
    connections: CollectionProperty(type=SUB_PG_swing_connection)
    # Below are needed properties for UI
    active_swing_bone_chain_index: IntProperty(name='Active Swing Bone Chain Index', default=0)
    active_sphere_index: IntProperty(name='Active Sphere', default=0)
    active_oval_index: IntProperty(name='Active Oval', default=0)
    active_ellipsoid_index: IntProperty(name='Active Ellipsoid', default=0)
    active_capsule_index: IntProperty(name='Active Capsule', default=0)
    active_plane_index: IntProperty(name='Active Plane', default=0)
    active_connection_index: IntProperty(name='Active Connection', default=0)
    # Hack since prop_search doesn't allow filtering. Still doesn't work for the UI, but for operators it will
    armature_swing_bones: CollectionProperty(type=SUB_PG_armature_swing_bone)
    armature_swing_bone_children: CollectionProperty(type=SUB_PG_armature_swing_bone_children)

# This is for UI only
class SUB_PG_blender_bone_data(PropertyGroup):
    swing_bone_chain_index: IntProperty(
        name='Index of swing bone chain this bone belongs to',
        default= -1,
    )
    swing_bone_index: IntProperty(
        name='Index of the swing bone data of this bone',
        default= -1,
    )
