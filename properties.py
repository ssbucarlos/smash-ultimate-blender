import bpy
import re
from bpy.types import Scene, Object, Armature, PropertyGroup, Camera
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty
from bpy.props import FloatVectorProperty
from .modules import exo_skel, import_anim, helper_bone_data
from . import modules

def register():
    Armature.sub_anim_properties = PointerProperty(
        type=SubAnimProperties
    )
    Scene.sub_scene_properties = PointerProperty(
        type=SubSceneProperties
    )
    Armature.sub_helper_bone_data = PointerProperty(
        type=helper_bone_data.SubHelperBoneData
    )

class SubSceneProperties(PropertyGroup):
    anim_import_arma: PointerProperty(
        name='Armature',
        description='Select the Armature',
        type=Object,
        poll=exo_skel.poll_armatures,  
    )
    anim_export_arma: PointerProperty(
        name='Armature',
        description='Select the Armature',
        type=Object,
        poll=exo_skel.poll_armatures,   
    )
    anim_import_camera: PointerProperty(
        name='Camera',
        description='Select the Camera',
        type=Object,
        poll=import_anim.poll_cameras,
    )
    anim_export_camera: PointerProperty(
        name='Camera',
        description='Select the Camera',
        type=Object,
        poll=import_anim.poll_cameras,
    )
    model_export_arma: PointerProperty(
        name='Armature',
        description='Select the Armature',
        type=Object,
        poll=exo_skel.poll_armatures,
    )
    vanilla_nusktb: StringProperty(
        name='Vanilla .NUSKTB file path',
        description='The path to the vanilla nusktb file',
        default='',
    )
    model_import_numatb_file_name: StringProperty(
        name='.numatb file name',
        description='The name of the .numatb file',
        default='',
    )
    model_import_numshb_file_name: StringProperty(
        name='.numshb file name',
        description='The name of the .numshb file',
        default='',
    )
    model_import_nusktb_file_name: StringProperty(
        name='.nusktb file name',
        description='The name of the .nusktb file',
        default='',
    )
    model_import_numdlb_file_name: StringProperty(
        name='.numdlb file name',
        description='The name of the .numdlb file',
        default='',
    )
    model_import_nuhlpb_file_name: StringProperty(
        name='.nuhlpb file name',
        description='The name the .nuhlpb file',
        default='',
    )
    model_import_folder_path: StringProperty(
        name='Model folder path',
        description='The path to the model folder',
        default='',
    )
    smash_armature: PointerProperty(
        name='Smash Armature',
        description='Select the Smash armature',
        type=Object,
        poll=exo_skel.poll_armatures,
    )
    other_armature: PointerProperty(
        name='Other Armature',
        description='Select the Other armature',
        type=Object,
        poll=exo_skel.poll_other_armatures,
    )
    bone_list: CollectionProperty(
        type=exo_skel.BoneListItem
    )
    saved_bone_list: CollectionProperty(
        type=exo_skel.BoneListItem
    )
    bone_list_index: IntProperty(
        name="Index for the exo bone list",
        default=0
    )
    pairable_bone_list: CollectionProperty(
        type=exo_skel.PairableBoneListItem
    )
    armature_prefix: StringProperty(
        name="Prefix",
        description="The Prefix that will be added to the bones in the 'Other' armature. Must begin with H_ or else it wont work!",
        default="H_Exo_"
    )
    material_reimport_arma: PointerProperty(
        name='Armature',
        description='Select the Armature',
        type=Object,
        poll=exo_skel.poll_armatures,  
    )
    material_reimport_folder: StringProperty(
        name='Material Reimport folder',
        description='The folder w/ .numatb & textures',
        default='',
    )
    material_reimport_numatb_path: StringProperty(
        name='Material Reimport .numatb',
        description='The selected .numatb',
        default='',
    )

def vis_track_name_update(self, context):
    sap = context.object.data.sub_anim_properties
    dupe = None
    for vt in sap.vis_track_entries:
        if vt.as_pointer() == self.as_pointer():
            continue
        if vt.name == self.name:
            dupe = vt
            break  
    if dupe is None:
        return
    regex = r"(\w+\.)(\d+)"
    matches = re.match(regex, self.name)
    if matches is None:
        self.name = self.name + '.001'
    else:
        base_name = matches.groups()[0]
        number = int(matches.groups()[1])
        self.name = f'{base_name}{number+1:003d}' 



def mat_track_prop_name_update(self, context):
    sap = context.object.data.sub_anim_properties
    found = False
    current_mat_track_index = None
    for mat_track_index, mat_track in enumerate(sap.mat_tracks):
        for property in mat_track.properties:
            if property.as_pointer() == self.as_pointer():
                current_mat_track_index = mat_track_index
                found = True
                break
        if found:
            break
    current_mat_track = sap.mat_tracks[current_mat_track_index]
    # There should be at most only one duplicate
    dupe = None
    for p in current_mat_track.properties:
        if p.as_pointer() == self.as_pointer():
            continue
        if p.name == self.name:
            dupe = p
            break
    # No duplicate found, name can remain as is
    if dupe is None:
        return
    # Regex match the name, see if it already has like '.001'
    # if it doesnt then add the '.001', otherwise increment the number
    regex = r"(\w+\.)(\d+)"
    matches = re.match(regex, self.name)
    if matches is None:
        self.name = self.name + '.001'
    else:
        base_name = matches.groups()[0]
        number = int(matches.groups()[1])
        self.name = f'{base_name}{number+1:003d}'

def mat_track_name_update(self, context):
    sap = context.object.data.sub_anim_properties
    dupe = None
    for mt in sap.mat_tracks:
        if mt.as_pointer() == self.as_pointer():
            continue
        if mt.name == self.name:
            dupe = mt
            break  
    if dupe is None:
        return
    regex = r"(\w+\.)(\d+)"
    matches = re.match(regex, self.name)
    if matches is None:
        self.name = self.name + '.001'
    else:
        base_name = matches.groups()[0]
        number = int(matches.groups()[1])
        self.name = f'{base_name}{number+1:003d}' 

class VisTrackEntry(PropertyGroup):
    name: StringProperty(
        name="Vis Name",
        default="Unknown",
        update=vis_track_name_update,)
    value: BoolProperty(name="Visible", default=False)

class MatTrackProperty(PropertyGroup):
    name: StringProperty(
        name="Property Name",
        default="Unknown",
        update=mat_track_prop_name_update,)
    sub_type: EnumProperty(
        name='Mat Track Entry Subtype',
        description='CustomVector or CustomFloat or CustomBool',
        items=modules.anim_data.mat_sub_types, 
        default='VECTOR',)
    custom_vector: FloatVectorProperty(name='Custom Vector', size=4)
    custom_bool: BoolProperty(name='Custom Bool')
    custom_float: FloatProperty(name='Custom Float')
    pattern_index: IntProperty(name='Pattern Index', subtype='UNSIGNED')
    texture_transform: FloatVectorProperty(name='Texture Transform', size=5)

class MatTrack(PropertyGroup):
    name: StringProperty(
        name="Material Name",
        default="Unknown",
        update=mat_track_name_update,)
    properties: CollectionProperty(type=MatTrackProperty)
    active_property_index: IntProperty(name='Active Mat Property Index', default=0)

class SubAnimProperties(PropertyGroup):
    vis_track_entries: CollectionProperty(type=VisTrackEntry)
    active_vis_track_index: IntProperty(name='Active Vis Track Index', default=0)
    mat_tracks: CollectionProperty(type=MatTrack)
    active_mat_track_index: IntProperty(name='Active Mat Track Index', default=0)



