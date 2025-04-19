import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

class SUB_OP_limit_weights(Operator):
    """Limit vertex weights to 4 bones per vertex for all selected meshes"""
    bl_idname = "sub.limit_weights"
    bl_label = "Limit Weights to 4"
    bl_description = "Limits vertex weights to a maximum of 4 bones per vertex"
    bl_options = {'REGISTER', 'UNDO'}
    
    remove_zero_weights: BoolProperty(
        name="Remove Zero Weights",
        description="Remove weights that are zero after limiting",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects and any(obj.type == 'MESH' for obj in context.selected_objects)
    
    def execute(self, context):
        modified_objects = 0
        total_vertices = 0
        vertices_modified = 0
        
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
                
            # Check if object has vertex groups
            if not hasattr(obj, 'vertex_groups') or not obj.vertex_groups:
                self.report({'WARNING'}, f"Object '{obj.name}' has no vertex groups")
                continue
                
            # Store original mode
            original_mode = obj.mode
            
            # Switch to object mode for vertex group operations
            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Get the mesh data
            mesh = obj.data
            total_vertices += len(mesh.vertices)
            
            # Process each vertex
            for vertex in mesh.vertices:
                if len(vertex.groups) > 4:
                    # Sort groups by weight
                    sorted_groups = sorted(vertex.groups, key=lambda x: x.weight, reverse=True)
                    
                    # Keep only top 4 weights
                    total_weight = sum(g.weight for g in sorted_groups[:4])
                    
                    # Normalize weights
                    for group in sorted_groups[:4]:
                        group.weight = group.weight / total_weight
                    
                    # Remove excess groups
                    for group in sorted_groups[4:]:
                        obj.vertex_groups[group.group].remove([vertex.index])
                    
                    vertices_modified += 1
            
            # Remove zero weights if requested
            if self.remove_zero_weights:
                for vertex in mesh.vertices:
                    zero_groups = [g for g in vertex.groups if g.weight < 0.0001]
                    for group in zero_groups:
                        obj.vertex_groups[group.group].remove([vertex.index])
            
            # Return to original mode
            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode=original_mode)
            
            modified_objects += 1
        
        if modified_objects > 0:
            self.report({'INFO'}, f"Modified {vertices_modified} vertices in {modified_objects} objects")
        else:
            self.report({'WARNING'}, "No mesh objects with vertex groups were selected")
            
        return {'FINISHED'}

def register():
    bpy.utils.register_class(SUB_OP_limit_weights)

def unregister():
    bpy.utils.unregister_class(SUB_OP_limit_weights) 