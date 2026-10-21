"""Detailed frontage for the Department of Production Technology, MIT Chromepet.

Reference: user's own campus photo 14.jpg (Mar 2019, Drive folder 'mit',
shared 2026-10-20; see ../REFERENCE_VIDEOS.md). Observation only: no
photo pixels are shipped; the department sign is an original PIL
rendering of the name, following the chrompet_identity.py precedent.

What the photo shows: a projecting porch whose fascia carries a big
dark-blue sign "DEPARTMENT OF PRODUCTION TECHNOLOGY" in white with a
light-blue trim; above it a square-grid concrete jali band; flanking
walls of oval-hole lattice screen; cream walls with a mustard-yellow
lower band and a zigzag skirting; open maroon double doors; a
brown-framed window; red tiled porch floor on cream square columns.

Existing-model note: in tools/mit_details.py this department is a
no-footprint procedural node styled 'auto' (white block, light-green
bands, thin yellow band lines). The photo contradicts that palette for
the entrance face -- the real frontage is cream + mustard-yellow with
the blue sign and lattice screens -- but mit_details.py cannot be
re-run on this machine (its OSM input is a Git LFS pointer), so the
correction is delivered as this additive frontage instead of editing
the area-wide generator's output. When mit_details.py is next run
elsewhere, the 'auto' style for Production Technology should use
cream/yellow/blue-sign colours (documented in data/production_frontage_meta.json).

Placement: ORIGIN-CENTRED, front normal = local +Y (north in the local
ENU frame; exported glTF x=east, y=up, z=-north). Width 26 m matches
the 28 m procedural node box in mit_details.py. Integration is
ADDITIVE, not a replacement: ChrompetSceneBuilder carries a placement
entry for this file (added 2026-10-21) that positions the frontage
just in front of the procedural box, rotated to its avenue facing
(mit_details.facing). The placement, derived from the OSM node
432468201 (Department of Production Technology, ENU (184.2, 66.2))
and mit_details.facing() = 146.29 deg ENU: builder anchor (facade
centre, back-wall plane) ENU (170.42, 75.39) -- the box surface along
the facing ray plus 0.35 m -- heading 303.71 deg, Unity rotation Y
-56.29 deg. Do NOT add a 'replaces' entry for it -- the procedural
building stays visible behind/above the frontage. Registry:
data/placement_map.json (id production_technology_frontage).

Run from Chromepet/:  python3 tools/production_technology_frontage.py
Dependencies: trimesh, numpy, pillow
Output: buildings/detailed/production_technology_frontage.glb
        + data/production_frontage_meta.json
"""

import json
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

COLORS = {
    "cream": (0.92, 0.88, 0.76),
    "cream_dark": (0.84, 0.79, 0.66),
    "mustard": (0.93, 0.70, 0.10),
    "sign_blue": (0.07, 0.22, 0.55),
    "sign_trim": (0.25, 0.62, 0.90),
    "maroon": (0.45, 0.10, 0.13),
    "doorway_dark": (0.05, 0.05, 0.05),
    "lattice": (0.90, 0.87, 0.78),
    "lattice_hole": (0.16, 0.15, 0.14),
    "jali_grey": (0.78, 0.78, 0.76),
    "jali_recess": (0.30, 0.31, 0.33),
    "window_brown": (0.42, 0.24, 0.14),
    "glass": (0.55, 0.68, 0.66),
    "porch_tile": (0.68, 0.36, 0.30),
    "skirting": (0.35, 0.33, 0.30),
    "white": (0.93, 0.93, 0.90),
}


def box(cx, cy, length, width, height, yaw=0.0, z0=0.0):
    mesh = trimesh.creation.box(extents=[length, width, height])
    mesh.apply_translation([0, 0, z0 + height / 2])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([cx, cy, 0])
    return mesh


def material(color, name):
    return trimesh.visual.material.PBRMaterial(
        name=name,
        baseColorFactor=[*(int(c * 255) for c in color), 255],
        metallicFactor=0.0,
        roughnessFactor=0.85,
    )


class SceneLayer:
    def __init__(self):
        self.parts = []
        self.textured = []

    def add(self, mesh, color, name):
        self.parts.append((name, mesh, COLORS[color] if isinstance(color, str) else color))

    def add_textured(self, mesh, name):
        self.textured.append((name, mesh))

    def export(self, path):
        scene = trimesh.Scene()
        enu_to_gltf = np.array(
            [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float
        )
        for index, (name, mesh, color) in enumerate(self.parts):
            mesh = mesh.copy()
            mesh.visual = trimesh.visual.TextureVisuals(material=material(color, f"{name}_material"))
            mesh.apply_transform(enu_to_gltf)
            scene.add_geometry(mesh, geom_name=f"{name}__{index}", node_name=f"{name}__{index}")
        for index, (name, mesh) in enumerate(self.textured):
            mesh = mesh.copy()
            mesh.apply_transform(enu_to_gltf)
            scene.add_geometry(mesh, geom_name=f"{name}__{index}", node_name=f"{name}__{index}")
        scene.export(path)


def font(size):
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def sign_texture():
    """Dark-blue department sign, white capitals, light-blue trim (original rendering)."""
    image = Image.new("RGB", (2048, 160), (18, 56, 140))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 2047, 14), fill=(64, 158, 230))
    draw.rectangle((0, 146, 2047, 159), fill=(64, 158, 230))
    text = "DEPARTMENT OF PRODUCTION TECHNOLOGY"
    size = 104
    while size > 20:
        fnt = font(size)
        bounds = draw.textbbox((0, 0), text, font=fnt)
        if bounds[2] - bounds[0] <= 1980:
            break
        size -= 6
    draw.text(((2048 - (bounds[2] - bounds[0])) / 2, 30), text, font=fnt, fill=(245, 245, 245))
    return image


def text_plane(image, width, height):
    vertices = np.array(
        [[-width / 2, 0, 0], [width / 2, 0, 0], [width / 2, 0, height], [-width / 2, 0, height]],
        dtype=float,
    )
    faces = np.array([[0, 2, 1], [0, 3, 2], [0, 1, 2], [0, 2, 3]])
    # u runs opposite to +x: a viewer in front of the plane (the +y side) sees +x
    # to their left, so u=0 (start of text) must sit at the +x edge or the sign
    # reads mirrored. Verified by render (previously read reversed).
    uv = np.array([[1, 0], [0, 0], [0, 1], [1, 1]], dtype=float)
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=uv,
        material=trimesh.visual.material.PBRMaterial(
            name="Production_Technology_sign",
            baseColorTexture=image,
            metallicFactor=0.0,
            roughnessFactor=0.8,
        ),
    )
    return mesh


def place(mesh, x, y, z, yaw):
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([x, y, z])
    return mesh


def oval_hole_panel(layer, cx, cy, width, height, yaw, name, z0=0.0, depth=0.30):
    """Cream lattice panel with dark oval holes in a regular grid (photo 14.jpg)."""
    layer.add(box(cx, cy, width, depth, height, yaw, z0), "lattice", name)
    ax = np.array([math.cos(yaw), math.sin(yaw)])
    nx = np.array([-math.sin(yaw), math.cos(yaw)])
    cols = max(2, int(width / 0.62))
    rows = max(2, int(height / 0.62))
    for i in range(cols):
        for j in range(rows):
            ox = (i - (cols - 1) / 2) * 0.62
            oz = z0 + 0.45 + j * 0.62
            px, py = cx + ax[0] * ox + nx[0] * (depth / 2 + 0.02), cy + ax[1] * ox + nx[1] * (depth / 2 + 0.02)
            hole = trimesh.creation.cylinder(radius=0.20, height=0.05, sections=12)
            hole.apply_scale([1.45, 1.0, 1.0])  # widen in the panel plane: oval, not round
            hole.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
            hole.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
            hole.apply_translation([px, py, oz])
            layer.add(hole, "lattice_hole", name)


def main():
    layer = SceneLayer()
    name = "Production_Technology_frontage"
    W = 26.0  # facade width (procedural node box is 28 m wide)

    # Back wall (cream) with mustard-yellow lower band + zigzag skirting.
    layer.add(box(0, 0, W, 0.45, 7.0, 0.0, 0.0), "cream", name)
    layer.add(box(0, 0.26, W, 0.06, 1.15, 0.0, 0.0), "mustard", name)
    for i in range(40):
        yaw = 0.55 if i % 2 == 0 else -0.55
        layer.add(box(-W / 2 + 0.35 + i * (W - 0.7) / 39, 0.30, 0.55, 0.05, 0.30, yaw, 0.02), "skirting", name)

    # Square-grid jali band above the sign (dark recess + light grid bars).
    layer.add(box(0, 0.28, W, 0.10, 2.30, 0.0, 4.70), "jali_recess", name)
    for i in range(43):
        x = -W / 2 + 0.3 + i * (W - 0.6) / 42
        layer.add(box(x, 0.36, 0.10, 0.08, 2.30, 0.0, 4.70), "jali_grey", name)
    for j in range(4):
        layer.add(box(0, 0.36, W, 0.08, 0.10, 0.0, 4.75 + j * 0.72), "jali_grey", name)
    layer.add(box(0, 0.30, W, 0.14, 0.18, 0.0, 7.0), "cream_dark", name)  # cornice

    # Oval-hole lattice screens flanking the porch and wrapping the ends.
    oval_hole_panel(layer, -10.6, 0.42, 4.6, 3.35, 0.0, f"{name}_lattice_L", z0=0.55)
    oval_hole_panel(layer, 10.6, 0.42, 4.6, 3.35, 0.0, f"{name}_lattice_R", z0=0.55)
    oval_hole_panel(layer, -13.05, 2.2, 4.2, 3.35, math.pi / 2, f"{name}_lattice_side_L", z0=0.55)
    oval_hole_panel(layer, 13.05, 2.2, 4.2, 3.35, -math.pi / 2, f"{name}_lattice_side_R", z0=0.55)

    # Porch: projecting slab on cream square columns, red tiled floor.
    layer.add(box(0, 2.6, 20.0, 5.6, 0.14, 0.0, 0.0), "porch_tile", f"{name}_porch")
    for dx in (-9.2, -3.1, 3.1, 9.2):
        layer.add(box(dx, 4.9, 0.48, 0.48, 3.55, 0.0, 0.14), "cream", f"{name}_porch")
    layer.add(box(0, 2.7, 21.0, 5.9, 0.35, 0.0, 3.55), "cream_dark", f"{name}_porch")

    # Sign band on the porch fascia with original text texture.
    layer.add(box(0, 5.55, 21.0, 0.22, 1.10, 0.0, 2.95), "sign_blue", f"{name}_sign")
    layer.add(box(0, 5.55, 21.0, 0.24, 0.14, 0.0, 4.05), "sign_trim", f"{name}_sign")
    texture = sign_texture()
    front = text_plane(texture, 20.6, 1.02)
    layer.add_textured(place(front, 0, 5.68, 2.99, 0.0), f"{name}_sign_text")

    # Entrance steps up to the porch floor (photo 14.jpg shows a stepped
    # threshold in front of the porch).
    layer.add(box(0, 5.62, 5.0, 0.44, 0.09, 0.0, 0.0), "cream_dark", f"{name}_steps")
    layer.add(box(0, 5.97, 5.0, 0.40, 0.045, 0.0, 0.0), "cream_dark", f"{name}_steps")

    # Open maroon double doors (centre) with dark doorway behind.
    layer.add(box(0, 0.30, 3.0, 0.10, 2.75, 0.0, 0.14), "doorway_dark", name)
    layer.add(box(-1.62, 0.55, 1.35, 0.10, 2.65, 0.5, 0.14), "maroon", name)  # left leaf, ajar
    layer.add(box(1.05, 0.32, 1.35, 0.10, 2.65, 0.0, 0.14), "maroon", name)  # right leaf, flat

    # Brown-framed glass window right of the doors (photo) + plain window left.
    for cx, glass_w in ((5.6, 1.9), (-5.6, 1.9)):
        layer.add(box(cx, 0.30, glass_w + 0.25, 0.10, 1.75, 0.0, 1.35), "window_brown", name)
        layer.add(box(cx, 0.36, glass_w, 0.06, 1.55, 0.0, 1.45), "glass", name)
        layer.add(box(cx, 0.40, 0.07, 0.05, 1.55, 0.0, 1.45), "window_brown", name)

    # Collision proxy: one box covering wall + porch footprint.
    layer.add(box(0, 2.4, W + 0.4, 6.2, 7.0, 0.0, 0.0), "cream_dark", "COL_frontage")

    out_path = os.path.join(ROOT, "buildings", "detailed", "production_technology_frontage.glb")
    layer.export(out_path)

    loaded = trimesh.load(out_path)
    geometries = list(loaded.geometry.values())
    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres); LOCAL origin at facade centre, front normal = local +Y (north before export transform)",
        "placement": "SITED via ChrompetSceneBuilder placement entry (approximate, source: osm): additive overlay for the 'Department of Production Technology' procedural node in tools/mit_details.py (OSM node 432468201, ENU (184.2, 66.2), style 'auto', 28x18 m node box measured in buildings/campus_buildings.glb as x 170.2-198.2, north 57.2-75.2). Builder anchor ENU (170.42, 75.39) = box surface along mit_details.facing() (146.29 deg ENU) + 0.35 m; heading 303.71 deg; Unity rotation Y -56.29 deg. Procedural building is NOT hidden (ground-floor overlay only).",
        "placement_enu": [170.42, 75.39],
        "heading_deg": 303.71,
        "unity_rotation_y_deg": -56.29,
        "provenance": "User's own photo 14.jpg (Mar 2019), Drive folder 'mit', observation only; no photo pixels shipped, no people modelled",
        "generator": "tools/production_technology_frontage.py",
        "output": "buildings/detailed/production_technology_frontage.glb",
        "style_correction_for_mit_details": "Production Technology entrance face is cream + mustard-yellow lower band with dark-blue sign and oval/square lattice screens (photo 14.jpg), not the generic 'auto' white + light-green bands; mit_details.py not re-run here because data/osm_raw.osm is a Git LFS pointer on this machine",
        "wider_context": "Photo 45.jpg shows this frontage is the ground floor of a taller pale-green lattice block shared with the Division of Applied Sciences & Humanities (same oval-lattice language as Mechatronics, photos 15/44.jpg); this additive model covers the ground-floor frontage only. Photos 40-43.jpg show a separate newer cream/teal Production Technology block (4 storeys, teal sunshades) -- a future detailed model, not covered here.",
        "contents": {
            "facade_width_m": W,
            "sign": "DEPARTMENT OF PRODUCTION TECHNOLOGY (original PIL rendering)",
            "lattice_panels": 4,
            "porch_columns": 4,
            "entrance_steps": 2,
        },
        "glb_stats": {
            "geometries": len(geometries),
            "vertices": int(sum(len(g.vertices) for g in geometries)),
            "faces": int(sum(len(g.faces) for g in geometries)),
            "bounds_gltf": [[round(float(v), 2) for v in row] for row in loaded.bounds.tolist()],
        },
        "integration": "ChrompetSceneBuilder.Placements carries the entry for 'production_technology_frontage' (position (170.42, 0, 75.39) in Unity ENU, rotation Y -56.29 deg); COL_frontage becomes its collider via the builder's COL_* handling. ChromepetSync already copies all buildings/detailed/*.glb. Registry: data/placement_map.json.",
    }
    with open(os.path.join(ROOT, "data", "production_frontage_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
