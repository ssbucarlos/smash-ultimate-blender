import bpy

def rename_textures_to_material():
    for mat in bpy.data.materials:
        if mat.node_tree:  # Ensure the material has a node tree
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:  # Check for image texture nodes
                    node.image.name = mat.name  # Rename the texture to the material name
                    print(f"Renamed texture to: {node.image.name}")

# Run the function
rename_textures_to_material()
