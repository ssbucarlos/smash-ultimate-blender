import os
import os.path
import bpy
import mathutils
import time

from .. import ssbh_data_py
import numpy as np
from pathlib import Path

from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from bpy_extras import image_utils

from ..operators import master_shader, material_inputs

import sqlite3

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
        return {'FINISHED'}

class ModelImporter(bpy.types.Operator):
    bl_idname = 'sub.model_importer'
    bl_label = 'Model Importer'

    def execute(self, context):
        start = time.time()

        import_model(self,context)

        end = time.time()
        print(f'Imported model in {end - start} seconds')
        return {'FINISHED'}

def import_model(self, context):
    dir = context.scene.sub_model_folder_path
    numdlb_name = context.scene.sub_model_numdlb_file_name
    numshb_name = context.scene.sub_model_numshb_file_name
    nusktb_name = context.scene.sub_model_nusktb_file_name
    numatb_name = context.scene.sub_model_numatb_file_name
    
    start = time.time()
    ssbh_model = ssbh_data_py.modl_data.read_modl(dir + numdlb_name) if numdlb_name != '' else None

    # Numpy provides much faster performance than Python lists.
    # TODO(SMG): This API for ssbh_data_py will likely have changes and improvements in the future.
    ssbh_mesh = ssbh_data_py.mesh_data.read_mesh(dir + numshb_name, use_numpy=True) if numshb_name != '' else None

    ssbh_skel = ssbh_data_py.skel_data.read_skel(dir + nusktb_name) if numshb_name != '' else None
    ssbh_matl = ssbh_data_py.matl_data.read_matl(dir + numatb_name) if numatb_name != '' else None
    end = time.time()
    print(f'Read files in {end - start} seconds')

    armature = create_armature(ssbh_skel, context)
    created_meshes = create_mesh(ssbh_model, ssbh_matl, ssbh_mesh, ssbh_skel, armature, context)
    
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
    # Use the Path class to handle path differences between Windows, Linux, and MacOS.
    this_file_path = Path(__file__)
    return this_file_path.parent.parent.joinpath('ssbh_lib_json').joinpath('ssbh_lib_json.exe').resolve()

def get_shader_db_file_path():
    # This file was generated with duplicates removed to optimize space.
    # https://github.com/ScanMountGoat/Smush-Material-Research#shader-database
    this_file_path = Path(__file__)
    return this_file_path.parent.parent.joinpath('shader_file').joinpath('Nufx.db').resolve()


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
        # print('bone name =%s: \n\tworld_transform = %s,\n\t matrix_world = %s' % (bone_data.name, world_transform, matrix_world)) 
        # Assign transform pre-parenting
        new_bone.transform(matrix_world, scale=True, roll=False)
        #new_bone.matrix = matrix_world <--- Doesnt actually do anything here lol
        bone_to_matrix_dict[new_bone] = matrix_world
        # print('bone name = %s: \n\tnew_bone.matrix= %s' % (bone_data.name, new_bone.matrix))
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
        # print ('current_bone=%s:\n\t matrix=%s\n\t current_bone.matrix = %s' % (current_bone.name, matrix, current_bone.matrix))

    end = time.time()
    print(f'Created armature in {end - start} seconds')

    return armature


def attach_armature_create_vertex_groups(mesh_obj, skel, armature, ssbh_mesh_object):
    if skel is not None:
        # Create vertex groups for each bone to support skinning.
        for bone in skel.bones:
            mesh_obj.vertex_groups.new(name=bone.name)

        # Apply the initial parent bone transform if present.
        parent_bone = find_bone(skel, ssbh_mesh_object.parent_bone_name)
        if parent_bone is not None:
            # TODO: Should this transform be baked to fix exported positions?
            world_transform = skel.calculate_world_transform(parent_bone)
            mesh_obj.matrix_world = get_matrix4x4_blender(world_transform)

            # Use regular skin weights for mesh objects parented to a bone.
            # TODO: Should this only apply if there are no influences?
            # TODO: Should this be handled by actual parenting in Blender?
            mesh_obj.vertex_groups[parent_bone.name].add(ssbh_mesh_object.vertex_indices, 1.0, 'REPLACE')
        else:
            # Set the vertex skin weights for each bone.
            # TODO: Is there a faster way than setting weights per vertex?
            for influence in ssbh_mesh_object.bone_influences:
                # TODO: Will influences always refer to valid bones in the skeleton?
                vertex_group = mesh_obj.vertex_groups[influence.bone_name]
                for w in influence.vertex_weights:
                    vertex_group.add([w.vertex_index], w.vertex_weight, 'REPLACE')

    # Attach the mesh object to the armature object.
    if armature is not None:
        mesh_obj.parent = armature
        for bone in armature.data.bones.values():
            mesh_obj.vertex_groups.new(name=bone.name)
        modifier = mesh_obj.modifiers.new(armature.data.name, type="ARMATURE")
        modifier.object = armature


def create_blender_mesh(ssbh_mesh_object, skel, name_index_mat_dict):
    blender_mesh = bpy.data.meshes.new(ssbh_mesh_object.name)

    # TODO: Handle attribute data arrays not having the appropriate number of rows and columns.
    # This won't be an issue for in game models.

    # Using foreach_set is much faster than bmesh or from_pydata.
    # https://devtalk.blender.org/t/alternative-in-2-80-to-create-meshes-from-python-using-the-tessfaces-api/7445/3
    positions = ssbh_mesh_object.positions[0].data[:,:3]
    blender_mesh.vertices.add(positions.shape[0])
    blender_mesh.vertices.foreach_set("co", positions.flatten())

    # Assume triangles, which is the only primitive used in Smash Ultimate.
    # TODO(SMG): ssbh_data_py can use a numpy array here in the future.
    vertex_indices = np.array(ssbh_mesh_object.vertex_indices, dtype=np.int32)
    loop_start = np.arange(0, vertex_indices.shape[0], 3, dtype=np.int32)
    loop_total = np.full(loop_start.shape[0], 3, dtype=np.int32)

    blender_mesh.loops.add(vertex_indices.shape[0])
    blender_mesh.loops.foreach_set("vertex_index", vertex_indices)

    blender_mesh.polygons.add(loop_start.shape[0])
    blender_mesh.polygons.foreach_set("loop_start", loop_start)
    blender_mesh.polygons.foreach_set("loop_total", loop_total)

    for attribute_data in ssbh_mesh_object.texture_coordinates:
        uv_layer = blender_mesh.uv_layers.new(name=attribute_data.name)

        # Flip vertical.
        uvs = attribute_data.data[:,:2].copy()
        uvs[:,1] = 1.0 - uvs[:,1]

        # This is set per loop rather than per vertex.
        loop_uvs = uvs[vertex_indices].flatten()
        uv_layer.data.foreach_set("uv", loop_uvs)

    for attribute_data in ssbh_mesh_object.color_sets:
        color_layer = blender_mesh.vertex_colors.new(name=attribute_data.name)
        # TODO: Create a function for this?
        colors = attribute_data.data[:,:4]

        # This is set per loop rather than per vertex.
        loop_colors = colors[vertex_indices].flatten()
        color_layer.data.foreach_set("color", loop_colors)

    # These calls are necessary since we're setting mesh data manually.
    blender_mesh.update()
    blender_mesh.validate()

    # TODO: Is there a faster way to do this?
    # Now that the mesh is created, now we can assign split custom normals
    blender_mesh.use_auto_smooth = True # Required to use custom normals
    blender_mesh.normals_split_custom_set_from_vertices(ssbh_mesh_object.normals[0].data[:,:3])

    # Try and assign the material.
    # Mesh import should still succeed even if materials couldn't be created.
    # Users can still choose to not export the matl.
    # TODO: Report errors to the user?
    try:
        material = name_index_mat_dict[(ssbh_mesh_object.name, ssbh_mesh_object.sub_index)]
        blender_mesh.materials.append(material)
    except Exception as e:
        print(f'Failed to assign material for {ssbh_mesh_object.name}{ssbh_mesh_object.sub_index}: {e}')


    return blender_mesh


def create_mesh(ssbh_model, ssbh_matl, ssbh_mesh, ssbh_skel, armature, context):
    '''
    So the goal here is to create a set of materials to share among the meshes for this model.
    But, other previously created models can have materials of the same name.
    Gonna make sure not to conflict.
    example, bpy.data.materials.new('A') might create 'A' or 'A.001', so store reference to the mat created rather than the name
    '''
    created_meshes = []
    unique_numdlb_material_labels = {e.material_label for e in ssbh_model.entries}
    
    # Make Master Shader if its not already made
    master_shader.create_master_shader()

    texture_name_to_image_dict = {}
    texture_name_to_image_dict = import_material_images(ssbh_matl, context)

    label_to_material_dict = {}
    for label in unique_numdlb_material_labels:
        blender_mat = bpy.data.materials.new(label)

        # Mesh import should still succeed even if materials can't be created.
        # TODO: Report some sort of error to the user?
        try:
            setup_blender_mat(blender_mat, label, ssbh_matl, texture_name_to_image_dict)
            label_to_material_dict[label] = blender_mat
        except Exception as e:
            print(f'Failed to create material for {label}: {e}')

    name_index_mat_dict = { 
        (e.mesh_object_name,e.mesh_object_sub_index):label_to_material_dict[e.material_label] 
        for e in ssbh_model.entries if e.material_label in label_to_material_dict
    }

    start = time.time()

    for i, ssbh_mesh_object in enumerate(ssbh_mesh.objects):
        blender_mesh = create_blender_mesh(ssbh_mesh_object, ssbh_skel, name_index_mat_dict)
        mesh_obj = bpy.data.objects.new(blender_mesh.name, blender_mesh)

        attach_armature_create_vertex_groups(mesh_obj, ssbh_skel, armature, ssbh_mesh_object)
        mesh_obj["numshb order"] = i
        context.collection.objects.link(mesh_obj)
        created_meshes.append(mesh_obj)
    
    end = time.time()
    print(f'Created meshes in {end - start} seconds')

    return created_meshes

def import_material_images(ssbh_matl, context):
    texture_name_to_image_dict = {}
    texture_name_set = set()

    for ssbh_mat_entry in ssbh_matl.entries:
        for attribute in ssbh_mat_entry.textures:
            texture_name_set.add(attribute.data)

    print('texture_name_set = %s' % texture_name_set)

    for texture_name in texture_name_set:
        dir = context.scene.sub_model_folder_path
        image = image_utils.load_image(texture_name + '.png', dir, place_holder=True, check_existing=False)  
        texture_name_to_image_dict[texture_name] = image

    return texture_name_to_image_dict


def enable_inputs(node_group_node, param_id):
    for input in node_group_node.inputs:
        if input.name.split(' ')[0] == param_id:
            input.hide = False


def setup_blender_mat(blender_mat, material_label, ssbh_matl: ssbh_data_py.matl_data.MatlData, texture_name_to_image_dict):
    # TODO: Handle none?
    entry = None
    for ssbh_mat_entry in ssbh_matl.entries:
        if ssbh_mat_entry.material_label == material_label:
            entry = ssbh_mat_entry

    # Change Mat Settings
    # Change Transparency Stuff Later
    blender_mat.blend_method = 'CLIP'
    blender_mat.use_backface_culling = True
    blender_mat.show_transparent_back = False
    # TODO: This should be based on the blend state and not the shader label.
    alpha_blend_suffixes = ['_far', '_sort', '_near']
    if any(suffix in entry.shader_label for suffix in alpha_blend_suffixes):
        blender_mat.blend_method = 'BLEND'
        
    # Clone Master Shader
    master_shader_name = master_shader.get_master_shader_name()
    master_node_group = bpy.data.node_groups.get(master_shader_name)
    clone_group = master_node_group.copy()

    # Setup Clone
    clone_group.name = entry.shader_label

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
    shader_name = entry.shader_label
    shader_label.default_value = entry.shader_label
    material_label = node_group_node.inputs['Material Name']
    material_label.hide = False
    material_label.default_value = entry.material_label

    # TODO: Refactor this to be cleaner?
    blend_state = entry.blend_states[0].data
    enable_inputs(node_group_node, entry.blend_states[0].param_id.name)

    blend_state_inputs = []
    for input in node_group_node.inputs:
        if input.name.split(' ')[0] == 'BlendState0':
            blend_state_inputs.append(input)
            
    for input in blend_state_inputs:
        field_name = input.name.split(' ')[1]
        if field_name == 'Field1':
            input.default_value = blend_state.source_color.name
        if field_name == 'Field3':
            input.default_value = blend_state.destination_color.name
        if field_name == 'Field7':
            input.default_value = blend_state.alpha_sample_to_coverage

    rasterizer_state = entry.rasterizer_states[0].data
    enable_inputs(node_group_node, entry.rasterizer_states[0].param_id.name)

    rasterizer_state_inputs = [input for input in node_group_node.inputs if input.name.split(' ')[0] == 'RasterizerState0']
    for input in rasterizer_state_inputs:
        field_name = input.name.split(' ')[1]
        if field_name == 'Field1':
            input.default_value = rasterizer_state.fill_mode.name
        if field_name == 'Field2':
            input.default_value = rasterizer_state.cull_mode.name
        if field_name == 'Field3':
            input.default_value = rasterizer_state.depth_bias

    for param in entry.booleans:
        input = node_group_node.inputs.get(param.param_id.name)
        input.hide = False
        input.default_value = param.data

    for param in entry.floats:
        input = node_group_node.inputs.get(param.param_id.name)
        input.hide = False
        input.default_value = param.data
    
    for param in entry.vectors:
        param_name = param.param_id.name

        if param_name in material_inputs.vec4_param_to_inputs:
            # Find and enable inputs.
            inputs = [node_group_node.inputs.get(name) for _, name, _ in material_inputs.vec4_param_to_inputs[param_name]]
            for input in inputs:
                input.hide = False

            # Assume inputs are RGBA, RGB/A, or X/Y/Z/W.
            x, y, z, w = param.data
            if len(inputs) == 1:
                inputs[0].default_value = (x,y,z,w)
            elif len(inputs) == 2:
                inputs[0].default_value = (x,y,z,1)
                inputs[1].default_value = w
            elif len(inputs) == 4:
                inputs[0].default_value = x
                inputs[1].default_value = y
                inputs[2].default_value = z
                inputs[3].default_value = w

            if param_name == 'CustomVector47':
                node_group_node.inputs['use_custom_vector_47'].default_value = 1.0

    links.new(material_output_node.inputs[0], node_group_node.outputs[0])

    # Add image texture nodes
    node_count = 0

    for texture_param in entry.textures:
        enable_inputs(node_group_node, texture_param.param_id.name)

        texture_node = nodes.new('ShaderNodeTexImage')
        texture_node.location = (-800, -500 * node_count + 1000)
        texture_file_name = texture_param.data
        texture_node.name = texture_file_name
        texture_node.label = texture_file_name
        texture_node.image = texture_name_to_image_dict[texture_file_name]
        #texture_node.image = texture_file_name + '.png', context.scene.sub_model_folder_path, place_holder=True, check_existing=False, force_reload=True)
        matched_rgb_input = None
        matched_alpha_input = None
        for input in node_group_node.inputs:
            if texture_param.param_id.name == input.name.split(' ')[0]:
                if 'RGB' == input.name.split(' ')[1]:
                    matched_rgb_input = input
                else:
                    matched_alpha_input = input
        # For now, manually set the colorspace types....
        linear_textures = ['Texture6', 'Texture4']
        if texture_param.param_id.name in linear_textures:
            texture_node.image.colorspace_settings.name = 'Linear'
            texture_node.image.alpha_mode = 'CHANNEL_PACKED'
        
        uv_map_node = nodes.new('ShaderNodeUVMap')
        uv_map_node.name = 'uv_map_node'
        uv_map_node.location = (texture_node.location[0] - 900, texture_node.location[1])
        uv_map_node.label = texture_param.param_id.name + ' UV Map'

        if texture_param.param_id.name == 'Texture9':
            uv_map_node.uv_map = 'bake1'
        elif texture_param.param_id.name == 'Texture1':
            uv_map_node.uv_map = 'uvSet'
        else:
            uv_map_node.uv_map = 'map1'

        # Create Sampler Node
        sampler_node = nodes.new('CustomNodeUltimateSampler')
        sampler_node.name = 'sampler_node'
        sampler_node.label = 'Sampler' + texture_param.param_id.name.split('Texture')[1]
        sampler_node.location = (texture_node.location[0] - 600, texture_node.location[1])
        sampler_node.width = 500

        # TODO: Handle the None case?
        sampler_entry = None
        for sampler_param in entry.samplers:
            if texture_param.param_id.name.split('Texture')[1] == sampler_param.param_id.name.split('Sampler')[1]:
                sampler_entry = sampler_param
                break

        enable_inputs(node_group_node, sampler_entry.param_id.name)
        sampler_data = sampler_entry.data
        sampler_node.wrap_s = sampler_data.wraps.name
        sampler_node.wrap_t = sampler_data.wrapt.name
        sampler_node.wrap_r = sampler_data.wrapr.name
        sampler_node.min_filter = sampler_data.min_filter.name
        sampler_node.mag_filter = sampler_data.mag_filter.name
        sampler_node.anisotropic_filtering = sampler_data.max_anisotropy is not None
        sampler_node.max_anisotropy = sampler_data.max_anisotropy.name if sampler_data.max_anisotropy else 'One'
        sampler_node.border_color = tuple(sampler_data.border_color)
        sampler_node.lod_bias = sampler_data.lod_bias       

        links.new(sampler_node.inputs['UV Input'], uv_map_node.outputs[0])
        links.new(texture_node.inputs[0], sampler_node.outputs[0])
        links.new(matched_rgb_input, texture_node.outputs['Color'])
        links.new(matched_alpha_input, texture_node.outputs['Alpha'])
        node_count = node_count + 1
    
    # Query the shader database for attribute information.
    # Using SQLite is much faster than iterating through the JSON dump.
    with sqlite3.connect(get_shader_db_file_path()) as con:
        # Construct a query to find all the vertex attributes for this shader.
        # Invalid shaders will return an empty list.
        sql = """
            SELECT v.AttributeName 
            FROM VertexAttribute v 
            INNER JOIN ShaderProgram s ON v.ShaderProgramID = s.ID 
            WHERE s.Name = ?
            """
        # The database has a single entry for each program, so don't include the render pass tag.
        attributes = [row[0] for row in con.execute(sql, (shader_name[:len('SFX_PBS_0000000000000080')],)).fetchall()]
        node_group_node.inputs['use_color_set_1'].default_value = 1.0 if 'colorSet1' in attributes else 0.0