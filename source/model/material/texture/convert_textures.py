import bpy
import os
import tempfile
import numpy as np
from mathutils import Color

def find_principled_bsdf_node(material):
    """Find Principled BSDF node in the material's node tree"""
    if not material or not material.node_tree:
        return None
    
    for node in material.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    
    return None

def extract_texture_from_input(input_socket, target_size):
    """
    Attempt to extract a texture from an input socket
    
    Args:
        input_socket: The input socket to extract from
        target_size: The target texture size
        
    Returns:
        numpy array of pixel values or None if extraction fails
    """
    if not input_socket.links:
        return None
    
    # Find the source node
    from_node = input_socket.links[0].from_node
    
    # If it's a texture node with an image
    if from_node.type == 'TEX_IMAGE' and from_node.image:
        try:
            # Get the image pixels
            img = from_node.image
            pixels = np.array(img.pixels[:]).reshape((-1, 4))
            
            # Check if image size matches target size
            if pixels.shape[0] != target_size * target_size:
                # Extract grayscale value (average of RGB)
                gray = np.mean(pixels[:, :3], axis=1)
                
                # Simple resize using nearest neighbor
                orig_width, orig_height = img.size
                
                # Simple bilinear sampling to resize
                y_indices = np.linspace(0, orig_height-1, target_size)
                x_indices = np.linspace(0, orig_width-1, target_size)
                
                # Floor the indices to get the pixel coordinates
                y0 = np.floor(y_indices).astype(int)
                x0 = np.floor(x_indices).astype(int)
                
                # Ensure we don't go out of bounds
                y0 = np.clip(y0, 0, orig_height-1)
                x0 = np.clip(x0, 0, orig_width-1)
                
                # Get the values at the pixel coordinates
                gray_2d = gray.reshape(orig_height, orig_width)
                resized_values = np.zeros((target_size, target_size))
                for i in range(target_size):
                    for j in range(target_size):
                        resized_values[i, j] = gray_2d[y0[i], x0[j]]
                
                return resized_values
            else:
                # Extract grayscale value
                return np.mean(pixels[:, :3], axis=1).reshape((target_size, target_size))
        except Exception as e:
            print(f"Failed to process texture: {e}")
            return None
    
    # For more complex node setups, we would need to bake
    return None

def create_prm_from_material(material, output_path=None, bake_size=1024):
    """
    Create a PRM texture from a Blender material. The PRM texture contains:
    - Red channel: Metalness (0-1)
    - Green channel: Roughness (0-1)
    - Blue channel: Ambient Occlusion (0-1)
    - Alpha channel: Specular (0-1, scaled by 0.2)
    
    Args:
        material: The Blender material to create a PRM texture from
        output_path: Optional path to save the PRM texture to. If None, returns the Blender image.
        bake_size: Size of the texture to create (square)
        
    Returns:
        If output_path is provided: The path to the saved PRM texture
        If output_path is None: The Blender image object
    """
    # Define default values based on Smash Ultimate defaults
    default_metalness = 0.0    # No metalness by default
    default_roughness = 0.5    # Mid roughness by default
    default_ao = 1.0           # Full ambient occlusion by default
    default_specular = 0.16    # Specular value scaled by 0.2 (0.8 * 0.2 = 0.16)
    
    # Create a new image for the PRM texture
    image_name = f"{material.name}_PRM"
    prm_img = bpy.data.images.new(image_name, width=bake_size, height=bake_size, alpha=True)
    prm_img.colorspace_settings.name = 'Non-Color'  # Important for non-color data

    # Initialize arrays for each channel
    metalness = np.full((bake_size, bake_size), default_metalness, dtype=np.float32)
    roughness = np.full((bake_size, bake_size), default_roughness, dtype=np.float32)
    ao = np.full((bake_size, bake_size), default_ao, dtype=np.float32)
    specular = np.full((bake_size, bake_size), default_specular, dtype=np.float32)
    
    try:
        # Extract values from Principled BSDF if it exists
        if material.use_nodes and material.node_tree:
            principled_node = None
            
            # Find Principled BSDF node
            for node in material.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled_node = node
                    break
            
            if principled_node:
                # Extract metalness value
                metal_input = principled_node.inputs.get('Metallic')
                if metal_input:
                    if metal_input.is_linked:
                        # Try to get texture from this input
                        metal_value = extract_texture_from_input(metal_input, bake_size)
                        if metal_value is not None:
                            metalness = metal_value
                    else:
                        # Use the direct value
                        metalness = np.full((bake_size, bake_size), metal_input.default_value, dtype=np.float32)
                
                # Extract roughness value
                roughness_input = principled_node.inputs.get('Roughness')
                if roughness_input:
                    if roughness_input.is_linked:
                        # Try to get texture from this input
                        roughness_value = extract_texture_from_input(roughness_input, bake_size)
                        if roughness_value is not None:
                            roughness = roughness_value
                    else:
                        # Use the direct value
                        roughness = np.full((bake_size, bake_size), roughness_input.default_value, dtype=np.float32)
                
                # Extract specular value (scaled by 0.2 as per Smash spec)
                specular_input = principled_node.inputs.get('Specular')
                if specular_input:
                    if specular_input.is_linked:
                        # Try to get texture from this input
                        specular_value = extract_texture_from_input(specular_input, bake_size)
                        if specular_value is not None:
                            # Scale by 0.2 as per Smash spec
                            specular = specular_value * 0.2
                    else:
                        # Use the direct value, scaled by 0.2
                        specular = np.full((bake_size, bake_size), specular_input.default_value * 0.2, dtype=np.float32)
            
            # Look for AO texture in material (common for games)
            # This is more speculative as AO isn't a standard Principled BSDF input
            for node in material.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image and node.image.name.lower().find('ao') >= 0:
                    try:
                        ao_pixels = np.array(node.image.pixels[:]).reshape((-1, 4))
                        # Resize if necessary
                        if ao_pixels.shape[0] != bake_size * bake_size:
                            # Extract grayscale value (average of RGB)
                            ao_gray = np.mean(ao_pixels[:, :3], axis=1)
                            # Simple resize
                            orig_width, orig_height = node.image.size
                            
                            # Simple bilinear sampling to resize
                            y_indices = np.linspace(0, orig_height-1, bake_size)
                            x_indices = np.linspace(0, orig_width-1, bake_size)
                            
                            # Floor the indices to get the pixel coordinates
                            y0 = np.floor(y_indices).astype(int)
                            x0 = np.floor(x_indices).astype(int)
                            
                            # Ensure we don't go out of bounds
                            y0 = np.clip(y0, 0, orig_height-1)
                            x0 = np.clip(x0, 0, orig_width-1)
                            
                            # Get the values at the pixel coordinates
                            gray_2d = ao_gray.reshape(orig_height, orig_width)
                            resized_values = np.zeros((bake_size, bake_size))
                            for i in range(bake_size):
                                for j in range(bake_size):
                                    resized_values[i, j] = gray_2d[y0[i], x0[j]]
                            
                            ao = resized_values
                        else:
                            # Extract grayscale value
                            ao = np.mean(ao_pixels[:, :3], axis=1).reshape((bake_size, bake_size))
                    except Exception as e:
                        print(f"Failed to process AO texture: {e}")
                        # Keep default AO
        
        # Combine channels to create the PRM texture
        # Reshape arrays to 1D for pixels assignment
        metalness_flat = metalness.flatten()
        roughness_flat = roughness.flatten()
        ao_flat = ao.flatten()
        specular_flat = specular.flatten()
        
        # Interleave the channel data (RGBA format)
        pixel_count = bake_size * bake_size
        pixels = np.empty(pixel_count * 4, dtype=np.float32)
        
        # Assign channels in the correct order
        pixels[0::4] = metalness_flat  # R channel = Metalness
        pixels[1::4] = roughness_flat  # G channel = Roughness
        pixels[2::4] = ao_flat         # B channel = AO
        pixels[3::4] = specular_flat   # A channel = Specular
        
        # Set the pixels
        prm_img.pixels = pixels.tolist()
        
        # Pack the image if we're keeping it in Blender
        if not output_path:
            if not prm_img.packed_file:
                prm_img.pack()
            return prm_img
        
        # Save to external file if requested
        prm_img.filepath_raw = output_path
        prm_img.file_format = 'PNG'
        prm_img.save()
        
        return output_path
    
    except Exception as e:
        print(f"Error creating PRM texture: {e}")
        if output_path:
            # Create a default PRM texture as fallback
            create_default_prm_texture(output_path, bake_size)
            return output_path
        else:
            # Fill with default values as fallback
            pixels = []
            for i in range(bake_size * bake_size):
                pixels.extend([default_metalness, default_roughness, default_ao, default_specular])
            prm_img.pixels = pixels
            if not prm_img.packed_file:
                prm_img.pack()
            return prm_img

def create_default_prm_texture(output_path, size=1024):
    """Create a default PRM texture with reasonable values using Blender's native functionality"""
    # Create a new image
    img = bpy.data.images.new(f"default_PRM", width=size, height=size, alpha=True)
    
    # Set the default values:
    # Red (Metalness): 0.0
    # Green (Roughness): 0.5
    # Blue (Ambient Occlusion): 1.0
    # Alpha (Specular): 0.16
    
    # Create array of pixel values
    pixel_count = size * size
    pixels = np.zeros(pixel_count * 4, dtype=np.float32)
    
    # Set default values for each channel
    pixels[0::4] = 0.0  # Red (Metalness)
    pixels[1::4] = 0.5  # Green (Roughness)
    pixels[2::4] = 1.0  # Blue (AO)
    pixels[3::4] = 0.16  # Alpha (Specular)
    
    # Assign to image
    img.pixels = pixels.tolist()
    
    # Save to file
    img.filepath_raw = output_path
    img.file_format = 'PNG'
    img.save()

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
        min=64,
        max=8192
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