"""Batch opaque base-color baking without editing the source materials."""

from pathlib import Path
import re
import shutil
import tempfile
import traceback

import bpy
import numpy as np
from bpy.props import EnumProperty, IntProperty, StringProperty
from bpy.types import Operator


_active_job = None


def linear_to_srgb(value):
    return 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1.0 / 2.4) - 0.055


def model_meshes(context):
    """Prefer the export rig, then the active rig, then selected meshes."""
    rig = context.scene.sub_scene_properties.model_export_arma
    if rig is None and context.object:
        rig = context.object if context.object.type == 'ARMATURE' else context.object.find_armature()
    candidates = rig.children if rig else context.selected_objects
    return sorted((obj for obj in candidates
                   if obj.type == 'MESH' and obj.visible_get(view_layer=context.view_layer)
                   and not obj.hide_render), key=lambda obj: obj.name)


def color_input(material):
    """Only accept shaders whose base color can be identified unambiguously."""
    if not material.use_nodes:
        return None
    output = material.node_tree.get_output_node('CYCLES')
    if output is None or not output.inputs['Surface'].is_linked:
        raise ValueError(f'{material.name}: no connected material output')
    node = output.inputs['Surface'].links[0].from_node
    while node.type == 'REROUTE' and node.inputs[0].is_linked:
        node = node.inputs[0].links[0].from_node
    socket_name = {'BSDF_PRINCIPLED': 'Base Color', 'BSDF_DIFFUSE': 'Color',
                   'EMISSION': 'Color'}.get(node.type)
    if socket_name is None:
        raise ValueError(f'{material.name}: connect a Principled BSDF, Diffuse BSDF, or Emission '
                         'directly to Material Output before baking colors')
    return node.inputs[socket_name]


class ColorBakeJob:
    """A transaction stepped once per mesh by the UI or synchronously in background."""

    def __init__(self, context, directory, resolution, margin, single_atlas=False, atlas_name='model_col'):
        self.context = context
        self.scene = context.scene
        self.meshes = model_meshes(context)
        if not self.meshes:
            raise ValueError('Select the model armature or its visible meshes first')
        self.materials = set()
        for obj in self.meshes:
            if obj.library or obj.data.library:
                raise ValueError(f'{obj.name}: make linked meshes local before baking')
            if not obj.data.uv_layers.get('map1'):
                raise ValueError(f'{obj.name}: needs a map1 UV map; use the Attribute Renamer first')
            if not obj.material_slots or any(slot.material is None for slot in obj.material_slots):
                raise ValueError(f'{obj.name}: assign a material to every slot before baking')
            self.materials.update(slot.material for slot in obj.material_slots)
        for material in self.materials:
            if material.sub_matl_data.shader_label:
                raise ValueError(f'{material.name}: already an Ultimate material; bake the original '
                                 'Blender materials instead')
            color_input(material)

        self.resolution = resolution
        self.margin = margin
        self.single_atlas = single_atlas
        self.atlas_name = re.sub(r'[^a-z0-9_]+', '_', atlas_name.lower()).strip('_')[:60] or 'model_col'
        self.atlas_image = None
        self.atlas_regions = {}
        self.root = Path(bpy.path.abspath(directory))
        self.folder = None
        self.images = {}
        self.proxies = {}
        self.results = {}
        self.source_meshes = {obj: obj.data for obj in self.meshes}
        self.bake_meshes = {}
        self.target_uvs = {}
        self.solid = set()
        self.index = 0
        self.started = False
        self.committed = False
        self.selection = list(context.selected_objects)
        self.active = context.view_layer.objects.active
        self.mode = self.active.mode if self.active else 'OBJECT'
        self.select_mode = tuple(self.scene.tool_settings.mesh_select_mode)
        self.engine = self.scene.render.engine
        self.cycles = {name: getattr(self.scene.cycles, name)
                       for name in ('device', 'samples', 'use_denoising', 'bake_type')}
        self.bake_settings = {prop.identifier: getattr(self.scene.render.bake, prop.identifier)
                              for prop in self.scene.render.bake.bl_rna.properties
                              if not prop.is_readonly and prop.type in {'BOOLEAN', 'ENUM', 'INT', 'FLOAT', 'STRING'}}
        self.slots = [(obj, i, slot.link, slot.material)
                      for obj in self.meshes for i, slot in enumerate(obj.material_slots)]

    def begin(self):
        self.started = True
        if self.context.object and self.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        self.root.mkdir(parents=True, exist_ok=True)
        self.folder = Path(tempfile.mkdtemp(prefix='model_colors_', dir=self.root))
        self.scene.render.engine = 'CYCLES'
        self.scene.cycles.device = 'CPU'
        self.scene.cycles.samples = 1
        self.scene.cycles.use_denoising = False
        # Work on copies so packing never changes the source UVs or hidden instances.
        for obj in self.meshes:
            data = obj.data.copy()
            self.bake_meshes[obj] = data
            obj.data = data
            uv = data.uv_layers.new(name='__sub_color_bake')
            self.target_uvs[obj] = uv.name
            data.uv_layers.active = uv
            data.uv_layers['map1'].active_render = True
        for number, material in enumerate(sorted(self.materials, key=lambda mat: mat.name), 1):
            socket = color_input(material)
            # In atlas mode uniform materials also need their own UV region baked;
            # filling a whole image with the constant would erase other materials.
            solid = not self.single_atlas and (socket is None or not socket.is_linked)
            stem = re.sub(r'[^a-z0-9_]+', '_', material.name.lower()).strip('_')[:40] or 'material'
            name = self.atlas_name if self.single_atlas else f'{number:02}_{stem}_col'
            size = 8 if solid else self.resolution
            # Alpha records bake coverage, so unpainted texels can be distinguished
            # from intentionally black hair, clothes, or rubber.
            image = self.atlas_image if self.single_atlas else None
            if image is None:
                image = bpy.data.images.new(name, width=size, height=size, alpha=True)
                image.generated_color = (0.0, 0.0, 0.0, 0.0)
                image.colorspace_settings.name = 'sRGB'
                image.file_format = 'PNG'
                image.filepath_raw = str(self.folder / f'{image.name}.png')
                if self.single_atlas:
                    self.atlas_image = image
            self.images[material] = image
            if solid:
                self.solid.add(material)
                color = tuple(socket.default_value) if socket else tuple(material.diffuse_color)
                # Byte image buffers store encoded values; shader sockets are scene-linear.
                encoded = tuple(linear_to_srgb(value) for value in color[:3]) + (1.0,)
                image.pixels[:] = encoded * (size * size)

            proxy = material.copy()
            self.proxies[material] = proxy
            proxy.name = f'{material.name} (bake temporary)'
            proxy.use_fake_user = False
            proxy.use_nodes = True
            nodes = proxy.node_tree.nodes
            output = proxy.node_tree.get_output_node('CYCLES')
            source = color_input(proxy) if socket is not None else None
            emission = nodes.new('ShaderNodeEmission')
            emission.inputs['Strength'].default_value = 1.0
            if source and source.is_linked:
                proxy.node_tree.links.new(source.links[0].from_socket, emission.inputs['Color'])
            else:
                emission.inputs['Color'].default_value = source.default_value if source else material.diffuse_color
            proxy.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
            target = nodes.new('ShaderNodeTexImage')
            target.image = image
            for node in nodes:
                node.select = False
            target.select = True
            nodes.active = target

        # Keep each material's charts together in a separate atlas region. Unwrapping
        # all scanned materials together fragments the face into tiny islands and
        # spends most of the texture on gutters instead of visible color detail.
        if self.single_atlas:
            weights = {material: 0 for material in self.materials}
            for obj in self.meshes:
                slots = {index: material for owner, index, link, material in self.slots if owner == obj}
                for face in obj.data.polygons:
                    weights[slots[face.material_index]] += 1

            def divide(items, lower, upper):
                if len(items) == 1:
                    self.atlas_regions[items[0][0]] = (lower, upper)
                    return
                total = sum(weight for material, weight in items)
                split = min(range(1, len(items)),
                            key=lambda index: abs(sum(weight for material, weight in items[:index]) - total * .5))
                fraction = sum(weight for material, weight in items[:split]) / total
                axis = int((upper - lower)[1] > (upper - lower)[0])
                boundary = lower[axis] + (upper[axis] - lower[axis]) * fraction
                left_upper, right_lower = upper.copy(), lower.copy()
                left_upper[axis], right_lower[axis] = boundary, boundary
                divide(items[:split], lower, left_upper)
                divide(items[split:], right_lower, upper)

            items = sorted(((material, max(1, weight)) for material, weight in weights.items()),
                           key=lambda item: (-item[1], item[0].name))
            divide(items, np.zeros(2), np.ones(2))

        self.scene.tool_settings.mesh_select_mode = (False, False, True)
        groups = [{material} for material in sorted(self.materials - self.solid, key=lambda mat: mat.name)]
        for group in groups:
            for selected in self.context.selected_objects:
                selected.select_set(False)
            owners = []
            for obj in self.meshes:
                indices = {index for owner, index, link, mat in self.slots
                           if owner == obj and mat in group}
                if indices:
                    owners.append(obj)
                    for polygon in obj.data.polygons:
                        polygon.select = polygon.material_index in indices
                    obj.select_set(True)
            self.context.view_layer.objects.active = owners[0]
            bpy.ops.object.mode_set(mode='EDIT')
            try:
                bpy.ops.uv.smart_project(angle_limit=1.1519173, island_margin=0.01,
                                         correct_aspect=False, scale_to_bounds=True)
            finally:
                bpy.ops.object.mode_set(mode='OBJECT')

            if self.single_atlas:
                material = next(iter(group))
                lower, upper = self.atlas_regions[material]
                inset = np.minimum((self.margin + 1) / self.resolution, (upper - lower) * .125)
                for obj in owners:
                    values = np.empty(len(obj.data.loops) * 2, dtype=np.float32)
                    layer = obj.data.uv_layers[self.target_uvs[obj]]
                    layer.data.foreach_get('uv', values)
                    values = values.reshape(-1, 2)
                    indices = {index for owner, index, link, mat in self.slots
                               if owner == obj and mat == material}
                    loops = np.array([loop for face in obj.data.polygons if face.material_index in indices
                                      for loop in face.loop_indices], dtype=np.int32)
                    values[loops] = lower + inset + values[loops] * (upper - lower - 2 * inset)
                    layer.data.foreach_set('uv', values.ravel())

        # Object links avoid changing shared mesh data or materials on hidden backups.
        for obj, index, link, material in self.slots:
            obj.material_slots[index].link = 'OBJECT'
            obj.material_slots[index].material = self.proxies[material]

    def step(self):
        obj = self.meshes[self.index]
        for selected in self.context.selected_objects:
            selected.select_set(False)
        obj.select_set(True)
        self.context.view_layer.objects.active = obj
        obj.update_tag()
        self.context.view_layer.update()
        if any(material not in self.solid for owner, index, link, material in self.slots if owner == obj):
            # Keep previous sections of a shared material's image. Explicit UV selection
            # leaves the source shaders' active render UV untouched.
            result = bpy.ops.object.bake(type='EMIT', target='IMAGE_TEXTURES',
                                         use_clear=False, use_selected_to_active=False,
                                         use_cage=False, margin=0 if self.single_atlas else self.margin,
                                         margin_type='EXTEND',
                                         uv_layer=self.target_uvs[obj])
            if result != {'FINISHED'}:
                raise RuntimeError(f'Color bake cancelled on {obj.name}')
        self.index += 1

    def finish(self):
        from .create_blender_materials_from_matl import create_default_textures, setup_blender_material_node_tree
        from .load_from_shader_label import create_sub_matl_data_from_shader_label

        self.repair_small_charts()
        create_default_textures()
        for image in set(self.images.values()):
            image.save()
            image.pack()
        for original, image in self.images.items():
            material = bpy.data.materials.new(f'{original.name} (baked)')
            self.results[original] = material
            material['sub_bake_original_material'] = original.name
            create_sub_matl_data_from_shader_label(material, 'SFX_PBS_010000000800ba69_opaque')
            material.sub_matl_data.textures['Texture0'].image = image
            # This shader uses mesh-wide PRM rather than multiplying the baked color by
            # vertex colors. Preserve constant Principled roughness and metalness.
            metal, rough, spec = original.metallic, original.roughness, original.specular_intensity
            socket = color_input(original)
            if socket and socket.node.type == 'BSDF_PRINCIPLED':
                bsdf = socket.node
                metal = bsdf.inputs['Metallic'].default_value
                rough = bsdf.inputs['Roughness'].default_value
                spec = bsdf.inputs['Specular IOR Level'].default_value
            material.sub_matl_data.vectors['CustomVector47'].value = (metal, rough, 1.0, spec)
            material.sub_matl_data.vectors['CustomVector13'].value = (1.0, 1.0, 1.0, 1.0)
            setup_blender_material_node_tree(material)

        # Commit only after every bake, PNG save, and material conversion succeeded.
        for obj in self.meshes:
            data = obj.data
            target = data.uv_layers[self.target_uvs[obj]]
            data.uv_layers.remove(data.uv_layers['map1'])
            target.name = 'map1'
            data.uv_layers.active = target
            target.active_render = True
        for obj, index, link, original in self.slots:
            obj.material_slots[index].material = self.results[original]
        for material in self.materials:
            material.use_fake_user = True
        for data in self.source_meshes.values():
            data.use_fake_user = True
        self.committed = True
        self.close()

    def repair_small_charts(self):
        """Resample charts missed by the pixel-center bake rasterizer.

        A chart smaller than a texel may receive no bake samples, and consequently
        no margin either. Re-evaluate those faces in larger temporary UV cells,
        then fill only their uncovered texels. Original black colors stay intact.
        """
        if self.context.workspace:
            self.context.workspace.status_text_set('Baking colors: resampling small UV charts...')
        buffers = {}
        repairs = []
        for obj in self.meshes:
            uv = np.empty(len(obj.data.loops) * 2, dtype=np.float32)
            obj.data.uv_layers[self.target_uvs[obj]].data.foreach_get('uv', uv)
            uv = uv.reshape(-1, 2)
            slots = {index: material for owner, index, link, material in self.slots if owner == obj}
            missing = []
            for face in obj.data.polygons:
                material = slots[face.material_index]
                if material in self.solid or face.area <= 1e-12:
                    continue
                image = self.images[material]
                if image not in buffers:
                    pixels = np.empty(len(image.pixels), dtype=np.float32)
                    image.pixels.foreach_get(pixels)
                    buffers[image] = pixels.reshape(image.size[1], image.size[0], 4)
                pixels = buffers[image]
                points = uv[list(face.loop_indices)]
                center = points.mean(axis=0)
                # Check the center and inset corners, including thin boundary faces.
                samples = np.concatenate([center[None, :], points * .8 + center * .2])
                x = np.clip((samples[:, 0] * image.size[0]).astype(int), 0, image.size[0] - 1)
                y = np.clip((samples[:, 1] * image.size[1]).astype(int), 0, image.size[1] - 1)
                if np.any(pixels[y, x, 3] < .5):
                    missing.append((face, material, points.copy()))
            if not missing:
                continue

            # One generous cell per missed face guarantees a sample even when the
            # final UV chart is a fraction of one pixel wide. Source UVs stay fixed.
            cell = 16
            columns = int(np.ceil(np.sqrt(len(missing))))
            rows = int(np.ceil(len(missing) / columns))
            width, height = columns * cell, rows * cell
            sample_image = bpy.data.images.new('__sub_color_samples', width, height, alpha=True)
            sample_image.generated_color = (0, 0, 0, 0)
            sample_image.colorspace_settings.name = 'sRGB'
            sample_uv = obj.data.uv_layers.new(name='__sub_color_samples', do_init=False)
            targets = {self.proxies[material].node_tree.nodes.active: self.images[material]
                       for material in set(slots.values())}
            try:
                coordinates = np.full((len(obj.data.loops), 2), -10.0, dtype=np.float32)
                centers = []
                for index, (face, material, points) in enumerate(missing):
                    x, y = index % columns * cell, index // columns * cell
                    count = len(face.loop_indices)
                    if count == 3:
                        local = np.array([(3., 3.), (13., 3.), (3., 13.)])
                    else:
                        angle = np.arange(count) * (2 * np.pi / count)
                        local = np.column_stack([np.cos(angle), np.sin(angle)]) * 5 + 8
                    coordinates[list(face.loop_indices)] = (local + (x, y)) / (width, height)
                    center = local.mean(axis=0) + (x, y)
                    centers.append((int(center[0]), int(center[1])))
                sample_uv.data.foreach_set('uv', coordinates.ravel())
                for node in targets:
                    node.image = sample_image
                for selected in self.context.selected_objects:
                    selected.select_set(False)
                obj.select_set(True)
                self.context.view_layer.objects.active = obj
                self.context.view_layer.update()
                result = bpy.ops.object.bake(type='EMIT', target='IMAGE_TEXTURES', use_clear=True,
                                             use_selected_to_active=False, use_cage=False,
                                             margin=0, uv_layer=sample_uv.name)
                if result != {'FINISHED'}:
                    raise RuntimeError(f'Could not resample small UV charts on {obj.name}')
                colors = np.empty(len(sample_image.pixels), dtype=np.float32)
                sample_image.pixels.foreach_get(colors)
                colors = colors.reshape(height, width, 4)
                for (face, material, points), (x, y) in zip(missing, centers):
                    color = colors[y, x].copy()
                    if color[3] < .5:
                        # Zero-area scan fragments can have no evaluable surface.
                        # The mesh exporter removes these degenerate faces.
                        if face.area > 1e-7:
                            raise RuntimeError(f'{obj.name}: face {face.index} has no bakeable surface')
                        continue
                    repairs.append((self.images[material], points, color))
            finally:
                for node, image in targets.items():
                    node.image = image
                obj.data.uv_layers.remove(sample_uv)
                bpy.data.images.remove(sample_image)

        # Fill every missed chart before adding padding, so another chart's border
        # cannot occupy its center first. Never overwrite already covered texels.
        for padding in ((1,) if self.single_atlas else (1, max(2, self.margin))):
            for image, points, color in repairs:
                pixels = buffers[image]
                height, width = pixels.shape[:2]
                lower = np.floor(points.min(axis=0) * (width, height)).astype(int) - padding
                upper = np.ceil(points.max(axis=0) * (width, height)).astype(int) + padding + 1
                x0, y0 = np.maximum(lower, (0, 0))
                x1, y1 = np.minimum(upper, (width, height))
                region = pixels[y0:y1, x0:x1]
                region[region[:, :, 3] < .5] = color
        for image, pixels in buffers.items():
            if self.single_atlas:
                self.extend_atlas_padding(pixels)
            image.pixels.foreach_set(pixels.ravel())
            image.update()

    def extend_atlas_padding(self, pixels):
        """Extend the completed atlas without overwriting another mesh's colors."""
        height, width = pixels.shape[:2]
        for iteration in range(self.margin):
            previous = pixels.copy()
            for dy, dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
                target = pixels[max(0,-dy):min(height,height-dy), max(0,-dx):min(width,width-dx)]
                source = previous[max(0,dy):min(height,height+dy), max(0,dx):min(width,width+dx)]
                fill = (target[:,:,3] < .5) & (source[:,:,3] >= .5)
                target[fill] = source[fill]

    def close(self):
        """Restore the user's scene on success, error, and cancellation."""
        if not self.started:
            return
        if not self.committed:
            if self.context.object and self.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            for obj, data in self.source_meshes.items():
                obj.data = data
            for obj, index, link, material in self.slots:
                obj.material_slots[index].material = material
                obj.material_slots[index].link = link
        for material in self.proxies.values():
            bpy.data.materials.remove(material)
        self.proxies.clear()
        if not self.committed:
            for material in self.results.values():
                bpy.data.materials.remove(material)
            for image in set(self.images.values()):
                bpy.data.images.remove(image)
            for data in self.bake_meshes.values():
                bpy.data.meshes.remove(data)
            if self.folder:
                shutil.rmtree(self.folder)
        self.scene.render.engine = self.engine
        for name, value in self.cycles.items():
            setattr(self.scene.cycles, name, value)
        for name, value in self.bake_settings.items():
            setattr(self.scene.render.bake, name, value)
        self.scene.tool_settings.mesh_select_mode = self.select_mode
        for selected in self.context.selected_objects:
            selected.select_set(False)
        for selected in self.selection:
            selected.select_set(True)
        self.context.view_layer.objects.active = self.active
        if self.active and self.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=self.mode)
        self.started = False


class SUB_OP_bake_model_colors(Operator):
    """Bake the model's opaque base colors and connect them for Ultimate texture export"""
    bl_idname = 'sub.bake_model_colors'
    bl_label = 'Bake Model Colors'
    bl_options = {'REGISTER', 'UNDO'}

    directory: StringProperty(name='Output Folder', subtype='DIR_PATH')
    texture_layout: EnumProperty(name='Textures', items=[
        ('ATLAS', 'One Color Atlas', 'Bake all mesh sections into one shared color texture'),
        ('MATERIAL', 'Separate Textures', 'Create a separate texture for each material')], default='ATLAS')
    atlas_name: StringProperty(name='Texture Name', default='model_col')
    resolution: EnumProperty(name='Texture Size', items=[
        ('1024', '1024', 'Fast preview'), ('2048', '2048', 'Standard'),
        ('4096', '4096', 'High detail')], default='4096')
    margin: IntProperty(name='Margin', default=8, min=0, max=64, subtype='PIXEL')

    @classmethod
    def poll(cls, context):
        return _active_job is None and context.scene is not None

    def draw(self, context):
        layout = self.layout
        meshes = model_meshes(context)
        materials = {slot.material for obj in meshes for slot in obj.material_slots if slot.material}
        layout.label(text=f'{len(meshes)} visible meshes / {len(materials)} materials', icon='MESH_DATA')
        layout.prop(self, 'directory')
        layout.prop(self, 'texture_layout')
        if self.texture_layout == 'ATLAS':
            layout.prop(self, 'atlas_name')
        layout.prop(self, 'resolution')
        layout.prop(self, 'margin')
        layout.label(text='Bakes opaque base color, including color node edits.')
        layout.label(text='Packs export UVs and preserves original meshes/materials.')

    def invoke(self, context, event):
        self._job = None
        self._timer = None
        if not self.directory:
            self.directory = bpy.path.abspath('//baked_textures') if bpy.data.filepath else tempfile.gettempdir()
        return context.window_manager.invoke_props_dialog(self, width=470, confirm_text='Bake Model Colors')

    def execute(self, context):
        global _active_job
        self._job = None
        self._timer = None
        try:
            if not self.directory:
                self.directory = bpy.path.abspath('//baked_textures') if bpy.data.filepath else tempfile.gettempdir()
            self._job = ColorBakeJob(context, self.directory, int(self.resolution), self.margin,
                                     self.texture_layout == 'ATLAS', self.atlas_name)
            _active_job = self._job
            self._job.begin()
            context.window_manager.progress_begin(0, len(self._job.meshes))
            if not bpy.app.background and context.window is not None:
                self._timer = context.window_manager.event_timer_add(0.2, window=context.window)
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            while self._job.index < len(self._job.meshes):
                self._job.step()
            return self._finish(context)
        except Exception as error:
            return self._fail(context, error)

    def modal(self, context, event):
        try:
            if event.type == 'ESC':
                self.cancel(context)
                self.report({'INFO'}, 'Color bake cancelled; original materials restored')
                return {'CANCELLED'}
            # Blender exposes the event type, but no Event.timer attribute. The timer
            # handle is retained only so it can be removed on completion or cancel.
            if event.type != 'TIMER':
                return {'RUNNING_MODAL'}
            if self._job.index == len(self._job.meshes):
                return self._finish(context)
            index = self._job.index
            context.workspace.status_text_set(f'Baking colors {index + 1}/{len(self._job.meshes)}: '
                                              f'{self._job.meshes[index].name} | Esc to cancel between meshes')
            self._job.step()
            context.window_manager.progress_update(self._job.index)
            return {'RUNNING_MODAL'}
        except Exception as error:
            return self._fail(context, error)

    def _finish(self, context):
        self._job.finish()
        self._cleanup(context)
        self.report({'INFO'}, f'Baked {len(set(self._job.images.values()))} color textures to {self._job.folder}. '
                    'Export Model Files with NUMATB and NUTEXB enabled, then save your .blend.')
        return {'FINISHED'}

    def _fail(self, context, error):
        traceback.print_exc()
        self.cancel(context)
        self.report({'ERROR'}, f'Color bake failed: {error}')
        return {'CANCELLED'}

    def cancel(self, context):
        try:
            if getattr(self, '_job', None):
                self._job.close()
        finally:
            self._cleanup(context)

    def _cleanup(self, context):
        global _active_job
        _active_job = None
        if getattr(self, '_timer', None):
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        if context.workspace:
            context.workspace.status_text_set(None)
