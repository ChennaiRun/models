"""Avenue / garden landmark set for MIT Chromepet -- one additive props GLB.

References: user's own campus photos (Mar 2019, Drive folder 'mit',
shared 2026-10-20; see ../REFERENCE_VIDEOS.md). Observation only:
no photo pixels are shipped and no identifiable people are modelled.

Items (each is a named node group with its own local centre, listed in
data/garden_landmarks_meta.json so the integrator can site them
individually; the GLB itself is ORIGIN-CENTRED as a set):

* MIT_letters (photo 11.jpg) -- large black 3D letters M I T. The photo
  shows them standing on the avenue lawn; a low dark stone slab is used
  here as a mounting plinth.
* Golden_statue_garden (photo 13.jpg; glimpsed again at the end of the
  road in 16.jpg) -- golden standing figure on a bright-blue stepped
  pedestal, with white globe lamp posts, green benches and a low blue
  railing. This is a detailed additive version of the crude statue
  approximations in props/landmarks.glb, which is NOT edited.
* Pergola_and_gazebo (photo 18.jpg) -- red-brick pergola (brick piers,
  white/red concrete beams) and a round gazebo: raised circular
  platform, central pole, conical tiled roof, circular bench ring,
  black lantern lamp posts. (The same gazebo type appears in
  mit_details.py as 'Pink_bench' by Applied Sciences; this is a
  standalone detailed garden version.)

Placement: APPROXIMATE / unsited as a set. Suggested sitings are in
data/garden_landmarks_meta.json.

Run from Chromepet/:  python3 tools/avenue_garden_landmarks.py
Dependencies: trimesh, numpy, pillow
Output: props/avenue_garden_landmarks.glb + data/garden_landmarks_meta.json
"""

import json
import math
import os

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

COLORS = {
    "letter_black": (0.06, 0.06, 0.07),
    "stone_dark": (0.28, 0.28, 0.30),
    "gold": (0.85, 0.62, 0.16),
    "gold_dark": (0.70, 0.50, 0.12),
    "pedestal_blue": (0.08, 0.32, 0.82),
    "pedestal_blue_dark": (0.06, 0.24, 0.62),
    "white": (0.93, 0.93, 0.90),
    "lamp": (0.96, 0.93, 0.72),
    "bench_green": (0.16, 0.42, 0.22),
    "brick": (0.65, 0.25, 0.18),
    "brick_dark": (0.55, 0.21, 0.15),
    "concrete": (0.74, 0.72, 0.68),
    "tile_roof": (0.66, 0.36, 0.22),
    "black": (0.05, 0.05, 0.05),
    "grass": (0.33, 0.47, 0.22),
    "book_white": (0.90, 0.88, 0.82),
}


def box(cx, cy, length, width, height, yaw=0.0, z0=0.0):
    mesh = trimesh.creation.box(extents=[length, width, height])
    mesh.apply_translation([0, 0, z0 + height / 2])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([cx, cy, 0])
    return mesh


def cylinder(x, y, radius, height, z0=0.0, sections=16):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation([x, y, z0 + height / 2])
    return mesh


def sphere(x, y, z, radius, subdivisions=2):
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    mesh.apply_translation([x, y, z])
    return mesh


def cone(x, y, radius, height, z0=0.0, sections=20):
    mesh = trimesh.creation.cone(radius=radius, height=height, sections=sections)
    mesh.apply_translation([x, y, z0 + height / 2])
    return mesh


def annulus(x, y, r_min, r_max, height, z0=0.0, sections=32):
    mesh = trimesh.creation.annulus(r_min=r_min, r_max=r_max, height=height, sections=sections)
    mesh.apply_translation([x, y, z0 + height / 2])
    return mesh


def beam3(a, b, radius=0.05, sections=8):
    a, b = np.asarray(a, float), np.asarray(b, float)
    vec = b - a
    length = np.linalg.norm(vec)
    mesh = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], vec / length))
    mesh.apply_translation((a + b) / 2)
    return mesh


def material(color, name):
    return trimesh.visual.material.PBRMaterial(
        name=name,
        baseColorFactor=[*(int(c * 255) for c in color), 255],
        metallicFactor=0.0,
        roughnessFactor=0.82,
    )


class SceneLayer:
    def __init__(self):
        self.parts = []

    def add(self, mesh, color, name):
        self.parts.append((name, mesh, COLORS[color] if isinstance(color, str) else color))

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
        scene.export(path)


# ---------------------------------------------------------------- letters
def add_mit_letters(layer, cx, cy):
    name = "MIT_letters"
    # Low polished-stone slab plinth (photo: letters on the lawn).
    layer.add(box(cx, cy, 11.6, 2.4, 0.28, 0.0, 0.0), "stone_dark", name)
    layer.add(box(cx, cy, 12.4, 3.2, 0.10, 0.0, 0.0), "concrete", name)
    depth, z0 = 0.55, 0.28
    def post(x, w, h):
        layer.add(box(cx + x, cy, w, depth, h, 0.0, z0), "letter_black", name)
    def bar(x, y_z, w, h):
        layer.add(box(cx + x, cy, w, depth, h, 0.0, y_z), "letter_black", name)
    # M (centre -3.9): two posts + two diagonals meeting low in the middle.
    for s in (-1.25, 1.25):
        post(-3.9 + s, 0.55, 3.1)
    for s in (-1, 1):
        a = (cx - 3.9 + s * 1.15, cy, z0 + 3.0)
        b = (cx - 3.9, cy, z0 + 1.35)
        layer.add(beam3(a, b, 0.30, 6), "letter_black", name)
    # I (centre 0): post + top/bottom bars.
    post(0.0, 0.55, 3.1)
    bar(0.0, z0 + 2.82, 1.7, 0.28)
    bar(0.0, z0, 1.7, 0.28)
    # T (centre +3.9): centre post + top bar.
    post(3.9, 0.55, 3.1)
    bar(3.9, z0 + 2.82, 2.9, 0.28)


# ---------------------------------------------------------------- statue
def add_golden_statue(layer, cx, cy):
    name = "Golden_statue_garden"
    # Garden pad + bright-blue stepped pedestal (photo 13.jpg).
    layer.add(cylinder(cx, cy, 3.4, 0.14, 0.0, 28), "concrete", name)
    layer.add(box(cx, cy, 3.6, 3.6, 0.35, 0.0, 0.14), "pedestal_blue_dark", name)
    layer.add(box(cx, cy, 2.7, 2.7, 0.35, 0.0, 0.49), "pedestal_blue", name)
    layer.add(box(cx, cy, 1.8, 1.8, 0.55, 0.0, 0.84), "pedestal_blue", name)
    top = 1.39
    # Stylised golden standing figure (scholar in dhoti + shawl, book in hand):
    # robe as a two-tier cylinder stack, then torso, head, arms and book.
    layer.add(cylinder(cx, cy, 0.42, 0.55, top, 14), "gold", name)
    robe2 = trimesh.creation.cylinder(radius=0.30, height=0.55, sections=14)
    robe2.apply_translation([cx, cy, top + 0.55 + 0.275])
    layer.add(robe2, "gold", name)
    layer.add(cylinder(cx, cy, 0.30, 0.62, top + 1.10, 14), "gold_dark", name)  # torso
    layer.add(sphere(cx, cy, top + 1.98, 0.17, 2), "gold", name)  # head
    # Arms: left arm down, right arm holding a book at the waist.
    layer.add(beam3((cx - 0.34, cy, top + 1.62), (cx - 0.48, cy, top + 0.95), 0.075, 8), "gold", name)
    layer.add(beam3((cx + 0.34, cy, top + 1.62), (cx + 0.55, cy - 0.10, top + 1.08), 0.075, 8), "gold", name)
    layer.add(box(cx + 0.60, cy - 0.16, 0.42, 0.10, 0.55, 0.3, top + 0.88), "book_white", name)
    # Staff in the right hand + gold emblem disc on the pedestal front (photos 36/39.jpg).
    layer.add(beam3((cx + 0.58, cy - 0.12, top + 1.78), (cx + 0.68, cy - 0.18, top + 0.02), 0.032, 8), "gold_dark", name)
    emblem = trimesh.creation.cylinder(radius=0.30, height=0.07, sections=18)
    emblem.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    emblem.apply_translation([cx, cy - 0.94, 1.12])
    layer.add(emblem, "gold", name)
    # Shawl diagonal across the torso.
    layer.add(beam3((cx - 0.28, cy - 0.30, top + 1.66), (cx + 0.28, cy - 0.30, top + 1.14), 0.09, 6), "gold_dark", name)
    # White globe lamp posts + green benches + low blue railing.
    for dx, dy in ((-3.1, 1.8), (3.1, 1.8), (-3.1, -1.8), (3.1, -1.8)):
        layer.add(cylinder(cx + dx, cy + dy, 0.06, 2.5, 0.0, 8), "white", name)
        layer.add(sphere(cx + dx, cy + dy, 2.72, 0.21, 2), "lamp", name)
    for dx in (-2.2, 2.2):
        layer.add(box(cx + dx, cy - 2.9, 1.9, 0.45, 0.10, 0.0, 0.48), "bench_green", name)
        layer.add(box(cx + dx, cy - 2.9, 1.9, 0.12, 0.45, 0.0, 0.0), "bench_green", name)
        layer.add(box(cx + dx, cy - 3.12, 1.9, 0.10, 0.55, 0.0, 0.55), "bench_green", name)
    for s in (-1, 1):
        layer.add(box(cx, cy + s * 3.35, 6.4, 0.08, 0.09, 0.0, 0.85), "pedestal_blue", name)
        for dx in (-3.0, -1.0, 1.0, 3.0):
            layer.add(cylinder(cx + dx, cy + s * 3.35, 0.035, 0.9, 0.0, 6), "pedestal_blue_dark", name)


# ---------------------------------------------------------------- pergola + gazebo
def add_pergola(layer, cx, cy):
    name = "Pergola"
    layer.add(box(cx, cy, 8.6, 4.6, 0.14, 0.0, 0.0), "concrete", name)
    for dx in (-3.6, 0.0, 3.6):
        for dy in (-1.7, 1.7):
            layer.add(box(cx + dx, cy + dy, 0.5, 0.5, 2.6, 0.0, 0.14), "brick", name)
    for dy in (-1.7, 1.7):
        layer.add(box(cx, cy + dy, 8.8, 0.42, 0.35, 0.0, 2.74), "white", name)
    for dx in (-3.6, -1.8, 0.0, 1.8, 3.6):
        layer.add(box(cx + dx, cy, 0.34, 4.4, 0.28, 0.0, 3.09), "brick_dark", name)
    layer.add(box(cx, cy, 8.8, 4.4, 0.16, 0.0, 3.37), "brick", name)


def add_gazebo(layer, cx, cy):
    name = "Gazebo"
    layer.add(cylinder(cx, cy, 3.3, 0.28, 0.0, 28), "concrete", name)
    layer.add(cylinder(cx, cy, 0.20, 2.9, 0.28, 10), "brick", name)  # central pole
    layer.add(annulus(cx, cy, 1.15, 1.95, 0.45, 0.28, 28), "concrete", name)  # circular bench
    layer.add(cylinder(cx, cy, 1.05, 0.12, 0.95, 20), "concrete", name)  # centre table top
    layer.add(cone(cx, cy, 3.6, 1.35, 3.18, 24), "tile_roof", name)  # conical tiled roof
    layer.add(cylinder(cx, cy, 0.09, 0.5, 4.53, 8), "brick_dark", name)  # finial
    for i in range(2):
        theta = math.radians(40 + i * 150)
        x, y = cx + 4.6 * math.cos(theta), cy + 4.6 * math.sin(theta)
        layer.add(cylinder(x, y, 0.06, 2.7, 0.0, 8), "black", name)
        lamp_head = cone(x, y, 0.30, 0.35, 2.95, 6)
        layer.add(lamp_head, "black", name)
        layer.add(sphere(x, y, 2.82, 0.13, 1), "lamp", name)


def main():
    layer = SceneLayer()
    centres = {
        "MIT_letters": [0.0, 0.0],
        "Golden_statue_garden": [17.0, 7.0],
        "Pergola": [-13.0, 11.0],
        "Gazebo": [-23.5, 3.0],
    }
    add_mit_letters(layer, *centres["MIT_letters"])
    add_golden_statue(layer, *centres["Golden_statue_garden"])
    add_pergola(layer, *centres["Pergola"])
    add_gazebo(layer, *centres["Gazebo"])
    # Shared lawn pad under the set (local arrangement only).
    layer.add(box(-3.0, 5.0, 52.0, 24.0, 0.04, 0.0, -0.05), "grass", "Garden_lawn")

    out_path = os.path.join(ROOT, "props", "avenue_garden_landmarks.glb")
    layer.export(out_path)

    loaded = trimesh.load(out_path)
    geometries = list(loaded.geometry.values())
    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres); LOCAL origin at the MIT letters; item centres below are local ENU (x=east, y=north)",
        "placement": "APPROXIMATE / unsited as a set; site each named group individually (suggested: letters on the avenue lawn inside the Main Gate, statue in its garden at the end of the internal road in photo 16.jpg, pergola/gazebo in the garden by the Admin/Library lawns in photo 18.jpg)",
        "provenance": "User's own photos 11.jpg, 13.jpg, 16.jpg, 18.jpg (Mar 2019), Drive folder 'mit', observation only; no photo pixels shipped, no people modelled",
        "generator": "tools/avenue_garden_landmarks.py",
        "output": "props/avenue_garden_landmarks.glb",
        "item_centres_local_enu": centres,
        "contents": {"mit_letters": 1, "golden_statue_garden": 1, "pergola": 1, "gazebo": 1},
        "glb_stats": {
            "geometries": len(geometries),
            "vertices": int(sum(len(g.vertices) for g in geometries)),
            "faces": int(sum(len(g.faces) for g in geometries)),
            "bounds_gltf": [[round(float(v), 2) for v in row] for row in loaded.bounds.tolist()],
        },
        "integration": "Outstanding: site each group, then add 'props/avenue_garden_landmarks.glb' to ChromepetSync.Glbs (or split per group). Detailed statue does not replace props/landmarks.glb.",
    }
    with open(os.path.join(ROOT, "data", "garden_landmarks_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
