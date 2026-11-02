"""Run with Blender --background --factory-startup --python this_file.py."""

import importlib
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
updater = importlib.import_module(f'{REPO.name}.source.updater.version_check')
updater.check_for_newer_version = lambda: None
addon.register()
bake = importlib.import_module(f'{REPO.name}.source.model.material.bake_model_colors')
exporter = importlib.import_module(f'{REPO.name}.source.model.export_model')
texture_export = importlib.import_module(f'{REPO.name}.source.model.material.texture.export_nutexb')
matl_export = importlib.import_module(f'{REPO.name}.source.model.material.create_matl_from_blender_materials')


class Reporter:
    def report(self, level, text):
        if 'ERROR' in level or 'WARNING' in level:
            raise AssertionError(text)


def mesh(name, material, u0=0.0, u1=1.0, color=(1, 0, 0, 1)):
    data = bpy.data.meshes.new(name)
    data.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(material)
    uv = data.uv_layers.new(name='map1')
    for loop, coordinate in zip(uv.data, [(u0, .1), (u1, .1), (u1, .9), (u0, .9)]):
        loop.uv = coordinate
    extra = data.uv_layers.new(name='bake1')
    for loop in extra.data:
        loop.uv = (.75, .75)
    data.uv_layers.active_index = 1
    data.uv_layers[0].active_render = True
    attribute = data.color_attributes.new(name='paint', type='FLOAT_COLOR', domain='CORNER')
    for value in attribute.data:
        value.color = color
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def material(name='source', solid=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Metallic'].default_value = .3
    bsdf.inputs['Roughness'].default_value = .82
    if solid is None:
        attr = mat.node_tree.nodes.new('ShaderNodeVertexColor')
        attr.layer_name = 'paint'
        mat.node_tree.links.new(attr.outputs['Color'], bsdf.inputs['Base Color'])
    else:
        bsdf.inputs['Base Color'].default_value = solid
    return mat


def pixel(image, x, y):
    width, height = image.size
    offset = (int(y * height) * width + int(x * width)) * 4
    return tuple(image.pixels[offset:offset + 4])


class BakeTests(unittest.TestCase):
    def setUp(self):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.context.scene.sub_scene_properties.model_export_arma = None
        self.directory = tempfile.TemporaryDirectory(prefix='ultimate_color_bake_test_')
        self.addCleanup(self.directory.cleanup)
        self.scene = bpy.context.scene
        self.scene.render.engine = 'BLENDER_EEVEE'
        self.scene.cycles.samples = 37
        self.scene.render.bake.use_clear = True
        defaults = importlib.import_module(f'{REPO.name}.source.model.material.create_blender_materials_from_matl')
        defaults.create_default_textures()

    def job(self):
        return bake.ColorBakeJob(bpy.context, self.directory.name, 32, 0)

    def test_split_shared_material_and_texture_export(self):
        original = material()
        graph = [(link.from_node.name, link.to_node.name) for link in original.node_tree.links]
        left = mesh('left', original, .05, .45, (1, 0, 0, 1))
        right = mesh('right', original, 2.55, 2.95, (0, 1, 0, 1))
        original_data = left.data
        original_uv = [tuple(value.uv) for value in left.data.uv_layers['map1'].data]
        # A hidden backup shares the same mesh datablock as a target.
        backup = bpy.data.objects.new('backup', left.data)
        bpy.context.collection.objects.link(backup)
        backup.hide_set(True)
        bpy.context.view_layer.objects.active = left
        selected = set(bpy.context.selected_objects)
        job = self.job()
        job.begin()
        while job.index < len(job.meshes):
            job.step()
        job.finish()
        self.assertEqual(1, len(job.images))
        image = job.images[original]
        def center(obj):
            uvs = [value.uv for value in obj.data.uv_layers['map1'].data]
            return tuple(sum(value[axis] for value in uvs) / len(uvs) for axis in (0, 1))
        self.assertGreater(pixel(image, *center(left))[0], .95)
        self.assertLess(pixel(image, *center(left))[1], .05)
        self.assertGreater(pixel(image, *center(right))[1], .95)
        self.assertLess(pixel(image, *center(right))[0], .05)
        self.assertIsNot(left.data, original_data)
        self.assertEqual(original_uv, [tuple(value.uv) for value in original_data.uv_layers['map1'].data])
        self.assertIs(backup.data, original_data)
        self.assertIs(backup.active_material, original)
        self.assertEqual(graph, [(link.from_node.name, link.to_node.name) for link in original.node_tree.links])
        self.assertIs(left.active_material, right.active_material)
        result = left.active_material
        self.assertIs(result.sub_matl_data.textures['Texture0'].image, image)
        self.assertAlmostEqual(.82, result.sub_matl_data.vectors['CustomVector47'].value[1], places=4)
        self.assertEqual('BLENDER_EEVEE', self.scene.render.engine)
        self.assertEqual(37, self.scene.cycles.samples)
        self.assertTrue(self.scene.render.bake.use_clear)
        self.assertIs(bpy.context.view_layer.objects.active, left)
        self.assertEqual(selected, set(bpy.context.selected_objects))
        self.assertEqual(1, left.data.uv_layers.active_index)
        self.assertTrue(left.data.uv_layers['map1'].active_render)
        self.assertIsNotNone(image.packed_file)
        materials = exporter.get_mesh_materials(Reporter(), [left, right])
        self.assertEqual({result}, materials)
        exported = matl_export.create_matl_from_blender_materials(Reporter(), materials)
        path = job.folder / 'model.numatb'
        exported.save(str(path))
        read_back = exporter.ssbh_data_py.matl_data.read_matl(str(path))
        texture0 = next(tex for tex in read_back.entries[0].textures if tex.param_id.name == 'Texture0')
        self.assertEqual(image.name, texture0.data)
        texture_export.export_nutexb_from_blender_materials(Reporter(), materials, job.folder)
        self.assertGreater((job.folder / f'{image.name}.nutexb').stat().st_size, 0)

    def test_secondary_uv_color_and_solid_dark_color(self):
        source = material('secondary UV')
        image = bpy.data.images.new('source image', 2, 2, float_buffer=True)
        image.pixels[:] = [1, 0, 0, 1] * 3 + [0, 0, 1, 1]
        node = source.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        node.interpolation = 'Closest'
        uv = source.node_tree.nodes.new('ShaderNodeUVMap')
        uv.uv_map = 'bake1'
        source.node_tree.links.new(uv.outputs['UV'], node.inputs['Vector'])
        source.node_tree.links.new(node.outputs['Color'], source.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        obj = mesh('secondary_uv_mesh', source, .05, .95)
        solid = material('dark rubber', (.0075, .008, .009, 1))
        solid_obj = mesh('solid', solid)
        # Degenerate UVs should still work for a uniform material.
        for loop in solid_obj.data.uv_layers['map1'].data:
            loop.uv = (0, 0)
        job = self.job()
        job.begin()
        while job.index < len(job.meshes):
            job.step()
        job.finish()
        self.assertGreater(pixel(job.images[source], .5, .5)[2], .95)
        self.assertLess(pixel(job.images[source], .5, .5)[0], .05)
        reloaded = bpy.data.images.load(job.images[solid].filepath_raw, check_existing=False)
        # Byte PNG pixels are sRGB; verify round-trip conversion to scene-linear.
        value = reloaded.pixels[0]
        linear = value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
        self.assertAlmostEqual(.0075, linear, delta=.001)
        self.assertEqual(1, obj.data.uv_layers.active_index)

    def test_cancel_and_conversion_failure_restore_originals(self):
        original = material()
        obj = mesh('cancelled', original)
        counts = (len(bpy.data.materials), len(bpy.data.images))
        job = self.job()
        job.begin()
        job.step()
        job.close()
        self.assertIs(obj.active_material, original)
        self.assertEqual('DATA', obj.material_slots[0].link)
        self.assertEqual(counts, (len(bpy.data.materials), len(bpy.data.images)))
        self.assertEqual([], list(Path(self.directory.name).iterdir()))
        self.assertEqual('BLENDER_EEVEE', self.scene.render.engine)
        self.assertTrue(self.scene.render.bake.use_clear)

        loader = importlib.import_module(f'{REPO.name}.source.model.material.load_from_shader_label')
        job = self.job()
        job.begin()
        with patch.object(loader, 'create_sub_matl_data_from_shader_label', side_effect=RuntimeError('test failure')):
            with self.assertRaisesRegex(RuntimeError, 'test failure'):
                job.finish()
        job.close()
        self.assertIs(obj.active_material, original)
        self.assertEqual(counts, (len(bpy.data.materials), len(bpy.data.images)))
        self.assertEqual([], list(Path(self.directory.name).iterdir()))

    def test_missing_uv_fails_before_changes_and_operator_execution(self):
        original = material(solid=(.1, .2, .3, 1))
        obj = mesh('no_uv', original)
        obj.data.uv_layers.remove(obj.data.uv_layers['map1'])
        with self.assertRaisesRegex(ValueError, 'map1'):
            self.job()
        self.assertIs(obj.active_material, original)
        self.assertEqual([], list(Path(self.directory.name).iterdir()))
        obj.data.uv_layers.new(name='map1')
        self.assertEqual({'FINISHED'}, bpy.ops.sub.bake_model_colors(directory=self.directory.name, resolution='1024'))
        self.assertIsNone(bake._active_job)
        self.assertIsNot(obj.active_material, original)

    def test_modal_timer_without_timer_attribute(self):
        original = material()
        obj = mesh('modal_mesh', original)
        job = self.job()
        job.begin()
        self.addCleanup(job.close)
        ui = SimpleNamespace(
            workspace=SimpleNamespace(status_text_set=lambda text: None),
            window_manager=SimpleNamespace(progress_update=lambda value: None))

        def finish(context):
            job.finish()
            return {'FINISHED'}

        def fail(context, error):
            job.close()
            raise error

        operator = SimpleNamespace(_job=job, _timer=object(), _finish=finish, _fail=fail)
        modal = bake.SUB_OP_bake_model_colors.modal
        self.assertEqual({'RUNNING_MODAL'}, modal(operator, ui, SimpleNamespace(type='MOUSEMOVE')))
        self.assertEqual(0, job.index)
        # Real Blender timer events have no .timer attribute. Exercise the whole
        # step/finish sequence that the synchronous background tests cannot cover.
        event = SimpleNamespace(type='TIMER')
        self.assertEqual({'RUNNING_MODAL'}, modal(operator, ui, event))
        self.assertEqual(1, job.index)
        self.assertEqual({'FINISHED'}, modal(operator, ui, event))
        self.assertTrue(job.committed)
        self.assertFalse(job.started)
        self.assertIsNot(obj.active_material, original)
        self.assertEqual('BLENDER_EEVEE', self.scene.render.engine)

    def test_subpixel_chart_gets_color_without_repainting_black(self):
        source = material()
        obj = mesh('small_chart', source, color=(.8, .3, .1, 1))
        job = self.job()
        job.begin()
        self.addCleanup(job.close)
        # Put an entire visible face between pixel centers. The first bake has no
        # samples to extend, so the chart is empty even with a nonzero bake margin.
        target = obj.data.uv_layers[job.target_uvs[obj]]
        for value, uv in zip(target.data, [(.2,.2),(.2001,.2),(.2001,.2001),(.2,.2001)]):
            value.uv = uv
        job.step()
        image = job.images[source]
        self.assertLess(pixel(image, .2, .2)[3], .5)
        # An intentional black texel is covered and must never be treated as a hole.
        pixels = list(image.pixels[:])
        index = (6 * image.size[0] + 7) * 4
        pixels[index:index+4] = [0, 0, 0, 1]
        image.pixels[:] = pixels
        job.finish()
        color = pixel(image, .2, .2)
        self.assertGreater(color[0], .8)
        self.assertGreater(color[1], .4)
        self.assertGreater(color[3], .99)
        self.assertEqual((0, 0, 0, 1), tuple(image.pixels[index:index+4]))

    def test_single_atlas_keeps_all_material_colors_and_exports_one_texture(self):
        red = material('red source')
        green = material('green source')
        black = material('black source', (0, 0, 0, 1))
        objects = [mesh('red mesh', red, color=(1,0,0,1)),
                   mesh('green mesh', green, color=(0,1,0,1)),
                   mesh('black mesh', black)]
        # The input UVs overlap completely, but each material must receive a
        # different atlas region without affecting the preserved source UVs.
        job = bake.ColorBakeJob(bpy.context, self.directory.name, 64, 2,
                               single_atlas=True, atlas_name='one_atlas_col')
        job.begin()
        self.addCleanup(job.close)
        while job.index < len(job.meshes):
            job.step()
        job.finish()
        self.assertEqual(1, len(set(job.images.values())))
        image = next(iter(job.images.values()))
        colors = []
        for obj in objects:
            values = [value.uv for value in obj.data.uv_layers['map1'].data]
            center = tuple(sum(uv[axis] for uv in values) / len(values) for axis in (0,1))
            colors.append(pixel(image, *center))
            self.assertIs(obj.active_material.sub_matl_data.textures['Texture0'].image, image)
        np = __import__('numpy')
        np.testing.assert_allclose(colors, [(1,0,0,1),(0,1,0,1),(0,0,0,1)], atol=.02)
        self.assertEqual(1, len(list(job.folder.glob('*.png'))))
        materials = exporter.get_mesh_materials(Reporter(), objects)
        texture_export.export_nutexb_from_blender_materials(Reporter(), materials, job.folder)
        self.assertEqual(1, len(list(job.folder.glob('*.nutexb'))))

    def test_single_atlas_cancel_removes_shared_image_once(self):
        sources = [material('first atlas source'), material('second atlas source')]
        objects = [mesh('first atlas mesh', sources[0]), mesh('second atlas mesh', sources[1])]
        before = (len(bpy.data.images), len(bpy.data.meshes), len(bpy.data.materials))
        job = bake.ColorBakeJob(bpy.context, self.directory.name, 32, 1, single_atlas=True)
        job.begin()
        self.assertEqual(1, len(set(job.images.values())))
        job.close()
        self.assertEqual(before, (len(bpy.data.images), len(bpy.data.meshes), len(bpy.data.materials)))
        self.assertEqual(sources, [obj.active_material for obj in objects])


suite = unittest.defaultTestLoader.loadTestsFromTestCase(BakeTests)
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():
    sys.exit(1)
