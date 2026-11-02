"""Run with Blender --background --factory-startup --python this_file.py."""

import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import bpy

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO.parent))
addon = importlib.import_module(REPO.name)
importlib.import_module(f'{REPO.name}.source.updater.version_check').check_for_newer_version = lambda: None
addon.register()
config = importlib.import_module(f'{REPO.name}.source.model.arcropolis_config')
exporter = importlib.import_module(f'{REPO.name}.source.model.export_model')
textures = importlib.import_module(f'{REPO.name}.source.model.material.texture.export_nutexb')
bake = importlib.import_module(f'{REPO.name}.source.model.material.bake_model_colors')
ssbh = importlib.import_module(f'{REPO.name}.dependencies.ssbh_data_py')


class Reporter:
    def report(self, level, message):
        if 'ERROR' in level:
            raise AssertionError(message)


class ARCropolisExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ultimate_config_test_')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.folder = config.model_folder(self.root, 'ken', 'c01')
        self.folder.mkdir(parents=True)
        self.texture = self.folder / 'sal_col.nutexb'
        self.texture.write_bytes(b'test')
        ssp = bpy.context.scene.sub_scene_properties
        ssp.vanilla_nusktb = ''
        ssp.model_export_override_target = False
        ssp.model_export_fighter = ''
        ssp.model_export_costume = 'c00'

    def test_target_inference_reads_windows_linux_and_relative_paths(self):
        for path in (r'C:\dump\fighter\ken\model\body\c01\model.nusktb',
                     '/dump/fighter/ken/model/body/c01/model.nusktb',
                     '//vanilla/ken/model/body/c01/model.nusktb',
                     'C:/DUMP/FIGHTER/KEN/MODEL/BODY/C01/MODEL.NUSKTB'):
            with self.subTest(path=path):
                self.assertEqual(('ken', 'c01'), config.target_from_vanilla(path))
        for path in ('model.nusktb', r'C:\vanilla\model.nusktb',
                     r'C:\vanilla\ken\model.nusktb',
                     'fighter/ken/model/body/c08/model.nusktb',
                     'fighter/ken/model/body/c01/def_ken_001_col.nutexb',
                     'fighter/ken/model/body/c01/backup/model.nusktb'):
            with self.subTest(path=path):
                self.assertIsNone(config.target_from_vanilla(path))

    def test_switch_package_is_the_default_and_flat_export_is_an_explicit_choice(self):
        ssp = bpy.context.scene.sub_scene_properties
        self.assertTrue(type(ssp).bl_rna.properties['model_export_switch_mod'].default)
        self.assertTrue(bpy.ops.sub.model_exporter.get_rna_type().properties['create_switch_mod'].default)
        # Preserve a user's deliberate choice to export loose files.
        ssp.model_export_switch_mod = False
        operator = SimpleNamespace()
        context = SimpleNamespace(scene=bpy.context.scene,
                                  window_manager=SimpleNamespace(fileselect_add=lambda op: None))
        exporter.SUB_OP_model_exporter.invoke(operator, context, None)
        self.assertFalse(operator.create_switch_mod)
        ssp.model_export_switch_mod = True

    def test_vanilla_selection_and_export_dialog_fill_target_and_allow_override(self):
        ssp = bpy.context.scene.sub_scene_properties
        ssp.vanilla_nusktb = r'C:\dump\fighter\ken\model\body\c01\model.nusktb'
        self.assertEqual(('ken', 'c01'), (ssp.model_export_fighter, ssp.model_export_costume))
        dialogs = []
        context = SimpleNamespace(scene=bpy.context.scene,
                                  window_manager=SimpleNamespace(fileselect_add=dialogs.append))
        operator = SimpleNamespace()
        self.assertEqual({'RUNNING_MODAL'}, exporter.SUB_OP_model_exporter.invoke(operator, context, None))
        self.assertEqual(('ken', 'c01'), (operator.fighter_name, operator.costume_slot))
        self.assertFalse(operator.override_vanilla_target)
        self.assertEqual([operator], dialogs)
        ssp.model_export_override_target = True
        ssp.model_export_fighter = 'mario'
        ssp.model_export_costume = 'c03'
        ssp.vanilla_nusktb = '/dump/fighter/ryu/model/body/c02/model.nusktb'
        exporter.SUB_OP_model_exporter.invoke(operator, context, None)
        self.assertEqual(('mario', 'c03'), (operator.fighter_name, operator.costume_slot))
        self.assertTrue(operator.override_vanilla_target)
        operator.override_vanilla_target = False
        exporter.vanilla_target_override_update(operator, context)
        self.assertEqual(('ryu', 'c02'), (operator.fighter_name, operator.costume_slot))
        # Flattened references have no reliable target; retain manual entries.
        ssp.vanilla_nusktb = r'C:\vanilla\model.nusktb'
        exporter.SUB_OP_model_exporter.invoke(operator, context, None)
        self.assertEqual(('mario', 'c03'), (operator.fighter_name, operator.costume_slot))

    def test_merge_preserves_other_settings_and_costumes_without_duplicates(self):
        original = {'unshare-blacklist': ['keep-this'], 'custom-setting': {'value': 7},
                    'new-dir-files': {'fighter/mario/c00': ['other.nutexb'],
                                      'fighter/ken/c01': ['existing.nutexb']}}
        (self.root / 'config.json').write_text(json.dumps(original), encoding='utf-8')
        for _ in range(2):
            config.write_config(self.root, 'Ken', 'c01', [self.texture, self.texture])
        actual = config.read_config(self.root)
        self.assertEqual(original['unshare-blacklist'], actual['unshare-blacklist'])
        self.assertEqual(original['custom-setting'], actual['custom-setting'])
        self.assertEqual(['other.nutexb'], actual['new-dir-files']['fighter/mario/c00'])
        self.assertEqual(['existing.nutexb', 'fighter/ken/model/body/c01/sal_col.nutexb'],
                         actual['new-dir-files']['fighter/ken/c01'])

    def test_multiple_textures_and_existing_serde_alias(self):
        (self.root / 'config.json').write_text('{"new_dir_files": {}}', encoding='utf-8')
        other = self.folder / 'sal_nor.nutexb'
        other.touch()
        config.write_config(self.root, 'ken', 'c01', [other, self.texture])
        actual = config.read_config(self.root)
        self.assertNotIn('new-dir-files', actual)
        self.assertEqual(2, len(actual['new_dir_files']['fighter/ken/c01']))

    def test_invalid_config_is_not_overwritten(self):
        for contents in ('broken json', '[]', '{"new-dir-files": []}',
                         '{"new-dir-files": {"fighter/ken/c01": "bad"}}',
                         '{"new-dir-files": {}, "new_dir_files": {}}'):
            path = self.root / 'config.json'
            path.write_text(contents, encoding='utf-8')
            with self.assertRaises(ValueError):
                config.write_config(self.root, 'ken', 'c01', [self.texture])
            self.assertEqual(contents, path.read_text(encoding='utf-8'))

    def test_failed_atomic_write_preserves_config_and_removes_temp(self):
        path = self.root / 'config.json'
        path.write_text('{}', encoding='utf-8')
        with patch.object(config.os, 'replace', side_effect=OSError('disk write failed')):
            with self.assertRaises(OSError):
                config.write_config(self.root, 'ken', 'c01', [self.texture])
        self.assertEqual('{}', path.read_text(encoding='utf-8'))
        self.assertEqual([], list(self.root.glob('.config-*.tmp')))

    def test_invalid_targets_and_missing_textures_are_rejected(self):
        for fighter, slot in (('../ken', 'c01'), ('', 'c01'), ('ken', 'c08'), ('ken', '../c01')):
            with self.assertRaises(ValueError):
                config.model_folder(self.root, fighter, slot)
        for path in (self.root / 'outside.nutexb', self.folder / 'missing.nutexb', self.folder / 'bad.png'):
            with self.assertRaises(ValueError):
                config.write_config(self.root, 'ken', 'c01', [path])
        self.assertFalse((self.root / 'config.json').exists())

    def make_baked_model(self):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.object.armature_add()
        arma = bpy.context.object
        bpy.context.scene.sub_scene_properties.model_export_arma = arma
        bpy.ops.mesh.primitive_plane_add()
        obj = bpy.context.object
        obj.parent = arma
        obj.data.uv_layers.active.name = 'map1'
        group = obj.vertex_groups.new(name='Bone')
        group.add(list(range(4)), 1.0, 'REPLACE')
        material = bpy.data.materials.new('source_color')
        material.use_nodes = True
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.6, .2, .1, 1)
        obj.data.materials.append(material)
        job = bake.ColorBakeJob(bpy.context, str(self.root / 'baked'), 32, 1,
                               single_atlas=True, atlas_name='sal_col')
        job.begin()
        while job.index < len(job.meshes):
            job.step()
        job.finish()
        self.addCleanup(lambda: bpy.data.objects.remove(arma, do_unlink=True) if arma.name in bpy.data.objects else None)
        return obj

    def test_operator_exports_real_model_and_matching_texture_config(self):
        self.make_baked_model()
        bpy.context.scene.sub_scene_properties.vanilla_nusktb = str(self.folder / 'model.nusktb')
        # Do not accidentally register unrelated files from an earlier export.
        (self.folder / 'stale.nutexb').touch()
        for _ in range(2):
            result = bpy.ops.sub.model_exporter(
                directory=str(self.root), create_switch_mod=True,
                include_nusktb=False, include_nuhlpb=False,
                linked_nusktb_settings='NO_LINK')
            self.assertEqual({'FINISHED'}, result)
        matl = ssbh.matl_data.read_matl(str(self.folder / 'model.numatb'))
        texture_names = {p.data for entry in matl.entries for p in entry.textures
                         if p.param_id == ssbh.matl_data.ParamId.Texture0}
        self.assertEqual({'sal_col'}, texture_names)
        actual = config.read_config(self.root)
        self.assertEqual(['fighter/ken/model/body/c01/sal_col.nutexb'],
                         actual['new-dir-files']['fighter/ken/c01'])
        self.assertGreater(self.texture.stat().st_size, 16)
        self.assertTrue((self.folder / 'model.numshb').is_file())
        self.assertFalse((self.root / 'model.numshb').exists())
        ssp = bpy.context.scene.sub_scene_properties
        self.assertTrue(ssp.model_export_switch_mod)
        self.assertEqual(('ken', 'c01'), (ssp.model_export_fighter, ssp.model_export_costume))

    def test_explicit_target_override_exports_to_the_selected_costume(self):
        self.make_baked_model()
        bpy.context.scene.sub_scene_properties.vanilla_nusktb = '/dump/fighter/ken/model/body/c00/model.nusktb'
        result = bpy.ops.sub.model_exporter(
            directory=str(self.root), create_switch_mod=True,
            override_vanilla_target=True, fighter_name='ken', costume_slot='c03',
            include_nusktb=False, include_nuhlpb=False, linked_nusktb_settings='NO_LINK')
        self.assertEqual({'FINISHED'}, result)
        actual = config.read_config(self.root)['new-dir-files']
        self.assertEqual({'fighter/ken/c03'}, set(actual))
        self.assertEqual(['fighter/ken/model/body/c03/sal_col.nutexb'], actual['fighter/ken/c03'])
        self.assertTrue(bpy.context.scene.sub_scene_properties.model_export_override_target)

    def test_flat_export_stays_flat_and_failed_conversion_is_not_registered(self):
        obj = self.make_baked_model()
        # A previous file with the same name must not count as a successful export.
        with patch.object(textures, 'run', side_effect=textures.CalledProcessError(1, 'converter', stderr=b'failure')):
            written = textures.export_nutexb_from_blender_materials(Reporter(), {obj.active_material}, self.folder)
        self.assertEqual(set(), written)
        result = bpy.ops.sub.model_exporter(
            directory=str(self.root), create_switch_mod=False,
            include_nusktb=False, include_nuhlpb=False,
            linked_nusktb_settings='NO_LINK')
        self.assertEqual({'FINISHED'}, result)
        self.assertTrue((self.root / 'model.numshb').is_file())
        self.assertFalse((self.root / 'config.json').exists())


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ARCropolisExportTests))
if not result.wasSuccessful():
    sys.exit(1)
