import os
import bpy
import os.path

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Panel
import re
from ..ssbh_data_py import ssbh_data_py

class ExportModelPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    bl_label = 'Model Exporter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        row = layout.row(align=True)
        row.label(text='Select an armature. The armature + its meshes will be exported')

        row = layout.row(align=True)
        row.prop(context.scene, 'sub_model_export_armature', icon='ARMATURE_DATA')

        if not context.scene.sub_model_export_armature:
            return
        
        row = layout.row(align=True)
        row.operator('sub.model_exporter', icon='EXPORT', text='Export Model Files to a Folder')
    
class ModelExporterOperator(Operator, ImportHelper):
    bl_idname = 'sub.model_exporter'
    bl_label = 'Export To This Folder'

    filter_glob: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped. Also blender has this in the example but tbh idk what it does yet
    )

    include_numdlb: BoolProperty(
        name="Export .NUMDLB",
        description="Export .NUMDLB",
        default=True,
    )
    include_numshb: BoolProperty(
        name="Export .NUMSHB",
        description="Export .NUMSHB",
        default=True,
    )
    include_numshexb: BoolProperty(
        name="Export .NUMSHEXB",
        description="Export .NUMSHEXB",
        default=True,
    )
    include_nusktb: BoolProperty(
        name="Export .NUSKTB",
        description="Export .NUSKTB",
        default=True,
    )
    include_numatb: BoolProperty(
        name="Export .NUMATB",
        description="Export .NUMATB",
        default=True,
    )

    def execute(self, context):
        export_model(context, self.filepath, self.include_numdlb, self.include_numshb, self.include_numshexb,
                     self.include_nusktb, self.include_numatb)
        return {'FINISHED'}

def export_model(context, filepath, include_numdlb, include_numshb, include_numshexb, include_nusktb, include_numatb):
    if include_numshb:
        export_numshb(context, filepath)
    if include_nusktb:
        export_nusktb(context, filepath)

def export_numshb(context, filepath):
    arma = context.scene.sub_model_export_armature
    export_meshes = [child for child in arma.children if child.type == 'MESH']
    ssbh_mesh_data = ssbh_data_py.mesh_data.MeshData()

    for mesh in export_meshes:
        real_mesh_name = re.split(r'.\d\d\d', mesh.name)[0] # Un-uniquify the names
        ssbh_mesh_object = ssbh_data_py.mesh_data.MeshObjectData(real_mesh_name, 0)

        position0 = ssbh_data_py.mesh_data.AttributeData('Postion0')
        position0.data = [list(vertex.co[:]) for vertex in mesh.data.vertices] # Thanks SMG for these one-liners
        ssbh_mesh_object.positions = [position0]

        normal0 = ssbh_data_py.mesh_data.AttributeData('Normal0')
        #normal0.data = [list(vertex.normal[:]) for vertex in mesh.data.vertices] <-- omg why cant this just contain custom normal data
        # So we gotta go through loop by loop
        # mesh.data.loops[index].normal contains the actual custom normal data
        index_to_normals_dict = {} # Dont judge the internet told me list insertion was bugged plus dictionaries are goated
        mesh.data.calc_normals_split() # Needed apparently or the vertex normal data wont be filled 
        for loop in mesh.data.loops:
            index_to_normals_dict[loop.vertex_index] = loop.normal[:]
        normal0.data = [list(index_to_normals_dict[key]) for key in sorted(index_to_normals_dict.keys())]
        ssbh_mesh_object.normals = [normal0]

        # Python magic to flatten the faces into a single list of vertex indices.
        ssbh_mesh_object.vertex_indices = [index for face in mesh.data.polygons for index in face.vertices]

        ssbh_mesh_data.objects.append(ssbh_mesh_object)

    ssbh_mesh_data.save(filepath + 'model.numshb')

    return

def export_nusktb(context, filepath):

    return


        