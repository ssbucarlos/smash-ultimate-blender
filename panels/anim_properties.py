import bpy
import re

mat_sub_types = (
    ('VECTOR', 'Custom Vector', 'Custom Vector'),
    ('FLOAT', 'Custom Float', 'Custom Float'),
    ('BOOL', 'Custom Bool', 'Custom Bool'),
    ('PATTERN', 'Pattern Index', 'Pattern Index'),
    ('TEXTURE', 'Texture Transform', 'Texture Transform')
)

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
        col = layout.column()
        row = col.row()
        split = row.split(factor=.4)
        c = split.column()
        c.label(text='Material Names')
        c.template_list(
            "SUB_UL_mat_tracks",
            "",
            arma.sub_anim_properties,
            "mat_tracks",
            arma.sub_anim_properties,
            "active_mat_track_index",
            rows=5,
            maxrows=5,
            )
        split = split.split(factor=.66)
        c = split.column()
        c.label(text='Property Names')
        amti = arma.sub_anim_properties.active_mat_track_index
        if len(arma.sub_anim_properties.mat_tracks) > 0:
            c.template_list(
                "SUB_UL_mat_properties",
                "",
                arma.sub_anim_properties.mat_tracks[amti],
                "properties",
                arma.sub_anim_properties.mat_tracks[amti],
                "active_property_index",
                rows=5,
                maxrows=5,
            )
        else:
            c.enabled = False
        split = split.split()
        c = split.column()
        c.enabled = False
        c.label(text='Property Values')
        if len(arma.sub_anim_properties.mat_tracks) > 0:
            if len(arma.sub_anim_properties.mat_tracks[amti].properties) > 0:
                '''
                After removing the last entry from the list, the 'active' index can remain its previous value
                which is now out of bounds
                '''
                amtpi = arma.sub_anim_properties.mat_tracks[amti].active_property_index
                if amtpi < len(arma.sub_anim_properties.mat_tracks[amti].properties):
                    ap = arma.sub_anim_properties.mat_tracks[amti].properties[amtpi]
                    if ap.sub_type == 'VECTOR':
                        c.prop(ap, "custom_vector", text="", emboss=False)
                    elif ap.sub_type == 'FLOAT':
                        c.prop(ap, "custom_float", text="", emboss=False)
                    elif ap.sub_type == 'BOOL':
                        icon = 'CHECKBOX_HLT' if ap.custom_bool == True else 'CHECKBOX_DEHLT'
                        c.prop(ap, "custom_bool", text="", icon=icon, emboss=False)
                    elif ap.sub_type == 'PATTERN':
                        c.prop(ap, "pattern_index", text="", emboss=False)
                    elif ap.sub_type == 'TEXTURE':
                        c.prop(ap, "texture_transform", text="", emboss=False)
                    c.enabled = True
        # Bottom Row, composed of 3 Sub Rows algined with the above columns
        row = layout.row()
        # Sub Row 1
        split = row.split(factor=.4)
        sr = split.row(align=True)
        sr.operator(SUB_OP_mat_track_add.bl_idname, text='+')
        sr.operator(SUB_OP_mat_track_remove.bl_idname, text='-')
        # Sub Row 2
        split = split.split(factor=.66)
        sr = split.row(align=True)
        sr.operator(SUB_OP_mat_property_add.bl_idname, text='+')
        sr.operator(SUB_OP_mat_property_remove.bl_idname, text='-')
        # Sub 3
        split = split.split()
        sr = split.row(align=True)
        sr.menu(SUB_MT_mat_entry_context_menu.bl_idname, text='Drivers...')

class SUB_OP_mat_track_add(bpy.types.Operator):
    bl_idname = 'sub.mat_track_add'
    bl_label  = 'Add Mat Track'

    def execute(self, context):
        mat_tracks = context.object.data.sub_anim_properties.mat_tracks
        mat_track = mat_tracks.add()
        mat_track.name = 'New Mat Track'
        return {'FINISHED'}

class SUB_OP_mat_track_remove(bpy.types.Operator):
    bl_idname = 'sub.mat_track_remove'
    bl_label = 'Remove Mat Track'

    @classmethod
    def poll(cls, context):
        sap = context.object.data.sub_anim_properties
        return len(sap.mat_tracks) > 0

    def execute(self, context):
        # Mark as Deleted
        # Find matching Fcurve and Remove
        return {'FINISHED'}

class SUB_OP_mat_property_add(bpy.types.Operator):
    bl_idname = 'sub.mat_prop_add'
    bl_label = 'Add Material Property'
    bl_property = "sub_type"

    sub_type: bpy.props.EnumProperty(
        name='Mat Track Entry Subtype',
        description='',
        items=mat_sub_types, 
        default='VECTOR',)

    @classmethod
    def poll(cls, context):
        sap = context.object.data.sub_anim_properties
        return len(sap.mat_tracks) > 0

    def execute(self, context):
        sap = context.object.data.sub_anim_properties
        props = sap.mat_tracks[sap.active_mat_track_index].properties
        prop = props.add()
        prop.sub_type = self.sub_type
        prop.name = f'New {self.sub_type} Property'
        return {'FINISHED'}
    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}

class SUB_OP_mat_property_remove(bpy.types.Operator):
    bl_idname = 'sub.mat_prop_remove'
    bl_label = 'Remove Material Property'

    @classmethod
    def poll(cls, context):
        sap = context.object.data.sub_anim_properties
        if len(sap.mat_tracks) > 0:
            active_track = sap.mat_tracks[sap.active_mat_track_index]
            if len(active_track.properties) > 0:
                return True
        return False

    def execute(self, context):
        sap = context.object.data.sub_anim_properties
        amt = sap.mat_tracks[sap.active_mat_track_index]  
        try:
            fcurves = context.object.data.animation_data.action.fcurves
        except AttributeError:
            amt.properties.remove(amt.active_property_index)
            return {'FINISHED'}
        # Remove matching fcurve
        for fc in fcurves:
            amti = sap.active_mat_track_index
            api = sap.mat_tracks[amti].active_property_index
            if fc.data_path.startswith(f"sub_anim_properties.mat_tracks[{amti}].properties[{api}]"):
                fcurves.remove(fc)
        # The material's remaining properties' fcurves with indexes greater to this one must be decremented
        fcurves = context.object.data.animation_data.action.fcurves

        for fc in fcurves:    
            regex = r"sub_anim_properties\.mat_tracks\[(\d+)\]\.properties\[(\d+)\](\.\w+)"
            matches = re.match(regex, fc.data_path)
            if matches is None:
                continue
            print(f'data_path = {fc.data_path}, match={matches}')
            if len(matches.groups()) < 3:
                continue
            cmti = int(matches.groups()[0])
            cpi = int(matches.groups()[1])
            suffix = matches.groups()[2]
            amti = sap.active_mat_track_index
            api = sap.mat_tracks[amti].active_property_index
            if cmti != amti or cpi <= api:
                continue
            new_data_path = f"sub_anim_properties.mat_tracks[{cmti}].properties[{cpi-1}]{suffix}"
            fc.data_path = new_data_path 
        # Now actually remove the property
        amt.properties.remove(amt.active_property_index)
        # Refresh Material Drivers
        remove_material_drivers(context.object)
        from .import_anim import setup_material_drivers
        setup_material_drivers(context.object)
        return {'FINISHED'}

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

    @classmethod
    def poll(cls, context):
        sap = context.object.data.sub_anim_properties
        vtes = [vte for vte in sap.vis_track_entries if vte.deleted == False]
        return len(vtes) > 0

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
        try:
            fcurves = context.object.data.animation_data.action.fcurves
        except AttributeError:
            return {'FINISHED'} 
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

def remove_material_drivers(arma:bpy.types.Object):
    mesh_children = [child for child in arma.children if child.type == 'MESH']
    materials = {material_slot.material for mesh in mesh_children for material_slot in mesh.material_slots}
    for material in materials:
        for node in material.node_tree.nodes:
            for input in node.inputs:
                if hasattr(input, 'default_value'):
                    input.driver_remove('default_value')

class SUB_OP_mat_drivers_refresh(bpy.types.Operator):
    bl_idname = 'sub.mat_drivers_refresh'
    bl_label = 'Refresh Material Drivers'   

    def execute(self, context):
        remove_material_drivers(context.object)
        from .import_anim import setup_material_drivers
        setup_material_drivers(context.object)
        return {'FINISHED'}  

class SUB_OP_mat_drivers_remove(bpy.types.Operator):
    bl_idname = 'sub.mat_drivers_remove'
    bl_label = 'Remove Material Drivers'

    def execute(self, context):
        remove_material_drivers(context.object)
        return {'FINISHED'}  

class SUB_MT_vis_entry_context_menu(bpy.types.Menu):
    bl_label = "Vis Entry Specials"

    def draw(self, context):
        layout = self.layout
        layout.operator('sub.vis_drivers_refresh', icon='FILE_REFRESH', text='Refresh Visibility Drivers')
        layout.operator('sub.vis_drivers_remove', icon='X', text='Remove Visibility Drivers')

class SUB_MT_mat_entry_context_menu(bpy.types.Menu):
    bl_idname = 'sub.mat_entry_context_menu'
    bl_label = "Mat Entry Specials"

    def draw(self, context):
        layout = self.layout
        layout.operator(SUB_OP_mat_drivers_refresh.bl_idname, icon='FILE_REFRESH', text='Refresh Material Drivers')
        layout.operator(SUB_OP_mat_drivers_remove.bl_idname, icon='X', text='Remove Material Drivers')

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

class SUB_UL_mat_tracks(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False, icon='MATERIAL')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_UL_mat_properties(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_UL_mat_property_values(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            if entry.sub_type == 'VECTOR':
                row.prop(entry, "custom_vector", text="", emboss=False)
            elif entry.sub_type == 'FLOAT':
                row.prop(entry, "custom_float", text="", emboss=False)
            elif entry.sub_type == 'BOOL':
                row.prop(entry, "custom_bool", text="", emboss=False)
            elif entry.sub_type == 'PATTERN':
                row.prop(entry, "pattern_index", text="", emboss=False)
            elif entry.sub_type == 'TEXTURE':
                row.prop(entry, "texture_transform", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)        

'''
class VisTrackEntry(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Vis Name", default="Unknown")
    value: bpy.props.BoolProperty(name="Visible", default=False)
    deleted: bpy.props.BoolProperty(name="Deleted", default=False)

class MatTrackProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Property Name", default="Unknown")
    sub_type: bpy.props.EnumProperty(
        name='Mat Track Entry Subtype',
        description='CustomVector or CustomFloat or CustomBool',
        items=mat_sub_types, 
        default='VECTOR',)
    deleted: bpy.props.BoolProperty(name="Deleted", default=False)
    custom_vector: bpy.props.FloatVectorProperty(name='Custom Vector', size=4)
    custom_bool: bpy.props.BoolProperty(name='Custom Bool')
    custom_float: bpy.props.FloatProperty(name='Custom Float')
    pattern_index: bpy.props.IntProperty(name='Pattern Index', subtype='UNSIGNED')
    texture_transform: bpy.props.FloatVectorProperty(name='Texture Transform', size=5)

class MatTrack(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Material Name", default="Unknown")
    properties: bpy.props.CollectionProperty(type=MatTrackProperty)
    deleted: bpy.props.BoolProperty(name="Deleted", default=False)
    active_property_index: bpy.props.IntProperty(name='Active Mat Property Index', default=0)

class SubAnimProperties(bpy.types.PropertyGroup):
    vis_track_entries: bpy.props.CollectionProperty(type=VisTrackEntry)
    active_vis_track_index: bpy.props.IntProperty(name='Active Vis Track Index', default=0)
    mat_tracks: bpy.props.CollectionProperty(type=MatTrack)
    active_mat_track_index: bpy.props.IntProperty(name='Active Mat Track Index', default=0)
#bpy.types.Armature.sub_anim_properties = bpy.props.PointerProperty(type=SubAnimProperties)

'''
