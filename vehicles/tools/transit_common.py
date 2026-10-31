"""Shared helpers for the Chennai transit vehicle generators.

Vehicle-local glTF frame used by every generator in this folder:
  metres, +Y up, +Z = vehicle front (glTF forward), +X = vehicle left
  (kerb/platform side when driving on the left), -X = vehicle right.
  y = 0 is road surface (bus) or top of rail (trains).

Dependencies: trimesh, numpy, pillow (with libraqm for correct Tamil shaping).
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont, features


SMOOTH_ANGLE = math.radians(40)

LATIN_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]
LED_FONTS = [
    "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
]
TAMIL_FONTS = [
    "/System/Library/Fonts/Supplemental/Tamil Sangam MN.ttc",
    "/System/Library/Fonts/Supplemental/Tamil MN.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf",
    "/usr/share/fonts/noto/NotoSansTamil-Bold.ttf",
]


# --------------------------------------------------------------------------- #
# Primitive geometry (all in vehicle-local glTF frame)
# --------------------------------------------------------------------------- #

def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box from min/max extents."""
    mesh = trimesh.creation.box(extents=[abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)])
    mesh.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return mesh


def cyl_x(cx, cy, cz, radius, width, sections=16):
    """Cylinder whose axis runs along X (wheels, axles)."""
    mesh = trimesh.creation.cylinder(radius=radius, height=width, sections=sections)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    mesh.apply_translation([cx, cy, cz])
    return mesh


def cyl_z(cx, cy, cz, radius, length, sections=16):
    """Cylinder whose axis runs along Z (lamps facing forward, buffers)."""
    mesh = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    mesh.apply_translation([cx, cy, cz])
    return mesh


def cyl_y(cx, cy, cz, radius, height, sections=12):
    """Vertical cylinder; cy is the bottom."""
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))
    mesh.apply_translation([cx, cy + height / 2, cz])
    return mesh


def beam(a, b, radius=0.03, sections=8):
    """Round bar between two 3D points."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    vec = b - a
    length = float(np.linalg.norm(vec))
    mesh = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], vec / length))
    mesh.apply_translation((a + b) / 2)
    return mesh


def side_profile(half_width, bottom_y, bands, roof_y, roof_radius, roof_segments=8):
    """Closed CCW (seen from +Z) car-body cross-section with vertical walls.

    ``bands`` is a list of (y_top, material_key) going upward from
    ``bottom_y``; both walls use the same bands so livery is symmetric. The
    last band top must not exceed the shoulder (roof_y - roof_radius); the wall
    is extended to the shoulder with the last band material. The roof is flat
    with rounded shoulders.

    Returns (points[N,2], edge_keys[N]); edge i joins point i -> i+1 and the
    last edge closes the loop. Generic keys: __bottom__, __shoulder__, __roof__.
    """
    w, r = half_width, roof_radius
    shoulder = roof_y - r
    spans = list(bands)
    if spans[-1][0] > shoulder + 1e-6:
        raise ValueError("band top above roof shoulder")
    if spans[-1][0] < shoulder - 1e-6:
        spans.append((shoulder, spans[-1][1]))
    pts = [(-w, bottom_y), (w, bottom_y)]
    keys = ["__bottom__"]
    for y, key in spans:                       # +X wall upward
        pts.append((w, y))
        keys.append(key)
    for i in range(1, roof_segments + 1):      # +X shoulder
        a = math.pi / 2 * i / roof_segments
        pts.append((w - r + r * math.cos(a), shoulder + r * math.sin(a)))
        keys.append("__shoulder__")
    pts.append((-w + r, roof_y))               # flat roof
    keys.append("__roof__")
    for i in range(1, roof_segments + 1):      # -X shoulder
        a = math.pi / 2 + math.pi / 2 * i / roof_segments
        pts.append((-w + r + r * math.cos(a), shoulder + r * math.sin(a)))
        keys.append("__shoulder__")
    for idx in range(len(spans) - 1, -1, -1):  # -X wall downward
        if idx > 0:
            pts.append((-w, spans[idx - 1][0]))
        keys.append(spans[idx][1])             # idx == 0 closes the loop
    pts = np.array(pts, dtype=float)
    assert len(pts) == len(keys), (len(pts), len(keys))
    return pts, keys


def loft(sections, edge_mats, resolve):
    """Loft closed profiles along Z.

    sections: list of (z, points[N,2]) in increasing z, same N for every section.
    edge_mats: list of N material keys (edge i = point i -> i+1), or a callable
        (span_index, edge_index) -> material key.
    resolve: callable mapping generic keys such as ``__roof__`` to real names.
    Returns {material: Trimesh}. Caps are not included (see ``cap_mesh``).
    """
    faces_by_mat: dict[str, list] = {}
    for k in range(len(sections) - 1):
        z0, p0 = sections[k]
        z1, p1 = sections[k + 1]
        n = len(p0)
        for i in range(n):
            j = (i + 1) % n
            key = edge_mats(k, i) if callable(edge_mats) else edge_mats[i]
            mat = resolve(key)
            a = (p0[i][0], p0[i][1], z0)
            b = (p0[j][0], p0[j][1], z0)
            c = (p1[j][0], p1[j][1], z1)
            d = (p1[i][0], p1[i][1], z1)
            faces_by_mat.setdefault(mat, []).append((a, b, c, d))
    out = {}
    for mat, quads in faces_by_mat.items():
        verts, faces = [], []
        for a, b, c, d in quads:
            base = len(verts)
            verts.extend([a, b, c, d])
            faces.extend([[base, base + 1, base + 2], [base, base + 2, base + 3]])
        mesh = trimesh.Trimesh(np.array(verts), np.array(faces), process=True)
        out[mat] = mesh
    return out


def cap_mesh(points, z, facing):
    """Fan-triangulated planar cap of a (star-shaped) profile at ``z``.

    facing=+1 for a +Z-facing (front) cap, -1 for a -Z-facing (rear) cap.
    Returns (mesh, uv) where uv is a planar projection over the cap bounds
    such that an image reads correctly when viewed from outside.
    """
    pts = np.asarray(points, float)
    centre = pts.mean(axis=0)
    verts = [(centre[0], centre[1], z)] + [(x, y, z) for x, y in pts]
    faces = []
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        if facing > 0:
            faces.append([0, 1 + i, 1 + j])
        else:
            faces.append([0, 1 + j, 1 + i])
    verts = np.array(verts)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    u = (verts[:, 0] - lo[0]) / (hi[0] - lo[0])
    if facing < 0:
        u = 1.0 - u  # viewer behind the vehicle sees +X on their right
    v = (verts[:, 1] - lo[1]) / (hi[1] - lo[1])
    mesh = trimesh.Trimesh(verts, np.array(faces), process=False)
    return mesh, np.column_stack([u, v])


def decal(image, centre, width, height, normal, name, offset=0.006):
    """Single-sided textured quad, readable from outside along ``normal``.

    normal is one of '+x', '-x', '+z', '-z'.
    """
    n = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}[normal]
    n = np.array(n, float)
    up = np.array([0.0, 1.0, 0.0])
    right = np.cross(-n, up)
    c = np.asarray(centre, float) + n * offset
    bl = c - right * width / 2 - up * height / 2
    br = c + right * width / 2 - up * height / 2
    tr = c + right * width / 2 + up * height / 2
    tl = c - right * width / 2 + up * height / 2
    mesh = trimesh.Trimesh(np.array([bl, br, tr, tl]), np.array([[0, 1, 2], [0, 2, 3]]), process=False)
    uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
    return textured(mesh, uv, image, name)


def textured(mesh, uv, image, name, emissive=False):
    mat = trimesh.visual.material.PBRMaterial(
        name=name,
        baseColorTexture=image,
        metallicFactor=0.0,
        roughnessFactor=0.6,
    )
    if emissive:
        mat.emissiveTexture = image
        mat.emissiveFactor = [1.0, 1.0, 1.0]
    mesh.visual = trimesh.visual.TextureVisuals(uv=uv, material=mat)
    return mesh


# --------------------------------------------------------------------------- #
# Text rendering
# --------------------------------------------------------------------------- #

def load_font(candidates, size):
    for candidate in candidates:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default()


def tamil_supported():
    """Tamil needs complex shaping (vowel-sign reordering) via libraqm."""
    return features.check("raqm") and any(os.path.exists(f) for f in TAMIL_FONTS)


def draw_text(draw, xy, text, font, fill, anchor="mm"):
    kwargs = {"font": font, "fill": fill, "anchor": anchor}
    if features.check("raqm"):
        kwargs["direction"] = "ltr"
    draw.text(xy, text, **kwargs)


def fit_font(draw, text, candidates, max_w, max_h):
    size = max_h
    while size > 8:
        font = load_font(candidates, size)
        kwargs = {"font": font}
        if features.check("raqm"):
            kwargs["direction"] = "ltr"
        x0, y0, x1, y1 = draw.textbbox((0, 0), text, **kwargs)
        if x1 - x0 <= max_w and y1 - y0 <= max_h:
            return font
        size -= 2
    return load_font(candidates, 8)


def led_board(text, size=(512, 96), color=(255, 160, 20), bg=(12, 12, 12), dot=True):
    """Amber/red dot-matrix style destination board."""
    w, h = size
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    font = fit_font(draw, text, LED_FONTS, int(w * 0.94), int(h * 0.78))
    draw_text(draw, (w / 2, h / 2), text, font, color)
    if dot:
        # Dot-matrix grid: darken every 4th row/column so it reads as LEDs.
        px = img.load()
        for y in range(h):
            for x in range(w):
                if x % 4 == 3 or y % 4 == 3:
                    r, g, b = px[x, y]
                    px[x, y] = (r // 3, g // 3, b // 3)
    return img


# --------------------------------------------------------------------------- #
# Scene assembly
# --------------------------------------------------------------------------- #

class Palette:
    def __init__(self, entries):
        """entries: name -> (rgb tuple 0..1, metallic, roughness)."""
        self.entries = entries
        self._cache = {}

    def material(self, name):
        if name not in self._cache:
            rgb, metallic, rough = self.entries[name]
            self._cache[name] = trimesh.visual.material.PBRMaterial(
                name=name,
                baseColorFactor=[int(round(c * 255)) for c in rgb] + [255],
                metallicFactor=metallic,
                roughnessFactor=rough,
            )
        return self._cache[name]

    def rgb(self, name):
        return self.entries[name][0]


class VehicleBuilder:
    """Collect geometry per (node, material) and export a tidy node hierarchy.

    Root node -> one child per part (car / body / collider) with its own
    translation -> one mesh node per material.
    """

    def __init__(self, root_name, palette):
        self.root = root_name
        self.palette = palette
        self.nodes: dict[str, np.ndarray] = {}
        self.groups: dict[tuple[str, str], list] = {}
        self.textured: list[tuple[str, str, trimesh.Trimesh]] = []

    def node(self, name, translation=(0, 0, 0)):
        self.nodes[name] = trimesh.transformations.translation_matrix(translation)
        return name

    def add(self, node, mat, mesh):
        self.groups.setdefault((node, mat), []).append(mesh)

    def add_many(self, node, mapping):
        for mat, mesh in mapping.items():
            self.add(node, mat, mesh)

    def add_textured(self, node, name, mesh):
        self.textured.append((node, name, mesh))

    def build_scene(self):
        scene = trimesh.Scene(base_frame=self.root)
        for name, matrix in self.nodes.items():
            scene.graph.update(frame_from=self.root, frame_to=name, matrix=matrix)
        for (node, mat), meshes in self.groups.items():
            parts = []
            for m in meshes:
                m = m.copy()
                m.merge_vertices()
                parts.append(trimesh.graph.smooth_shade(m, angle=SMOOTH_ANGLE, facet_minarea=None))
            mesh = trimesh.util.concatenate(parts)
            mesh.visual = trimesh.visual.TextureVisuals(material=self.palette.material(mat))
            geom = f"{node}__{mat}"
            scene.add_geometry(mesh, node_name=geom, geom_name=geom, parent_node_name=node)
        for index, (node, name, mesh) in enumerate(self.textured):
            geom = f"{node}__{name}"
            scene.add_geometry(mesh, node_name=geom, geom_name=geom, parent_node_name=node)
        return scene

    def export(self, path):
        scene = self.build_scene()
        data = trimesh.exchange.gltf.export_glb(scene, include_normals=True)
        with open(path, "wb") as handle:
            handle.write(data)
        return scene


def collider_box(builder, name, x0, x1, y0, y1, z0, z1, translation=(0, 0, 0)):
    node = builder.node(f"COL_{name}", translation)
    builder.add(node, "collider", box(x0, x1, y0, y1, z0, z1))


def scene_stats(path):
    loaded = trimesh.load(path, force="scene")
    verts = sum(len(g.vertices) for g in loaded.geometry.values())
    tris = sum(len(g.faces) for g in loaded.geometry.values())
    lo, hi = loaded.bounds
    return {
        "geometries": len(loaded.geometry),
        "vertices": int(verts),
        "triangles": int(tris),
        "bounds_min": [round(float(v), 3) for v in lo],
        "bounds_max": [round(float(v), 3) for v in hi],
    }


def write_meta(path, meta):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False, sort_keys=False)
        handle.write("\n")


def warn(msg):
    print(f"WARNING: {msg}", file=sys.stderr)
