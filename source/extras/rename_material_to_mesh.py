import bpy

def clean_name(name):
    """Removes specific substrings from the material name."""
    return name

def rename_materials_to_mesh():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':  # Ensure we're dealing with mesh objects
            for i, slot in enumerate(obj.material_slots):
                if slot.material:
                    # Use object name as base for material renaming
                    new_name = f"{obj.name}_mat{i+1}" if len(obj.material_slots) > 1 else obj.name
                    cleaned_name = clean_name(new_name)  # Clean the material name
                    slot.material.name = cleaned_name
                    print(f"Renamed material to: {slot.material.name}")

# Run the function
rename_materials_to_mesh()
