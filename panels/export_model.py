import os
from .import_model import get_color_scale
import bpy
import os.path

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, Panel
import re
from ..ssbh_data_py import ssbh_data_py
import bmesh
import sys

class ExportModelPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Model Exporter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        row = layout.row(align=True)
        row.label(text='Select an armature. The armature + its meshes will be exported')

        row = layout.row(align=True)
        row.prop(context.scene, 'sub_model_export_armature', icon='ARMATURE_DATA')

        if not context.scene.sub_model_export_armature:
            return
        
        if '' == context.scene.sub_vanilla_nusktb:
            row = layout.row(align=True)
            row.label(text='Please select the vanilla .nusktb for the exporter to reference!')
            row = layout.row(align=True)
            row.label(text='Impossible to accurately replace an existing ultimate fighter skeleton without it...')
            row = layout.row(align=True)
            row.label(text='If you know you really dont need to link it, then go ahead and skip this step and export...')
            row = layout.row(align=True)
            row.operator('sub.vanilla_nusktb_selector', icon='FILE', text='Select Vanilla Nusktb')
        else:
            row = layout.row(align=True)
            row.label(text='Selected reference .nusktb: ' + context.scene.sub_vanilla_nusktb)
            row = layout.row(align=True)
            row.operator('sub.vanilla_nusktb_selector', icon='FILE', text='Re-Select Vanilla Nusktb')

        row = layout.row(align=True)
        row.operator('sub.model_exporter', icon='EXPORT', text='Export Model Files to a Folder')
    
class VanillaNusktbSelector(Operator, ImportHelper):
    bl_idname = 'sub.vanilla_nusktb_selector'
    bl_label = 'Vanilla Nusktb Selector'

    filter_glob: StringProperty(
        default='*.nusktb',
        options={'HIDDEN'}
    )
    def execute(self, context):
        context.scene.sub_vanilla_nusktb = self.filepath
        return {'FINISHED'}   

class ModelExporterOperator(Operator, ImportHelper):
    bl_idname = 'sub.model_exporter'
    bl_label = 'Export To This Folder'

    filter_glob: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped. Also blender has this in the example but tbh idk what it does yet
    )

    include_numdlb: BoolProperty(
        name="Export .NUMDLB",
        description="Export .NUMDLB",
        default=True,
    )
    include_numshb: BoolProperty(
        name="Export .NUMSHB",
        description="Export .NUMSHB",
        default=True,
    )
    include_numshexb: BoolProperty(
        name="Export .NUMSHEXB",
        description="Export .NUMSHEXB",
        default=True,
    )
    include_nusktb: BoolProperty(
        name="Export .NUSKTB",
        description="Export .NUSKTB",
        default=True,
    )
    include_numatb: BoolProperty(
        name="Export .NUMATB",
        description="Export .NUMATB",
        default=True,
    )
    linked_nusktb_settings: EnumProperty(
        name="Bone Linkage",
        description="Pick 'Order & Values' unless you intentionally edited the vanilla bones.",
        items=(
            ('ORDER_AND_VALUES', "Order & Values", "Pick this one unless u know not too"),
            ('ORDER_ONLY', "Order Only", "Pick this if you edited the vanilla bones"),
            ('NO_LINK', "No Link", "Pick this if you really know what ur doing"),
        ),
        default='ORDER_AND_VALUES',
    )
    
    def execute(self, context):
        export_model(context, self.filepath, self.include_numdlb, self.include_numshb, self.include_numshexb,
                     self.include_nusktb, self.include_numatb, self.linked_nusktb_settings)
        return {'FINISHED'}

def export_model(context, filepath, include_numdlb, include_numshb, include_numshexb, include_nusktb, include_numatb, linked_nusktb_settings):
    '''
    numdlb and numshb are inherently linked, must export both if exporting one
    if include_numdlb:
        export_numdlb(context, filepath)
    '''
    ssbh_skel_data = None
    if '' == context.scene.sub_vanilla_nusktb or 'NO_LINK' == linked_nusktb_settings:
        ssbh_skel_data = make_skel_no_link(context)
    else:
        ssbh_skel_data = make_skel(context, linked_nusktb_settings)
    
    ssbh_modl_data = None
    ssbh_mesh_data = None
    ssbh_matl_json = None
    ssbh_modl_data, ssbh_mesh_data, ssbh_matl_json= make_modl_mesh_matl_data(context, ssbh_skel_data)

    if include_numdlb:
        ssbh_modl_data.save(filepath + 'model.numdlb')
    if include_numshb:
        ssbh_mesh_data.save(filepath + 'model.numshb')
    if include_nusktb:
        ssbh_skel_data.save(filepath + 'model.nusktb')
    if include_numatb:
        save_matl_json(ssbh_matl_json)

def save_matl_json(ssbh_matl_json):
    return

'''
def export_numdlb(context, filepath):
    arma = context.scene.sub_model_export_armature
    ssbh_model = ssbh_data_py.modl_data.ModlData()
    ssbh_model.model_name = 'model'
    ssbh_model.skeleton_file_name = 'model.nusktb'
    ssbh_model.material_file_names = ['model.numatb']
    ssbh_model.animation_file_name = None
'''
def get_material_label_from_mesh(mesh):
    material = mesh.material_slots[0].material
    nodes = material.node_tree.nodes
    node_group_node = nodes['smash_ultimate_shader']
    mat_label = node_group_node.inputs['Material Name'].default_value

    return mat_label

def find_bone_index(skel, name):
    for i, bone in enumerate(skel.bones):
        if bone.name == name:
            return i

    return None

def make_modl_mesh_matl_data(context, ssbh_skel_data):

    ssbh_mesh_data = ssbh_data_py.mesh_data.MeshData()
    ssbh_modl_data = ssbh_data_py.modl_data.ModlData()
    ssbh_matl_data = None

    ssbh_modl_data.model_name = 'model'
    ssbh_modl_data.skeleton_file_name = 'model.nusktb'
    ssbh_modl_data.material_file_names = ['model.numatb']
    ssbh_modl_data.animation_file_name = None
    ssbh_modl_data.mesh_file_name = 'model.numshb'

    arma = context.scene.sub_model_export_armature
    export_meshes = [child for child in arma.children if child.type == 'MESH']
    export_meshes = [m for m in export_meshes if len(m.data.vertices) > 0] # Skip Empty Objects

    '''
    # TODO split meshes
    Potential uv_layer clean_up code?
    remove = [uv_layer for uv_layer in mesh.data.uv_layers if all([uv == 0.0 for data in uv_layer.data for uv in data.uv])]
    for l in remove:
        mesh.data.uv_layers.remove(l)
    '''
    #  Gather Material Info
    

    real_mesh_name_list = []
    for mesh in export_meshes:
        '''
        Need to Make a copy of the mesh, split by material, apply transforms, and validate for potential errors.

        list of potential issues that need to validate
        1.) Shape Keys 2.) Negative Scaling 3.) Invalid Materials
        '''
        mesh_object_copy = mesh.copy() # Copy the Mesh Object
        mesh_object_copy.data = mesh.data.copy() # Make a copy of the mesh DATA, so that the original remains unmodified
        mesh_data_copy = mesh_object_copy.data
        #mesh_data_copy = mesh.data.copy()
        #mesh_object_copy = bpy.data.objects.new(mesh.name, mesh_data_copy)
        real_mesh_name = re.split(r'.\d\d\d', mesh.name)[0] # Un-uniquify the names

        # Quick Detour to file out MODL stuff
        ssbh_mesh_object_sub_index = real_mesh_name_list.count(real_mesh_name)
        real_mesh_name_list.append(real_mesh_name)
        mat_label = get_material_label_from_mesh(mesh)
        ssbh_modl_entry = ssbh_data_py.modl_data.ModlEntryData(real_mesh_name, ssbh_mesh_object_sub_index, mat_label)
        ssbh_modl_data.entries.append(ssbh_modl_entry)

        # Back to MESH stuff
        ssbh_mesh_object = ssbh_data_py.mesh_data.MeshObjectData(real_mesh_name, ssbh_mesh_object_sub_index)
        position0 = ssbh_data_py.mesh_data.AttributeData('Position0')
        position0.data = [list(vertex.co[:]) for vertex in mesh_data_copy.vertices] # Thanks SMG for these one-liners 
        ssbh_mesh_object.positions = [position0]

        normal0 = ssbh_data_py.mesh_data.AttributeData('Normal0')
        #normal0.data = [list(vertex.normal[:]) for vertex in mesh.data.vertices] <-- omg why cant this just contain custom normal data
        # So we gotta go through loop by loop
        # mesh.data.loops[index].normal contains the actual custom normal data
        index_to_normals_dict = {} # Dont judge the internet told me list insertion was bugged plus dictionaries are goated
        mesh_data_copy.calc_normals_split() # Needed apparently or the vertex normal data wont be filled 
        for loop in mesh_data_copy.loops:
            index_to_normals_dict[loop.vertex_index] = loop.normal[:]
        normal0.data = [list(index_to_normals_dict[key]) for key in sorted(index_to_normals_dict.keys())]
        ssbh_mesh_object.normals = [normal0]
        

        # Calculate Tangents
        # it is so hard to find examples of this online pls if you know how to better calculate tangents
        # please let me know
        tangent0 = ssbh_data_py.mesh_data.AttributeData('Tangent0')
        try:
            mesh_data_copy.calc_tangents()
        except RuntimeError as err:
            print(f'Could Not Calculate Tangents for mesh {mesh.name}, skipping for now, err = {err}')
            print(f'For reference, this is the meshs uvmaps{mesh.data.uv_layers.items()}')
            print(f'and now the copies {mesh_data_copy.uv_layers.items()}')
        else:
            index_to_tangents_dict = {l.vertex_index : [l.tangent[0], l.tangent[1], l.tangent[2], -1.0 * l.bitangent_sign] for l in mesh_data_copy.loops}
            sorted_dict = sorted(index_to_tangents_dict.items())
            tangent0.data = [val for index, val in sorted_dict]
            ssbh_mesh_object.tangents = [tangent0]

            mesh_data_copy.free_normals_split()
            mesh_data_copy.free_tangents()

        # Python magic to flatten the faces into a single list of vertex indices.
        #ssbh_mesh_object.vertex_indices = [index for face in mesh_data_copy.polygons for index in face.vertices]
        ssbh_mesh_object.vertex_indices = [loop.vertex_index for loop in mesh_data_copy.loops]



        # Export Weights
        blender_weight_layer = 0 # TODO: Research weight layers
        
        index_to_name_dict = {vg.index: vg.name for vg in mesh_object_copy.vertex_groups}
       
        bone_name_to_vertex_weights = {bone.name : [] for bone in ssbh_skel_data.bones}

        for vertex in mesh_data_copy.vertices:
            for group in vertex.groups:
                group_index = group.group
                weight = group.weight
                group_name = index_to_name_dict[group_index]
                bone_index = find_bone_index(ssbh_skel_data, group_name)
                if bone_index is None:
                    continue
                ssbh_vertex_weight = ssbh_data_py.mesh_data.VertexWeight(vertex.index, weight)
                bone_name_to_vertex_weights[group_name].append(ssbh_vertex_weight)
        
        BoneInfluence = ssbh_data_py.mesh_data.BoneInfluence
        ssbh_mesh_object.bone_influences = [BoneInfluence(name, weights) for name, weights in bone_name_to_vertex_weights.items()]

        '''
        # Export color sets
        for vertex_color_layer in mesh_data_copy.vertex_colors:
            ssbh_color_set = ssbh_data_py.mesh_data.AttributeData(vertex_color_layer.name)
            scale = get_color_scale(vertex_color_layer.name)
            ssbh_color_set.data = [list(val / scale for val in vc.color[:]) for vc in vertex_color_layer.data.values()]
            if real_mesh_name == 'TopN_1_Shape1' and ssbh_mesh_object_sub_index == 0:
                print('%s %s' % (ssbh_color_set.name, len(ssbh_color_set.data)))
                print('%s %s' % (ssbh_color_set.name, ssbh_color_set.data))

            
            ssbh_mesh_object.color_sets.append(ssbh_color_set)       
        '''
        '''
        for vertex_color_layer in mesh_data_copy.vertex_colors:
            ssbh_color_set = ssbh_data_py.mesh_data.AttributeData(vertex_color_layer.name)
            vertex_index_to_vertex_color = {loop.vertex_index : vertex_color_layer.data[loop.index].color[:] for loop in mesh_data_copy.loops}
            scale = get_color_scale(vertex_color_layer.name)       
            ssbh_color_set.data = [[index / scale for index in val] for val in vertex_index_to_vertex_color.values()]
            ssbh_mesh_object.color_sets.append(ssbh_color_set) 
        
        # Export UV maps
        for uv_layer in mesh_data_copy.uv_layers:
            ssbh_uv_layer = ssbh_data_py.mesh_data.AttributeData(uv_layer.name)
            vertex_index_to_vertex_uv = {loop.vertex_index : uv_layer.data[loop.index].uv for loop in mesh_data_copy.loops}
            ssbh_uv_layer.data = [[val[0], 1 - val[1]] for val in vertex_index_to_vertex_uv.values()]            
            if real_mesh_name == 'TopN_1_Shape1' and ssbh_mesh_object_sub_index == 0:
                print('%s %s' % (ssbh_uv_layer.name, len(ssbh_uv_layer.data)))
                #print('%s %s' % (ssbh_uv_layer.name, ssbh_uv_layer.data))
                for index, val in enumerate(ssbh_uv_layer.data):
                    print('%s  %s' % (index, val))
            ssbh_mesh_object.texture_coordinates.append(ssbh_uv_layer)
        '''
        '''
        So it seems like the issue is that i can't produce a reliable mapping between vertex_index to vertex,
        but with bmesh i can avoid the issue
        '''
        context.collection.objects.link(mesh_object_copy)
        context.view_layer.update()
        context.view_layer.objects.active = mesh_object_copy
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(mesh_object_copy.data)
        # Export UV Maps
        for uv_layer in bm.loops.layers.uv.values():
            ssbh_uv_layer = ssbh_data_py.mesh_data.AttributeData(uv_layer.name)
            v_to_uvs = {}
            for v in bm.verts:
                for l in v.link_loops:
                    uv_data = l[uv_layer]
                    v_to_uvs[v] = uv_data.uv
            fixed = [[uv[0], 1 - uv[1]] for uv in v_to_uvs.values()]
            ssbh_uv_layer.data = fixed
            ssbh_mesh_object.texture_coordinates.append(ssbh_uv_layer)
        # Export Color Set 
        for color_set_layer in bm.loops.layers.color.values():
            ssbh_color_set = ssbh_data_py.mesh_data.AttributeData(color_set_layer.name)
            v_to_color_set = {v : l[color_set_layer] for v in bm.verts for l in v.link_loops}
            scale = get_color_scale(color_set_layer.name)
            fixed = [[i / scale for i in col] for col in v_to_color_set.values()]
            ssbh_color_set.data = fixed
            ssbh_mesh_object.color_sets.append(ssbh_color_set)


        bm.free()
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.data.meshes.remove(mesh_data_copy)
        #bpy.data.objects.remove(mesh_object_copy)
        ssbh_mesh_data.objects.append(ssbh_mesh_object)

    #ssbh_mesh_data.save(filepath + 'model.numshb')
    #ssbh_model_data.save(filepath + 'model.numdlb')
    return ssbh_modl_data, ssbh_mesh_data

def make_skel_no_link(context):
    arma = context.scene.sub_model_export_armature
    bpy.context.view_layer.objects.active = arma
    arma.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    ssbh_skel = ssbh_data_py.skel_data.SkelData()
    edit_bones = arma.data.edit_bones
    edit_bones_list = list(edit_bones)
    for edit_bone in edit_bones_list:
        if edit_bone.use_deform == False:
            continue
        ssbh_bone = None
        if edit_bone.parent is not None:
            rel_mat = edit_bone.parent.matrix.inverted() @ edit_bone.matrix
            ssbh_bone = ssbh_data_py.skel_data.BoneData(edit_bone.name, rel_mat.transposed(), edit_bones_list.index(edit_bone.parent))
        else:
            ssbh_bone = ssbh_data_py.skel_data.BoneData(edit_bone.name, edit_bone.matrix.transposed(), None)
        ssbh_skel.bones.append(ssbh_bone) 

    #ssbh_skel.save(filepath + 'model.nusktb')

    bpy.ops.object.mode_set(mode='OBJECT')
    arma.select_set(False)
    bpy.context.view_layer.objects.active = None
    return ssbh_skel

def make_skel(context, linked_nusktb_settings):
    '''
    Wow i wrote this terribly lol, #TODO ReWrite this
    '''
    arma = context.scene.sub_model_export_armature
    bpy.context.view_layer.objects.active = arma
    arma.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    
    normal_bones = []
    swing_bones = []
    misc_bones = []
    null_bones = []
    helper_bones = []

    output_bones = {}
    eb = arma.data.edit_bones
    keys = eb.keys()
    for key in keys:
        if 'S_' in key:
            swing_bones.append(eb[key])
        elif any(ss in key for ss in ['_eff', '_offset'] ):
            null_bones.append(eb[key])
        elif 'H_' in key:
            helper_bones.append(eb[key])
        elif any(ss in key for ss in ['Mouth', 'Finger', 'Face']) or key == 'Have':
            misc_bones.append(eb[key])
            for child in eb[key].children_recursive:
                if any(ss in child.name for ss in ['_eff', '_offset']):
                    continue
                misc_bones.append(child)
                keys.remove(child.name)
        else:
            normal_bones.append(eb[key])
            
    for boneList in [normal_bones, swing_bones, misc_bones, null_bones, helper_bones]:
        for bone in boneList:
            if bone.use_deform == False:
                continue
            output_bones[bone.name] = bone
    
    ssbh_skel = ssbh_data_py.skel_data.SkelData()
 
    if '' != context.scene.sub_vanilla_nusktb:
        reordered_bones = []
        vanilla_ssbh_skel = ssbh_data_py.skel_data.read_skel(context.scene.sub_vanilla_nusktb)
        for vanilla_ssbh_bone in vanilla_ssbh_skel.bones:
            linked_bone = output_bones.get(vanilla_ssbh_bone.name)
            reordered_bones.append(linked_bone)
            del output_bones[linked_bone.name]
        
        for remaining_bone in output_bones:
            reordered_bones.append(remaining_bone)
        
        ssbh_bone_name_to_bone_dict = {}
        for ssbh_bone in vanilla_ssbh_skel.bones:
            ssbh_bone_name_to_bone_dict[ssbh_bone.name] = ssbh_bone
        
        index = 0 # Debug
        for blender_bone in reordered_bones:
            ssbh_bone = None
            if 'ORDER_AND_VALUES' == linked_nusktb_settings:
                vanilla_ssbh_bone = ssbh_bone_name_to_bone_dict.get(blender_bone.name)
                print('OV: index %s, transform= %s' % (index, vanilla_ssbh_bone.transform))
                index = index + 1
                ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, vanilla_ssbh_bone.transform, reordered_bones.index(blender_bone.parent) if blender_bone.parent else None)
            else:
                if blender_bone.parent:
                    '''
                    blender_bone_matrix_as_list = [list(row) for row in blender_bone.matrix.transposed()]
                    blender_bone_parent_matrix_as_list = [list(row) for row in blender_bone.parent.matrix.transposed()]
                    rel_transform = ssbh_data_py.skel_data.calculate_relative_transform(blender_bone_matrix_as_list, blender_bone_parent_matrix_as_list)
                    ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, rel_transform, reordered_bones.index(blender_bone.parent))
                    '''
                    rel_mat = blender_bone.parent.matrix.inverted() @ blender_bone.matrix
                    ssbh_bone = ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, rel_mat.transposed(), reordered_bones.index(blender_bone.parent))
                    print('OO: index %s, name %s, rel_mat.transposed()= %s' % (index, blender_bone.name, rel_mat.transposed()))
                    index = index + 1
                else:
                    ssbh_bone = ssbh_data_py.skel_data.BoneData(blender_bone.name, blender_bone.matrix.transposed(), None)
            ssbh_skel.bones.append(ssbh_bone)    

    #ssbh_skel.save(filepath + 'model.nusktb')

    bpy.ops.object.mode_set(mode='OBJECT')
    arma.select_set(False)
    bpy.context.view_layer.objects.active = None
    return ssbh_skel


        