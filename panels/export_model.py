import os
import bpy
import os.path

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, Panel
import re
from ..ssbh_data_py import ssbh_data_py

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
    if include_numdlb:
        export_numdlb(context, filepath)
    if include_numshb:
        export_numshb(context, filepath)
    if include_nusktb:
        if '' == context.scene.sub_vanilla_nusktb or 'NO_LINK' == linked_nusktb_settings:
            export_nusktb_no_link(context, filepath)
        else:
            export_nusktb(context, filepath, linked_nusktb_settings)

def export_numdlb(context, filepath):
    arma = context.scene.sub_model_export_armature

def export_numshb(context, filepath):
    arma = context.scene.sub_model_export_armature
    export_meshes = [child for child in arma.children if child.type == 'MESH']
    ssbh_mesh_data = ssbh_data_py.mesh_data.MeshData()

    for mesh in export_meshes:
        '''
        Need to Make a copy of the mesh, split by material, apply transforms, and validate for potential errors.

        list of potential issues that need to validate
        1.) Shape Keys 2.) Negative Scaling 3.) Invalid Materials
        '''
        mesh_object_copy = mesh.copy() # Copy the Mesh Object
        mesh_object_copy.data = mesh.data.copy() # Make a copy of the mesh DATA, so that the original remains unmodified
        mesh_data_copy = mesh_object_copy.data
        real_mesh_name = re.split(r'.\d\d\d', mesh.name)[0] # Un-uniquify the names
        ssbh_mesh_object = ssbh_data_py.mesh_data.MeshObjectData(real_mesh_name, 0)

        position0 = ssbh_data_py.mesh_data.AttributeData('Postion0')
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

        # Python magic to flatten the faces into a single list of vertex indices.
        ssbh_mesh_object.vertex_indices = [index for face in mesh_data_copy.polygons for index in face.vertices]

        # Export Weights

        # Export Maps

        
        bpy.data.meshes.remove(mesh_data_copy)

        ssbh_mesh_data.objects.append(ssbh_mesh_object)

    ssbh_mesh_data.save(filepath + 'model.numshb')

    return

def export_nusktb_no_link(context, filepath):
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

    ssbh_skel.save(filepath + 'model.nusktb')

    bpy.ops.object.mode_set(mode='OBJECT')
    arma.select_set(False)
    bpy.context.view_layer.objects.active = None
    return

def export_nusktb(context, filepath, linked_nusktb_settings):
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

    ssbh_skel.save(filepath + 'model.nusktb')

    bpy.ops.object.mode_set(mode='OBJECT')
    arma.select_set(False)
    bpy.context.view_layer.objects.active = None
    return


        