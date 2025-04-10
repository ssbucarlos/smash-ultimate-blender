import bpy
from bpy.types import Operator

class SUB_OT_rename_materials_to_mesh(Operator):
    """Rename materials to match their mesh names for selected objects"""
    bl_idname = "sub.rename_materials_to_mesh"
    bl_label = "Rename Materials to Mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        renamed_count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH' or not obj.data.materials:
                continue
            
            # Get base mesh name
            mesh_name = obj.name
            
            # Rename materials for this mesh
            for slot_idx, slot in enumerate(obj.material_slots):
                if not slot.material:
                    continue
                
                # Create unique material name based on mesh name and slot index
                # Only if there are multiple materials, otherwise just use mesh name
                if len(obj.material_slots) > 1:
                    new_name = f"{mesh_name}_{slot_idx+1}"
                else:
                    new_name = mesh_name
                    
                # Skip if material already has this name
                if slot.material.name == new_name:
                    continue
                
                # Check if this name already exists and make it unique
                if new_name in bpy.data.materials:
                    base_name = new_name
                    counter = 1
                    while new_name in bpy.data.materials:
                        new_name = f"{base_name}.{counter:03d}"
                        counter += 1
                
                # Rename the material
                original_name = slot.material.name
                slot.material.name = new_name
                renamed_count += 1
                print(f"Renamed material: {original_name} → {new_name}")
        
        if renamed_count > 0:
            self.report({'INFO'}, f"Renamed {renamed_count} materials based on mesh names")
        else:
            self.report({'INFO'}, "No materials needed renaming")
            
        return {'FINISHED'}

class SUB_OT_rename_textures_to_material(Operator):
    """Rename texture images to match their material names for selected objects"""
    bl_idname = "sub.rename_textures_to_material"
    bl_label = "Rename Textures to Material"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        renamed_count = 0
        processed_images = set()  # To avoid processing the same image multiple times
        
        # Common texture suffixes in Smash Ultimate materials
        texture_types = {
            "Texture0": "Col",    # Diffuse/albedo
            "Texture4": "Nor",    # Normal map
            "Texture6": "Prm",    # PRM (Metallic, Roughness, etc.)
            "Texture7": "Emm",    # Emission
            "Texture8": "Spm",    # Specular
            "Texture10": "Bak",   # Baked lighting
            "Texture11": "Dif",   # Diffuse
            "CustomVector13": "Clr", # Custom color
            "CustomVector47": "Mat"  # Material properties
        }
        
        for obj in context.selected_objects:
            if obj.type != 'MESH' or not obj.data.materials:
                continue
                
            # Process each material on this mesh
            for slot in obj.material_slots:
                if not slot.material:
                    continue
                
                material = slot.material
                material_name = material.name
                
                # Check if this material has a sub_matl_data property group
                if not hasattr(material, "sub_matl_data"):
                    continue
                    
                # Process textures in the sub_matl_data
                if hasattr(material.sub_matl_data, "textures"):
                    for tex in material.sub_matl_data.textures:
                        if not tex.image or tex.image in processed_images:
                            continue
                            
                        # Generate new texture name based on material name and texture type
                        suffix = texture_types.get(tex.param_id_name, tex.param_id_name.replace("Texture", "Tex"))
                        new_name = f"{material_name}_{suffix}"
                        
                        # Skip if image already has this name
                        if tex.image.name == new_name:
                            continue
                            
                        # Check if this name already exists and make it unique
                        if new_name in bpy.data.images:
                            base_name = new_name
                            counter = 1
                            while new_name in bpy.data.images:
                                new_name = f"{base_name}.{counter:03d}"
                                counter += 1
                        
                        # Rename the texture
                        original_name = tex.image.name
                        tex.image.name = new_name
                        processed_images.add(tex.image)
                        renamed_count += 1
                        print(f"Renamed texture: {original_name} → {new_name}")
        
        if renamed_count > 0:
            self.report({'INFO'}, f"Renamed {renamed_count} textures based on material names")
        else:
            self.report({'INFO'}, "No textures needed renaming")
            
        return {'FINISHED'}

# List of classes to register
classes = (
    SUB_OT_rename_materials_to_mesh,
    SUB_OT_rename_textures_to_material,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register() 