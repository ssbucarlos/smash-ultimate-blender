# BPY Imports
import bpy
from bpy.types import (
    PropertyGroup)
from bpy.props import (
    IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty, FloatVectorProperty)
# Core Library imports
import re
from math import(
    radians,)
# 3rd Party Imports
# Local Project Imports
from ..extras import create_meshes

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

def swing_bone_update(self, context):
    if self.blender_object is None:
        return
    if self.name == "":
        return
    try:
        arma: bpy.types.Armature = self.id_data
        bone = arma.bones[self.name]
        child_bone = bone.children[0]
        mesh_obj: bpy.types.Object = self.blender_object
    except:
        return
    else:
        create_meshes.make_capsule_mesh(
            mesh_obj,
            self.collision_size[0],
            self.collision_size[1],
            (0,0,0),
            (0,0,0),
            bone,
            child_bone,
            True
        )

class SUB_PG_swing_bone(PropertyGroup):
    air_resistance: FloatProperty(name='Air Resistance', default=1.0)
    water_resistance: FloatProperty(name='Water Resistance', default=1.0)
    #min_angle_z: FloatProperty(name='Min Angle Z')
    #max_angle_z: FloatProperty(name='Max Angle Z')
    angle_z: FloatVectorProperty(name='Angle Z Min/Max', size=2, unit='ROTATION', default=(radians(-180),radians(180)))
    #min_angle_y: FloatProperty(name='Min Angle Y')
    #max_angle_y: FloatProperty(name='Max Angle Y')
    angle_y: FloatVectorProperty(name='Angle X Min/Max', size=2, unit='ROTATION', default=(radians(-180),radians(180))) # Smash and blender have different primary bone axis (X & Y)
    #collision_size_tip: FloatProperty(name='Collision Size Tip')
    #collision_size_root: FloatProperty(name='Collision Size Root')
    collision_size: FloatVectorProperty(name='Collsion Size Head/Tail', size=2, unit='LENGTH', default=(1.0, 1.0), update=swing_bone_update)
    friction_rate: FloatProperty(name='Friction Rate', default=1.0)
    goal_strength: FloatProperty(name='Goal Strength', default=1.0)
    inertial_mass: FloatProperty(name='Mass', default=1.0)
    local_gravity: FloatProperty(name='Local Gravity', default=1.0)
    fall_speed_scale: FloatProperty(name='Fall Speed Scale', default=1.0)
    ground_hit: BoolProperty(name='Ground Hit', default=True)
    wind_affect: FloatProperty(name='Wind Affect', default=1.0)
    collisions: CollectionProperty(type=SUB_PG_swing_bone_collision)
    # Properties Below are for UI Only
    name: StringProperty(name='Swing Bone Name') # The swing.prc doesn't track individual bone names
    # Ok so it turns out bones cant be used for pointer props when made thru python
    #bone: PointerProperty(type=bpy.types.Bone) # Testing using pointer prop instead
    # Keep track of the mesh object
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Swing Bone Object',
    )
    active_collision_index: IntProperty(name='Active Collision Index', default=0, options={'HIDDEN'},) 

class SUB_PG_swing_bone_chain(PropertyGroup):
    name: StringProperty(name='SwingBoneChain Name Hash40', update=swing_bone_chain_name_update)
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    is_skirt: BoolProperty(name='Is Skirt')
    rotate_order: IntProperty(name='Rotate Order')
    curve_rotate_x: BoolProperty(name='Curve Rotate Y') # Smash and blender have different primary bone axis (X & Y)
    has_unk_8: BoolProperty(name='Has Unk 8', default=False)
    unk_8: IntProperty(name='0x0f7316a113', default=0)
    swing_bones: CollectionProperty(type=SUB_PG_swing_bone)
    # Properties below are for UI Only
    active_swing_bone_index: IntProperty(name='Active Bone Index', default=0, options={'HIDDEN'},)
    # Ok so it turns out bones cant be used for pointer props when made thru python
    # Testing Pointer Properties Instead
    #start_bone: PointerProperty(type=bpy.types.Bone)
    #end_bone: PointerProperty(type=bpy.types.Bone)

def swing_sphere_update(self, context):
    if self.blender_object is None:
        return
    if self.bone == "":
        return
    arma = self.id_data
    sphere_obj: bpy.types.Object = self.blender_object
    
    create_meshes.make_sphere_2(sphere_obj, self.radius, self.offset, arma.bones[self.bone])

def swing_oval_update(self, context):
    if self.blender_object is None:
        return
    if self.start_bone_name is None:
        return
    if self.end_bone_name is None:
        return
    
    arma_data: bpy.types.Armature = self.id_data
    oval_obj: bpy.types.Object = self.blender_object

    create_meshes.make_capsule_mesh(
        oval_obj,
        start_radius = self.radius,
        end_radius = self.radius,
        start_offset = self.start_offset,
        end_offset = self.end_offset,
        start_bone = arma_data.bones.get(self.start_bone_name),
        end_bone = arma_data.bones.get(self.end_bone_name),)

def swing_ellipsoid_update(self, context):
    if self.blender_object is None:
        return
    if self.bone_name == "":
        return
    arma = self.id_data
    ellipsoid_obj: bpy.types.Object = self.blender_object
    
    create_meshes.make_ellipsoid_mesh(ellipsoid_obj, self.offset, self.rotation, self.scale, arma.bones[self.bone_name])

class SUB_PG_swing_sphere(PropertyGroup):
    name: StringProperty(name='Sphere Name Hash40', update=collision_object_name_update)
    #bone_name: StringProperty(name='Bone Name Hash40')
    bone: StringProperty(
        name='Bone',
        description='The bone this sphere is attached to',
        update=swing_sphere_update,
    )
    offset: FloatVectorProperty(name='Offset', subtype='XYZ', size=3, update=swing_sphere_update)
    radius: FloatProperty(name='Radius', update=swing_sphere_update)
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Sphere Object',
    )

class SUB_PG_swing_oval(PropertyGroup):
    name: StringProperty(name='Oval Name Hash40', update=collision_object_name_update)
    start_bone_name: StringProperty(name='Start Bone Name Hash40', update=swing_oval_update)
    end_bone_name: StringProperty(name='End Bone Name Hash40', update=swing_oval_update)
    radius: FloatProperty(name='Radius', update=swing_oval_update)
    start_offset: FloatVectorProperty(name='Start Offset', subtype='XYZ', size=3, update=swing_oval_update)
    end_offset: FloatVectorProperty(name='End Offset', subtype='XYZ', size=3, update=swing_oval_update)
    # Store the blender object for optimization 
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Oval Object',
    )

class SUB_PG_swing_ellipsoid(PropertyGroup):
    name: StringProperty(name='Ellipoid Name Hash40', update=collision_object_name_update)
    bone_name: StringProperty(name='BoneName Hash40', update=swing_ellipsoid_update)
    offset: FloatVectorProperty(name='Offset', subtype='XYZ', size=3, update=swing_ellipsoid_update)
    rotation: FloatVectorProperty(name='Rotation', subtype='XYZ', size=3, update=swing_ellipsoid_update)
    scale: FloatVectorProperty(name='Scale', subtype='XYZ', size=3, update=swing_ellipsoid_update)
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Ellipse Object',
    )

def swing_capsule_update(self, context):
    if self.blender_object is None:
        return
    if self.start_bone_name == "":
        return
    if self.end_bone_name == "":
        return
    arma = self.id_data
    capsule_obj: bpy.types.Object = self.blender_object
    start_bone = arma.bones[self.start_bone_name]
    end_bone = arma.bones[self.end_bone_name]
    create_meshes.make_capsule_mesh(capsule_obj, self.start_radius, self.end_radius, self.start_offset, self.end_offset, start_bone, end_bone)

class SUB_PG_swing_capsule(PropertyGroup):
    name: StringProperty(name='Capsule Name Hash40', update=collision_object_name_update)
    start_bone_name: StringProperty(name='Start Bone Name Hash40', update=swing_capsule_update)
    end_bone_name: StringProperty(name='End Bone Name Hash40', update=swing_capsule_update)
    start_offset: FloatVectorProperty(name='Start Offset', subtype='XYZ', size=3, update=swing_capsule_update)
    end_offset: FloatVectorProperty(name='End Offset', subtype='XYZ', size=3, update=swing_capsule_update)
    start_radius: FloatProperty(name='Start Radius', update=swing_capsule_update)
    end_radius: FloatProperty(name='End Radius', update=swing_capsule_update)
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Capsule Object',
    )


def swing_plane_update(self, context):
    if self.blender_object is None:
        return
    if self.bone_name == "":
        return
    
    arma = self.id_data
    plane_obj = self.blender_object
    bone = arma.bones[self.bone_name]
    create_meshes.make_plane_mesh(plane_obj, bone, self.nx, self.ny, self.nz, self.distance)

class SUB_PG_swing_plane(PropertyGroup):
    name: StringProperty(name='Plane Name Hash40', update=collision_object_name_update)
    bone_name: StringProperty(name='Bone Name Hash40', update=swing_plane_update)
    nx: FloatProperty(name='nx', update=swing_plane_update)
    ny: FloatProperty(name='ny', update=swing_plane_update)
    nz: FloatProperty(name='nz', update=swing_plane_update)
    distance: FloatProperty(name='d', update=swing_plane_update)
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Plane Object',
    )

def swing_connection_update(self, context):
    if self.blender_object is None:
        return
    if self.start_bone_name == "":
        return
    if self.end_bone_name == "":
        return
    arma = self.id_data
    connection_obj: bpy.types.Object = self.blender_object
    start_bone = arma.bones[self.start_bone_name]
    end_bone = arma.bones[self.end_bone_name]
    create_meshes.make_connection_mesh(connection_obj, self.radius, start_bone, end_bone)

class SUB_PG_swing_connection(PropertyGroup):
    start_bone_name: StringProperty(name='Start Bone Name Hash40', update=swing_connection_update)
    end_bone_name: StringProperty(name='End Bone Name Hash40', update=swing_connection_update)
    radius: FloatProperty(name='Radius', update=swing_connection_update)
    length: FloatProperty(name='Length')
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Connection Object',
    )

# Armature.sub_swing_data
class SUB_PG_sub_swing_data(PropertyGroup):
    swing_bone_chains: CollectionProperty(type=SUB_PG_swing_bone_chain)
    spheres: CollectionProperty(type=SUB_PG_swing_sphere)
    ovals: CollectionProperty(type=SUB_PG_swing_oval)
    ellipsoids: CollectionProperty(type=SUB_PG_swing_ellipsoid)
    capsules: CollectionProperty(type=SUB_PG_swing_capsule)
    planes: CollectionProperty(type=SUB_PG_swing_plane)
    connections: CollectionProperty(type=SUB_PG_swing_connection)
    # Below are needed properties for UI
    active_swing_bone_chain_index: IntProperty(name='Active Swing Bone Chain Index', default=0, options={'HIDDEN'},)
    active_sphere_index: IntProperty(name='Active Sphere', default=0, options={'HIDDEN'},)
    active_oval_index: IntProperty(name='Active Oval', default=0, options={'HIDDEN'},)
    active_ellipsoid_index: IntProperty(name='Active Ellipsoid', default=0, options={'HIDDEN'},)
    active_capsule_index: IntProperty(name='Active Capsule', default=0, options={'HIDDEN'},)
    active_plane_index: IntProperty(name='Active Plane', default=0, options={'HIDDEN'},)
    active_connection_index: IntProperty(name='Active Connection', default=0, options={'HIDDEN'},)
    # Hack since prop_search doesn't allow filtering. Still doesn't work for the UI, but for operators it will
    armature_swing_bones: CollectionProperty(type=SUB_PG_armature_swing_bone)
    armature_swing_bone_children: CollectionProperty(type=SUB_PG_armature_swing_bone_children)

# Bone.sub_swing_blender_bone_data
# This is so the user can click on a swing bone in the scene and get info from it.
class SUB_PG_blender_bone_data(PropertyGroup):
    swing_bone_chain_index: IntProperty(
        name='Index of swing bone chain this bone belongs to',
        default= -1,
        options={'HIDDEN'},
    )
    swing_bone_index: IntProperty(
        name='Index of the swing bone data of this bone',
        default= -1,
        options={'HIDDEN'},
    )

# Mesh.sub_swing_blender_bone_data
# This is so the user can click on a swing mesh in the scene and get info from it.
collision_collection_types = (
    ('NONE', 'None', 'None'),
    ('SPHERE', 'Sphere', 'Sphere'),
    ('OVAL', 'Oval', 'Oval'),
    ('ELLIPSOID', 'Ellipsoid', 'Ellipsoid'),
    ('CAPSULE', 'Capsule', 'Capsule'),
    ('PLANE', 'Plane', 'Plane'),
    ('CONNECTION', 'Connection', 'Connection')
)
class SUB_PG_sub_swing_data_linked_mesh(PropertyGroup):
    is_swing_mesh: BoolProperty(
        name='Is this a smush_blender created swing mesh',
        default=False,
        options={'HIDDEN'}
    )
    collision_collection_type: EnumProperty(
        name='Collision Type',
        items=collision_collection_types,
        default='NONE',
    )
    collision_collection_index: IntProperty(
        name='collision_collection_index',
        default=0,
    )
    is_swing_bone_shape: BoolProperty(
        name='Is this representing a swing bone',
        default=False,
        options={'HIDDEN'}
    )
    swing_chain_index: IntProperty(
        name='collision_collection_index',
        default=0,
    )
    swing_bone_index: IntProperty(
        name='collision_collection_index',
        default=0,
    )

class SUB_PG_sub_swing_master_collection_props(PropertyGroup):
    linked_object: PointerProperty(
        name="The linked Armature",
        type=bpy.types.Object,
    )
    swing_chains_collection: PointerProperty(
        type=bpy.types.Collection,
    )
    collision_shapes_collection: PointerProperty(
        type=bpy.types.Collection,
    )
    spheres_collection: PointerProperty(
        type=bpy.types.Collection,
    )
    ovals_collection: PointerProperty(
        type=bpy.types.Collection,
    )
    ellipsoids_collection: PointerProperty(
        type=bpy.types.Collection,
    )
    capsules_collection: PointerProperty(
        type=bpy.types.Collection,
    )
    planes_collection: PointerProperty(
        type=bpy.types.Collection,
    )
    connections_collection: PointerProperty(
        type=bpy.types.Collection,
    )
    

