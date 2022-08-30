import bpy
from bpy.types import Panel
from rna_prop_ui import PropertyPanel

class DATA_PT_sub_smush_anim_data_master(bpy.types.Panel):
    bl_label = "Ultimate Animation Data"
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
        obj = context.object
        arma = obj.data

class DATA_PT_sub_smush_anim_data_vis_tracks(bpy.types.Panel):
    bl_label = "Ultimate Visibility Track Entries"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "DATA_PT_sub_smush_anim_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        arma = obj.data
        row = layout.row()
        row.template_list(
            "SUB_UL_vis_track_entries",
            "",
            arma.sub_anim_properties,
            "vis_track_entries",
            arma.sub_anim_properties,
            "active_vis_track_index",
            rows=3,
            maxrows=10,
            )
        col = row.column(align=True)
        col.operator('sub.vis_entry_add', icon='ADD', text="")
        col.operator('sub.vis_entry_remove', icon='REMOVE', text="")
        col.separator()
        col.menu("SUB_MT_vis_entry_context_menu", icon='DOWNARROW_HLT', text="")
        '''
        for vis_track in arma.sub_anim_properties.vis_track_entries:
            split = layout.split(factor=0.4, align=True)
            label_row = split.row()
            label_row.alignment = 'RIGHT'
            label_row.label(text=vis_track.name, translate=False)
            value_row = split.row(align=True)
            value_column = value_row.column(align=True)
            value_column.prop(vis_track, 'value', text="")
        '''

class SUB_OP_vis_entry_add(bpy.types.Operator):
    bl_idname = 'sub.vis_entry_add'
    bl_label = 'Add Vis Track Entry'

    def execute(self, context):
        entries = context.object.data.sub_anim_properties.vis_track_entries
        entry = entries.add()
        entry.name = 'New Vis Track Entry'
        entry.value = True
        return {'FINISHED'} 

class SUB_OP_vis_entry_remove(bpy.types.Operator):
    bl_idname = 'sub.vis_entry_remove'
    bl_label = 'Remove Vis Track Entry'

    def execute(self, context):
        '''
        Dont actually remove from list cuz fcurves and drivers will be messed up
            since they rely on the index of the entry.
        Current workaround, mark the entry as 'deleted' and remove fcurve.
        Make sure UI and exporter dont show/export a 'deleted' entry.
        '''
        # Mark as Deleted
        sap = context.object.data.sub_anim_properties
        active_entry = sap.vis_track_entries[sap.active_vis_track_index]
        active_entry.deleted = True
        # Find matching Fcurve and Remove
        fcurves = context.object.data.animation_data.action.fcurves
        for fc in fcurves:
            ai = sap.active_vis_track_index
            if fc.data_path == f'sub_anim_properties.vis_track_entries[{ai}].value':
                fcurves.remove(fc)
        return {'FINISHED'} 


class SUB_OP_vis_drivers_refresh(bpy.types.Operator):
    bl_idname = 'sub.vis_drivers_refresh'
    bl_label = 'Refresh Visibility Drivers'

    def execute(self, context):
        from .import_anim import setup_visibility_drivers
        setup_visibility_drivers(context.object)
        return {'FINISHED'} 

class SUB_OP_vis_drivers_remove(bpy.types.Operator):
    bl_idname = 'sub.vis_drivers_remove'
    bl_label = 'Remove Visibility Drivers'

    def execute(self, context):
        remove_visibility_drivers(context)
        return {'FINISHED'}    

def remove_visibility_drivers(context):
    arma = context.object
    mesh_children = [child for child in arma.children if child.type == 'MESH']
    for m in mesh_children:
        if not m.animation_data:
            continue
        drivers = m.animation_data.drivers
        for d in drivers:
            if any(d.data_path == s for s in ['hide_viewport', 'hide_render']):
                drivers.remove(d)

class SUB_MT_vis_entry_context_menu(bpy.types.Menu):
    bl_label = "Vis Entry Specials"

    def draw(self, context):
        layout = self.layout
        layout.operator('sub.vis_drivers_refresh', icon='FILE_REFRESH', text='Refresh Visibility Drivers')
        layout.operator('sub.vis_drivers_remove', icon='X', text='Remove Visibility Drivers')

class SUB_UL_vis_track_entries(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        # assert(isinstance(item, bpy.types.ShapeKey))
        obj = active_data
        # key = data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.66, align=False)
            split.prop(entry, "name", text="", emboss=False, icon='HIDE_OFF')
            row = split.row(align=True)
            row.emboss = 'NONE_OR_STATUS'
            row.label(text="")
            icon = 'CHECKBOX_HLT' if entry.value == True else 'CHECKBOX_DEHLT'
            row.prop(entry, "value", text="", icon=icon, emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
    def draw_filter(self, context, layout):
        # Nothing much to say here, it's usual UI code...
        split = layout.split(factor=0.66, align=False)
        split.prop(self, "filter_name", text="")
        row = split.row(align=True)
        row.prop(self, "use_filter_sort_alpha", icon='SORTALPHA', toggle=True)
        icon = 'SORT_DESC' if self.use_filter_sort_reverse else 'SORT_ASC'
        row.prop(self, "use_filter_sort_reverse", text="", icon=icon)

    def filter_items(self, context, data, propname):
        '''
        Pretty much default UI code except for not displaying the "deleted" entries
        '''
        entries = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        # Default return values.
        flt_flags = []
        flt_neworder = []

        # Filtering by name
        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name,
                                        self.bitflag_filter_item, entries, "name",
                                        reverse=self.use_filter_invert)
        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(entries)

        # Filter by deletion.
        for index, entry in enumerate(entries):
            if entry.deleted == True:
                flt_flags[index] &= ~self.bitflag_filter_item


        # Reorder by name
        if self.use_filter_sort_alpha:
            flt_neworder = helper_funcs.sort_items_by_name(entries, "name")
        
        return flt_flags, flt_neworder

class DATA_PT_sub_smush_anim_data_mat_track_entry(bpy.types.Panel):
    bl_label = "Ultimate Material Track Entry"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "DATA_PT_sub_smush_anim_data_mat_tracks"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        arma = obj.data
        for mat_track in arma.sub_anim_properties.mat_tracks:
            pass

class DATA_PT_sub_smush_anim_data_mat_tracks(bpy.types.Panel):
    bl_label = "Ultimate Material Tracks"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "DATA_PT_sub_smush_anim_data_master"

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        arma = obj.data
        for mat_track in arma.sub_anim_properties.mat_tracks:
            pass

class VisTrackEntry(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Vis Name", default="Unknown")
    value: bpy.props.BoolProperty(name="Visible", default=False)
    deleted: bpy.props.BoolProperty(name="Deleted", default=False)

mat_sub_types = (
    ('VECTOR', 'Vector', 'Custom Vector'),
    ('FLOAT', 'Float', 'Custom Float'),
    ('BOOL', 'Bool', 'Custom Bool'),
)
class MatTrackEntry(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Property Name", default="Unknown")
    sub_type: bpy.props.EnumProperty(
        name='Mat Track Entry Subtype',
        description='CustomVector or CustomFloat or CustomBool',
        items=mat_sub_types, 
        default='VECTOR',)

class MatTrack(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Material Name", default="Unknown")
    entries: bpy.props.CollectionProperty(type=MatTrackEntry)
    
class SubAnimProperties(bpy.types.PropertyGroup):
    vis_track_entries: bpy.props.CollectionProperty(type=VisTrackEntry)
    active_vis_track_index: bpy.props.IntProperty(name='Active Vis Track Index', default=0)
    mat_tracks: bpy.props.CollectionProperty(type=MatTrack)

#bpy.types.Armature.sub_anim_properties = bpy.props.PointerProperty(type=SubAnimProperties)


