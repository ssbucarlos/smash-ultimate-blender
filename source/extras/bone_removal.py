'''
Adapted from https://blender.stackexchange.com/a/226914/132453
'''
import bpy
from bpy.types import Operator

class SUB_OT_remove_selected_bones(Operator):
    bl_idname = "sub.remove_selected_bones"
    bl_label = "Remove Selected Bones"
    bl_description = "Removes selected bones and transfers their weights to their parents"
    bl_options = {'REGISTER', 'UNDO'}

    def transfer_weights(self, source, target, obj):
        source_group = obj.vertex_groups.get(source.name)
        if source_group is None:
            return
        source_i = source_group.index
        target_group = obj.vertex_groups.get(target.name)
        if target_group is None:
            target_group = obj.vertex_groups.new(name=target.name)
            
        for v in obj.data.vertices:
            for g in v.groups:
                if g.group == source_i:
                    target_group.add((v.index,), g.weight, 'ADD')
        obj.vertex_groups.remove(source_group)

    def remove_bone(self, source, target):
        for o in bpy.data.objects:
            self.transfer_weights(source, target, o)
        edit_bone = bpy.context.object.data.edit_bones.get(source.name)
        bpy.context.object.data.edit_bones.remove(edit_bone)

    def find_parent_not_in_collection(self, bone, collection):
        if bone.parent in collection:
            return self.find_parent_not_in_collection(bone.parent, collection)
        else:
            return bone.parent

    @classmethod
    def poll(cls, context):
        return (context.active_object 
                and context.active_object.type == 'ARMATURE'
                and context.active_object.mode == 'EDIT')

    def execute(self, context):
        selected_bones = [bone for bone in context.object.data.edit_bones if bone.select]
        for selected_bone in selected_bones:
            target = self.find_parent_not_in_collection(selected_bone, selected_bones)
            self.remove_bone(selected_bone, target)
        return {'FINISHED'}

# Register the operator
def register():
    bpy.utils.register_class(SUB_OT_remove_selected_bones)

def unregister():
    bpy.utils.unregister_class(SUB_OT_remove_selected_bones)

if __name__ == "__main__":
    register()