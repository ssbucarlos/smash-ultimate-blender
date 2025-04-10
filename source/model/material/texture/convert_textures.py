import bpy
import os
from pathlib import Path
from mathutils import Color
import tempfile
import numpy as np  # Add NumPy import for faster array processing
from multiprocessing.pool import ThreadPool  # For parallel processing
import time

def process_image_in_parallel(func, args_list, max_workers=4):
    """
    Process multiple images in parallel using a thread pool
    
    Args:
        func: The function to run in parallel
        args_list: List of argument tuples to pass to the function
        max_workers: Maximum number of parallel workers
    
    Returns:
        List of results from the function calls
    """
    print(f"Processing {len(args_list)} images in parallel with {max_workers} workers")
    start_time = time.time()
    
    # Create thread pool
    pool = ThreadPool(processes=max_workers)
    
    # Map function over arguments
    results = pool.starmap(func, args_list)
    
    # Close the pool
    pool.close()
    pool.join()
    
    elapsed_time = time.time() - start_time
    print(f"Parallel processing completed in {elapsed_time:.2f} seconds")
    
    return results

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
    """
    Bake a specific attribute of a material to a new texture
    
    Args:
        material: The material to bake
        attribute: The attribute to bake ('diffuse', 'normal', 'metallic', etc.)
        size: The size of the baked texture
        temp_dir: Directory to save the temporary image
    
    Returns:
        The baked image
    """
    start_time = time.time()
    print(f"Baking {attribute} for material {material.name} at size {size}x{size}")
    
    # Create a temporary file if temp_dir is specified
    if temp_dir:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, f"bake_{material.name}_{attribute}.png")
    else:
        # Create a dummy file for the target path
        temp_file = os.path.join(tempfile.gettempdir(), f"bake_{material.name}_{attribute}.png")
    
    print(f"Temporary bake file: {temp_file}")
    
    # Get active object and check materials
    active_object = bpy.context.active_object
    if not active_object:
        raise ValueError("No active object")
        
    # We'll restore the active material later
    original_active_material = None
    if active_object and active_object.active_material:
        original_active_material = active_object.active_material
    
    # Temporarily set our target material as the active material
    # Find an object using this material or the active object
    found_object = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for mat in obj.material_slots:
                if mat.material == material:
                    found_object = obj
                    break
            if found_object:
                break
    
    if not found_object:
        # If we can't find an object with this material, use the active object
        # and temporarily assign the material to it
        if not active_object or active_object.type != 'MESH':
            raise ValueError("No suitable object found to apply material for baking")
        
        found_object = active_object
        
        # Temporarily add a material slot if needed
        material_slot_added = False
        if len(found_object.material_slots) == 0:
            bpy.ops.object.material_slot_add()
            material_slot_added = True
        
        # Store the original material to restore later
        original_material = found_object.material_slots[found_object.active_material_index].material
        
        # Assign our material
        found_object.material_slots[found_object.active_material_index].material = material
    
    # Set as active object
    bpy.context.view_layer.objects.active = found_object
    
    # Create a new temporary image to bake to
    if attribute in ['normal', 'metallic', 'roughness', 'specular', 'ao']:
        # Technical textures get Non-Color space
        colorspace = 'Non-Color'
    else:
        # Color textures get sRGB space
        colorspace = 'sRGB'
    
    temp_image = bpy.data.images.new(
        f"bake_{material.name}_{attribute}",
        width=size,
        height=size,
        alpha=True
    )
    temp_image.filepath = temp_file
    temp_image.colorspace_settings.name = colorspace
    
    # Wait for dependency graph to update
    bpy.context.view_layer.update()
    
    # Store original render settings
    original_engine = bpy.context.scene.render.engine
    original_samples = None
    if hasattr(bpy.context.scene.cycles, 'samples'):
        original_samples = bpy.context.scene.cycles.samples
    
    # Configure for baking
    bpy.context.scene.render.engine = 'CYCLES'
    
    # Reduce samples for quicker baking
    if hasattr(bpy.context.scene.cycles, 'samples'):
        bpy.context.scene.cycles.samples = 32  # Lower for quicker baking
    
    # Configure bake settings
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.use_pass_color = True
    
    # Different settings for different attributes
    if attribute == 'normal':
        bake_type = 'NORMAL'
        bpy.context.scene.render.bake.normal_space = 'TANGENT'
    elif attribute == 'ao':
        bake_type = 'AO'
    elif attribute == 'roughness':
        bake_type = 'ROUGHNESS'
    elif attribute == 'metallic':
        bake_type = 'EMISSION'  # Blender doesn't have a direct metallic bake, use emission
    elif attribute == 'specular':
        bake_type = 'EMISSION'  # Blender doesn't have a direct specular bake, use emission
    else:
        bake_type = 'DIFFUSE'
    
    try:
        # Prepare material for baking based on attribute
        if attribute in ['metallic', 'roughness', 'specular']:
            # For PBR attributes that don't have direct baking, we need to create a temporary node setup
            # Save existing node setup
            original_use_nodes = material.use_nodes
            original_nodes = []
            original_links = []
            
            if material.use_nodes:
                for node in material.node_tree.nodes:
                    original_nodes.append(node)
                for link in material.node_tree.links:
                    original_links.append((link.from_socket, link.to_socket))
            
            # Enable nodes
            material.use_nodes = True
            
            # Create emission node for baking attribute
            emission = material.node_tree.nodes.new('ShaderNodeEmission')
            output = None
            
            # Find the Principled BSDF
            principled = find_principled_bsdf_node(material)
            
            if principled:
                # Find material output
                for node in material.node_tree.nodes:
                    if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
                        output = node
                        break
                
                if not output:
                    output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
                    output.is_active_output = True
                
                # Connect attribute to emission
                if attribute == 'metallic':
                    # Try to get existing value or connection
                    input_socket = principled.inputs.get("Metallic")
                elif attribute == 'roughness':
                    input_socket = principled.inputs.get("Roughness")
                elif attribute == 'specular':
                    input_socket = principled.inputs.get("Specular")
                
                if input_socket:
                    # If input is linked, connect the same texture to emission
                    if input_socket.is_linked:
                        from_socket = input_socket.links[0].from_socket
                        material.node_tree.links.new(from_socket, emission.inputs[0])
                    else:
                        # Otherwise use the value directly
                        emission.inputs[0].default_value = (
                            input_socket.default_value,
                            input_socket.default_value,
                            input_socket.default_value,
                            1.0
                        )
                
                # Connect emission to output
                material.node_tree.links.new(emission.outputs[0], output.inputs[0])
        
        # Set active image in all UV editors
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.spaces.active.image = temp_image
        
        # Bake
        print(f"Starting {attribute} bake with type {bake_type}...")
        bpy.ops.object.bake(
            type=bake_type,
            width=size,
            height=size,
            margin=16,
            use_clear=True,
            save_mode='INTERNAL'
        )
        
        print(f"Bake completed for {attribute}.")
        
        # Save baked image
        temp_image.save()
        
    except Exception as e:
        print(f"Error during baking: {str(e)}")
        raise
    
    finally:
        # Restore original material connections if we modified them
        if attribute in ['metallic', 'roughness', 'specular'] and material.use_nodes:
            # Clear nodes
            material.node_tree.nodes.clear()
            
            # Restore original nodes
            for node in original_nodes:
                material.node_tree.nodes.append(node)
            
            # Restore links
            for from_socket, to_socket in original_links:
                try:
                    material.node_tree.links.new(from_socket, to_socket)
                except:
                    # Some sockets might not exist anymore
                    pass
            
            # Restore use_nodes setting
            material.use_nodes = original_use_nodes
        
        # Restore original material if we temporarily assigned one
        if not found_object == active_object and original_active_material:
            bpy.context.view_layer.objects.active = active_object
            active_object.active_material = original_active_material
        elif 'original_material' in locals():
            found_object.material_slots[found_object.active_material_index].material = original_material
            if material_slot_added:
                bpy.ops.object.material_slot_remove()
        
        # Restore render settings
        bpy.context.scene.render.engine = original_engine
        if original_samples is not None and hasattr(bpy.context.scene.cycles, 'samples'):
            bpy.context.scene.cycles.samples = original_samples
    
    # Return the baked image
    elapsed_time = time.time() - start_time
    print(f"Baking completed in {elapsed_time:.2f} seconds")
    return temp_image

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

def create_simple_texture(name, size=1024, color=(0.5, 0.5, 0.5, 1.0), color_space='Non-Color'):
    """
    Create a simple texture with a solid color
    
    Args:
        name: Name of the texture
        size: Size of the texture (width and height)
        color: RGBA color tuple
        color_space: Colorspace to use ('sRGB' or 'Non-Color')
    
    Returns:
        Created image
    """
    print(f"Creating simple texture: {name} with size {size}x{size}")
    img = bpy.data.images.new(name, width=size, height=size, alpha=True)
    
    # Create a NumPy array of the correct size and fill with the color
    total_pixels = size * size * 4
    pixels_np = np.tile(np.array(color, dtype=np.float32), size * size).reshape(size * size, 4)
    
    # Convert to a flat array for Blender
    pixels_flat = pixels_np.flatten()
    
    # Assign pixels to the image
    img.pixels.foreach_set(pixels_flat, total_pixels)
    
    # Set the color space
    img.colorspace_settings.name = color_space
    
    return img

def extract_pbr_data_simple(material):
    """Extract basic PBR data from a Principled BSDF without baking"""
    print(f"Using simple extraction method for material: {material.name}")
    principled = find_principled_bsdf_node(material)
    if not principled:
        raise ValueError(f"Material '{material.name}' doesn't have a Principled BSDF node")
    
    result = {}
    
    # Get all input values at once for efficiency
    inputs = {
        "Normal": (0.5, 0.5, 1.0, 1.0),  # Default normal map (neutral - flat surface)
        "Metallic": 0.0,                 # Default metallic (non-metal)
        "Roughness": 0.5,                # Default roughness (semi-rough)
        "Specular": 0.5,                 # Default specular (medium)
        "Base Color": (0.8, 0.8, 0.8, 1.0) # Default albedo (light gray)
    }
    
    # Extract values from Principled BSDF
    for input_name in inputs.keys():
        value = get_input_value(principled, input_name)
        if value is not None:
            if isinstance(inputs[input_name], tuple):
                # For color inputs, get the color
                if hasattr(principled.inputs[input_name], "default_value"):
                    # Copy the color but ensure alpha is 1.0
                    color_value = list(principled.inputs[input_name].default_value)
                    if len(color_value) == 4:
                        color_value[3] = 1.0
                    inputs[input_name] = tuple(color_value)
            else:
                # For scalar inputs, store the value
                inputs[input_name] = value
    
    # Create textures efficiently
    texture_size = 1024
    
    # Create normal map - Use Non-Color space
    normal_img = create_simple_texture(
        f"{material.name}_normal", 
        texture_size, 
        inputs["Normal"],
        'Non-Color'
    )
    result['normal'] = normal_img
    
    # Create metallic map - Use Non-Color space
    metallic_val = inputs["Metallic"]
    metallic_img = create_simple_texture(
        f"{material.name}_metallic", 
        texture_size, 
        (metallic_val, metallic_val, metallic_val, 1.0),
        'Non-Color'
    )
    result['metallic'] = metallic_img
    
    # Create roughness map - Use Non-Color space
    roughness_val = inputs["Roughness"]
    roughness_img = create_simple_texture(
        f"{material.name}_roughness", 
        texture_size, 
        (roughness_val, roughness_val, roughness_val, 1.0),
        'Non-Color'
    )
    result['roughness'] = roughness_img
    
    # Create specular map - Use Non-Color space
    specular_val = inputs["Specular"]
    specular_img = create_simple_texture(
        f"{material.name}_specular", 
        texture_size, 
        (specular_val, specular_val, specular_val, 1.0),
        'Non-Color'
    )
    result['specular'] = specular_img
    
    # Create default AO map (no occlusion) - Use Non-Color space
    ao_img = create_simple_texture(
        f"{material.name}_ao", 
        texture_size, 
        (1.0, 1.0, 1.0, 1.0),
        'Non-Color'
    )
    result['ao'] = ao_img
    
    # Create color/albedo map - Use sRGB space for color
    color_val = inputs["Base Color"]
    color_img = create_simple_texture(
        f"{material.name}_color", 
        texture_size, 
        color_val,
        'sRGB'
    )
    result['color'] = color_img
    
    print(f"Successfully created simple PBR textures for {material.name} at {texture_size}x{texture_size}")
    print(f"Values used - Metallic: {metallic_val:.2f}, Roughness: {roughness_val:.2f}, Specular: {specular_val:.2f}")
    
    return result

def create_nor_from_material(material, output_path=None, directx_format=False, bake_size=1024):
    """
    Create a NOR texture from a Blender material using optimized NumPy operations
    
    Args:
        material: The Blender material to extract data from
        output_path: Where to save the NOR texture
        directx_format: Whether to handle normal maps as DirectX format
        bake_size: Size to use for baking textures
    
    Returns:
        Path to the created NOR texture
    """
    start_time = time.time()
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
    
    # Get pixel data as NumPy arrays
    pixel_count = width * height * 4
    normal_pixels_np = np.zeros(pixel_count, dtype=np.float32)
    normal_img.pixels.foreach_get(normal_pixels_np, pixel_count)
    normal_pixels_np = normal_pixels_np.reshape(width * height, 4)
    
    # Create output array
    nor_pixels_np = np.zeros_like(normal_pixels_np)
    
    # Get AO pixels for cavity map if available
    cavity_pixels_np = None
    if 'ao' in pbr_data:
        ao_img = pbr_data['ao']
        # Check if AO image has same dimensions
        if ao_img.size[0] == width and ao_img.size[1] == height:
            cavity_pixels_np = np.zeros(pixel_count, dtype=np.float32)
            ao_img.pixels.foreach_get(cavity_pixels_np, pixel_count)
            cavity_pixels_np = cavity_pixels_np.reshape(width * height, 4)
        else:
            print("AO texture has different dimensions, using default white")
    else:
        print("No AO data found for cavity map, using default white")
    
    # Process pixel data using NumPy operations
    # Red channel (X+) - copy directly from normal map
    nor_pixels_np[:, 0] = normal_pixels_np[:, 0]
    
    # Green channel (Y+)
    if directx_format:
        # For DirectX normal maps (Y-), flip the green channel
        nor_pixels_np[:, 1] = 1.0 - normal_pixels_np[:, 1]
    else:
        # For OpenGL normal maps (Y+), use as is
        nor_pixels_np[:, 1] = normal_pixels_np[:, 1]
    
    # Blue channel (transition blend) - use flat white by default
    nor_pixels_np[:, 2] = 1.0
    
    # Alpha channel (cavity map) - use AO if available, otherwise flat white
    if cavity_pixels_np is not None:
        nor_pixels_np[:, 3] = cavity_pixels_np[:, 0]  # Use red channel of AO map
    else:
        nor_pixels_np[:, 3] = 1.0
    
    # Flatten the array for Blender
    nor_pixels_flat = nor_pixels_np.flatten()
    
    # Assign the processed pixels to the output image
    nor_img.pixels.foreach_set(nor_pixels_flat, pixel_count)
    
    # Save the output image
    nor_img.filepath_raw = output_path
    nor_img.file_format = 'PNG'
    print(f"Saving NOR texture to: {output_path}")
    nor_img.save()
    
    # Clean up
    bpy.data.images.remove(nor_img)
    
    elapsed_time = time.time() - start_time
    print(f"NOR texture creation completed successfully in {elapsed_time:.2f} seconds")
    return output_path

def create_prm_from_material(material, output_path=None, bake_size=1024):
    """
    Create a PRM texture from a Blender material using optimized NumPy operations
    
    Args:
        material: The Blender material to extract data from
        output_path: Where to save the PRM texture
        bake_size: Size to use for baking textures
    
    Returns:
        Path to the created PRM texture
    """
    start_time = time.time()
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
    
    # Get pixel data as NumPy arrays
    pixel_count = width * height * 4
    
    # Initialize arrays
    metallic_pixels_np = np.zeros(pixel_count, dtype=np.float32)
    roughness_pixels_np = np.zeros(pixel_count, dtype=np.float32)
    ao_pixels_np = None
    specular_pixels_np = None
    
    # Get metallic pixels
    metallic_img.pixels.foreach_get(metallic_pixels_np, pixel_count)
    metallic_pixels_np = metallic_pixels_np.reshape(width * height, 4)
    
    # Get roughness pixels
    roughness_img = pbr_data['roughness']
    if roughness_img.size[0] == width and roughness_img.size[1] == height:
        roughness_img.pixels.foreach_get(roughness_pixels_np, pixel_count)
        roughness_pixels_np = roughness_pixels_np.reshape(width * height, 4)
    else:
        print("Roughness texture has different dimensions, resizing...")
        # Create default roughness with correct size
        roughness_pixels_np = np.ones((width * height, 4), dtype=np.float32) * 0.5
    
    # Get AO pixels if available
    if 'ao' in pbr_data:
        ao_img = pbr_data['ao']
        if ao_img.size[0] == width and ao_img.size[1] == height:
            ao_pixels_np = np.zeros(pixel_count, dtype=np.float32)
            ao_img.pixels.foreach_get(ao_pixels_np, pixel_count)
            ao_pixels_np = ao_pixels_np.reshape(width * height, 4)
        else:
            print("AO texture has different dimensions, using default white")
    else:
        print("No AO data found, using default white")
    
    # Get specular pixels if available
    if 'specular' in pbr_data:
        specular_img = pbr_data['specular']
        if specular_img.size[0] == width and specular_img.size[1] == height:
            specular_pixels_np = np.zeros(pixel_count, dtype=np.float32)
            specular_img.pixels.foreach_get(specular_pixels_np, pixel_count)
            specular_pixels_np = specular_pixels_np.reshape(width * height, 4)
        else:
            print("Specular texture has different dimensions, using default value")
    else:
        print("No specular data found, using default 0.16")
    
    # Create the PRM pixel data array
    prm_pixels_np = np.zeros((width * height, 4), dtype=np.float32)
    
    # Process pixel data using NumPy operations
    # Red channel (Metalness) - copy directly
    prm_pixels_np[:, 0] = metallic_pixels_np[:, 0]
    
    # Green channel (Roughness)
    # Smash squares roughness, so take square root to compensate
    roughness_values = roughness_pixels_np[:, 0]
    roughness_values = np.sqrt(roughness_values)  # Square root for compensation
    roughness_values = np.maximum(roughness_values, 0.01)  # Ensure minimum 0.01
    prm_pixels_np[:, 1] = roughness_values
    
    # Blue channel (Ambient Occlusion)
    if ao_pixels_np is not None:
        prm_pixels_np[:, 2] = ao_pixels_np[:, 0]  # Use red channel of AO map
    else:
        # Default AO - full white (no occlusion)
        prm_pixels_np[:, 2] = 1.0
    
    # Alpha channel (Specular)
    if specular_pixels_np is not None:
        # Convert Blender's specular (0-8%) to Smash (0-20%)
        # smashSpecular = blenderSpecular * 0.4
        prm_pixels_np[:, 3] = specular_pixels_np[:, 0] * 0.4
    else:
        # Default specular - 0.16 (40/255)
        prm_pixels_np[:, 3] = 0.16
    
    # Flatten the array for Blender
    prm_pixels_flat = prm_pixels_np.flatten()
    
    # Assign the processed pixels to the output image
    prm_img.pixels.foreach_set(prm_pixels_flat, pixel_count)
    
    # Save the output image
    prm_img.filepath_raw = output_path
    prm_img.file_format = 'PNG'
    print(f"Saving PRM texture to: {output_path}")
    prm_img.save()
    
    # Clean up
    bpy.data.images.remove(prm_img)
    
    elapsed_time = time.time() - start_time
    print(f"PRM texture creation completed successfully in {elapsed_time:.2f} seconds")
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