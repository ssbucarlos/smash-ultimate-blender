import bpy

from .. import pyprc
from ..operators import create_meshes
from bpy.types import Panel, Operator, PropertyGroup, Context, UIList, CopyTransformsConstraint, Menu, CopyLocationConstraint, CopyRotationConstraint, TrackToConstraint
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty, FloatVectorProperty
from math import radians, degrees
from mathutils import Vector
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..properties import SubSceneProperties


''' # TODOS:
1.) Capsule Offset
2.) Planes

'''


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
        sub_swing_data: SubSwingData = context.object.data.sub_swing_data
        sub_swing_blender_bone_data: SubSwingBlenderBoneData = active_bone.sub_swing_blender_bone_data
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
        swing_bone_chain: SwingBoneChain = sub_swing_data.swing_bone_chains[chain_index]
        col.label(text=f'Swing Bone Chain Name: {swing_bone_chain.name}')
        swing_bone: SwingBone = swing_bone_chain.swing_bones[sub_swing_blender_bone_data.swing_bone_index]
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
        col.prop(swing_bone, 'unk_11')
        col.prop(swing_bone, 'local_gravity')
        col.prop(swing_bone, 'fall_speed_scale')
        col.prop(swing_bone, 'ground_hit')
        col.prop(swing_bone, 'wind_affect')


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
            #row.prop(entry, "name", text="", emboss=False)
            row.label(text=f'{entry.name}', icon='BONE_DATA')
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

class SUB_PT_swing_data_spheres(Panel, SwingPropertyPanel):
    bl_label = "Spheres"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        ssd: SubSwingData = context.object.data.sub_swing_data
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

class SUB_OP_swing_data_sphere_add(Operator):
    bl_idname = 'sub.swing_data_sphere_add'
    bl_label = 'Add Sphere Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_data_sphere_remove(Operator):
    bl_idname = 'sub.swing_data_sphere_remove'
    bl_label = 'Remove Sphere Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
        
    def execute(self, context):
        return {'FINISHED'}

class SUB_UL_swing_data_spheres(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
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
        ssd: SubSwingData = context.object.data.sub_swing_data
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
        row.prop(active_oval, 'start_bone_name')
        row = layout.row()
        row.prop(active_oval, 'end_bone_name')
        row = layout.row()
        row.prop(active_oval, 'radius')
        row = layout.row()
        row.prop(active_oval, 'start_offset')
        row = layout.row()
        row.prop(active_oval, 'end_offset')

class SUB_OP_swing_data_oval_add(Operator):
    bl_idname = 'sub.swing_data_oval_add'
    bl_label = 'Add Oval Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_data_oval_remove(Operator):
    bl_idname = 'sub.swing_data_oval_remove'
    bl_label = 'Remove Oval Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
        
    def execute(self, context):
        return {'FINISHED'}

class SUB_UL_swing_data_ovals(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
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
        ssd: SubSwingData = context.object.data.sub_swing_data
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
        row.prop(active_ellipsoid, 'bone_name')
        row = layout.row()
        row.prop(active_ellipsoid, 'offset')
        row = layout.row()
        row.prop(active_ellipsoid, 'rotation')
        row = layout.row()
        row.prop(active_ellipsoid, 'scale')

class SUB_OP_swing_data_ellipsoid_add(Operator):
    bl_idname = 'sub.swing_data_ellipsoid_add'
    bl_label = 'Add Ellipsoid Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_data_ellipsoid_remove(Operator):
    bl_idname = 'sub.swing_data_ellipsoid_remove'
    bl_label = 'Remove Ellipsoids Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
        
    def execute(self, context):
        return {'FINISHED'}

class SUB_UL_swing_data_ellipsoids(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
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
        ssd: SubSwingData = context.object.data.sub_swing_data
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
        col.menu("SUB_MT_swing_data_capsule_context_menu", icon='DOWNARROW_HLT', text="")

        active_index = ssd.active_capsule_index
        if active_index >= len(ssd.capsules):
            return
        active_capsule = ssd.capsules[active_index]
        row = layout.row()
        row.prop(active_capsule, 'start_bone_name')
        row = layout.row()
        row.prop(active_capsule, 'end_bone_name')
        row = layout.row()
        row.prop(active_capsule, 'start_offset')
        row = layout.row()
        row.prop(active_capsule, 'end_offset')
        row = layout.row()
        row.prop(active_capsule, 'start_radius')
        row = layout.row()
        row.prop(active_capsule, 'end_radius')

class SUB_OP_swing_data_capsule_add(Operator):
    bl_idname = 'sub.swing_data_capsule_add'
    bl_label = 'Add Capsule Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_data_capsule_remove(Operator):
    bl_idname = 'sub.swing_data_capsule_remove'
    bl_label = 'Remove Capsule Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
        
    def execute(self, context):
        return {'FINISHED'}

class SUB_UL_swing_data_capsules(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_MT_swing_data_capsules_context_menu(Menu):
    bl_label = "Capsule Collisons Menu"

    def draw(self, context):
        layout = self.layout

class SUB_PT_swing_data_planes(Panel, SwingPropertyPanel):
    bl_label = "Planes"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        ssd: SubSwingData = context.object.data.sub_swing_data
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
        col.menu("SUB_MT_swing_data_plane_context_menu", icon='DOWNARROW_HLT', text="")

        active_index = ssd.active_plane_index
        if active_index >= len(ssd.planes):
            return
        active_plane = ssd.planes[active_index]
        row = layout.row()
        row.prop(active_plane, 'bone_name')
        row = layout.row()
        row.prop(active_plane, 'nx')
        row = layout.row()
        row.prop(active_plane, 'ny')
        row = layout.row()
        row.prop(active_plane, 'nz')
        row = layout.row()
        row.prop(active_plane, 'distance')

class SUB_OP_swing_data_plane_add(Operator):
    bl_idname = 'sub.swing_data_plane_add'
    bl_label = 'Add Plane Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_data_plane_remove(Operator):
    bl_idname = 'sub.swing_data_plane_remove'
    bl_label = 'Remove Plane Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
        
    def execute(self, context):
        return {'FINISHED'}

class SUB_UL_swing_data_planes(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_MT_swing_data_planes_context_menu(Menu):
    bl_label = "Plane Collisons Menu"

    def draw(self, context):
        layout = self.layout

class SUB_PT_swing_data_connections(Panel, SwingPropertyPanel):
    bl_label = "Connections"
    bl_parent_id = "SUB_PT_swing_data_master"
    
    def draw(self, context):
        ssd: SubSwingData = context.object.data.sub_swing_data
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
        row.prop(active_connection, 'start_bone_name')
        row = layout.row()
        row.prop(active_connection, 'end_bone_name')
        row = layout.row()
        row.prop(active_connection, 'radius')
        row = layout.row()
        row.prop(active_connection, 'length')

class SUB_OP_swing_data_connection_add(Operator):
    bl_idname = 'sub.swing_data_connection_add'
    bl_label = 'Add Swing Bone Connection Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'

    def execute(self, context):
        return {'FINISHED'}

class SUB_OP_swing_data_connection_remove(Operator):
    bl_idname = 'sub.swing_data_connection_remove'
    bl_label = 'Remove Swing Bone Connection Collision'

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE'
        
    def execute(self, context):
        return {'FINISHED'}

class SUB_UL_swing_data_connections(UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data, _active_propname, index):
        obj = active_data
        entry = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(entry, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SUB_MT_swing_data_connections_context_menu(Menu):
    bl_label = "Swing Bone Connections Menu"

    def draw(self, context):
        layout = self.layout

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
        swing_prc_import(self, context, self.filepath)
        setup_bone_soft_bodies(self, context)
        return {'FINISHED'}

def struct_get(param_struct, input, fallback=None):
    return dict(param_struct).get(pyprc.hash(input), fallback)

def struct_get_str(param_struct, input):
    h = struct_get(param_struct, input)
    return str(h.value) if h is not None else None 

def struct_get_val(param_struct, input):
    r = struct_get(param_struct, input)
    return r.value if r is not None else None

def swing_prc_import(operator: Operator, context: Context, filepath: str):
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
    
    raw_hash_to_blender_bone = {pyprc.hash(bone.name.lower()) : bone for bone in arma_data.bones}
    for chain in prc_swing_bone_chains:
        matched_start_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(chain, 'start_bonename').value)
        matched_end_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(chain, 'end_bonename').value)
        if matched_start_bone is None or matched_end_bone is None:
            start_bone_hash = struct_get_str(chain, 'start_bonename')
            end_bone_hash = struct_get_str(chain, 'end_bonename')
            operator.report({'WARNING'}, f'Could not match bones for a bone chain, skipping. {start_bone_hash=}, {end_bone_hash=}')
            continue
        new_chain: SwingBoneChain = ssd.swing_bone_chains.add()
        new_chain.name            = struct_get_str(chain, 'name')
        new_chain.start_bone_name = matched_start_bone.name
        new_chain.end_bone_name   = matched_end_bone.name
        new_chain.is_skirt        = struct_get_val(chain, 'isskirt')
        new_chain.rotate_order    = struct_get_val(chain, 'rotateorder')
        new_chain.curve_rotate_x  = struct_get_val(chain, 'curverotatex')
        unk_8 = struct_get_val(chain, 0x0f7316a113)
        if unk_8 is not None:
            new_chain.has_unk_8 = True
            new_chain.unk_8 = unk_8
        
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
                if str(prc_swing_bone_collision.value) == '':
                    continue
                new_swing_bone_collision: SwingBoneCollision   = new_swing_bone.collisions.add()
                new_swing_bone_collision.target_collision_name = str(prc_swing_bone_collision.value)
    swing_bone_chain: SwingBoneChain
    swing_bone: SwingBone
    for chain_index, swing_bone_chain in enumerate(ssd.swing_bone_chains):
        starting_blender_bone = arma_data.bones.get(swing_bone_chain.start_bone_name) 
        current_blender_bone = starting_blender_bone
        for bone_index, swing_bone in enumerate(swing_bone_chain.swing_bones):
            swing_bone.name = current_blender_bone.name
            current_blender_bone.sub_swing_blender_bone_data.swing_bone_chain_index = chain_index
            current_blender_bone.sub_swing_blender_bone_data.swing_bone_index = bone_index
            current_blender_bone = current_blender_bone.children[0]
            

    try:
        prc_spheres = list(dict(prc_root).get(pyprc.hash('spheres')))
    except:
        operator.report({'ERROR'}, 'No "spheres" list in the prc!')
        return

    for prc_sphere in prc_spheres:
        matched_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(prc_sphere, 'bonename').value)
        if matched_bone is None:
            operator.report({'WARNING'}, f"Could not match bone for a sphere. {struct_get_str(prc_sphere, 'name')}, {struct_get_str(prc_sphere, 'bonename')}")
            continue
        new_sphere: Sphere = ssd.spheres.add()
        new_sphere.name = struct_get_str(prc_sphere, 'name')
        new_sphere.bone = matched_bone.name
        new_sphere.offset.x = -(struct_get_val(prc_sphere, 'cy'))
        new_sphere.offset.y = struct_get_val(prc_sphere, 'cx')
        new_sphere.offset.z = struct_get_val(prc_sphere, 'cz')
        new_sphere.radius = struct_get_val(prc_sphere, 'radius')

    
    try:
        prc_ovals = list(dict(prc_root).get(pyprc.hash('ovals')))
    except:
        operator.report({'ERROR'}, 'No "ovals" list in the prc!')
        return

    for prc_oval in prc_ovals:
        matched_start_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(prc_oval, 'start_bonename').value)
        matched_end_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(prc_oval, 'end_bonename').value)
        if matched_start_bone is None or matched_end_bone is None:
            start_bone_hash = struct_get_str(prc_oval, 'start_bonename')
            end_bone_hash = struct_get_str(prc_oval, 'end_bonename')
            operator.report({'WARNING'}, f'Could not match bones for a oval. {start_bone_hash=}, {end_bone_hash=}')
            continue
        new_oval: Oval = ssd.ovals.add()
        new_oval.name = struct_get_str(prc_oval, 'name')
        new_oval.start_bone_name = matched_start_bone.name
        new_oval.end_bone_name = matched_end_bone.name
        new_oval.radius = struct_get_val(prc_oval, 'radius')
        new_oval.start_offset.x = -(struct_get_val(prc_oval, 'start_offset_y'))
        new_oval.start_offset.y = struct_get_val(prc_oval, 'start_offset_x')
        new_oval.start_offset.z = struct_get_val(prc_oval, 'start_offset_z')
        new_oval.end_offset.x = -(struct_get_val(prc_oval, 'end_offset_y'))
        new_oval.end_offset.y = struct_get_val(prc_oval, 'end_offset_x') 
        new_oval.end_offset.z = struct_get_val(prc_oval, 'end_offset_z')

    try:
        prc_ellipsoids = list(dict(prc_root).get(pyprc.hash('ellipsoids')))
    except:
        operator.report({'ERROR'}, 'No "ellipsoids" list in the prc!')
        return
    
    for prc_ellipsoid in prc_ellipsoids:
        matched_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(prc_ellipsoid, 'bonename').value)
        if matched_bone is None:
            operator.report({'WARNING'}, f"Could not match bone for a ellipsoid. {struct_get_str(prc_ellipsoid, 'name')}, {struct_get_str(prc_ellipsoid, 'bonename')}")
            continue
        new_ellipsoid: Ellipsoid = ssd.ellipsoids.add()
        new_ellipsoid.name = struct_get_str(prc_ellipsoid, 'name')
        new_ellipsoid.bone_name = matched_bone.name
        new_ellipsoid.offset.x =  -(struct_get_val(prc_ellipsoid, 'cy')) 
        new_ellipsoid.offset.y = struct_get_val(prc_ellipsoid, 'cx')
        new_ellipsoid.offset.z = struct_get_val(prc_ellipsoid, 'cz')
        new_ellipsoid.rotation.x =  -(struct_get_val(prc_ellipsoid, 'ry'))
        new_ellipsoid.rotation.y = struct_get_val(prc_ellipsoid, 'rx')
        new_ellipsoid.rotation.z = struct_get_val(prc_ellipsoid, 'rz')
        new_ellipsoid.scale.x = struct_get_val(prc_ellipsoid, 'sy')
        new_ellipsoid.scale.y = struct_get_val(prc_ellipsoid, 'sx')
        new_ellipsoid.scale.z = struct_get_val(prc_ellipsoid, 'sz')
    
    try:
        prc_capsules = list(dict(prc_root).get(pyprc.hash('capsules')))
    except:
        operator.report({'ERROR'}, 'No "capsules" list in the prc!')
        return
    
    for prc_capsule in prc_capsules:
        matched_start_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(prc_capsule, 'start_bonename').value)
        matched_end_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(prc_capsule, 'end_bonename').value)
        if matched_start_bone is None or matched_end_bone is None:
            start_bone_hash = struct_get_str(prc_capsule, 'start_bonename')
            end_bone_hash = struct_get_str(prc_capsule, 'end_bonename')
            operator.report({'WARNING'}, f'Could not match bones for a capsule. {start_bone_hash=}, {end_bone_hash=}')
            continue
        new_capsule: Capsule = ssd.capsules.add()
        new_capsule.name = struct_get_str(prc_capsule, 'name')
        new_capsule.start_bone_name = matched_start_bone.name
        new_capsule.end_bone_name = matched_end_bone.name
        new_capsule.start_offset.x = -(struct_get_val(prc_capsule, 'start_offset_y'))
        new_capsule.start_offset.y = struct_get_val(prc_capsule, 'start_offset_x') 
        new_capsule.start_offset.z = struct_get_val(prc_capsule, 'start_offset_z')
        new_capsule.end_offset.x = -(struct_get_val(prc_capsule, 'end_offset_y'))
        new_capsule.end_offset.y = struct_get_val(prc_capsule, 'end_offset_x') 
        new_capsule.end_offset.z = struct_get_val(prc_capsule, 'end_offset_z')
        new_capsule.start_radius = struct_get_val(prc_capsule, 'start_radius')
        new_capsule.end_radius = struct_get_val(prc_capsule, 'end_radius')

    try:
        prc_planes = list(dict(prc_root).get(pyprc.hash('planes')))
    except:
        operator.report({'ERROR'}, 'No "planes" list in the prc!')
        return

    for prc_plane in prc_planes:
        matched_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(prc_plane, 'bonename').value)
        if matched_bone is None:
            operator.report({'WARNING'}, f"Could not match bone for a plane. {struct_get_str(prc_plane, 'name')}, {struct_get_str(prc_plane, 'bonename')}")
            continue
        new_plane: Plane = ssd.planes.add()
        new_plane.name = struct_get_str(prc_plane, 'name')
        new_plane.bone_name = matched_bone.name
        new_plane.nx = -(struct_get_val(prc_plane, 'ny'))
        new_plane.ny = struct_get_val(prc_plane, 'nx')
        new_plane.nz = struct_get_val(prc_plane, 'nz')
        new_plane.distance = struct_get_val(prc_plane, 'distance')

    try:
        prc_connections = list(dict(prc_root).get(pyprc.hash('connections')))
    except:
        operator.report({'ERROR'}, 'No "connections" list in the prc!')
        return

    for prc_connection in prc_connections:
        matched_start_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(prc_connection, 'start_bonename').value)
        matched_end_bone: bpy.types.Bone = raw_hash_to_blender_bone.get(struct_get(prc_connection, 'end_bonename').value)
        if matched_start_bone is None:
            start_bone_hash = struct_get_str(prc_connection, 'start_bonename')
            end_bone_hash = struct_get_str(prc_connection, 'end_bonename')
            operator.report({'WARNING'}, f'Could not match start bone for a connection. {start_bone_hash=}, {end_bone_hash=}')
            continue
        elif matched_end_bone is None:
            start_bone_hash = struct_get_str(prc_connection, 'start_bonename')
            end_bone_hash = struct_get_str(prc_connection, 'end_bonename')
            operator.report({'WARNING'}, f'Could not match end bone for a connction. {start_bone_hash=}, {end_bone_hash=}')
            continue
        new_connection: Connection = ssd.connections.add()
        new_connection.start_bone_name = matched_start_bone.name
        new_connection.end_bone_name = matched_end_bone.name
        new_connection.radius = struct_get_val(prc_connection, 'radius')
        new_connection.length = struct_get_val(prc_connection, 'length')

def setup_bone_soft_bodies(operator: Operator, context: Context):
    ssd: SubSwingData = context.object.data.sub_swing_data
    swing_master_collection = bpy.data.collections.new(f'{context.object.name} Swing Objects')
    swing_chains_collection = bpy.data.collections.new('Swing Bone Chains')
    collision_shapes_collection = bpy.data.collections.new('Collision Shapes')
    shape_collection_names = ('Spheres', 'Ovals', 'Ellipsoids', 'Capsules', 'Planes', 'Connections')
    shape_name_to_collection: dict[str, bpy.types.Collection] = {}
    for shape_collection_name in shape_collection_names:
        shape_collection = bpy.data.collections.new(shape_collection_name)
        collision_shapes_collection.children.link(shape_collection)
        shape_name_to_collection[shape_collection_name] = shape_collection
    context.collection.children.link(swing_master_collection)
    swing_master_collection.children.link(swing_chains_collection)
    swing_master_collection.children.link(collision_shapes_collection)
    
    swing_sphere: Sphere
    for swing_sphere in ssd.spheres:
        blender_bone: bpy.types.Bone = context.object.data.bones.get(swing_sphere.bone)
        if blender_bone is None:
                continue
        
        sphere_obj = create_meshes.make_sphere_object(swing_sphere.name, swing_sphere.radius, swing_sphere.offset)
        swing_sphere.blender_object = sphere_obj
        ctc: CopyTransformsConstraint = sphere_obj.constraints.new('COPY_TRANSFORMS')
        ctc.target = context.object
        ctc.subtarget = blender_bone.name
        spheres_collection = shape_name_to_collection['Spheres']
        spheres_collection.objects.link(sphere_obj)

    swing_oval: Oval
    for swing_oval in ssd.ovals:
        start_bone: bpy.types.Bone = context.object.data.bones.get(swing_oval.start_bone_name)
        end_bone: bpy.types.Bone = context.object.data.bones.get(swing_oval.end_bone_name)
        length = (start_bone.head_local - end_bone.head_local).length
        oval_obj = create_meshes.make_capsule_object(context, swing_oval.name, swing_oval.radius, swing_oval.radius, length, swing_oval.start_offset, swing_oval.end_offset)
        swing_oval.blender_object = oval_obj

        clc: CopyLocationConstraint = oval_obj.constraints.new('COPY_LOCATION')
        clc.target = context.object
        clc.subtarget = start_bone.name

        ttc: TrackToConstraint = oval_obj.constraints.new('TRACK_TO')
        ttc.target = context.object
        ttc.subtarget = end_bone.name
        ttc.track_axis = 'TRACK_Y'
        ttc.up_axis = 'UP_Z'

        driver_handle = oval_obj.driver_add('scale', 1)
        driver: bpy.types.Driver = driver_handle.driver
        var = driver.variables.new()
        var.type = 'LOC_DIFF'
        target_1 = var.targets[0]
        target_1.id = context.object
        target_1.bone_target = start_bone.name
        target_2 = var.targets[1]
        target_2.id = context.object
        target_2.bone_target = end_bone.name
        driver.expression = f' {var.name} / {length} '

        ovals_collection = shape_name_to_collection['Ovals']
        ovals_collection.objects.link(oval_obj)

    swing_ellipsoid: Ellipsoid
    for swing_ellipsoid in ssd.ellipsoids:
        blender_bone: bpy.types.Bone = context.object.data.bones.get(swing_ellipsoid.bone_name)
        s = Vector(swing_ellipsoid.scale)
        r = Vector(swing_ellipsoid.rotation)
        o = Vector(swing_ellipsoid.offset)
        ellipsoid_obj = create_meshes.make_ellipsoid_object(swing_ellipsoid.name, scale=s, offset=o, rotation=r)
        swing_ellipsoid.blender_object = ellipsoid_obj
        ctc: CopyTransformsConstraint = ellipsoid_obj.constraints.new('COPY_TRANSFORMS')
        ctc.target = context.object
        ctc.subtarget = blender_bone.name
        ellipsoids_collection = shape_name_to_collection['Ellipsoids']
        ellipsoids_collection.objects.link(ellipsoid_obj)

    swing_capsule: Capsule
    for swing_capsule in ssd.capsules:
        start_bone: bpy.types.Bone = context.object.data.bones.get(swing_capsule.start_bone_name)
        end_bone: bpy.types.Bone = context.object.data.bones.get(swing_capsule.end_bone_name)
        start_offset = Vector(swing_capsule.start_offset)
        end_offset = Vector(swing_capsule.end_offset)
        length = (start_bone.head_local - end_bone.head_local).length
        capsule_obj = create_meshes.make_capsule_object(context, swing_capsule.name, swing_capsule.start_radius, swing_capsule.end_radius, length, start_offset=start_offset, end_offset=end_offset)
        swing_capsule.blender_object = capsule_obj

        clc: CopyLocationConstraint = capsule_obj.constraints.new('COPY_LOCATION')
        clc.target = context.object
        clc.subtarget = start_bone.name

        ttc: TrackToConstraint = capsule_obj.constraints.new('TRACK_TO')
        ttc.target = context.object
        ttc.subtarget = end_bone.name
        ttc.track_axis = 'TRACK_Y'
        ttc.up_axis = 'UP_Z'

        driver_handle = capsule_obj.driver_add('scale', 1)
        driver: bpy.types.Driver = driver_handle.driver
        var = driver.variables.new()
        var.type = 'LOC_DIFF'
        target_1 = var.targets[0]
        target_1.id = context.object
        target_1.bone_target = start_bone.name
        target_2 = var.targets[1]
        target_2.id = context.object
        target_2.bone_target = end_bone.name
        driver.expression = f' {var.name} / {length} '

        capsules_collection = shape_name_to_collection['Capsules']
        capsules_collection.objects.link(capsule_obj)

    swing_plane: Plane
    for swing_plane in ssd.planes:
        blender_bone: bpy.types.Bone = context.object.data.bones.get(swing_plane.bone_name)
        
    swing_connection: Connection
    for swing_connection in ssd.connections:
        start_bone: bpy.types.Bone = context.object.data.bones.get(swing_connection.start_bone_name)
        end_bone: bpy.types.Bone = context.object.data.bones.get(swing_connection.end_bone_name)
        connection_name = f'{start_bone.name} -> {end_bone.name} '
        length = (start_bone.head_local - end_bone.head_local).length
        capsule_obj = create_meshes.make_capsule_object(context, connection_name, swing_connection.radius, swing_connection.radius, length)
        swing_connection.blender_object = capsule_obj

        clc: CopyLocationConstraint = capsule_obj.constraints.new('COPY_LOCATION')
        clc.target = context.object
        clc.subtarget = start_bone.name

        ttc: TrackToConstraint = capsule_obj.constraints.new('TRACK_TO')
        ttc.target = context.object
        ttc.subtarget = end_bone.name
        ttc.track_axis = 'TRACK_Y'
        ttc.up_axis = 'UP_Z'

        driver_handle = capsule_obj.driver_add('scale', 1)
        driver: bpy.types.Driver = driver_handle.driver
        var = driver.variables.new()
        var.type = 'LOC_DIFF'
        target_1 = var.targets[0]
        target_1.id = context.object
        target_1.bone_target = start_bone.name
        target_2 = var.targets[1]
        target_2.id = context.object
        target_2.bone_target = end_bone.name
        driver.expression = f' {var.name} / {length} '

        connections_collection = shape_name_to_collection['Connections']
        connections_collection.objects.link(capsule_obj)

    swing_bone_chain: SwingBoneChain
    swing_bone: SwingBone
    swing_bone_collision: SwingBoneCollision
    collision_name_to_collision = {}
    collision_lists =(ssd.spheres, ssd.ovals, ssd.ellipsoids, ssd.capsules,) #ssd.planes
    for collision_list in collision_lists:
        for collision in collision_list:
            collision_name_to_collision[collision.name] = collision
    for swing_bone_chain in ssd.swing_bone_chains: # type: list[SwingBoneChain]
        chain_collection = bpy.data.collections.new(swing_bone_chain.name)
        chain_swing_bones_collection = bpy.data.collections.new(f'{swing_bone_chain.name} swing bones')
        chain_collision_collection = bpy.data.collections.new(f'{swing_bone_chain.name} collisions')
        swing_chains_collection.children.link(chain_collection)
        chain_collection.children.link(chain_swing_bones_collection)
        chain_collection.children.link(chain_collision_collection)
        for swing_bone in swing_bone_chain.swing_bones:
            # Set Up Swing Bone Capsules
            blender_bone: bpy.types.Bone = context.object.data.bones.get(swing_bone.name)
            if blender_bone is None:
                continue

            cap = create_meshes.make_capsule_object(context, swing_bone.name, swing_bone.collision_size[0], swing_bone.collision_size[1], blender_bone.length)
            ctc: CopyTransformsConstraint = cap.constraints.new('COPY_TRANSFORMS')
            ctc.target = context.object
            ctc.subtarget = blender_bone.name
            chain_swing_bones_collection.objects.link(cap)
            swing_bone_collision_collection = bpy.data.collections.new(f'{swing_bone_chain.name} {swing_bone.name} collisions')
            chain_collision_collection.children.link(swing_bone_collision_collection)
            for swing_bone_collision in swing_bone.collisions:
                # Set Up A Collection for this bone's collisions, 'link' collision objects to it.
                collision = collision_name_to_collision.get(swing_bone_collision.target_collision_name)
                if collision is None:
                    operator.report({'WARNING'}, f"Could not find collision {swing_bone_collision.target_collision_name} for Swing bone {blender_bone.name}")
                    continue
                if collision.blender_object is None:
                    operator.report({'WARNING'}, f"Collision {swing_bone_collision.target_collision_name} for Swing bone {blender_bone.name} has missing blender object")
                    continue
                swing_bone_collision_collection.objects.link(collision.blender_object)

class SUB_OP_swing_export(Operator):
    bl_idname = 'sub.swing_export'
    bl_label = 'Export swing.prc'

    filter_glob: StringProperty(
        default='*.prc',
        options={'HIDDEN'},
    )

    filepath: StringProperty(subtype='FILE_PATH')

    @classmethod
    def poll(cls, context):
        arma: bpy.types.Object = context.object
        if not arma:
            return False
        if arma.type != 'ARMATURE':
            return False
        ssd: SubSwingData = arma.data.sub_swing_data
        return len(ssd.swing_bone_chains) > 0

    def invoke(self, context, _event):
        self.filepath = ''
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        swing_prc_export(self, context, self.filepath)
        return {'FINISHED'}

'''
A 'list' in the prc is really a 'struct' with entries (hash, list).
swing.prc format
pyprc.param.struct([
    (pyprc.param.struct([
        (pyprc.hash('swingbones'), pyprc.param.list([

        ]))
    ])),
])
    swingbones: list_struct i.e. struct([(hash('swingbones'), list)])
        struct([ # One for each swing bone chain
            name: hash_struct aka struct([hash(hash_name), hash(hash_value)])
            start_bonename: hash_struct
            end_bonename: hash_struct
            params: list_struct i.e. struct([(hash('params'), list)])
                struct([ # One for each swing bone in this chain
                airresistance: float_struct i.e. struct([(hash('airresistance'))])
                ])
                ...
        ])
        ...
    list aka struct([hash(bone_name.lower() + col), list]) # the collisions for each swing bone re-listed
        hash40(collision_name)
        ...

'''
from typing import Union # in python 3.10 this is deprecated
def new_prc_list(list_name):
    return pyprc.param.struct([
        (pyprc.hash(list_name),pyprc.param.list([]))
    ])

def new_prc_struct():
    return pyprc.param.struct([])

def new_prc_hash(hash_name: Union[str, int], hash_value: Union[str, int]):
    try: 
        int(hash_name, base=16) 
    except ValueError: 
        pass
    else: 
        hash_name = int(hash_name, base=16)
    try: 
        int(hash_value, base=16) 
    except ValueError: 
        pass
    else: 
        hash_value = int(hash_value, base=16)
    return pyprc.param.struct([
        (pyprc.hash(hash_name), pyprc.param.hash(pyprc.hash(hash_value)))
    ])

def new_prc_hash_simple(hash_value):
    try: 
        int(hash_value, base=16) 
    except ValueError: 
        pass
    else: 
        hash_value = int(hash_value, base=16)
    return pyprc.param.hash(pyprc.hash(hash_value))

def new_prc_float(float_name: Union[str, int], float_value: float):
    return pyprc.param.struct([
        (pyprc.hash(float_name), pyprc.param.float(float_value))
    ])

def new_prc_byte(byte_name: Union[str, int], byte_value: int):
    return pyprc.param.struct([
        (pyprc.hash(byte_name), pyprc.param.i8(byte_value))
    ])
def new_prc_int(int_name: Union[str, int], int_value: int):
    return pyprc.param.struct([
        (pyprc.hash(int_name), pyprc.param.i8(int_value))
    ])
def extend_struct(struct, new_thing):
    struct.set_struct(list(struct) + list(new_thing))

class PrcStruct():
    _prc_struct = None
    def __init__(self, params: list = []):
        self._prc_struct = pyprc.param.struct([])
        for param in params:
            self += param
    def __iter__(self):
        return self._prc_struct.__iter__()
    def __iadd__(self, other):
        self.extend_struct(other)
        return self
    def __repr__(self):
        return self._prc_struct.__repr__()
    def get_param(self):
        return self._prc_struct
    def extend_struct(self, new_prc_param):
        self._prc_struct.set_struct(list(self._prc_struct) + list(new_prc_param))
        return self
    def save(self, path):
        self._prc_struct.save(path)

class PrcList(PrcStruct):
    def __init__(self, list_name: str):
        self._prc_struct = pyprc.param.struct([
            (pyprc.hash(list_name), pyprc.param.list([]))
        ])
    def __iadd__(self, other):
        self.extend_list(other)
        return self
    def get_prc_list(self):
        return list(self._prc_struct)[0][1]
    def get_prc_list_as_py_list(self):
        return list(self.get_prc_list())
    def extend_list(self, new_prc_param: PrcStruct):
        self.get_prc_list().set_list(self.get_prc_list_as_py_list() + [new_prc_param.get_param()])
        return self

class PrcHash40():
    _prc_param = None
    def __init__(self, hash_value):
        try: 
            int(hash_value, base=16) 
        except ValueError: 
            pass
        else: 
            hash_value = int(hash_value, base=16)
        self._prc_param = pyprc.param.hash(pyprc.hash(hash_value))
    def get_param(self):
        return self._prc_param
    def __repr__(self):
        return self._prc_param.__repr__()

def swing_prc_export(operator: Operator, context: Context, filepath: str):
    # forward declaration for typechecking.
    swing_bone_chain: SwingBoneChain
    swing_bone: SwingBone 
    collision: SwingBoneCollision 
    sphere: Sphere
    oval: Oval
    ellipsoid: Ellipsoid
    capsule: Capsule
    plane: Plane
    connection: Connection

    arma_data: bpy.types.Armature = context.object.data
    ssd: SubSwingData = arma_data.sub_swing_data
    prc_root = PrcStruct()
    # Add 'swingbones' list
    swing_bone_chains_list = PrcList('swingbones')
    for swing_bone_chain in ssd.swing_bone_chains:
        '''
        swing_bone_chain_struct  = PrcStruct()
        swing_bone_chain_struct += new_prc_hash('name', swing_bone_chain.name)
        swing_bone_chain_struct += new_prc_hash('start_bonename', swing_bone_chain.start_bone_name.lower())
        swing_bone_chain_struct += new_prc_hash('end_bonename', swing_bone_chain.end_bone_name.lower())
        swing_bone_param_list    = PrcList('params')
        swing_bone_chain_struct += swing_bone_param_list
        swing_bone_chain_struct += new_prc_byte('isskirt', swing_bone_chain.is_skirt)
        swing_bone_chain_struct += new_prc_int('rotateorder', swing_bone_chain.rotate_order)
        swing_bone_chain_struct += new_prc_byte('curverotatex', swing_bone_chain.is_skirt)
        if swing_bone_chain.has_unk_8 == True:
            swing_bone_chain_struct += new_prc_byte(0x0f7316a113, swing_bone_chain.unk_8)
        '''
        swing_bone_param_list    = PrcList('params')
        swing_bone_chain_struct  = PrcStruct([
            new_prc_hash('name', swing_bone_chain.name),
            new_prc_hash('start_bonename', swing_bone_chain.start_bone_name.lower()),
            new_prc_hash('end_bonename', swing_bone_chain.end_bone_name.lower()),
            swing_bone_param_list,
            new_prc_byte('isskirt', swing_bone_chain.is_skirt),
            new_prc_int('rotateorder', swing_bone_chain.rotate_order),
            new_prc_byte('curverotatex', swing_bone_chain.is_skirt),
        ])
        if swing_bone_chain.has_unk_8 == True:
            swing_bone_chain_struct += new_prc_byte(0x0f7316a113, swing_bone_chain.unk_8)
        for swing_bone in swing_bone_chain.swing_bones:
            '''
            swing_bone_params_struct = PrcStruct()
            swing_bone_params_struct += new_prc_float('airresistance', swing_bone.air_resistance)
            swing_bone_params_struct += new_prc_float('waterresistance', swing_bone.water_resistance)
            swing_bone_params_struct += new_prc_float('minanglez', degrees(swing_bone.angle_z[0]))
            swing_bone_params_struct += new_prc_float('maxanglez', degrees(swing_bone.angle_z[1]))
            swing_bone_params_struct += new_prc_float('minangley', degrees(swing_bone.angle_y[0]))
            swing_bone_params_struct += new_prc_float('maxangley', degrees(swing_bone.angle_y[1]))
            swing_bone_params_struct += new_prc_float('collisionsizetip', swing_bone.collision_size[1])
            swing_bone_params_struct += new_prc_float('collisionsizeroot', swing_bone.collision_size[0])
            swing_bone_params_struct += new_prc_float('frictionrate', swing_bone.friction_rate)
            swing_bone_params_struct += new_prc_float('goalstrength', swing_bone.goal_strength)
            swing_bone_params_struct += new_prc_float(0x0cc10e5d3a, swing_bone.unk_11)
            swing_bone_params_struct += new_prc_float('localgravity', swing_bone.local_gravity)
            swing_bone_params_struct += new_prc_float('fallspeedscale', swing_bone.fall_speed_scale)
            swing_bone_params_struct += new_prc_byte('groundhit', swing_bone.ground_hit)
            swing_bone_params_struct += new_prc_float('windaffect', swing_bone.wind_affect)
            '''
            collision_list = PrcList('collisions')
            swing_bone_params_struct = PrcStruct([
                new_prc_float('airresistance', swing_bone.air_resistance),
                new_prc_float('waterresistance', swing_bone.water_resistance),
                new_prc_float('minanglez', degrees(swing_bone.angle_z[0])),
                new_prc_float('maxanglez', degrees(swing_bone.angle_z[1])),
                new_prc_float('minangley', degrees(swing_bone.angle_y[0])),
                new_prc_float('maxangley', degrees(swing_bone.angle_y[1])),
                new_prc_float('collisionsizetip', swing_bone.collision_size[1]),
                new_prc_float('collisionsizeroot', swing_bone.collision_size[0]),
                new_prc_float('frictionrate', swing_bone.friction_rate),
                new_prc_float('goalstrength', swing_bone.goal_strength),
                new_prc_float(0x0cc10e5d3a, swing_bone.unk_11),
                new_prc_float('localgravity', swing_bone.local_gravity),
                new_prc_float('fallspeedscale', swing_bone.fall_speed_scale),
                new_prc_byte('groundhit', swing_bone.ground_hit),
                new_prc_float('windaffect', swing_bone.wind_affect),
                collision_list,
            ])
            for collision in swing_bone.collisions:
                collision_list += PrcHash40(collision.target_collision_name)
            swing_bone_param_list += swing_bone_params_struct
        swing_bone_chains_list += swing_bone_chain_struct
    prc_root += swing_bone_chains_list

    # add spheres
    spheres_list = PrcList('spheres')
    for sphere in ssd.spheres:
        spheres_list += PrcStruct([
            new_prc_hash('name', sphere.name),
            new_prc_hash('bonename', sphere.bone.lower()),
            new_prc_float('cx', sphere.offset.y),
            new_prc_float('cy', -sphere.offset.x),
            new_prc_float('cz', sphere.offset.z),
            new_prc_float('radius', sphere.radius),
        ])
    prc_root += spheres_list
    
    # add ovals
    ovals_list = PrcList('ovals')
    for oval in ssd.ovals:
        ovals_list += PrcStruct([
            new_prc_hash('name', oval.name),
            new_prc_hash('start_bonename', oval.start_bone_name.lower()),
            new_prc_hash('end_bonename', oval.end_bone_name.lower()),
            new_prc_float('radius', oval.radius),
            new_prc_float('start_offset_x',  oval.start_offset.y),
            new_prc_float('start_offset_y', -oval.start_offset.x),
            new_prc_float('start_offset_z',  oval.start_offset.z),
            new_prc_float('end_offset_x',  oval.end_offset.y),
            new_prc_float('end_offset_y', -oval.end_offset.x),
            new_prc_float('end_offset_z',  oval.end_offset.z),
        ])
    prc_root += ovals_list

    # add ellipsoids
    ellipsoids_list = PrcList('ellipsoids')
    for ellipsoid in ssd.ellipsoids:
        ellipsoids_list += PrcStruct([
            new_prc_hash('name', ellipsoid.name),
            new_prc_hash('bonename', ellipsoid.bone_name.lower()),
            new_prc_float('cx',  ellipsoid.offset.y),
            new_prc_float('cy', -ellipsoid.offset.x),
            new_prc_float('cz',  ellipsoid.offset.z),
            new_prc_float('rx',  ellipsoid.rotation.y),
            new_prc_float('ry', -ellipsoid.rotation.x),
            new_prc_float('rz',  ellipsoid.rotation.z),
            new_prc_float('sx',  ellipsoid.scale.y),
            new_prc_float('sy',  ellipsoid.scale.x),
            new_prc_float('sz',  ellipsoid.scale.z),
        ])
    prc_root += ellipsoids_list

    # add capsules
    capsules_list = PrcList('capsules')
    for capsule in ssd.capsules:
        capsules_list += PrcStruct([
            new_prc_hash('name', capsule.name),
            new_prc_hash('start_bonename', capsule.start_bone_name.lower()),
            new_prc_hash('end_bonename', capsule.end_bone_name.lower()),
            new_prc_float('start_offset_x',  capsule.start_offset.y),
            new_prc_float('start_offset_y', -capsule.start_offset.x),
            new_prc_float('start_offset_z',  capsule.start_offset.z),
            new_prc_float('end_offset_x',  capsule.end_offset.y),
            new_prc_float('end_offset_y', -capsule.end_offset.x),
            new_prc_float('end_offset_z',  capsule.end_offset.z),
            new_prc_float('start_radius',  capsule.start_radius),
            new_prc_float('end_radius',  capsule.end_radius),
        ])
    prc_root += capsules_list

    # add planes
    planes_list = PrcList('planes')
    for plane in ssd.planes:
        planes_list += PrcStruct([
            new_prc_hash('name', plane.name),
            new_prc_hash('bonename', plane.bone_name.lower()),
            new_prc_float('nx',  plane.nx),
            new_prc_float('ny',  plane.ny),
            new_prc_float('nz',  plane.nz),
            new_prc_float('distance', plane.distance),
        ])
    prc_root += planes_list

    # add connections
    connections_list = PrcList('connections')
    for connection in ssd.connections:
        connections_list += PrcStruct([
            new_prc_hash('start_bonename', connection.start_bone_name.lower()),
            new_prc_hash('end_bonename', connection.end_bone_name.lower()),
            new_prc_float('radius', connection.radius),
            new_prc_float('length', connection.length),
        ])
    prc_root += connections_list

    # add swing bone collisions lists
    for swing_bone_chain in ssd.swing_bone_chains:
        for swing_bone in swing_bone_chain.swing_bones:
            swing_bone_collision_list = PrcList(swing_bone.name.lower() + 'col')
            for collision in swing_bone.collisions:
                swing_bone_collision_list += PrcHash40(collision.target_collision_name)
            prc_root += swing_bone_collision_list

    prc_root.save(filepath)

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
    has_unk_8: BoolProperty(name='Has Unk 8', default=False)
    unk_8: IntProperty(name='0x0f7316a113', default=0)
    swing_bones: CollectionProperty(type=SwingBone)
    # Properties below are for UI Only
    active_swing_bone_index: IntProperty(name='Active Bone Index', default=0)

class Sphere(PropertyGroup):
    name: StringProperty(name='Sphere Name Hash40')
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

class Oval(PropertyGroup):
    name: StringProperty(name='Oval Name Hash40')
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

class Ellipsoid(PropertyGroup):
    name: StringProperty(name='Ellipoid Name Hash40')
    bone_name: StringProperty(name='BoneName Hash40')
    offset: FloatVectorProperty(name='Offset', subtype='XYZ', size=3)
    rotation: FloatVectorProperty(name='Rotation', subtype='XYZ', size=3)
    scale: FloatVectorProperty(name='Scale', subtype='XYZ', size=3)
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Ellipse Object',
    )


class Capsule(PropertyGroup):
    name: StringProperty(name='Capsule Name Hash40')
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

class Plane(PropertyGroup):
    name: StringProperty(name='Plane Name Hash40')
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

class Connection(PropertyGroup):
    start_bone_name: StringProperty(name='Start Bone Name Hash40')
    end_bone_name: StringProperty(name='End Bone Name Hash40')
    radius: FloatProperty(name='Radius')
    length: FloatProperty(name='Length')
    # Store the blender object for optimization
    blender_object: PointerProperty(
        type=bpy.types.Object,
        name='Connection Object',
    )

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
    active_sphere_index: IntProperty(name='Active Sphere', default=0)
    active_oval_index: IntProperty(name='Active Oval', default=0)
    active_ellipsoid_index: IntProperty(name='Active Ellipsoid', default=0)
    active_capsule_index: IntProperty(name='Active Capsule', default=0)
    active_plane_index: IntProperty(name='Active Plane', default=0)
    active_connection_index: IntProperty(name='Active Connection', default=0)

# This is for UI only
class SubSwingBlenderBoneData(PropertyGroup):
    swing_bone_chain_index: IntProperty(
        name='Index of swing bone chain this bone belongs to',
        default= -1,
    )
    swing_bone_index: IntProperty(
        name='Index of the swing bone data of this bone',
        default= -1,
    )
