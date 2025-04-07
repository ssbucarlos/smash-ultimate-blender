import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty

class SUB_OP_transfer_exo_weights(Operator):
    bl_idname = "sub.transfer_exo_weights"
    bl_label = "Transfer Exo Weights"
    bl_description = "Transfer weights from Exo helper bones to their controlling Smash bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    delete_original_groups: BoolProperty(
        name="Delete Original Groups",
        description="Delete the original Exo bone vertex groups after transfer",
        default=False
    )
    
    mix_mode: BoolProperty(
        name="Mix Mode",
        description="Mix weights with existing weights instead of replacing them",
        default=False
    )
    
    mix_factor: FloatProperty(
        name="Mix Factor",
        description="Amount of mixing with existing weights (1.0 = full source weight)",
        default=1.0,
        min=0.0,
        max=1.0
    )
    
    @classmethod
    def poll(cls, context):
        # Ensure we have an armature with helper bone data and selected meshes
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                hasattr(context.active_object.data, "sub_helper_bone_data") and
                any(obj.type == 'MESH' and obj.select_get() for obj in context.selected_objects))
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "delete_original_groups")
        layout.prop(self, "mix_mode")
        if self.mix_mode:
            layout.prop(self, "mix_factor", slider=True)
    
    def execute(self, context):
        armature = context.active_object
        helper_bone_data = armature.data.sub_helper_bone_data
        
        # Get exo bone mapping from helper bone data
        exo_bone_mapping = {}
        
        # Process orient constraints - they connect Exo bones to controlling bones
        for constraint in helper_bone_data.orient_constraints:
            # Check if this is an Exo bone constraint
            if "H_Exo_" in constraint.target_bone_name:
                exo_bone_mapping[constraint.target_bone_name] = constraint.source_bone_name
        
        # Process selected meshes
        processed_meshes = 0
        transferred_groups = 0
        
        for obj in context.selected_objects:
            if obj.type != 'MESH' or not obj.parent or obj.parent.type != 'ARMATURE':
                continue
                
            processed_meshes += 1
            
            # Get vertex groups
            for exo_bone_name, controlling_bone_name in exo_bone_mapping.items():
                # Skip if exo bone has no vertex group
                if exo_bone_name not in obj.vertex_groups:
                    continue
                    
                # Create controlling bone group if it doesn't exist
                controlling_group = None
                if controlling_bone_name in obj.vertex_groups:
                    controlling_group = obj.vertex_groups[controlling_bone_name]
                else:
                    controlling_group = obj.vertex_groups.new(name=controlling_bone_name)
                
                # Get exo bone vertex group
                exo_group = obj.vertex_groups[exo_bone_name]
                exo_group_index = exo_group.index
                
                # Transfer weights
                for v in obj.data.vertices:
                    # Find weight in exo group
                    exo_weight = 0
                    for g in v.groups:
                        if g.group == exo_group_index:
                            exo_weight = g.weight
                            break
                    
                    if exo_weight > 0:
                        if self.mix_mode:
                            # Mix weights - first get existing weight if any
                            try:
                                existing_weight = controlling_group.weight(v.index)
                            except:
                                existing_weight = 0
                                
                            # Calculate mixed weight
                            mixed_weight = existing_weight * (1 - self.mix_factor) + exo_weight * self.mix_factor
                            
                            # Set mixed weight
                            controlling_group.add([v.index], mixed_weight, 'REPLACE')
                        else:
                            # Direct replacement mode
                            controlling_group.add([v.index], exo_weight, 'REPLACE')
                
                transferred_groups += 1
                
                # Delete exo bone group if requested
                if self.delete_original_groups:
                    obj.vertex_groups.remove(exo_group)
        
        # Report results
        if processed_meshes == 0:
            self.report({'WARNING'}, "No valid meshes selected with vertex groups")
            return {'CANCELLED'}
        elif transferred_groups == 0:
            self.report({'WARNING'}, "No Exo bone weights found to transfer")
            return {'CANCELLED'}
        else:
            self.report({'INFO'}, f"Transferred weights from {transferred_groups} Exo bone groups across {processed_meshes} meshes")
            return {'FINISHED'}

def register():
    bpy.utils.register_class(SUB_OP_transfer_exo_weights)

def unregister():
    bpy.utils.unregister_class(SUB_OP_transfer_exo_weights)

if __name__ == "__main__":
    register() 