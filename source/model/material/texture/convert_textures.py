import bpy
import os
from pathlib import Path
from mathutils import Color
import tempfile

def find_principled_bsdf_node(material):
    """Find Principled BSDF node in the material's node tree"""
    if not material or not material.node_tree:
        return None
    
    for node in material.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    
    return None

def get_input_texture(node, input_name):
    """Get texture from an input socket of a node"""
    if not node:
        return None
    
    input_socket = node.inputs.get(input_name)
    if not input_socket or not input_socket.links:
        return None
    
    # Trace back through links
    from_node = input_socket.links[0].from_node
    
    # If it's an image texture node, return the image
    if from_node.type == 'TEX_IMAGE' and from_node.image:
        return from_node.image
    
    return None

def get_input_value(node, input_name):
    """Get value from an input socket of a node"""
    if not node:
        return None
    
    input_socket = node.inputs.get(input_name)
    if not input_socket:
        return None
    
    # If connected, can't get direct value
    if input_socket.links:
        return None
    
    return input_socket.default_value

def bake_texture(material, attribute, size=1024, temp_dir=None):
    """Bake a specific attribute of a material to a new texture"""
    if not temp_dir:
        temp_dir = tempfile.gettempdir()
    
    print(f"Baking {attribute} for material {material.name}")
    print(f"  Size: {size}x{size}")
    print(f"  Temp directory: {temp_dir}")
        
    # Create a new image to bake to
    image_name = f"{material.name}_{attribute}"
    bake_image = bpy.data.images.new(image_name, width=size, height=size, alpha=True)
    
    # Set up the temporary file path
    temp_file = os.path.join(temp_dir, f"{image_name}.png")
    print(f"  Output file: {temp_file}")
    bake_image.filepath_raw = temp_file
    
    # Get active object and material
    obj = bpy.context.active_object
    if not obj:
        bpy.data.images.remove(bake_image)
        print("  ERROR: No active object to bake from")
        raise ValueError("No active object to bake from")
    
    print(f"  Active object: {obj.name}")
    
    # Make sure the object has the target material
    material_found = False
    for mat_slot in obj.material_slots:
        if mat_slot.material == material:
            material_found = True
            break
    
    if not material_found:
        # If material is not found on the object, temporarily assign it
        print(f"  Material {material.name} not found on object, temporarily assigning")
        if len(obj.material_slots) == 0:
            obj.data.materials.append(material)
        else:
            # Remember the original material
            original_mat = obj.material_slots[0].material
            obj.material_slots[0].material = material
    
    # Save current engine and switch to CYCLES for baking
    original_engine = bpy.context.scene.render.engine
    print(f"  Switching render engine from {original_engine} to CYCLES")
    bpy.context.scene.render.engine = 'CYCLES'
    
    # Set up baking settings
    previous_bake_type = bpy.context.scene.cycles.bake_type
    
    # Set up nodes for baking
    original_active_material = obj.active_material
    obj.active_material = material
    
    print(f"  Preparing material node tree for baking")
    
    # Store original node selection state
    selected_nodes = []
    active_node = None
    if material.node_tree:
        active_node = material.node_tree.nodes.active
        for node in material.node_tree.nodes:
            if node.select:
                selected_nodes.append(node)
                node.select = False
    
    # Create an image texture node for the bake target
    print(f"  Creating temporary image node for baking")
    bake_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    bake_node.select = True
    bake_node.image = bake_image
    material.node_tree.nodes.active = bake_node
    
    # Configure bake type based on attribute
    if attribute == 'normal':
        bpy.context.scene.cycles.bake_type = 'NORMAL'
    elif attribute == 'roughness':
        bpy.context.scene.cycles.bake_type = 'ROUGHNESS'
    elif attribute == 'metallic':
        bpy.context.scene.cycles.bake_type = 'DIFFUSE'  # Not ideal but workable
    elif attribute == 'ao':
        bpy.context.scene.cycles.bake_type = 'AO'
    elif attribute == 'specular':
        bpy.context.scene.cycles.bake_type = 'GLOSSY'  # Not ideal but workable
    
    print(f"  Baking with type: {bpy.context.scene.cycles.bake_type}")
    
    # Try to perform the bake
    try:
        bpy.ops.object.bake(type=bpy.context.scene.cycles.bake_type)
        print(f"  Bake successful")
    except Exception as e:
        print(f"  ERROR during baking: {str(e)}")
        
        # Clean up
        material.node_tree.nodes.remove(bake_node)
        bpy.context.scene.cycles.bake_type = previous_bake_type
        bpy.context.scene.render.engine = original_engine
        obj.active_material = original_active_material
        
        # Restore node selection
        if material.node_tree:
            for node in selected_nodes:
                node.select = True
            if active_node:
                material.node_tree.nodes.active = active_node
        
        # If we temporarily assigned the material, restore the original
        if not material_found and len(obj.material_slots) > 0:
            if 'original_mat' in locals():
                obj.material_slots[0].material = original_mat
        
        # Delete the temp image
        bpy.data.images.remove(bake_image)
        
        # Re-raise the exception
        raise
    
    # Save baked image
    print(f"  Saving baked image to {temp_file}")
    bake_image.file_format = 'PNG'
    bake_image.save()
    
    # Restore original state
    print(f"  Cleaning up temporary baking setup")
    material.node_tree.nodes.remove(bake_node)
    bpy.context.scene.cycles.bake_type = previous_bake_type
    bpy.context.scene.render.engine = original_engine
    obj.active_material = original_active_material
    
    # Restore node selection
    if material.node_tree:
        for node in selected_nodes:
            node.select = True
        if active_node:
            material.node_tree.nodes.active = active_node
    
    # If we temporarily assigned the material, restore the original
    if not material_found and len(obj.material_slots) > 0:
        if 'original_mat' in locals():
            obj.material_slots[0].material = original_mat
    
    print(f"  Baking completed successfully")
    # Return the newly created image
    return bake_image

def extract_pbr_data_from_material(material, bake_size=1024):
    """Extract PBR data from a Blender material"""
    principled = find_principled_bsdf_node(material)
    if not principled:
        raise ValueError(f"Material '{material.name}' doesn't have a Principled BSDF node")
    
    result = {}
    
    # Extract normal map
    normal_img = get_input_texture(principled, "Normal")
    if normal_img:
        result['normal'] = normal_img
    else:
        # Bake normal map if there's no direct texture
        # But only if there's a normal input value that's not 0
        normal_val = get_input_value(principled, "Normal")
        if normal_val and normal_val > 0.01:
            result['normal'] = bake_texture(material, 'normal', bake_size)
    
    # Extract metallic
    metallic_img = get_input_texture(principled, "Metallic")
    if metallic_img:
        result['metallic'] = metallic_img
    else:
        # Get metallic value or bake if necessary
        metallic_val = get_input_value(principled, "Metallic")
        if metallic_val is not None:
            # Create a simple metallic texture
            metallic_img = bpy.data.images.new(f"{material.name}_metallic", width=2, height=2, alpha=True)
            # Fill with solid color based on metallic value
            pixels = [metallic_val, metallic_val, metallic_val, 1.0] * 4
            metallic_img.pixels = pixels
            result['metallic'] = metallic_img
        else:
            # Complex node setup, need to bake
            result['metallic'] = bake_texture(material, 'metallic', bake_size)
    
    # Extract roughness
    roughness_img = get_input_texture(principled, "Roughness")
    if roughness_img:
        result['roughness'] = roughness_img
    else:
        # Get roughness value or bake if necessary
        roughness_val = get_input_value(principled, "Roughness")
        if roughness_val is not None:
            # Create a simple roughness texture
            roughness_img = bpy.data.images.new(f"{material.name}_roughness", width=2, height=2, alpha=True)
            # Fill with solid color based on roughness value
            pixels = [roughness_val, roughness_val, roughness_val, 1.0] * 4
            roughness_img.pixels = pixels
            result['roughness'] = roughness_img
        else:
            # Complex node setup, need to bake
            result['roughness'] = bake_texture(material, 'roughness', bake_size)
    
    # Extract specular
    specular_img = get_input_texture(principled, "Specular")
    if specular_img:
        result['specular'] = specular_img
    else:
        # Get specular value
        specular_val = get_input_value(principled, "Specular")
        if specular_val is not None:
            # Create a simple specular texture
            specular_img = bpy.data.images.new(f"{material.name}_specular", width=2, height=2, alpha=True)
            # Fill with solid color based on specular value
            pixels = [specular_val, specular_val, specular_val, 1.0] * 4
            specular_img.pixels = pixels
            result['specular'] = specular_img
        else:
            # Complex node setup, need to bake
            result['specular'] = bake_texture(material, 'specular', bake_size)
    
    # Try to find Ambient Occlusion
    # AO is often not connected to principled directly, so we need to check other nodes
    ao_img = None
    for node in material.node_tree.nodes:
        if node.type == 'AMBIENT_OCCLUSION':
            if node.outputs['AO'].links:
                # Try to trace back if this is connected to a texture
                ao_socket = node.inputs.get('Color')
                if ao_socket and ao_socket.links:
                    from_node = ao_socket.links[0].from_node
                    if from_node.type == 'TEX_IMAGE' and from_node.image:
                        ao_img = from_node.image
                        break
    
    if ao_img:
        result['ao'] = ao_img
    else:
        # Bake AO if we couldn't find it
        result['ao'] = bake_texture(material, 'ao', bake_size)
    
    return result

def create_simple_texture(name, size=1024, color=(0.5, 0.5, 0.5, 1.0)):
    """Create a simple single-color texture"""
    img = bpy.data.images.new(name, width=size, height=size, alpha=True)
    pixels = list(color) * (size * size)
    img.pixels = pixels
    return img

def extract_pbr_data_simple(material):
    """Extract basic PBR data from a Principled BSDF without baking"""
    print(f"Using simple extraction method for material: {material.name}")
    principled = find_principled_bsdf_node(material)
    if not principled:
        raise ValueError(f"Material '{material.name}' doesn't have a Principled BSDF node")
    
    result = {}
    
    # Create default normal map (neutral - flat surface)
    normal_img = create_simple_texture(f"{material.name}_normal", 1024, (0.5, 0.5, 1.0, 1.0))
    result['normal'] = normal_img
    
    # Get metallic value
    metallic_val = get_input_value(principled, "Metallic")
    if metallic_val is None:
        metallic_val = 0.0
    metallic_img = create_simple_texture(f"{material.name}_metallic", 1024, (metallic_val, metallic_val, metallic_val, 1.0))
    result['metallic'] = metallic_img
    
    # Get roughness value
    roughness_val = get_input_value(principled, "Roughness")
    if roughness_val is None:
        roughness_val = 0.5
    roughness_img = create_simple_texture(f"{material.name}_roughness", 1024, (roughness_val, roughness_val, roughness_val, 1.0))
    result['roughness'] = roughness_img
    
    # Get specular value
    specular_val = get_input_value(principled, "Specular")
    if specular_val is None:
        specular_val = 0.5
    specular_img = create_simple_texture(f"{material.name}_specular", 1024, (specular_val, specular_val, specular_val, 1.0))
    result['specular'] = specular_img
    
    # Create default AO map (no occlusion)
    ao_img = create_simple_texture(f"{material.name}_ao", 1024, (1.0, 1.0, 1.0, 1.0))
    result['ao'] = ao_img
    
    return result

def create_nor_from_material(material, output_path=None, directx_format=False, bake_size=1024):
    """
    Create a NOR texture from a Blender material
    
    Args:
        material: The Blender material to extract data from
        output_path: Where to save the NOR texture
        directx_format: Whether to handle normal maps as DirectX format
        bake_size: Size to use for baking textures
    
    Returns:
        Path to the created NOR texture
    """
    if not output_path:
        output_path = os.path.join(tempfile.gettempdir(), f"{material.name}_NOR.png")
    
    print(f"Creating NOR texture for material: {material.name}")
    print(f"Output path: {output_path}")
    
    # Try to extract PBR data with full baking
    try:
        print("Trying full PBR data extraction...")
        pbr_data = extract_pbr_data_from_material(material, bake_size)
    except Exception as e:
        print(f"Full extraction failed: {str(e)}")
        print("Falling back to simple extraction method...")
        pbr_data = extract_pbr_data_simple(material)
    
    # Check if we have the required textures
    if 'normal' not in pbr_data:
        print("No normal map data found, creating default normal map")
        pbr_data['normal'] = create_simple_texture(f"{material.name}_normal", 1024, (0.5, 0.5, 1.0, 1.0))
    
    # Create a new image for the output NOR texture
    normal_img = pbr_data['normal']
    width, height = normal_img.size
    print(f"Creating NOR texture with size {width}x{height}")
    nor_img = bpy.data.images.new(f"{material.name}_NOR", width=width, height=height, alpha=True)
    
    # Get pixel data
    normal_pixels = list(normal_img.pixels)
    nor_pixels = [0] * len(normal_pixels)
    
    # Get AO pixels for cavity map if available
    cavity_pixels = None
    if 'ao' in pbr_data:
        ao_img = pbr_data['ao']
        # Resize AO image if needed to match normal map
        if ao_img.size[0] != width or ao_img.size[1] != height:
            # Just use as is, can't easily resize in Blender API
            pass
        cavity_pixels = list(ao_img.pixels)
    else:
        print("No AO data found for cavity map, using default white")
    
    # Process pixel data
    # Blender stores pixels as RGBA flat array [R, G, B, A, R, G, B, A, ...]
    for i in range(0, len(normal_pixels), 4):
        # Red channel (X+) - copy directly
        nor_pixels[i] = normal_pixels[i]
        
        # Green channel (Y+)
        if directx_format:
            # For DirectX normal maps (Y-), flip the green channel
            nor_pixels[i+1] = 1.0 - normal_pixels[i+1]
        else:
            # For OpenGL normal maps (Y+), use as is
            nor_pixels[i+1] = normal_pixels[i+1]
        
        # Blue channel (transition blend) - use flat white by default
        nor_pixels[i+2] = 1.0
        
        # Alpha channel (cavity map) - use AO if available, otherwise flat white
        if cavity_pixels and i < len(cavity_pixels):
            nor_pixels[i+3] = cavity_pixels[i]  # Use red channel of AO map
        else:
            nor_pixels[i+3] = 1.0
    
    # Assign the processed pixels to the output image
    nor_img.pixels = nor_pixels
    
    # Save the output image
    nor_img.filepath_raw = output_path
    nor_img.file_format = 'PNG'
    print(f"Saving NOR texture to: {output_path}")
    nor_img.save()
    
    # Clean up
    bpy.data.images.remove(nor_img)
    
    print(f"NOR texture creation completed successfully")
    return output_path

def create_prm_from_material(material, output_path=None, bake_size=1024):
    """
    Create a PRM texture from a Blender material
    
    Args:
        material: The Blender material to extract data from
        output_path: Where to save the PRM texture
        bake_size: Size to use for baking textures
    
    Returns:
        Path to the created PRM texture
    """
    if not output_path:
        output_path = os.path.join(tempfile.gettempdir(), f"{material.name}_PRM.png")
    
    print(f"Creating PRM texture for material: {material.name}")
    print(f"Output path: {output_path}")
    
    # Try to extract PBR data with full baking
    try:
        print("Trying full PBR data extraction...")
        pbr_data = extract_pbr_data_from_material(material, bake_size)
    except Exception as e:
        print(f"Full extraction failed: {str(e)}")
        print("Falling back to simple extraction method...")
        pbr_data = extract_pbr_data_simple(material)
    
    # Make sure we have the minimum required data
    if 'metallic' not in pbr_data:
        print("No metallic data found, creating default metallic map")
        pbr_data['metallic'] = create_simple_texture(f"{material.name}_metallic", 1024, (0.0, 0.0, 0.0, 1.0))
        
    if 'roughness' not in pbr_data:
        print("No roughness data found, creating default roughness map")
        pbr_data['roughness'] = create_simple_texture(f"{material.name}_roughness", 1024, (0.5, 0.5, 0.5, 1.0))
    
    # Create a new image for the output PRM texture
    metallic_img = pbr_data['metallic']
    width, height = metallic_img.size
    print(f"Creating PRM texture with size {width}x{height}")
    prm_img = bpy.data.images.new(f"{material.name}_PRM", width=width, height=height, alpha=True)
    
    # Get pixel data
    metallic_pixels = list(metallic_img.pixels)
    
    # Get other pixel data
    roughness_img = pbr_data['roughness']
    roughness_pixels = list(roughness_img.pixels)
    
    ao_pixels = None
    if 'ao' in pbr_data:
        ao_img = pbr_data['ao']
        ao_pixels = list(ao_img.pixels)
    else:
        print("No AO data found, using default white")
    
    specular_pixels = None
    if 'specular' in pbr_data:
        specular_img = pbr_data['specular']
        specular_pixels = list(specular_img.pixels)
    else:
        print("No specular data found, using default 0.16")
    
    # Create the PRM pixel data
    prm_pixels = [0] * len(metallic_pixels)
    
    # Process pixel data
    # Blender stores pixels as RGBA flat array [R, G, B, A, R, G, B, A, ...]
    for i in range(0, len(metallic_pixels), 4):
        # Red channel (Metalness) - copy directly
        prm_pixels[i] = metallic_pixels[i]
        
        # Green channel (Roughness)
        # Smash squares roughness, so take square root to compensate
        if i < len(roughness_pixels):
            roughness_value = roughness_pixels[i]
            roughness_value = max(pow(roughness_value, 0.5), 0.01)  # Ensure minimum 0.01
            prm_pixels[i+1] = roughness_value
        else:
            prm_pixels[i+1] = 0.01  # Default minimum roughness
        
        # Blue channel (Ambient Occlusion)
        if ao_pixels and i < len(ao_pixels):
            prm_pixels[i+2] = ao_pixels[i]  # Use red channel of AO map
        else:
            # Default AO - full white (no occlusion)
            prm_pixels[i+2] = 1.0
        
        # Alpha channel (Specular)
        if specular_pixels and i < len(specular_pixels):
            specular_value = specular_pixels[i]  # Use red channel of specular map
            # Convert Blender's specular (0-8%) to Smash (0-20%)
            # smashSpecular = blenderSpecular * 0.4
            specular_value *= 0.4
            prm_pixels[i+3] = specular_value
        else:
            # Default specular - 0.16 (40/255)
            prm_pixels[i+3] = 0.16
    
    # Assign the processed pixels to the output image
    prm_img.pixels = prm_pixels
    
    # Save the output image
    prm_img.filepath_raw = output_path
    prm_img.file_format = 'PNG'
    print(f"Saving PRM texture to: {output_path}")
    prm_img.save()
    
    # Clean up
    bpy.data.images.remove(prm_img)
    
    print(f"PRM texture creation completed successfully")
    return output_path

class ULTIMATE_OT_create_nor_from_material(bpy.types.Operator):
    """Create a NOR texture from the active material's Principled BSDF shader"""
    bl_idname = "ultimate.create_nor_from_material"
    bl_label = "Create NOR from Material"
    bl_options = {'REGISTER', 'UNDO'}
    
    output_path: bpy.props.StringProperty(
        name="Output Path",
        description="Where to save the NOR texture",
        subtype='FILE_PATH'
    )
    
    directx_format: bpy.props.BoolProperty(
        name="DirectX Format (Y-)",
        description="Enable if your normal map uses DirectX format with Y-",
        default=False
    )
    
    bake_size: bpy.props.IntProperty(
        name="Bake Size",
        description="Size of textures to bake if needed",
        default=1024,
        min=128,
        max=4096
    )
    
    show_warning: bpy.props.BoolProperty(default=True)
    
    def invoke(self, context, event):
        # Show warning first if this is the initial invoke
        if self.show_warning:
            self.show_warning = False
            return context.window_manager.invoke_confirm(
                self, event, 
                message="Creating a NOR texture is resource-intensive and may take time depending on your computer."
            )
        
        # Set a default output path based on the active material name
        if context.active_object and context.active_object.active_material:
            material_name = context.active_object.active_material.name
            self.output_path = os.path.join(tempfile.gettempdir(), f"{material_name}_NOR.png")
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        if not context.active_object or not context.active_object.active_material:
            self.report({'ERROR'}, "No active material selected")
            return {'CANCELLED'}
        
        material = context.active_object.active_material
        
        try:
            output = create_nor_from_material(
                material,
                self.output_path,
                self.directx_format,
                self.bake_size
            )
            self.report({'INFO'}, f"NOR texture created at {output}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error creating NOR texture: {str(e)}")
            return {'CANCELLED'}

class ULTIMATE_OT_create_prm_from_material(bpy.types.Operator):
    """Create a PRM texture from the active material's Principled BSDF shader"""
    bl_idname = "ultimate.create_prm_from_material"
    bl_label = "Create PRM from Material"
    bl_options = {'REGISTER', 'UNDO'}
    
    output_path: bpy.props.StringProperty(
        name="Output Path",
        description="Where to save the PRM texture",
        subtype='FILE_PATH'
    )
    
    bake_size: bpy.props.IntProperty(
        name="Bake Size",
        description="Size of textures to bake if needed",
        default=1024,
        min=128,
        max=4096
    )
    
    show_warning: bpy.props.BoolProperty(default=True)
    
    def invoke(self, context, event):
        # Show warning first if this is the initial invoke
        if self.show_warning:
            self.show_warning = False
            return context.window_manager.invoke_confirm(
                self, event, 
                message="Creating a PRM texture is resource-intensive and may take time depending on your computer."
            )
        
        # Set a default output path based on the active material name
        if context.active_object and context.active_object.active_material:
            material_name = context.active_object.active_material.name
            self.output_path = os.path.join(tempfile.gettempdir(), f"{material_name}_PRM.png")
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        if not context.active_object or not context.active_object.active_material:
            self.report({'ERROR'}, "No active material selected")
            return {'CANCELLED'}
        
        material = context.active_object.active_material
        
        try:
            output = create_prm_from_material(
                material,
                self.output_path,
                self.bake_size
            )
            self.report({'INFO'}, f"PRM texture created at {output}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error creating PRM texture: {str(e)}")
            return {'CANCELLED'}

# List of classes to register
classes = (
    ULTIMATE_OT_create_nor_from_material,
    ULTIMATE_OT_create_prm_from_material,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register() 