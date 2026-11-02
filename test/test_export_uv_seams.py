"""Run with Blender --background --factory-startup --python this_file.py."""

import importlib
from pathlib import Path
import sys
import unittest

import bpy
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO.parent))
addon = importlib.import_module(REPO.name)
importlib.import_module(f'{REPO.name}.source.updater.version_check').check_for_newer_version = lambda: None
addon.register()
exporter = importlib.import_module(f'{REPO.name}.source.model.export_model')


class ExportUVSeamTests(unittest.TestCase):
    def make_mesh(self, active):
        # Two coplanar triangles touch at one vertex, without a shared edge. Edge
        # seam splitting cannot separate their distinct texture coordinates.
        data = bpy.data.meshes.new('vertex_only_seam')
        data.from_pydata([(0,0,0),(1,0,0),(0,1,0),(-1,0,0),(0,-1,0)], [], [(0,1,2),(0,3,4)])
        obj = bpy.data.objects.new('vertex_only_seam', data)
        bpy.context.collection.objects.link(obj)
        data.uv_layers.new(name='bake1')
        uv = data.uv_layers.new(name='map1')
        for value, coordinate in zip(uv.data, [(.1,.1),(.2,.1),(.1,.2),(.8,.8),(.9,.8),(.8,.9)]):
            value.uv = coordinate
        data.uv_layers.active = data.uv_layers[active]
        normals = data.color_attributes.new(name='_smush_blender_custom_normals', type='FLOAT_COLOR', domain='CORNER')
        for value in normals.data:
            value.color = (0,0,1,0)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        return obj

    def check_uvs(self, active):
        obj = self.make_mesh(active)
        expected = {layer.name: np.array([value.uv[:] for value in layer.data]) for layer in obj.data.uv_layers}
        exporter.split_duplicate_loop_attributes(obj)
        vertex_indices = np.array([loop.vertex_index for loop in obj.data.loops])
        for layer in obj.data.uv_layers:
            per_loop = np.array([value.uv[:] for value in layer.data])
            # Mimic the exact per-loop -> per-vertex conversion written to NUMSHB.
            vertices = exporter.per_loop_to_per_vertex(per_loop.ravel(), vertex_indices, (len(obj.data.vertices),2))
            np.testing.assert_allclose(vertices[vertex_indices], expected[layer.name], atol=1e-7)

    def test_vertex_only_seam_in_active_uv(self):
        self.check_uvs(1)

    def test_vertex_only_seam_in_inactive_uv(self):
        self.check_uvs(0)


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExportUVSeamTests))
if not result.wasSuccessful():
    sys.exit(1)
