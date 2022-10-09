import bpy

from .. import pyprc

from bpy.types import Panel, Operator, PropertyGroup, Context, UIList
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty, FloatVectorProperty
from math import radians
from pathlib import Path
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

class SUB_PT_swing_bone_chains(Panel):
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
        layout = self.layout
        sub_swing_data: SubSwingData = context.object.data.sub_swing_data
        col = layout.column()
        row = col.row()
        split = row.split(factor=.33)
        c = split.column()
        c.label(text='Swing Bone Chains')
        c.template_list(
            "SUB_UL_swing_bone_chains",
            "",
            sub_swing_data,
            "swing_bone_chains",
            sub_swing_data,
            "active_swing_bone_chain_index",
            rows=5,
            maxrows=5,
            )
        split = split.split(factor=.5)
        c = split.column()
        c.label(text='Swing Bones')
        if len(sub_swing_data.swing_bone_chains) > 0:
            active_swing_bone_chain = sub_swing_data.swing_bone_chains[sub_swing_data.active_swing_bone_chain_index]
            c.template_list(
                'SUB_UL_swing_bones',
                '',
                active_swing_bone_chain,
                'swing_bones',
                active_swing_bone_chain,
                'active_swing_bone_index',
                rows=5,
                maxrows=5,
            )        
        else:
            c.enabled = False
        
        split = split.split()
        c = split.column()
        c.enabled = False
        c.label(text="Bone's Collisions")
        if len(sub_swing_data.swing_bone_chains) > 0:
            if len(active_swing_bone_chain.swing_bones) > 0:
                active_swing_bone: SwingBone = active_swing_bone_chain.swing_bones[active_swing_bone_chain.active_swing_bone_index]
                if len(active_swing_bone.collisions) > 0:
                    c.template_list(
                        'SUB_UL_swing_bone_collisions',
                        '',
                        active_swing_bone,
                        'collisions',
                        active_swing_bone,
                        'active_collision_index',
                        rows=5,
                        maxrows=5,
                    )
                    c.enabled = True

        # Button Row, composed of 3 Sub Rows algined with the above columns
        row = layout.row()
        # Sub Row 1
        split = row.split(factor=.33)
        sr = split.row(align=True)
        sr.operator(SUB_OP_swing_bone_chain_add.bl_idname, text='+')
        sr.operator(SUB_OP_swing_bone_chain_remove.bl_idname, text='-')
        # Sub Row 2
        split = split.split(factor=.5)
        sr = split.row(align=True)
        sr.operator(SUB_OP_swing_bone_chain_length_edit.bl_idname, text='Edit Chain Start/End')
        # Sub Row 3
        split = split.split()
        sr = split.row(align=True)
        sr.operator(SUB_OP_swing_bone_collision_add.bl_idname, text='+')
        sr.operator(SUB_OP_swing_bone_collision_remove.bl_idname, text='-')  

        # Swing Bone Chain & Bone Info Area
        if len(sub_swing_data.swing_bone_chains) == 0:
            return
        active_swing_bone_chain: SwingBoneChain = sub_swing_data.swing_bone_chains[sub_swing_data.active_swing_bone_chain_index]
        if len(active_swing_bone_chain.swing_bones) == 0:
            return
        active_swing_bone: SwingBone = active_swing_bone_chain.swing_bones[active_swing_bone_chain.active_swing_bone_index]

        row = layout.row()
        split = row.split(factor=.5)
        c = split.column()
        c.label(text='Bone Chain Info')
        c.prop(active_swing_bone_chain, 'is_skirt')
        c.prop(active_swing_bone_chain, 'rotate_order')
        c.prop(active_swing_bone_chain, 'curve_rotate_x')
        c.prop(active_swing_bone_chain, 'unk_8')
        split = split.split()
        c = split.column()
        c.label(text='Bone Info')
        c.prop(active_swing_bone, 'air_resistance')
        c.prop(active_swing_bone, 'water_resistance')
        c.prop(active_swing_bone, 'angle_z')
        c.prop(active_swing_bone, 'angle_y')
        c.prop(active_swing_bone, 'collision_size')
        c.prop(active_swing_bone, 'friction_rate')
        c.prop(active_swing_bone, 'goal_strength')
        c.prop(active_swing_bone, 'unk_11')
        c.prop(active_swing_bone, 'local_gravity')
        c.prop(active_swing_bone, 'fall_speed_scale')
        c.prop(active_swing_bone, 'ground_hit')
        c.prop(active_swing_bone, 'wind_affect')
        return



class SUB_UL_swing_bone_chains(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_UL_swing_bones(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_UL_swing_bone_collisions(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "target_collision_name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_OP_swing_bone_chain_add(Operator):
    bl_idname = 'sub.swing_bone_chain_add'
    bl_label = 'Add Swing Bone Chain'

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_bone_chain_remove(Operator):
    bl_idname = 'sub.swing_bone_chain_remove'
    bl_label = 'Remove Swing Bone Chain'

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_bone_chain_length_edit(Operator):
    bl_idname = 'sub.swing_bone_chain_length_edit'
    bl_label = 'Edit Start/End of Swing Bone Chain'

    def execute(self, context):
        return {'FINISHED'}  

class SUB_OP_swing_bone_collision_add(Operator):
    bl_idname = 'sub.swing_bone_collision_add'
    bl_label = 'Add Swing Bone Collision'

    def execute(self, context):
        return {'FINISHED'}  

class SUB_OP_swing_bone_collision_remove(Operator):
    bl_idname = 'sub.swing_bone_collision_remove'
    bl_label = 'Remove Swing Bone Collision'

    def execute(self, context):
        return {'FINISHED'}    

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

    filter_glob: StringProperty(
        default='*.prc',
        options={'HIDDEN'},
    )

    filepath: StringProperty(subtype='FILE_PATH')

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def invoke(self, context, _event):
        self.filepath = ''
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        swing_import(self, context, self.filepath)
        return {'FINISHED'}

def struct_get(param_struct, input, fallback=None):
    return dict(param_struct).get(pyprc.hash(input), fallback)

def struct_get_str(param_struct, input):
    h = struct_get(param_struct, input)
    return str(h.value) if h is not None else None 

def struct_get_val(param_struct, input):
    r = struct_get(param_struct, input)
    return r.value if r is not None else None

def swing_import(operator: Operator, context: Context, filepath: str):
    arma_data: bpy.types.Armature = context.object.data
    ssd: SubSwingData = arma_data.sub_swing_data
    prc_root = pyprc.param(filepath)
    labels_path = (Path(__file__).parent.parent / 'pyprc' / 'ParamLabels.csv').resolve()
    pyprc.hash.load_labels(str(labels_path))
    try:
        prc_swing_bone_chains = list(dict(prc_root).get(pyprc.hash('swingbones')))
    except:
        operator.report({'ERROR'}, 'No "swingbones" list in the prc!')
        return
    
    for chain in prc_swing_bone_chains:
        new_chain: SwingBoneChain = ssd.swing_bone_chains.add()
        new_chain.name            = struct_get_str(chain, 'name')
        new_chain.start_bone_name = struct_get_str(chain, 'start_bonename')
        new_chain.end_bone_name   = struct_get_str(chain, 'end_bonename')
        new_chain.is_skirt        = struct_get_val(chain, 'isskirt')
        new_chain.rotate_order    = struct_get_val(chain, 'rotateorder')
        new_chain.curve_rotate_x  = struct_get_val(chain, 'curverotatex')
        new_chain.unk_8           = struct_get_val(chain, 0x0f7316a113)
        for prc_swing_bone_parameters in list(struct_get(chain, 'params')):
            new_swing_bone: SwingBone           = new_chain.swing_bones.add()
            new_swing_bone.air_resistance       = struct_get_val(prc_swing_bone_parameters, 'airresistance')
            new_swing_bone.water_resistance     = struct_get_val(prc_swing_bone_parameters, 'waterresistance')
            #new_swing_bone.min_angle_z          = struct_get_val(prc_swing_bone_parameters, 'minanglez')
            #new_swing_bone.max_angle_z          = struct_get_val(prc_swing_bone_parameters, 'maxanglez')
            new_swing_bone.angle_z[0]           = radians(struct_get_val(prc_swing_bone_parameters, 'minanglez'))
            new_swing_bone.angle_z[1]           = radians(struct_get_val(prc_swing_bone_parameters, 'maxanglez'))
            #new_swing_bone.min_angle_y          = struct_get_val(prc_swing_bone_parameters, 'minangley')
            #new_swing_bone.max_angle_y          = struct_get_val(prc_swing_bone_parameters, 'maxangley')
            new_swing_bone.angle_y[0]           = radians(struct_get_val(prc_swing_bone_parameters, 'minangley'))
            new_swing_bone.angle_y[1]           = radians(struct_get_val(prc_swing_bone_parameters, 'maxangley'))
            #new_swing_bone.collision_size_tip   = struct_get_val(prc_swing_bone_parameters, 'collisionsizetip')
            #new_swing_bone.collision_size_root  = struct_get_val(prc_swing_bone_parameters, 'collisionsizeroot')
            new_swing_bone.collision_size[0]    = struct_get_val(prc_swing_bone_parameters, 'collisionsizeroot')
            new_swing_bone.collision_size[1]    = struct_get_val(prc_swing_bone_parameters, 'collisionsizetip')
            new_swing_bone.friction_rate        = struct_get_val(prc_swing_bone_parameters, 'frictionrate')
            new_swing_bone.goal_strength        = struct_get_val(prc_swing_bone_parameters, 'goalstrength')
            new_swing_bone.unk_11               = struct_get_val(prc_swing_bone_parameters, 0x0cc10e5d3a)
            new_swing_bone.local_gravity        = struct_get_val(prc_swing_bone_parameters, 'localgravity')
            new_swing_bone.fall_speed_scale     = struct_get_val(prc_swing_bone_parameters, 'fallspeedscale')
            new_swing_bone.ground_hit           = struct_get_val(prc_swing_bone_parameters, 'groundhit')
            new_swing_bone.wind_affect          = struct_get_val(prc_swing_bone_parameters, 'windaffect')
            for prc_swing_bone_collision in list(struct_get(prc_swing_bone_parameters, 'collisions')):
                new_swing_bone_collision: SwingBoneCollision   = new_swing_bone.collisions.add()
                new_swing_bone_collision.target_collision_name = str(prc_swing_bone_collision.value)
    hash_to_blender_bone = {str(pyprc.hash(bone.name.lower())) : bone for bone in arma_data.bones}
    swing_bone_chains: list[SwingBoneChain] = ssd.swing_bone_chains
    for swing_bone_chain in swing_bone_chains:
        starting_blender_bone = arma_data.bones.get(swing_bone_chain.start_bone_name, None) 
        if starting_blender_bone is None:
            starting_blender_bone = hash_to_blender_bone.get(str(pyprc.hash(swing_bone_chain.start_bone_name)))
        if starting_blender_bone is not None:
            current_blender_bone = starting_blender_bone
            for swing_bone in swing_bone_chain.swing_bones:
                swing_bone.name = current_blender_bone.name
                current_blender_bone = current_blender_bone.children[0]
        else:
            for index, swing_bone in enumerate(swing_bone_chain.swing_bones):
                swing_bone.name = f'Bone {index+1}'

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

class SwingBoneCollision(PropertyGroup):
    target_collision_name: StringProperty(name='The cracked hash of the collision name if possible, otherwise the raw hash')

class SwingBone(PropertyGroup):
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
    collisions: CollectionProperty(type=SwingBoneCollision)
    # Properties Below are for UI Only
    name: StringProperty(name='Swing Bone Name') # The swing.prc doesn't track individual bone names
    active_collision_index: IntProperty(name='Active Collision Index', default=0) 

class SwingBoneChain(PropertyGroup):
    name: StringProperty(name='SwingBoneChain Name Hash40')
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    is_skirt: BoolProperty(name='Is Skirt')
    rotate_order: IntProperty(name='Rotate Order')
    curve_rotate_x: BoolProperty(name='Curve Rotate X')
    unk_8: IntProperty(name='0x0f7316a113')
    swing_bones: CollectionProperty(type=SwingBone)
    # Properties below are for UI Only
    active_swing_bone_index: IntProperty(name='Active Bone Index', default=0)

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
    # Below are needed properties for UI
    active_swing_bone_chain_index: IntProperty(name='Active Swing Bone Chain Index', default=0)