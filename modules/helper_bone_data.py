import bpy
from bpy.types import Panel, Operator, UIList, Menu, PropertyGroup
from bpy.props import IntProperty, BoolProperty, FloatProperty, FloatVectorProperty, StringProperty, CollectionProperty

class SUB_PT_helper_bone_data_master(Panel):
    bl_label = "Ultimate Helper Bone Data"
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
        arma: bpy.types.Object = context.object
        shbd: SubHelperBoneData = arma.data.sub_helper_bone_data
        layout = self.layout

class SUB_PT_helper_bone_data_aim_constraints(Panel):
    bl_label = "Aim Constraints"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_helper_bone_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        arma: bpy.types.Object = context.object
        shbd: SubHelperBoneData = arma.data.sub_helper_bone_data

        layout = self.layout
        row = layout.row()
        row.template_list(
            SUB_UL_aim_constraints.__name__,
            "",
            shbd,
            "aim_constraints",
            shbd,
            "active_aim_constraint_index",
        )
        col = row.column(align=True)
        col.operator(SUB_OP_aim_constraint_add.bl_idname, icon='ADD', text="")
        col.operator(SUB_OP_aim_constraint_remove.bl_idname, icon='REMOVE', text="")
        col.separator()
        col.menu(SUB_MT_helper_bone_constraint_context_menu.__name__,icon='DOWNARROW_HLT', text='')
        active_index = shbd.active_aim_constraint_index 
        if active_index >= len(shbd.aim_constraints):
            return
        active_entry = shbd.aim_constraints[active_index]
        row = layout.row()
        row.prop(active_entry, 'aim_bone_name1')
        row = layout.row()
        row.prop(active_entry, 'aim_bone_name2')
        row = layout.row()
        row.prop(active_entry, 'aim_type1')
        row = layout.row()
        row.prop(active_entry, 'aim_type2')
        row = layout.row()
        row.prop(active_entry, 'target_bone_name1')
        row = layout.row()
        row.prop(active_entry, 'target_bone_name2')
        row = layout.row()
        row.prop(active_entry, 'aim')
        row = layout.row()
        row.prop(active_entry, 'up')
        row = layout.row()
        row.prop(active_entry, 'quat1')
        row = layout.row()
        row.prop(active_entry, 'quat2')

class SUB_PT_helper_bone_data_orient_constraints(Panel):
    bl_label = "Orient Constraints"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_helper_bone_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        arma: bpy.types.Object = context.object
        shbd: SubHelperBoneData = arma.data.sub_helper_bone_data

        layout = self.layout
        row = layout.row()
        row.template_list(
            SUB_UL_orient_constraints.__name__,
            "",
            shbd,
            "orient_constraints",
            shbd,
            "active_orient_constraint_index",
        )
        col = row.column(align=True)
        col.operator(SUB_OP_orient_constraint_add.bl_idname, icon='ADD', text="")
        col.operator(SUB_OP_orient_constraint_remove.bl_idname, icon='REMOVE', text="")
        col.separator()
        col.menu(SUB_MT_helper_bone_constraint_context_menu.__name__, icon='DOWNARROW_HLT', text='')
        active_index = shbd.active_orient_constraint_index 
        if active_index >= len(shbd.orient_constraints):
            return
        active_entry = shbd.orient_constraints[active_index]
        row = layout.row()
        row.prop(active_entry, 'parent_bone_name1')
        row = layout.row()
        row.prop(active_entry, 'parent_bone_name2')
        row = layout.row()
        row.prop(active_entry, 'source_bone_name')
        row = layout.row()
        row.prop(active_entry, 'target_bone_name')
        row = layout.row()
        row.prop(active_entry, 'unk_type')
        row = layout.row()
        row.prop(active_entry, 'constraint_axes')
        row = layout.row()
        row.prop(active_entry, 'quat1')
        row = layout.row()
        row.prop(active_entry, 'quat2')
        row = layout.row()
        row.prop(active_entry, 'range_min')
        row = layout.row()
        row.prop(active_entry, 'range_max')


class SUB_PT_helper_bone_data_version_info(Panel):
    bl_label = "Version Info Data"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "SUB_PT_helper_bone_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        arma: bpy.types.Object = context.object
        shbd: SubHelperBoneData = arma.data.sub_helper_bone_data

        layout = self.layout
        row = layout.row()
        row.prop(shbd, 'major_version')
        row = layout.row()
        row.prop(shbd, 'major_version')

class SUB_UL_aim_constraints(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_UL_orient_constraints(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_OP_orient_constraint_add(Operator):
    bl_idname = 'sub.orient_constraint_add'
    bl_label = 'Add Orient Constraint'

    def execute(self, context):
        shbd: SubHelperBoneData = context.object.data.sub_helper_bone_data
        entries = shbd.orient_constraints
        entry: OrientConstraint = entries.add()
        entry.name = 'nuHelperBoneRotateInterp999'
        # Entries are not gauranteed to be unique so find the index
        insertion_index = len(entries) - 1
        shbd.active_orient_constraint_index = insertion_index
        return {'FINISHED'} 

class SUB_OP_orient_constraint_remove(Operator):
    bl_idname = 'sub.orient_constraint_remove'
    bl_label = 'Remove Orient Constraint'

    @classmethod
    def poll(cls, context):
        shbd: SubHelperBoneData = context.object.data.sub_helper_bone_data
        return len(shbd.orient_constraints) > 0

    def execute(self, context):
        shbd: SubHelperBoneData = context.object.data.sub_helper_bone_data
        entries = shbd.orient_constraints
        entries.remove(shbd.active_orient_constraint_index)
        i = shbd.active_orient_constraint_index
        shbd.active_orient_constraint_index= max(0 , min(i-1, len(entries)-1))
        return {'FINISHED'} 

class SUB_OP_aim_constraint_add(Operator):
    bl_idname = 'sub.aim_constraint_add'
    bl_label = 'Add Aim Constraint'

    def execute(self, context):
        shbd: SubHelperBoneData = context.object.data.sub_helper_bone_data
        entries = shbd.aim_constraints
        entry: AimConstraint = entries.add()
        entry.name = 'nuHelperBoneRotateAim999'
        # Entries are not gauranteed to be unique so find the index
        insertion_index = len(entries) - 1
        shbd.active_aim_constraint_index = insertion_index
        return {'FINISHED'} 

class SUB_OP_aim_constraint_remove(Operator):
    bl_idname = 'sub.aim_constraint_remove'
    bl_label = 'Remove Aim Constraint'

    @classmethod
    def poll(cls, context):
        shbd: SubHelperBoneData = context.object.data.sub_helper_bone_data
        return len(shbd.aim_constraints) > 0

    def execute(self, context):
        shbd: SubHelperBoneData = context.object.data.sub_helper_bone_data
        entries = shbd.aim_constraints
        entries.remove(shbd.active_aim_constraint_index)
        i = shbd.active_aim_constraint_index
        shbd.active_aim_constraint_index = max(0 , min(i-1, len(entries)-1))
        return {'FINISHED'} 

class SUP_OP_helper_bone_constraints_remove(Operator):
    bl_idname = 'sub.helper_bone_constraints_remove'
    bl_label = 'Remove Helper Bone constraints'

    def execute(self, context):
        from .import_model import remove_helper_bone_constraints
        remove_helper_bone_constraints(context.object)
        return {'FINISHED'}  
    

class SUP_OP_helper_bone_constraints_refresh(Operator):
    bl_idname = 'sub.helper_bone_constraints_refresh'
    bl_label = 'Refresh Helper Bone constraints'

    def execute(self, context):
        from .import_model import remove_helper_bone_constraints, setup_helper_bone_constraints
        remove_helper_bone_constraints(context.object)
        setup_helper_bone_constraints(context.object)
        return {'FINISHED'} 

class SUB_MT_helper_bone_constraint_context_menu(Menu):
    bl_label = "Helper Bone Constraint Specials"

    def draw(self, context):
        layout = self.layout
        layout.operator('sub.helper_bone_constraints_refresh', icon='FILE_REFRESH', text='Refresh Helper Bone Constraints')
        layout.operator('sub.helper_bone_constraints_remove', icon='X', text='Remove Helper Bone Constraints')

class AimConstraint(PropertyGroup):
    name: StringProperty(default="")
    aim_bone_name1: StringProperty(default="")
    aim_bone_name2: StringProperty(default="")
    aim_type1: StringProperty(default="")
    aim_type2: StringProperty(default="")
    target_bone_name1: StringProperty(default="")
    target_bone_name2: StringProperty(default="")
    #unk1: IntProperty(default=0) # always 0, dont expose in UI
    #unk2: IntProperty(default=1) # always 1, dont expose in UI
    aim: FloatVectorProperty(
        size=3,
        subtype='XYZ',
        default=(1.0, 0.0, 0.0),
    ) # unks 3 4 5
    up: FloatVectorProperty(
        size=3,
        subtype='XYZ',
        default=(1.0, 0.0, 0.0),
    ) # unks 6 7 8
    quat1: FloatVectorProperty(
        size=4,
        subtype='QUATERNION',
        default=(0.0, 0.0, 0.0, 0.0),
    ) # unks 9 10 11 12
    quat2: FloatVectorProperty(
        size=4,
        subtype='QUATERNION',
        default=(0.0, 0.0, 0.0, 0.0),
    ) # unks 13 14 15 16
    #unk17: FloatProperty(default=0.0) # always 0, dont expose in UI
    #unk18: FloatProperty(default=0.0) # always 0, dont expose in UI
    #unk19: FloatProperty(default=0.0) # always 0, dont expose in UI
    #unk20: FloatProperty(default=0.0) # always 0, dont expose in UI
    #unk21: FloatProperty(default=0.0) # always 0, dont expose in UI
    #unk22: FloatProperty(default=0.0) # always 0, dont expose in UI

class OrientConstraint(PropertyGroup):
    name: StringProperty(default="")
    parent_bone_name1: StringProperty(name='parent_bone_name1', default="")
    parent_bone_name2: StringProperty(name='parent_bone_name2', default="")
    source_bone_name: StringProperty(name='source_bone_name', default="")
    target_bone_name: StringProperty(name='target_bone_name', default="")
    unk_type: IntProperty(name='unk_type', default=1, soft_min=1, soft_max=2)
    constraint_axes: FloatVectorProperty(
        size=3,
        subtype='XYZ',
        default=(0.0, 0.0, 0.0),
    )
    quat1: FloatVectorProperty(
        size=4,
        subtype='QUATERNION',
        default=(0.0, 0.0, 0.0, 0.0),
    )
    quat2: FloatVectorProperty(
        size=4,
        subtype='QUATERNION',
        default=(0.0, 0.0, 0.0, 0.0),
    )
    range_min: FloatVectorProperty(
        size=3,
        subtype='XYZ',
        default=(-180.0, -180.0, -180.0),
    )
    range_max: FloatVectorProperty(
        size=3,
        subtype='XYZ',
        default=(180.0, 180.0, 180.0),
    )

class SubHelperBoneData(PropertyGroup):
    major_version: IntProperty(
        name='Major Version',
        default=1,
    )
    minor_version: IntProperty(
        name='Minor Version',
        default=1,
    )
    aim_constraints: CollectionProperty(
        type=AimConstraint,
    )
    orient_constraints: CollectionProperty(
        type=OrientConstraint,
    )
    # The below are just for the UI
    active_aim_constraint_index: IntProperty(name='Active Aim Entry Index', default=0)
    active_orient_constraint_index:  IntProperty(name='Active Interpolation Entry Index', default=0)

def copy_helper_bone_data(src_arma: bpy.types.Object, dst_arma: bpy.types.Object):
    src_shbd:SubHelperBoneData = src_arma.data.sub_helper_bone_data
    dst_shbd:SubHelperBoneData = dst_arma.data.sub_helper_bone_data
    dst_shbd.major_version = src_shbd.major_version
    dst_shbd.minor_version = src_shbd.minor_version
    for src_aim_entry in src_shbd.aim_constraints:
        dst_aim_entry = dst_shbd.aim_constraints.add()
        for k,v in src_aim_entry.items():
            dst_aim_entry[k] = v
    for src_interpolation_entry in src_shbd.orient_constraints:
        dst_interpolation_entry = dst_shbd.orient_constraints.add()
        for k,v in src_interpolation_entry.items():
            dst_interpolation_entry[k] = v
    dst_shbd.active_aim_constraint_index = src_shbd.active_aim_constraint_index
    dst_shbd.active_orient_constraint_index = src_shbd.active_orient_constraint_index