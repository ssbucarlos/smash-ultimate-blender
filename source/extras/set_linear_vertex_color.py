import bpy

from bpy.types import Context, Object, Mesh, ByteColorAttribute, FloatColorAttribute, MeshPolygon

def main(context: Context):
    obj: Object = context.object
    mesh: Mesh = obj.data
    active_color_set: ByteColorAttribute | FloatColorAttribute  = mesh.color_attributes.active_color
    active_brush = context.tool_settings.vertex_paint.brush

    if mesh.use_paint_mask:
        selected_polygons: set[MeshPolygon] = {polygon for polygon in mesh.polygons if polygon.select == True}
        for polygon in selected_polygons:
            if active_color_set.domain == "POINT": # Per-Vertex
                for vertex_index in polygon.vertices:
                    active_color_set.data[vertex_index].color[0:3] = active_brush.color[:]
            elif active_color_set.domain == "CORNER": # Per-Loop
                for loop_index in polygon.loop_indices:
                    active_color_set.data[loop_index].color[0:3] = active_brush.color[:]
    elif mesh.use_paint_mask_vertex:
        selected_vertex_indices = {vert.index for vert in mesh.vertices if vert.select == True}
        if active_color_set.domain == "POINT": # Per-Vertex
            for vert_index in selected_vertex_indices:
                active_color_set.data[vert_index].color[0:3] = active_brush.color[:]
        elif active_color_set.domain == "CORNER": # Per-Loop
            selected_loop_indices = {loop.index for loop in mesh.loops if loop.vertex_index in selected_vertex_indices}
            for loop_index in selected_loop_indices:
                active_color_set.data[loop_index].color[0:3] = active_brush.color[:]
    else:
        for vertex_data in active_color_set.data:
            vertex_data.color[0:3] = active_brush.color[:]


class SUB_OP_LinearColorSet(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "paint.sub_vertex_color_set_linear"
    bl_label = "Set Vertex Colors (Linear)"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(SUB_OP_LinearColorSet.bl_idname, text=SUB_OP_LinearColorSet.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register():
    bpy.utils.register_class(SUB_OP_LinearColorSet)
    bpy.types.VIEW3D_MT_paint_vertex.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SUB_OP_LinearColorSet)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()

