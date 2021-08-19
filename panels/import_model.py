import os
import bpy
import os.path
from bpy.props import StringProperty

from bpy_extras.io_utils import ImportHelper

import mathutils
import time
import bmesh

class ImportModelPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Model Importer'
    bl_options = {'DEFAULT_CLOSED'}

    '''
    def find_model_files(self, context):
        all_files = os.listdir(context.scene.sub_model_folder_path)
        model_files = [file for file in all_files if 'model' in file]
        for model_file in model_files:
            extension = model_file.split('.')[1]
            if 'numshb' == extension:
                context.scene.sub_model_numshb_file_name = model_file
            elif 'nusktb' == extension:
                context.scene.sub_model_nusktb_file_name = model_file
            elif 'numdlb' == extension:
                context.scene.sub_model_numdlb_file_name = model_file
    '''
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        
        if '' == context.scene.sub_model_folder_path:
            row = layout.row(align=True)
            row.label(text='Please select a folder...')
            row = layout.row(align=True)
            row.operator('sub.ssbh_model_folder_selector', icon='ZOOM_ALL', text='Browse for the model folder')
            return
        
        row = layout.row(align=True)
        row.label(text='Selected Folder: "' + context.scene.sub_model_folder_path +'"')
        row = layout.row(align=True)
        row.operator('sub.ssbh_model_folder_selector', icon='ZOOM_ALL', text='Browse for a different model folder')

        all_requirements_met = True
        min_requirements_met = True
        if '' == context.scene.sub_model_numshb_file_name:
            row = layout.row(align=True)
            row.alert = True
            row.label(text='No .numshb file found! Cannot import without it!', icon='ERROR')
            all_requirements_met = False
            min_requirements_met = False

        else:
            row = layout.row(align=True)
            row.alert = False
            row.label(text='NUMSHB file: "' + context.scene.sub_model_numshb_file_name+'"', icon='FILE')

        if '' == context.scene.sub_model_nusktb_file_name:
            row = layout.row(align=True)
            row.alert = True
            row.label(text='No .nusktb file found! Cannot import without it!', icon='ERROR')
            all_requirements_met = False
            min_requirements_met = False
        else:
            row = layout.row(align=True)
            row.alert = False
            row.label(text='NUSKTB file: "' + context.scene.sub_model_nusktb_file_name+'"', icon='FILE')

        if '' == context.scene.sub_model_numdlb_file_name:
            row = layout.row(align=True)
            row.alert = True
            row.label(text='No .numdlb file found! Can import, but without materials...', icon='ERROR')
            all_requirements_met = False
        else:
            row = layout.row(align=True)
            row.alert = False
            row.label(text='NUMDLB file: "' + context.scene.sub_model_numdlb_file_name+'"', icon='FILE')

        if '' ==  context.scene.sub_model_numatb_file_name:
            row = layout.row(align=True)
            row.alert = True
            row.label(text='No .numatb file found! Can import, but without materials...', icon='ERROR')
            all_requirements_met = False
        else:
            row = layout.row(align=True)
            row.alert = False
            row.label(text='NUMATB file: "' + context.scene.sub_model_numatb_file_name+'"', icon='FILE')

        if not min_requirements_met:
            row = layout.row(align=True)
            row.alert = True
            row.label(text='Needs .NUMSHB and .NUSKTB at a minimum to import!', icon='ERROR')
            return
        elif not all_requirements_met:
            row = layout.row(align=True)
            row.operator('sub.model_importer', icon='IMPORT', text='Limited Model Import')
        else:
            row = layout.row(align=True)
            row.operator('sub.model_importer', icon='IMPORT', text='Import Model')
        

class ModelFolderSelector(bpy.types.Operator, ImportHelper):
    bl_idname = 'sub.ssbh_model_folder_selector'
    bl_label = 'Folder Selector'

    filter_glob: StringProperty(
        default='',
        options={'HIDDEN'}
    )
    def execute(self, context):
        context.scene.sub_model_numshb_file_name = '' 
        context.scene.sub_model_nusktb_file_name = '' 
        context.scene.sub_model_numdlb_file_name = '' 
        context.scene.sub_model_numatb_file_name = ''  
        print(self.filepath)
        context.scene.sub_model_folder_path = self.filepath
        all_files = os.listdir(context.scene.sub_model_folder_path)
        model_files = [file for file in all_files if 'model' in file]
        for model_file in model_files:
            print(model_file)
            name, extension = os.path.splitext(model_file)
            print(extension)
            if '.numshb' == extension:
                context.scene.sub_model_numshb_file_name = model_file
            elif '.nusktb' == extension:
                context.scene.sub_model_nusktb_file_name = model_file
            elif '.numdlb' == extension:
                context.scene.sub_model_numdlb_file_name = model_file
            elif '.numatb' == extension:
                context.scene.sub_model_numatb_file_name = model_file
        return {'FINISHED'}

class ModelImporter(bpy.types.Operator):
    bl_idname = 'sub.model_importer'
    bl_label = 'Model Importer'

    def execute(self, context):
        import_model(self,context)
        return {'FINISHED'}

def import_model(self, context):
    from ..ssbh_data_py import ssbh_data_py
    dir = context.scene.sub_model_folder_path
    mumdlb_name = context.scene.sub_model_numdlb_file_name
    numshb_name = context.scene.sub_model_numshb_file_name
    nusktb_name = context.scene.sub_model_nusktb_file_name
    numatb_name = context.scene.sub_model_numatb_file_name
    
    mesh = ssbh_data_py.mesh_data.read_mesh(dir + numshb_name)
    skel = ssbh_data_py.skel_data.read_skel(dir + nusktb_name)

    armature = create_armature(skel, context)
    create_mesh(mesh, skel, armature, context)

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    return


'''
The following code is mostly shamelessly stolen from SMG
'''
def get_matrix4x4_blender(ssbh_matrix):
    return mathutils.Matrix(ssbh_matrix).transposed()


def find_bone(skel, name):
    for bone in skel.bones:
        if bone.name == name:
            return bone

    return None


def find_bone_index(skel, name):
    for i, bone in enumerate(skel.bones):
        if bone.name == name:
            return i

    return None


def create_verts(bm, mesh_object, skel):
    for (index, (pos, nrm)) in enumerate(zip(mesh_object.positions[0].data, mesh_object.normals[0].data)):
        # Vertex attributes
        # TODO: Tangents/bitangents?
        # Ok but fr need to figure out tangents/bitangents in blender
        vert = bm.verts.new()
        vert.co = pos[:3]
        vert.normal = nrm[:3] # <--- Funny prank, this doesn't actually set the custom normals in blender
        vert.index = index


    # Make sure the indices are set to make faces.
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()

    # Meshes can only have a single deform layer active at a time.
    # The mesh was just recently created, so create the new layer.
    weight_layer = bm.verts.layers.deform.new()

    # Set the vertex skin weights for each bone.
    if skel is not None:
        for influence in mesh_object.bone_influences:
            bone_index = find_bone_index(skel, influence.bone_name)
            if bone_index is not None:
                for w in influence.vertex_weights:
                    bm.verts[w.vertex_index][weight_layer][bone_index] = w.vertex_weight

    # Set the vertex skin weights for single bind meshes
    if skel is not None:
        parent_bone = find_bone(skel, mesh_object.parent_bone_name)
        if parent_bone is not None: # This is a single bind mesh
            bone_index = find_bone_index(skel, parent_bone.name)
            for vert in bm.verts:
                vert[weight_layer][bone_index] = 1.0

def create_faces(bm, mesh):
    # Create the faces from vertices.
    for i in range(0, len(mesh.vertex_indices), 3):
        # This will fail if the face has already been added.
        v0, v1, v2 = mesh.vertex_indices[i:i+3]
        try:
            face = bm.faces.new([bm.verts[v0], bm.verts[v1], bm.verts[v2]])
            face.smooth = True
        except:
            continue

    bm.faces.ensure_lookup_table()
    bm.faces.index_update()


def create_uvs(bm, mesh):
    for attribute_data in mesh.texture_coordinates:
        uv_layer = bm.loops.layers.uv.new(attribute_data.name)

        for face in bm.faces:
            for loop in face.loops:
                # Get the index of the vertex the loop contains.
                loop[uv_layer].uv = attribute_data.data[loop.vert.index][:2]


def create_color_sets(bm, mesh):
    for attribute_data in mesh.color_sets:
        color_layer = bm.loops.layers.color.new(attribute_data.name)

        for face in bm.faces:
            for loop in face.loops:
                # Get the index of the vertex the loop contains.
                loop[color_layer] = attribute_data.data[loop.vert.index]


def create_armature(skel, context):
    start = time.time()
    
    # Create a new armature and select it.
    base_skel_name = "new_armature"
    armature = bpy.data.objects.new(base_skel_name, bpy.data.armatures.new(base_skel_name))
    given_skel_obj_name = armature.name
    given_skel_data_name = armature.data.name

    armature.rotation_mode = 'QUATERNION'

    armature.show_in_front = True

    context.view_layer.active_layer_collection.collection.objects.link(armature)
    context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    # HACK: Store Transform in order to assign the matrix to the blender bone after bones been parented
    bone_to_matrix_dict = {}
    for bone_data in skel.bones:
        new_bone = armature.data.edit_bones.new(bone_data.name)
        
        world_transform = skel.calculate_world_transform(bone_data)

           
        matrix_world = get_matrix4x4_blender(world_transform)
        print('bone name =%s: \n\tworld_transform = %s,\n\t matrix_world = %s' % (bone_data.name, world_transform, matrix_world)) 
        # Assign transform pre-parenting
        new_bone.transform(matrix_world, scale=True, roll=False)
        #new_bone.matrix = matrix_world <--- Doesnt actually do anything here lol
        bone_to_matrix_dict[new_bone] = matrix_world
        print('bone name = %s: \n\tnew_bone.matrix= %s' % (bone_data.name, new_bone.matrix))
        new_bone.length = 1
        new_bone.use_deform = True
        new_bone.use_inherit_rotation = True
        new_bone.use_inherit_scale = True

    # Associate each bone with its parent.
    for bone_data in skel.bones: 
        current_bone = armature.data.edit_bones[bone_data.name]
        if bone_data.parent_index is not None:
            try:
                current_bone.parent = armature.data.edit_bones[bone_data.parent_index]
            except:
                continue
        else:
            # HACK: Prevent root bones from being removed
            #current_bone.tail[1] = current_bone.tail[1] - 0.001
            pass
    # HACK: Use that matrix dict from earlier to re-assign matrixes
    for bone_data in skel.bones:
        current_bone = armature.data.edit_bones[bone_data.name]
        matrix = bone_to_matrix_dict[current_bone]
        current_bone.matrix = matrix
        print ('current_bone=%s:\n\t matrix=%s\n\t current_bone.matrix = %s' % (current_bone.name, matrix, current_bone.matrix))

    end = time.time()
    print(f'Created armature in {end - start} seconds')

    return armature


def attach_armature_create_vertex_groups(mesh_obj, skel, armature, parent_bone_name):
    if skel is not None:
        # Create vertex groups for each bone to support skinning.
        for bone in skel.bones:
            mesh_obj.vertex_groups.new(name=bone.name)

        # Apply the initial parent bone transform for single bound meshes.
        parent_bone = find_bone(skel, parent_bone_name)
        if parent_bone is not None:
            world_transform = skel.calculate_world_transform(parent_bone)
            mesh_obj.matrix_world = get_matrix4x4_blender(world_transform)

    # Attach the mesh object to the armature object.
    if armature is not None:
        mesh_obj.parent = armature
        for bone in armature.data.bones.values():
            mesh_obj.vertex_groups.new(name=bone.name)
        modifier = mesh_obj.modifiers.new(armature.data.name, type="ARMATURE")
        modifier.object = armature


def create_blender_mesh(mesh_object, skel):
    blender_mesh = bpy.data.meshes.new(mesh_object.name)

    # Using bmesh is faster than from_pydata and setting additional vertex parameters.
    bm = bmesh.new()

    create_verts(bm, mesh_object, skel)
    create_faces(bm, mesh_object)
    create_uvs(bm, mesh_object)
    create_color_sets(bm, mesh_object)

    bm.to_mesh(blender_mesh)
    bm.free()

    # Now that the mesh is created, now we can assign split custom normals
    blender_mesh.use_auto_smooth = True # Required to use custom normals
    vertex_normals = mesh_object.normals[0].data
    blender_mesh.normals_split_custom_set_from_vertices([(vn[0], vn[1], vn[2]) for vn in vertex_normals])
    return blender_mesh


def create_mesh(mesh, skel, armature, context):
    for mesh_object in mesh.objects:
        blender_mesh = create_blender_mesh(mesh_object, skel)
        mesh_obj = bpy.data.objects.new(blender_mesh.name, blender_mesh)
        
        attach_armature_create_vertex_groups(mesh_obj, skel, armature, mesh_object.parent_bone_name)

        context.collection.objects.link(mesh_obj)