import bpy
from bpy.types import Panel, Operator

class SUB_PT_attribute_renamer(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Ultimate'
    bl_label = 'Attribute Renamer'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        modes = ['POSE', 'OBJECT']
        return context.mode in modes

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        # Each button gets its own row for individual spacing
        row = layout.row()
        row.operator("sub.rename_mesh_attributes")
        
        row = layout.row()
        row.operator("sub.rename_material_to_mesh")
        
        row = layout.row()
        row.operator("sub.rename_texture_to_material")


class SUB_OP_rename_mesh_attributes(Operator):
    bl_idname = 'sub.rename_mesh_attributes'
    bl_label = 'Rename Mesh Attributes'
    bl_description = 'Renames UV Maps and Color Attributes for the selected meshes to match Smash Ultimate\'s attribute names'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        # TODO: Only store these names in one place?
        smash_uv_names = ['map1', 'bake1', 'uvSet', 'uvSet1', 'uvSet2']
        smash_color_names = ['colorSet1', 'colorSet2', 'colorSet2_1', 'colorSet2_2',
                             'colorSet2_3', 'colorSet3', 'colorSet4', 'colorSet5', 'colorSet6', 'colorSet7']

        renamed_meshes = set()
        meshes_with_non_renamable_attributes = set()

        # TODO: Filter to only meshes?
        for selected_object in context.selected_objects:
            try:
                for i, uv_layer in enumerate(selected_object.data.uv_layers):
                    if uv_layer.name not in smash_uv_names:
                        if i == 0:
                            # Only the first UV attribute can be assumed to be map1.
                            uv_layer.name = 'map1'
                            renamed_meshes.add(selected_object.name)
                        else:
                            meshes_with_non_renamable_attributes.add(
                                selected_object.name)

                for i, attribute in enumerate(selected_object.data.color_attributes):
                    if attribute.name not in smash_color_names:
                        if i == 0:
                            # Only the first color attribute can be assumed to be colorSet1.
                            attribute.name = 'colorSet1'
                            renamed_meshes.add(selected_object.name)
                        else:
                            meshes_with_non_renamable_attributes.add(
                                selected_object.name)
            except:
                # TODO: Handle errors?
                pass

            count = len(renamed_meshes)
            message = f'Successfully renamed attributes for {count} meshes.'
            self.report({'INFO'}, message)

            if len(meshes_with_non_renamable_attributes) > 0:
                message = f'Failed to automatically rename some attributes for meshes {meshes_with_non_renamable_attributes}.'
                message += ' Attributes after the first Color Attribute and UV Map must be renamed manually.'
                self.report({'WARNING'}, message)

        return {'FINISHED'}


class SUB_OP_rename_material_to_mesh(Operator):
    bl_idname = 'sub.rename_material_to_mesh'
    bl_label = 'Rename Materials to Mesh'
    bl_description = 'Renames materials based on their mesh object names'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                for i, slot in enumerate(obj.material_slots):
                    if slot.material:
                        new_name = f"{obj.name}_mat{i+1}" if len(obj.material_slots) > 1 else obj.name
                        cleaned_name = self.clean_name(new_name)
                        slot.material.name = cleaned_name
        
        self.report({'INFO'}, "Successfully renamed materials to match mesh names")
        return {'FINISHED'}

    def clean_name(self, name):
        """Removes specific substrings from the material name."""
        name = name.replace("Pikachu_", "").replace("_VIS_O_OBJShape", "")
        return name


class SUB_OP_rename_texture_to_material(Operator):
    bl_idname = 'sub.rename_texture_to_material'
    bl_label = 'Rename Textures to Material'
    bl_description = 'Renames textures to match their material names'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mat in bpy.data.materials:
            if mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        node.image.name = mat.name
        
        self.report({'INFO'}, "Successfully renamed textures to match material names")
        return {'FINISHED'}


# Register
classes = (
    SUB_PT_attribute_renamer,
    SUB_OP_rename_mesh_attributes,
    SUB_OP_rename_material_to_mesh,
    SUB_OP_rename_texture_to_material,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
