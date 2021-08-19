import bpy
from bpy.types import FileSelectParams
import subprocess, json
from ..operators import master_shader

def get_ssbh_lib_json_path():
    return bpy.context.scene.ssbh_lib_json_path
def get_numatb_path():
    return bpy.context.scene.numatb_file_path
def get_io_matl_armature():
    return bpy.context.scene.io_matl_armature

class MaterialPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Material Re-Importer'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        
        row = layout.row(align=True)
        row.label(text='Select ssbh_lib_json.exe')
        
        row = layout.row(align=True)
        row.prop(context.scene, 'ssbh_lib_json_path', icon='FILE')

        row = layout.row(align=True)
        row.operator('sub.ssbh_lib_json_file_selector', icon='ZOOM_ALL', text='Browse for ssbh_lib_json.exe')

        if not context.scene.ssbh_lib_json_path:
            return

        row = layout.row(align=True)
        row.label(text='Nice, now select the .numatb file to import')

        row = layout.row(align=True)
        row.prop(context.scene, 'numatb_file_path', icon='FILE')

        row = layout.row(align=True)
        row.operator('sub.numatb_file_selector', icon='ZOOM_ALL', text='Browse for the .numatb file')

        if not context.scene.numatb_file_path:
            return
        
        row = layout.row(align=True)
        row.label(text="Ok, now select an armature. The children meshes' materials will be modified.")

        row = layout.row(align=True)
        row.prop(context.scene, 'io_matl_armature', icon='ARMATURE_DATA')

        if not context.scene.io_matl_armature:
            return

        row = layout.row(align=True)
        row.operator('sub.matl_reimporter',icon='IMPORT', text='Re-Import Materials')

class MatlReimporter(bpy.types.Operator):
    bl_idname = 'sub.matl_reimporter'
    bl_label = 'Material Reimporter'

    def execute(self, context):
        reimport_materials()
        return {'FINISHED'}

def reimport_materials():
    '''
    Plan is:
        run ssbh_lib_json to convert .numatb to .json
        parse json
        create master shader if not already made
        for material belonging to armature, match blender material name to parsed material,
        , and then delete the existing material nodes,
        , and then create a copy of the master shader for this material,
        , and then hide the unneeded sockets of that shader,
        , and then create texture nodes,
        , and lastly link it all up.
    '''
    ssbh_lib_json_path = get_ssbh_lib_json_path()
    numatb_path = get_numatb_path()
    output_json_path = numatb_path + '.json'

    # Run ssbh_lib_json
    subprocess.run([ssbh_lib_json_path, numatb_path])

    # Load Outputed Json
    numatb_json = None
    with open(output_json_path) as f:
        numatb_json = json.load(f)
    
    # Parse Json
    mat_entries = numatb_json['data']['Matl']['entries']

    materials = []
    armature = get_io_matl_armature()
    for child in armature.children:
        if child.type == 'MESH':
            mat = child.material_slots[0].material
            if mat not in materials:
                materials.append(mat)
    
    # Make Master Shader if its not already made
    master_shader.create_master_shader() 

    #find matching mat
    for material in materials:
        entry = None
        for mat_entry in mat_entries:
            if mat_entry['material_label'] == material.name:
                entry = mat_entry
        if entry is None:
            print('No matching material found for material %s, leaving as-is' % (material.name))
            continue
        print(entry['shader_label'])

        # purge time (except texture nodes)
        nodes = material.node_tree.nodes
        texture_nodes = []
        for node in nodes:
            if node.type == 'TEX_IMAGE':
                texture_nodes.append(node)
            else:
                nodes.remove(node)

        # Clone Master Shader
        master_shader_name = master_shader.get_master_shader_name()
        master_node_group = bpy.data.node_groups.get(master_shader_name)
        clone_group = master_node_group.copy()
        
        # Setup Clone
        clone_group.name = entry['shader_label']

        # Add our new nodes
        node_group_node = nodes.new('ShaderNodeGroup')
        node_group_node.width = 600
        node_group_node.location = (-300, 300)
        node_group_node.node_tree = clone_group
        for input in node_group_node.inputs:
            input.hide = True
        shader_label = node_group_node.inputs['Shader Label']
        shader_label.hide = False
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
            
        
        

        




class SsbhLibJsonFileSelector(bpy.types.Operator):
    bl_idname = 'sub.ssbh_lib_json_file_selector'
    bl_label = 'File Selector'

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    def execute(self, context):
        print(self.filepath)
        context.scene.ssbh_lib_json_path = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NumatbFileSelector(bpy.types.Operator):
    bl_idname = 'sub.numatb_file_selector'
    bl_label = 'File Selector'

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    def execute(self, context):
        print(self.filepath)
        context.scene.numatb_file_path = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

