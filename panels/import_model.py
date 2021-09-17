import os
import os.path
import subprocess
import bpy
import mathutils
import time
import bmesh
import json
import re

from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from bpy_extras import image_utils

from ..operators import master_shader



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
    """
    Cancelled until further notice.
    merge_same_name_meshes: BoolProperty(
        name="Merge Same Name Meshes",
        description="Merge Same Name Meshes",
        default=True,
    )   
    """

    def execute(self, context):
        context.scene.sub_model_numshb_file_name = '' 
        context.scene.sub_model_nusktb_file_name = '' 
        context.scene.sub_model_numdlb_file_name = '' 
        context.scene.sub_model_numatb_file_name = ''  
        context.scene.sub_model_nuhlpb_file_name = ''
        #context.scene.sub_merge_same_name_meshes = self.merge_same_name_meshes
        #print(self.filepath)
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
            elif '.nuhlpb' == extension:
                context.scene.sub_model_nuhlpb_file_name = model_file
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
    numdlb_name = context.scene.sub_model_numdlb_file_name
    numshb_name = context.scene.sub_model_numshb_file_name
    nusktb_name = context.scene.sub_model_nusktb_file_name
    numatb_name = context.scene.sub_model_numatb_file_name
    nuhlpb_name = context.scene.sub_model_nuhlpb_file_name

    ssbh_model = ssbh_data_py.modl_data.read_modl(dir + numdlb_name) if numdlb_name != '' else None
    ssbh_mesh = ssbh_data_py.mesh_data.read_mesh(dir + numshb_name) if numshb_name != '' else None
    ssbh_skel = ssbh_data_py.skel_data.read_skel(dir + nusktb_name) if numshb_name != '' else None
    ssbh_material_json = load_ssbh_file_as_json(dir + numatb_name) if numshb_name != '' else None
    ssbh_helper_bone_json = load_ssbh_file_as_json(dir + nuhlpb_name) if nuhlpb_name != '' else None
    armature = create_armature(ssbh_skel, context)
    
    created_meshes = create_mesh(ssbh_model, ssbh_material_json, ssbh_mesh, ssbh_skel, armature, context)
    if ssbh_helper_bone_json is not None:
        create_helper_bone_constraints(armature, ssbh_helper_bone_json, context)
    else:
        print('Did not find a .nuhlpb, so wont create helper bone constraints')

    '''
    # TODO So merging meshes in blenders and then seperating them is terrible for UV and color layer management.
            Can't split a mesh after joining, or else all meshes will have all uv layers.
    
    if context.scene.sub_merge_same_name_meshes == True:
        real_names = {re.split(r'.\d\d\d', mesh.name)[0] for mesh in created_meshes} 
        real_name_to_meshes = {real_name: [mesh for mesh in created_meshes if real_name == re.split(r'.\d\d\d', mesh.name)[0]] for real_name in real_names}
        for mesh_list in real_name_to_meshes.values():
            if len(mesh_list) == 1:
                continue
            context.view_layer.objects.active = mesh_list[0]
            c = {}
            c['object'] = c['active_object'] = context.object
            c['selected_objects'] = c['selected_editable_objects'] = mesh_list
            bpy.ops.object.join(c)  
    '''

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    return

def get_ssbh_lib_json_exe_path():
    #print('this_file_path = %s' % (__file__))
    this_file_path = __file__
    return this_file_path + '/../../ssbh_lib_json/ssbh_lib_json.exe'

def get_shader_json_file_path():
    this_file_path = __file__
    return this_file_path + '/../../shader_file/nuc2effectlibrary.nufxlb.json'

'''
def load_numatb_json(numatb_path):
    ssbh_lib_json_exe_path = get_ssbh_lib_json_exe_path()
    print('ssbh_lib_json_exe_path = %s' % ssbh_lib_json_exe_path)
    output_json_path = numatb_path + '.json'

    # Run ssbh_lib_json
    try:
        subprocess.run([ssbh_lib_json_exe_path, numatb_path, output_json_path], capture_output=True, check=True)
    except:
        pass

    # Load Outputted Json
    numatb_json = None
    with open(output_json_path) as f:
        numatb_json = json.load(f)

    return numatb_json
'''

def load_ssbh_file_as_json(ssbh_file_path):
    ssbh_lib_json_exe_path = get_ssbh_lib_json_exe_path()
    print('ssbh_lib_json_exe_path = %s' % ssbh_lib_json_exe_path)
    output_json_path = ssbh_file_path + '.json'

    # Run ssbh_lib_json
    try:
        subprocess.run([ssbh_lib_json_exe_path, ssbh_file_path, output_json_path], capture_output=True, check=True)
    except:
        pass

    # Load Outputted Json
    ssbh_json = None
    with open(output_json_path) as f:
        ssbh_json = json.load(f)

    return ssbh_json

def create_helper_bone_constraints(armature, ssbh_helper_bone_json, context):
    ''' Currently only interpolation entries are somewhat understood'''

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE', toggle=False)
    interpolation_entries = ssbh_helper_bone_json['data']['Hlpb']['interpolation_entries']
    for entry in interpolation_entries:
        name = entry['name']
        bone_name = entry['bone_name']
        root_bone_name = entry['root_bone_name']
        parent_bone_name = entry['parent_bone_name']
        driver_bone_name = entry['driver_bone_name']
        aoi = entry['aoi']
        x, y, z = 'X', 'Y', 'Z'
        target_bone = armature.pose.bones.get(parent_bone_name)
        owner_bone = armature.pose.bones.get(driver_bone_name)
        for axis in [x, y, z]:
            crc = owner_bone.constraints.new('COPY_ROTATION')
            crc.name = f'SUB CRC {axis}'
            crc.target = armature
            crc.subtarget = target_bone.name
            crc.target_space = 'POSE'
            crc.owner_space = 'POSE'
            crc.influence = aoi['x'] if axis is x else\
                            aoi['y'] if axis is y else\
                            aoi['z']
            crc.use_x = True if axis is x else False
            crc.use_y = True if axis is y else False
            crc.use_z = True if axis is z else False

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        


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
                loop[uv_layer].uv = [attribute_data.data[loop.vert.index][0], 1 - attribute_data.data[loop.vert.index][1]] # This 'Flips' the imported UVs

def get_color_scale(color_set_name):
    scale = 2 if color_set_name == 'colorSet1' else\
            7 if color_set_name == 'colorSet2' else\
            7 if color_set_name == 'colorSet2_1' else\
            7 if color_set_name == 'colorSet2_2' else\
            7 if color_set_name == 'colorSet2_3' else\
            2 if color_set_name == 'colorSet3' else\
            2 if color_set_name == 'colorSet4' else\
            3 if color_set_name == 'colorSet5' else\
            1 if color_set_name == 'colorSet6' else\
            1 if color_set_name == 'colorSet7' else\
            1
    return scale

def create_color_sets(bm, mesh):
    for attribute_data in mesh.color_sets:
        color_layer = bm.loops.layers.color.new(attribute_data.name)

        for face in bm.faces:
            for loop in face.loops:
                # Get the index of the vertex the loop contains.
                # For ease of use and to meet user expectations, vertex colors will be scaled on import
                # For instance this will let users paint vertex colors for colorset1 without needing the user to scale
                # This scaling will be compensated for on export in this plugin.
                # Sadly this might break the vertex colors in external apps if exported via .FBX or .DAE
                # Update: So blender clamps vertex colors to 1.0, so scaling on import is not viable, will address scaling in shader
                # scale = get_color_scale(attribute_data.name)
                # loop[color_layer] = [value * scale for value in attribute_data.data[loop.vert.index]]
                loop[color_layer] = [value for value in attribute_data.data[loop.vert.index]]


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


def create_blender_mesh(ssbh_mesh_object, skel, name_index_mat_dict):
    blender_mesh = bpy.data.meshes.new(ssbh_mesh_object.name)

    # Using bmesh is faster than from_pydata and setting additional vertex parameters.
    bm = bmesh.new()

    create_verts(bm, ssbh_mesh_object, skel)
    create_faces(bm, ssbh_mesh_object)
    create_uvs(bm, ssbh_mesh_object)
    create_color_sets(bm, ssbh_mesh_object)

    bm.to_mesh(blender_mesh)
    bm.free()

    # Now that the mesh is created, now we can assign split custom normals
    blender_mesh.use_auto_smooth = True # Required to use custom normals
    vertex_normals = ssbh_mesh_object.normals[0].data
    blender_mesh.normals_split_custom_set_from_vertices([(vn[0], vn[1], vn[2]) for vn in vertex_normals])

    # Assign Tangents?
    # Tangents are read only??
    # Ok i spend way too much time googling this, not sure why i can't find how to assign
    # tangents, maybe theyre just something that gets calculated....
    


    # Assign Material
    material = name_index_mat_dict[ssbh_mesh_object.name][ssbh_mesh_object.sub_index]
    blender_mesh.materials.append(material)
    for polygon in blender_mesh.polygons:
        polygon.material_index = blender_mesh.materials.find(material.name)


    return blender_mesh

def create_mesh(ssbh_model, ssbh_material_json, ssbh_mesh, ssbh_skel, armature, context):
    '''
    So the goal here is to create a set of materials to share among the meshes for this model.
    But, other previously created models can have materials of the same name.
    Gonna make sure not to conflict.
    example, bpy.data.materials.new('A') might create 'A' or 'A.001', so store reference to the mat created rather than the name
    '''
    created_meshes = []
    
    numdlb_material_labels = {e.material_label for e in ssbh_model.entries} # {blah} creates a set aka a list with no duplicates. {} creates an empty dictionary tho
    label_to_material_dict = {} # This creates an empty Dictionary
    
    # Make Master Shader if its not already made
    master_shader.create_master_shader()

    texture_name_to_image_dict = {}
    texture_name_to_image_dict = import_material_images(ssbh_material_json, context)

    for label in numdlb_material_labels:
        blender_mat = bpy.data.materials.new(label)

        setup_blender_mat(blender_mat, label, ssbh_material_json, texture_name_to_image_dict)
        label_to_material_dict[label] = blender_mat
        
    
    name_index_mat_dict = {}
    for e in ssbh_model.entries:
	    name_index_mat_dict[e.mesh_object_name] = {}
    for e in ssbh_model.entries:
        name_index_mat_dict[e.mesh_object_name][e.mesh_object_sub_index] = label_to_material_dict[e.material_label]

    for ssbh_mesh_object in ssbh_mesh.objects:
        blender_mesh = create_blender_mesh(ssbh_mesh_object, ssbh_skel, name_index_mat_dict)
        mesh_obj = bpy.data.objects.new(blender_mesh.name, blender_mesh)

        attach_armature_create_vertex_groups(mesh_obj, ssbh_skel, armature, ssbh_mesh_object.parent_bone_name)

        context.collection.objects.link(mesh_obj)
        created_meshes.append(mesh_obj)
    
    return created_meshes

def import_material_images(ssbh_material_json, context):
    texture_name_to_image_dict = {}
    texture_name_set = set()

    ssbh_mat_entries = ssbh_material_json['data']['Matl']['entries']
    for ssbh_mat_entry in ssbh_mat_entries:
        attributes = ssbh_mat_entry['attributes']['Attributes16']
        for attribute in attributes:
            if 'Texture' in attribute['param_id']:
                texture_name_set.add(attribute['param']['data']['MatlString'])

    print('texture_name_set = %s' % texture_name_set)

    for texture_name in texture_name_set:
        dir = context.scene.sub_model_folder_path
        image = image_utils.load_image(texture_name + '.png', dir, place_holder=True, check_existing=False)  
        texture_name_to_image_dict[texture_name] = image

    return texture_name_to_image_dict

def setup_blender_mat(blender_mat, material_label, ssbh_material_json, texture_name_to_image_dict):
    ssbh_mat_entries = ssbh_material_json['data']['Matl']['entries']

    entry = None
    for ssbh_mat_entry in ssbh_mat_entries:
        if ssbh_mat_entry['material_label'] == material_label:
            entry = ssbh_mat_entry

    # Change Mat Settings
    # Change Transparency Stuff Later
    blender_mat.blend_method = 'CLIP'
    blender_mat.use_backface_culling = True
    blender_mat.show_transparent_back = False
    alpha_blend_suffixes = ['_far', '_sort', '_near']
    if any(suffix in entry['shader_label'] for suffix in alpha_blend_suffixes):
        blender_mat.blend_method = 'BLEND'
        
    # Clone Master Shader
    master_shader_name = master_shader.get_master_shader_name()
    master_node_group = bpy.data.node_groups.get(master_shader_name)
    clone_group = master_node_group.copy()

    # Setup Clone
    clone_group.name = entry['shader_label']

    # Add our new Nodes
    blender_mat.use_nodes = True
    nodes = blender_mat.node_tree.nodes
    links = blender_mat.node_tree.links

    # Cleanse Node Tree
    nodes.clear()
    
    material_output_node = nodes.new('ShaderNodeOutputMaterial')
    material_output_node.location = (900,0)
    node_group_node = nodes.new('ShaderNodeGroup')
    node_group_node.name = 'smash_ultimate_shader'
    node_group_node.width = 600
    node_group_node.location = (-300, 300)
    node_group_node.node_tree = clone_group
    for input in node_group_node.inputs:
        input.hide = True
    shader_label = node_group_node.inputs['Shader Label']
    shader_label.hide = False
    shader_name = entry['shader_label']
    shader_label.default_value = entry['shader_label']
    material_label = node_group_node.inputs['Material Name']
    material_label.hide = False
    material_label.default_value = entry['material_label']

    attributes = entry['attributes']['Attributes16']
    for attribute in attributes:
        param_id = attribute['param_id']
        for input in node_group_node.inputs:
            if input.name.split(' ')[0] == param_id:
                input.hide = False
        if 'BlendState0' in param_id:
            blend_state = attribute['param']['data']['BlendState']
            source_color = blend_state['source_color']
            unk2 = blend_state['unk2']
            destination_color = blend_state['destination_color']
            unk4 = blend_state['unk4']
            unk5 = blend_state['unk5']
            unk6 = blend_state['unk6']
            unk7 = blend_state['unk7']
            unk8 = blend_state['unk8']
            unk9 = blend_state['unk9']
            unk10 = blend_state['unk10']
            blend_state_inputs = []
            for input in node_group_node.inputs:
                if input.name.split(' ')[0] == 'BlendState0':
                    blend_state_inputs.append(input)
            for input in blend_state_inputs:
                field_name = input.name.split(' ')[1]
                if field_name == 'Field1':
                    input.default_value = source_color
                if field_name == 'Field2':
                    input.default_value = unk2
                if field_name == 'Field3':
                    input.default_value = destination_color
                if field_name == 'Field4':
                    input.default_value = unk4
                if field_name == 'Field5':
                    input.default_value = unk5
                if field_name == 'Field6':
                    input.default_value = unk6
                if field_name == 'Field7':
                    input.default_value = unk7
                if field_name == 'Field8':
                    input.default_value = unk8
                if field_name == 'Field9':
                    input.default_value = unk9
                if field_name == 'Field10':
                    input.default_value = unk10
        if 'RasterizerState0' in param_id:
            rasterizer_state = attribute['param']['data']['RasterizerState']
            fill_mode = rasterizer_state['fill_mode']
            cull_mode = rasterizer_state['cull_mode']
            depth_bias = rasterizer_state['depth_bias']
            unk4 = rasterizer_state['unk4']
            unk5 = rasterizer_state['unk5']
            unk6 = rasterizer_state['unk6']
            rasterizer_state_inputs = [input for input in node_group_node.inputs if input.name.split(' ')[0] == 'RasterizerState0']
            for input in rasterizer_state_inputs:
                field_name = input.name.split(' ')[1]
                if field_name == 'Field1':
                    input.default_value = 0 if fill_mode == 'Line' else 1
                if field_name == 'Field2':
                    input.default_value = 0 if cull_mode == 'Back' else\
                                          1 if cull_mode == 'Front' else\
                                          2  
                if field_name == 'Field3':
                    input.default_value = depth_bias
                if field_name == 'Field4':
                    input.default_value = unk4
                if field_name == 'Field5':
                    input.default_value = unk5
                if field_name == 'Field6':
                    input.default_value = unk6

        if 'CustomBoolean' in param_id:
            bool_value = attribute['param']['data']['Boolean']
            input = node_group_node.inputs.get(param_id)
            input.default_value = bool_value

        if 'CustomFloat' in param_id:
            float_value = attribute['param']['data']['Float']
            input = node_group_node.inputs.get(param_id)
            input.default_value = float_value
        
        if 'CustomVector' in param_id:
            vector4 = attribute['param']['data']['Vector4']
            x = vector4['x']
            y = vector4['y']
            z = vector4['z']
            w = vector4['w']
            inputs = []
            for input in node_group_node.inputs:
                if input.name.split(' ')[0] == param_id:
                    inputs.append(input)
            if len(inputs) == 1:
                inputs[0].default_value = (x,y,z,w)
            elif len(inputs) == 2:
                for input in inputs:
                    field = input.name.split(' ')[1]
                    if field == 'RGB':
                        input.default_value = (x,y,z,1)
                    if field == 'Alpha':
                        input.default_value = w
            else:
                for input in inputs:
                    axis = input.name.split(' ')[1]
                    if axis == 'X':
                        input.default_value = x
                    if axis == 'Y':
                        input.default_value = y
                    if axis == 'Z':
                        input.default_value = z
                    if axis == 'W':
                        input.default_value = w
            if 'CustomVector47' == param_id:
                node_group_node.inputs['use_custom_vector_47'].default_value = 1.0

    links.new(material_output_node.inputs[0], node_group_node.outputs[0])

    # Add image texture nodes
    samplers = [a for a in attributes if 'Sampler' in a['param_id']]
    textures = [a for a in attributes if 'Texture' in a['param_id']]
    texture_name_to_sampler_entry = {t['param_id']:s for t in textures for s in samplers if t['param_id'].split('Texture')[1] == s['param_id'].split('Sampler')[1]}
    node_count = 0
    for attribute in attributes:
        param_id = attribute['param_id']
        if 'Texture' in param_id:
            texture_node = nodes.new('ShaderNodeTexImage')
            texture_node.location = (-800, -500 * node_count + 1000)
            texture_file_name = attribute['param']['data']['MatlString']
            texture_node.name = texture_file_name
            texture_node.label = texture_file_name
            texture_node.image = texture_name_to_image_dict[texture_file_name]
            #texture_node.image = texture_file_name + '.png', context.scene.sub_model_folder_path, place_holder=True, check_existing=False, force_reload=True)
            matched_rgb_input = None
            matched_alpha_input = None
            for input in node_group_node.inputs:
                if param_id == input.name.split(' ')[0]:
                    if 'RGB' == input.name.split(' ')[1]:
                        matched_rgb_input = input
                    else:
                        matched_alpha_input = input
            # For now, manually set the colorspace types....
            linear_textures = ['Texture6', 'Texture4']
            if param_id in linear_textures:
                texture_node.image.colorspace_settings.name = 'Linear'
                texture_node.image.alpha_mode = 'CHANNEL_PACKED'
            
            uv_map_node = nodes.new('ShaderNodeUVMap')
            uv_map_node.name = 'uv_map_node'
            uv_map_node.location = (texture_node.location[0] - 900, texture_node.location[1])
            uv_map_node.label = param_id + ' UV Map'

            if param_id == 'Texture9':
                uv_map_node.uv_map = 'bake1'
            elif param_id == 'Texture1':
                uv_map_node.uv_map = 'uvSet'
            else:
                uv_map_node.uv_map = 'map1'

            # Create Sampler Node
            sampler_node = nodes.new('CustomNodeUltimateSampler')
            sampler_node.name = 'sampler_node'
            sampler_node.label = 'Sampler' + param_id.split('Texture')[1]
            sampler_node.location = (texture_node.location[0] - 600, texture_node.location[1])
            sampler_node.width = 500

            sampler_entry = texture_name_to_sampler_entry[param_id]
            sampler_data = sampler_entry['param']['data']['Sampler']
            sampler_node.wrap_s = 'REPEAT' if sampler_data['wraps'] == 'Repeat' else\
                                  'CLAMP_TO_BORDER' if sampler_data['wraps'] == 'ClampToBorder' else\
                                  'CLAMP_TO_EDGE' if sampler_data['wraps'] == 'ClampToEdge' else\
                                  'MIRRORED_REPEAT'
            sampler_node.wrap_t = 'REPEAT' if sampler_data['wrapt'] == 'Repeat' else\
                                  'CLAMP_TO_BORDER' if sampler_data['wrapt'] == 'ClampToBorder' else\
                                  'CLAMP_TO_EDGE' if sampler_data['wrapt'] == 'ClampToEdge' else\
                                  'MIRRORED_REPEAT'

            sampler_node.wrap_r = 'REPEAT' if sampler_data['wrapr'] == 'Repeat' else\
                                  'CLAMP_TO_BORDER' if sampler_data['wrapr'] == 'ClampToBorder' else\
                                  'CLAMP_TO_EDGE' if sampler_data['wrapr'] == 'ClampToEdge' else\
                                  'MIRRORED_REPEAT'
            sampler_node.min_filter = 'NEAREST' if sampler_data['min_filter'] == 'Nearest' else\
                                      'LINEAR_MIPMAP_LINEAR' if sampler_data['min_filter'] == 'LinearMipmapLinear' else\
                                      'LINEAR_MIPMAP_LINEAR_2' 
            sampler_node.mag_filter = 'NEAREST' if sampler_data['mag_filter'] == 'Nearest' else\
                                      'LINEAR' if sampler_data['mag_filter'] == 'Linear' else\
                                      'LINEAR_2'
            sampler_node.texture_filter = 'DEFAULT' if sampler_data['texture_filtering_type'] == 'Default' else\
                                          'DEFAULT_2' if sampler_data['texture_filtering_type'] == 'Default2' else\
                                          'ANISOTROPIC_FILTERING'
            r = sampler_data['border_color']['r']
            g = sampler_data['border_color']['g']
            b = sampler_data['border_color']['b']
            a = sampler_data['border_color']['a']

            sampler_node.border_color = (r,g,b,a)

            sampler_node.unk11 = sampler_data['unk11']
            sampler_node.unk12 = sampler_data['unk12']
            sampler_node.lod_bias = sampler_data['lod_bias']
            sampler_node.max_anisotropy = '1X' if sampler_data['max_anisotropy'] == 0 else\
                                          '2X' if sampler_data['max_anisotropy'] == 2 else\
                                          '4X' if sampler_data['max_anisotropy'] == 4 else\
                                          '16X' if sampler_data['max_anisotropy'] == 8 else\
                                          '128X'                               

            links.new(sampler_node.inputs['UV Input'], uv_map_node.outputs[0])
            links.new(texture_node.inputs[0], sampler_node.outputs[0])
            links.new(matched_rgb_input, texture_node.outputs['Color'])
            links.new(matched_alpha_input, texture_node.outputs['Alpha'])
            node_count = node_count + 1
    
    # Read Shader Label File
    shader_json_path = get_shader_json_file_path()
    shader_json = None
    with open(shader_json_path, 'r') as f:
        shader_json = json.load(f)
    
    shader_array = shader_json['data']['Nufx']['programs']['ProgramsV1']
    found_shader = None
    for shader in shader_array:
        if shader['name'] == shader_name:
            found_shader = shader
            break
    
    if found_shader is None:
        raise RuntimeError(f'did not find a matching shader for shader name "{shader_name}"')

    vertex_attributes = found_shader['vertex_attributes']
    color_set_1_found = False
    for vertex_attribute in vertex_attributes:
        if vertex_attribute['attribute_name'] == 'colorSet1':
            color_set_1_found = True
            break
        
    node_group_node.inputs['use_color_set_1'].default_value = 1.0 if color_set_1_found else 0.0
    


    return