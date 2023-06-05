# BPY Imports
import bpy
from bpy.types import (
    Panel, UIList, Menu, UILayout)
# Standard Library Imports
# 3rd Party Imports
# Local Project Imports
from .sub_swing_data import *
from .operators import *
from ...properties import SubSceneProperties

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

class SUB_PT_active_bone_swing_info(Panel):
    bl_label = 'Ultimate Swing Data'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_bone

    def draw(self, context):
        active_bone: bpy.types.Bone = context.active_object.data.bones.get(context.active_bone.name) 
        sub_swing_data: SUB_PG_sub_swing_data = context.object.data.sub_swing_data
        sub_swing_blender_bone_data: SUB_PG_blender_bone_data = active_bone.sub_swing_blender_bone_data
        layout = self.layout
        col = layout.column()
        chain_index = sub_swing_blender_bone_data.swing_bone_chain_index
        if not active_bone.name.startswith('S_'):
            col.label(text='This bone does not start with "S_",')
            col.label(text='so it cannot be part of a swing bone chain')
            return
        if active_bone.name.endswith('_null'):
            col.label(text='This is a "null" swing bone,') 
            col.label(text='so it contains no swing info,')
            col.label(text='but it is needed for the swing chain to properly function.')
            return
        if chain_index == -1:
            col.label(text='This swing bone is not part of a swing bone chain')
            return
        swing_bone_chain: SUB_PG_swing_bone_chain = sub_swing_data.swing_bone_chains[chain_index]
        col.label(text=f'Swing Bone Chain Name: {swing_bone_chain.name}')
        swing_bone: SUB_PG_swing_bone = swing_bone_chain.swing_bones[sub_swing_blender_bone_data.swing_bone_index]
        col.label(text=f'Swing Bone Collisions')
        col.template_list(
                        'SUB_UL_swing_bone_collisions',
                        '',
                        swing_bone,
                        'collisions',
                        swing_bone,
                        'active_collision_index',
                        rows=5,
                        maxrows=5,
                    )
        col.label(text='Swing Bone Props:')
        col.prop(swing_bone, 'air_resistance')
        col.prop(swing_bone, 'water_resistance')
        col.prop(swing_bone, 'angle_z')
        col.prop(swing_bone, 'angle_y')
        col.prop(swing_bone, 'collision_size')
        col.prop(swing_bone, 'friction_rate')
        col.prop(swing_bone, 'goal_strength')
        col.prop(swing_bone, 'inertial_mass')
        col.prop(swing_bone, 'local_gravity')
        col.prop(swing_bone, 'fall_speed_scale')
        col.prop(swing_bone, 'ground_hit')
        col.prop(swing_bone, 'wind_affect')

class SUB_PT_active_mesh_swing_info(Panel):
    bl_label = 'Ultimate Swing Data'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        try:
            type = bpy.context.active_object.type
        except:
            return False
        else:
            return type == 'MESH'

    def draw(self, context):
        layout = self.layout
        mesh_obj: bpy.types.Object = bpy.context.active_object
        mesh_data: bpy.types.Mesh = mesh_obj.data
        sub_swing_data_linked_mesh: SUB_PG_sub_swing_data_linked_mesh = mesh_data.sub_swing_data_linked_mesh

        if not sub_swing_data_linked_mesh.is_swing_mesh:
            layout.row().label(text="This is not a swing collision mesh.")
            return
        sub_swing_data: SUB_PG_sub_swing_data = mesh_obj.parent.data.sub_swing_data

        if sub_swing_data_linked_mesh.is_swing_bone_shape:
            swing_bone_chain: SUB_PG_swing_bone_chain = sub_swing_data.swing_bone_chains[sub_swing_data_linked_mesh.swing_chain_index]
            swing_bone: SUB_PG_swing_bone = swing_bone_chain.swing_bones[sub_swing_data_linked_mesh.swing_bone_index]
            col = layout.column()
            col.label(text=f'Swing Bone Chain Name: {swing_bone_chain.name}')
            col.label(text=f'Swing Bone Name: {swing_bone.name}')
            col.label(text=f'Swing Bone Collisions')
            col.template_list(
                            'SUB_UL_swing_bone_collisions',
                            '',
                            swing_bone,
                            'collisions',
                            swing_bone,
                            'active_collision_index',
                            rows=5,
                            maxrows=5,
                        )
            col.label(text='Swing Bone Props:')
            col.prop(swing_bone, 'air_resistance')
            col.prop(swing_bone, 'water_resistance')
            col.prop(swing_bone, 'angle_z')
            col.prop(swing_bone, 'angle_y')
            col.prop(swing_bone, 'collision_size')
            col.prop(swing_bone, 'friction_rate')
            col.prop(swing_bone, 'goal_strength')
            col.prop(swing_bone, 'inertial_mass')
            col.prop(swing_bone, 'local_gravity')
            col.prop(swing_bone, 'fall_speed_scale')
            col.prop(swing_bone, 'ground_hit')
            col.prop(swing_bone, 'wind_affect')
            return

        
        if sub_swing_data_linked_mesh.collision_collection_type == 'SPHERE':
            swing_sphere: SUB_PG_swing_sphere = sub_swing_data.spheres[sub_swing_data_linked_mesh.collision_collection_index]
            layout.row().prop(swing_sphere, "bone")
            layout.row().prop(swing_sphere, "offset")
            layout.row().prop(swing_sphere, "radius")
        
        if sub_swing_data_linked_mesh.collision_collection_type == 'OVAL':
            swing_oval = sub_swing_data.ovals[sub_swing_data_linked_mesh.collision_collection_index]
            layout.row().prop(swing_oval, "start_bone_name")
            layout.row().prop(swing_oval, "end_bone_name")
            layout.row().prop(swing_oval, "radius")
            layout.row().prop(swing_oval, "start_offset")
            layout.row().prop(swing_oval, "end_offset")

        if sub_swing_data_linked_mesh.collision_collection_type == 'ELLIPSOID':
            swing_ellipsoid = sub_swing_data.ellipsoids[sub_swing_data_linked_mesh.collision_collection_index]
            layout.row().prop(swing_ellipsoid, "bone_name")
            layout.row().prop(swing_ellipsoid, "offset")
            layout.row().prop(swing_ellipsoid, "rotation")
            layout.row().prop(swing_ellipsoid, "scale")

        if sub_swing_data_linked_mesh.collision_collection_type == 'CAPSULE':
            swing_capsule = sub_swing_data.capsules[sub_swing_data_linked_mesh.collision_collection_index]
            layout.row().prop(swing_capsule, "start_bone_name")
            layout.row().prop(swing_capsule, "end_bone_name")
            layout.row().prop(swing_capsule, "start_offset")
            layout.row().prop(swing_capsule, "end_offset")
            layout.row().prop(swing_capsule, "start_radius")
            layout.row().prop(swing_capsule, "end_radius")
        
        if sub_swing_data_linked_mesh.collision_collection_type == 'PLANE':
            swing_plane = sub_swing_data.planes[sub_swing_data_linked_mesh.collision_collection_index]
            layout.row().prop(swing_plane, "bone_name")
            layout.row().prop(swing_plane, "nx")
            layout.row().prop(swing_plane, "ny")
            layout.row().prop(swing_plane, "nz")
            layout.row().prop(swing_plane, "distance")

        if sub_swing_data_linked_mesh.collision_collection_type == 'CONNECTION':
            swing_connection = sub_swing_data.connections[sub_swing_data_linked_mesh.collision_collection_index]
            layout.row().prop(swing_connection, "start_bone_name")
            layout.row().prop(swing_connection, "end_bone_name")
            layout.row().prop(swing_connection, "radius")
            layout.row().prop(swing_connection, "length")
        

class SwingPropertyPanel: # Mix-in for the swing info property panel classes
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

class SUB_PT_swing_data_master(Panel, SwingPropertyPanel):
    bl_label = "Ultimate Swing Data"

    def draw(self, context):
        layout = self.layout
        arma = context.object

class SUB_PT_swing_bone_chains(Panel, SwingPropertyPanel):
    bl_label = "Swing Bone Chains"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        layout = self.layout
        sub_swing_data: SUB_PG_sub_swing_data = context.object.data.sub_swing_data
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
                active_swing_bone: SUB_PG_swing_bone = active_swing_bone_chain.swing_bones[active_swing_bone_chain.active_swing_bone_index]
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
        sr.menu('SUB_MT_swing_bone_collision_add', text='+')
        sr.operator(SUB_OP_swing_bone_collision_remove.bl_idname, text='-')  

        # Swing Bone Chain & Bone Info Area
        if len(sub_swing_data.swing_bone_chains) == 0:
            return
        active_swing_bone_chain: SUB_PG_swing_bone_chain = sub_swing_data.swing_bone_chains[sub_swing_data.active_swing_bone_chain_index]
        if len(active_swing_bone_chain.swing_bones) == 0:
            return
        active_swing_bone: SUB_PG_swing_bone = active_swing_bone_chain.swing_bones[active_swing_bone_chain.active_swing_bone_index]

        row = layout.row()
        split = row.split(factor=.5)
        c = split.column()
        c.label(text='Bone Chain Info')
        c.prop(active_swing_bone_chain, 'is_skirt')
        c.prop(active_swing_bone_chain, 'rotate_order')
        c.prop(active_swing_bone_chain, 'curve_rotate_x')
        c.prop(active_swing_bone_chain, 'has_unk_8')
        if active_swing_bone_chain.has_unk_8:
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
        c.prop(active_swing_bone, 'inertial_mass')
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
            row.prop(entry, "name", text="", emboss=False, icon='GROUP_BONE')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_UL_swing_bones(UIList):
    def draw_item(self, context, layout: UILayout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            #row.prop(entry, "name", text="", emboss=False)
            row.label(text=f'{entry.name}', icon='BONE_DATA')
            #row.prop(entry, "bone", icon='BONE_DATA')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_UL_swing_bone_collisions(UIList):
    def draw_item(self, context, layout: bpy.types.UILayout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry: SUB_PG_swing_bone_collision = item

        arma = entry.id_data
        ssd: SUB_PG_sub_swing_data = arma.sub_swing_data
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            if entry.collision_type == 'SPHERE':
                collision = ssd.spheres[entry.collision_index]
                icon = 'SPHERE'
            elif entry.collision_type == 'OVAL':
                collision = ssd.ovals[entry.collision_index]
                icon = 'MESH_CYLINDER'
            elif entry.collision_type == 'ELLIPSOID':
                collision = ssd.ellipsoids[entry.collision_index]
                icon = 'META_ELLIPSOID'
            elif entry.collision_type == 'CAPSULE':
                collision = ssd.capsules[entry.collision_index]
                icon = 'META_CAPSULE'
            elif entry.collision_type == 'PLANE':
                collision = ssd.planes[entry.collision_index]
                icon = 'MESH_PLANE'
            row.label(text=f'{collision.name}', icon=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)



class SUB_MT_swing_bone_collision_add(Menu):
    bl_label = "Add from existing collision"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row = layout.operator(SUB_OP_swing_bone_collision_add_sphere.bl_idname, text='Sphere', icon='SPHERE')
        row = layout.row()
        row = layout.operator(SUB_OP_swing_bone_collision_add_oval.bl_idname, text='Oval', icon='MESH_CYLINDER')
        row = layout.row()
        row = layout.operator(SUB_OP_swing_bone_collision_add_ellipsoid.bl_idname, text='Ellipsoid', icon='META_ELLIPSOID')
        row = layout.row()
        row = layout.operator(SUB_OP_swing_bone_collision_add_capsule.bl_idname, text='Capsule', icon='META_CAPSULE')
        row = layout.row()
        row = layout.operator(SUB_OP_swing_bone_collision_add_plane.bl_idname, text='Plane', icon='MESH_PLANE')


class SUB_PT_swing_data_spheres(Panel, SwingPropertyPanel):
    bl_label = "Spheres"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        ssd: SUB_PG_sub_swing_data = context.object.data.sub_swing_data
        layout = self.layout
        row = layout.row()
        row.template_list(
            "SUB_UL_swing_data_spheres",
            "",
            ssd,
            "spheres",
            ssd,
            "active_sphere_index",
            rows=3,
            maxrows=10,
            )
        col = row.column(align=True)
        col.operator('sub.swing_data_sphere_add', icon='ADD', text="")
        col.operator('sub.swing_data_sphere_remove', icon='REMOVE', text="")
        col.separator()
        col.menu("SUB_MT_swing_data_spheres_context_menu", icon='DOWNARROW_HLT', text="")

        active_index = ssd.active_sphere_index
        if active_index >= len(ssd.spheres):
            return
        active_sphere = ssd.spheres[active_index]
        row = layout.row()
        row.prop_search(active_sphere, 'bone', context.object.data, 'bones', text='Bone')
        row = layout.row()
        row.prop(active_sphere, 'offset')
        row = layout.row()
        row.prop(active_sphere, 'radius')


class SUB_UL_swing_data_spheres(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False, icon='SPHERE')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_MT_swing_data_spheres_context_menu(Menu):
    bl_label = "Sphere Collisons Menu"

    def draw(self, context):
        layout = self.layout

class SUB_PT_swing_data_ovals(Panel, SwingPropertyPanel):
    bl_label = "Ovals"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        ssd: SUB_PG_sub_swing_data = context.object.data.sub_swing_data
        layout = self.layout
        row = layout.row()
        row.template_list(
            "SUB_UL_swing_data_ovals",
            "",
            ssd,
            "ovals",
            ssd,
            "active_oval_index",
            rows=3,
            maxrows=10,
            )
        col = row.column(align=True)
        col.operator('sub.swing_data_oval_add', icon='ADD', text="")
        col.operator('sub.swing_data_oval_remove', icon='REMOVE', text="")
        col.separator()
        col.menu("SUB_MT_swing_data_ovals_context_menu", icon='DOWNARROW_HLT', text="")

        active_index = ssd.active_oval_index
        if active_index >= len(ssd.ovals):
            return
        active_oval = ssd.ovals[active_index]
        row = layout.row()
        row.prop_search(active_oval, 'start_bone_name', context.object.data, 'bones', text='Start Bone')
        row = layout.row()
        row.prop_search(active_oval, 'end_bone_name', context.object.data, 'bones', text='End Bone')
        row = layout.row()
        row.prop(active_oval, 'radius')
        row = layout.row()
        row.prop(active_oval, 'start_offset')
        row = layout.row()
        row.prop(active_oval, 'end_offset')


class SUB_UL_swing_data_ovals(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False, icon='MESH_CYLINDER')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_MT_swing_data_ovals_context_menu(Menu):
    bl_label = "Oval Collisons Menu"

    def draw(self, context):
        layout = self.layout

class SUB_PT_swing_data_ellipsoids(Panel, SwingPropertyPanel):
    bl_label = "Ellipsoids"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        ssd: SUB_PG_sub_swing_data = context.object.data.sub_swing_data
        layout = self.layout
        row = layout.row()
        row.template_list(
            "SUB_UL_swing_data_ellipsoids",
            "",
            ssd,
            "ellipsoids",
            ssd,
            "active_ellipsoid_index",
            rows=3,
            maxrows=10,
            )
        col = row.column(align=True)
        col.operator('sub.swing_data_ellipsoid_add', icon='ADD', text="")
        col.operator('sub.swing_data_ellipsoid_remove', icon='REMOVE', text="")
        col.separator()
        col.menu("SUB_MT_swing_data_ellipsoids_context_menu", icon='DOWNARROW_HLT', text="")

        active_index = ssd.active_ellipsoid_index
        if active_index >= len(ssd.ellipsoids):
            return
        active_ellipsoid = ssd.ellipsoids[active_index]
        row = layout.row()
        row.prop_search(active_ellipsoid, 'bone_name', context.object.data, 'bones', text='Bone')
        row = layout.row()
        row.prop(active_ellipsoid, 'offset')
        row = layout.row()
        row.prop(active_ellipsoid, 'rotation')
        row = layout.row()
        row.prop(active_ellipsoid, 'scale')


class SUB_UL_swing_data_ellipsoids(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False, icon='META_ELLIPSOID')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_MT_swing_data_ellipsoids_context_menu(Menu):
    bl_label = "Ellipsoids Collisons Menu"

    def draw(self, context):
        layout = self.layout


class SUB_PT_swing_data_capsules(Panel, SwingPropertyPanel):
    bl_label = "Capsules"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        ssd: SUB_PG_sub_swing_data = context.object.data.sub_swing_data
        layout = self.layout
        row = layout.row()
        row.template_list(
            "SUB_UL_swing_data_capsules",
            "",
            ssd,
            "capsules",
            ssd,
            "active_capsule_index",
            rows=3,
            maxrows=10,
            )
        col = row.column(align=True)
        col.operator('sub.swing_data_capsule_add', icon='ADD', text="")
        col.operator('sub.swing_data_capsule_remove', icon='REMOVE', text="")
        col.separator()
        col.menu(SUB_MT_swing_data_capsules_context_menu.bl_idname, icon='DOWNARROW_HLT', text="")

        active_index = ssd.active_capsule_index
        if active_index >= len(ssd.capsules):
            return
        active_capsule = ssd.capsules[active_index]
        row = layout.row()
        row.prop_search(active_capsule, 'start_bone_name',  context.object.data, 'bones', text='Start Bone')
        row = layout.row()
        row.prop_search(active_capsule, 'end_bone_name',  context.object.data, 'bones', text='End Bone')
        row = layout.row()
        row.prop(active_capsule, 'start_offset')
        row = layout.row()
        row.prop(active_capsule, 'end_offset')
        row = layout.row()
        row.prop(active_capsule, 'start_radius')
        row = layout.row()
        row.prop(active_capsule, 'end_radius')


class SUB_UL_swing_data_capsules(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False, icon='META_CAPSULE')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_MT_swing_data_capsules_context_menu(Menu):
    bl_label = "Capsule Collisons Menu"
    bl_idname =  "SUB_MT_swing_data_capsules_context_menu"

    def draw(self, context):
        layout = self.layout

class SUB_PT_swing_data_planes(Panel, SwingPropertyPanel):
    bl_label = "Planes"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        ssd: SUB_PG_sub_swing_data = context.object.data.sub_swing_data
        layout = self.layout
        row = layout.row()
        row.template_list(
            "SUB_UL_swing_data_planes",
            "",
            ssd,
            "planes",
            ssd,
            "active_plane_index",
            rows=3,
            maxrows=10,
            )
        col = row.column(align=True)
        col.operator('sub.swing_data_plane_add', icon='ADD', text="")
        col.operator('sub.swing_data_plane_remove', icon='REMOVE', text="")
        col.separator()
        col.menu(SUB_MT_swing_data_planes_context_menu.bl_idname, icon='DOWNARROW_HLT', text="")

        active_index = ssd.active_plane_index
        if active_index >= len(ssd.planes):
            return
        active_plane = ssd.planes[active_index]
        row = layout.row()
        row.prop_search(active_plane, 'bone_name', context.object.data, 'bones', text='Bone')
        row = layout.row()
        row.prop(active_plane, 'nx')
        row = layout.row()
        row.prop(active_plane, 'ny')
        row = layout.row()
        row.prop(active_plane, 'nz')
        row = layout.row()
        row.prop(active_plane, 'distance')


class SUB_UL_swing_data_planes(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False, icon='MESH_PLANE')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_MT_swing_data_planes_context_menu(Menu):
    bl_label = "Plane Collisons Menu"
    bl_idname = "SUB_MT_swing_data_planes_context_menu"

    def draw(self, context):
        layout = self.layout

class SUB_PT_swing_data_connections(Panel, SwingPropertyPanel):
    bl_label = "Connections"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        ssd: SUB_PG_sub_swing_data = context.object.data.sub_swing_data
        layout = self.layout
        row = layout.row()
        row.template_list(
            "SUB_UL_swing_data_connections",
            "",
            ssd,
            "connections",
            ssd,
            "active_connection_index",
            rows=3,
            maxrows=10,
            )
        col = row.column(align=True)
        col.operator('sub.swing_data_connection_add', icon='ADD', text="")
        col.operator('sub.swing_data_connection_remove', icon='REMOVE', text="")
        col.separator()
        col.menu("SUB_MT_swing_data_connections_context_menu", icon='DOWNARROW_HLT', text="")

        active_index = ssd.active_connection_index
        if active_index >= len(ssd.connections):
            return
        active_connection = ssd.connections[active_index]
        row = layout.row()
        row.prop_search(active_connection, 'start_bone_name', context.object.data, 'bones', text='Start Bone')
        row = layout.row()
        row.prop_search(active_connection, 'end_bone_name', context.object.data, 'bones', text='End Bone')
        row = layout.row()
        row.prop(active_connection, 'radius')
        row = layout.row()
        row.prop(active_connection, 'length')


class SUB_UL_swing_data_connections(UIList):
    def draw_item(self, _context, layout: bpy.types.UILayout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text=f"{item.start_bone_name} -> {item.end_bone_name}", icon='MOD_LENGTH')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_MT_swing_data_connections_context_menu(Menu):
    bl_label = "Swing Bone Connections Menu"

    def draw(self, context):
        layout = self.layout

