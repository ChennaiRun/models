"""Avenue / garden landmark set for MIT Chromepet -- additive props.

References: user's own campus photos (Mar 2019, Drive folder 'mit',
shared 2026-10-20; see ../REFERENCE_VIDEOS.md). Observation only:
no photo pixels are shipped and no identifiable people are modelled.

Since 2026-10-21 each item is exported as its OWN world-positioned GLB
(the combined avenue_garden_landmarks.glb was retired), sited from the
model's road/campus geometry (roads_v2.glb + data/osm_raw.osm):

* MIT_letters (photo 11.jpg) -> props/mit_letters.glb -- large black 3D
  letters M I T on a stone plinth with concrete edging. Sited on the
  avenue lawn inside the Main Gate at ENU (-50.1, -245.7), rotated to
  the avenue direction at the gate (yaw 55.73 deg, heading 304.27).
* Golden_statue_garden (photos 13.jpg, 16.jpg) ->
  props/golden_statue_garden.glb -- golden standing figure (C. Rajam)
  on a bright-blue stepped pedestal, globe lamps, benches, railing and
  a paved path spur. Sited at ENU (224.0, 10.0), 7.6 m north-east of
  the OSM Rajam Statue node (582775241), clear of Rajam Hall and Rajam
  Hall Road, facing the road bend (yaw -34 deg, heading 34). This is a
  detailed companion to the crude statue arch in props/landmarks.glb,
  which is NOT edited or replaced.
* Pergola (photo 18.jpg) -> props/pergola.glb -- red-brick pergola.
  Sited on the Admin Block lawn at ENU (-18.0, -80.0), heading 0.
* Gazebo (photo 18.jpg) -> props/gazebo.glb -- round gazebo: raised
  circular platform, central pole, conical tiled roof, circular bench
  ring, lantern lamp posts. Sited at ENU (-36.0, -64.0), heading 0,
  in the same Admin-side garden as the pergola.

All sites are APPROXIMATE (geometry-derived, not surveyed) and are
registered in data/placement_map.json. Paved connectors in
props/connector_paths.glb link the letters and the statue garden to
the road network.

Run from Chromepet/:  python3 tools/avenue_garden_landmarks.py
Dependencies: trimesh, numpy, pillow
Output: props/mit_letters.glb, props/golden_statue_garden.glb,
        props/pergola.glb, props/gazebo.glb + data/garden_landmarks_meta.json
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

    def export(self, path, yaw_deg=0.0, site_enu=(0.0, 0.0)):
        """Export with the world site baked in: rotate by yaw (ENU, CCW
        from east, about the local origin) then translate to site_enu."""
        scene = trimesh.Scene()
        enu_to_gltf = np.array(
            [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float
        )
        yaw = trimesh.transformations.rotation_matrix(math.radians(yaw_deg), [0, 0, 1])
        for index, (name, mesh, color) in enumerate(self.parts):
            mesh = mesh.copy()
            mesh.visual = trimesh.visual.TextureVisuals(material=material(color, f"{name}_material"))
            mesh.apply_transform(yaw)
            # Translate in ENU before the axis transform: ENU (tx, ty)
            # becomes glTF (tx, 0, -ty) through enu_to_gltf.
            mesh.apply_translation([site_enu[0], site_enu[1], 0.0])
            mesh.apply_transform(enu_to_gltf)
            scene.add_geometry(mesh, geom_name=f"{name}__{index}", node_name=f"{name}__{index}")
        scene.export(path)


# ---------------------------------------------------------------- letters
def add_mit_letters(layer, cx, cy):
    name = "MIT_letters"
    # Low polished-stone slab plinth (photo: letters on the lawn).
    layer.add(box(cx, cy, 11.6, 2.4, 0.28, 0.0, 0.0), "stone_dark", name)
    layer.add(box(cx, cy, 12.4, 3.2, 0.10, 0.0, 0.0), "concrete", name)
    # Concrete edging frame around the plinth (keeps the lawn edge tidy).
    for dy in (-1.72, 1.72):
        layer.add(box(cx, cy + dy, 12.9, 0.22, 0.18, 0.0, 0.0), "concrete", name)
    for dx in (-6.5, 6.5):
        layer.add(box(cx + dx, cy, 0.22, 3.66, 0.18, 0.0, 0.0), "concrete", name)
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
    # Paved path spur leaving the garden pad on the front (-y) side;
    # props/connector_paths.glb continues it to Rajam Hall Road.
    layer.add(box(cx, cy - 5.2, 2.4, 3.8, 0.07, 0.0, 0.0), "concrete", name)


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


def glb_stats(path):
    loaded = trimesh.load(path)
    geometries = list(loaded.geometry.values())
    return {
        "geometries": len(geometries),
        "vertices": int(sum(len(g.vertices) for g in geometries)),
        "faces": int(sum(len(g.faces) for g in geometries)),
        "bounds_gltf": [[round(float(v), 2) for v in row] for row in loaded.bounds.tolist()],
    }


# World sites (ENU) + ENU yaw per group; heading_deg = bearing of the
# group's local +Y axis = (-yaw) mod 360. See data/placement_map.json.
SITES = {
    "mit_letters": {"file": "mit_letters.glb", "site_enu": [-50.1, -245.7], "yaw_deg": 55.73,
                    "build": add_mit_letters},
    "golden_statue_garden": {"file": "golden_statue_garden.glb", "site_enu": [224.0, 10.0], "yaw_deg": -34.0,
                             "build": add_golden_statue},
    "pergola": {"file": "pergola.glb", "site_enu": [-18.0, -80.0], "yaw_deg": 0.0,
                "build": add_pergola},
    "gazebo": {"file": "gazebo.glb", "site_enu": [-36.0, -64.0], "yaw_deg": 0.0,
               "build": add_gazebo},
}


def main():
    stats = {}
    for key, spec in SITES.items():
        layer = SceneLayer()
        spec["build"](layer, 0.0, 0.0)
        out_path = os.path.join(ROOT, "props", spec["file"])
        layer.export(out_path, yaw_deg=spec["yaw_deg"], site_enu=tuple(spec["site_enu"]))
        stats[key] = glb_stats(out_path)

    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres), origin 12.9487N 80.1394E; each GLB is WORLD-POSITIONED (site + yaw baked in)",
        "placement": "SITED per group (approximate, sources: osm + roads_geometry + photo_relative). The combined avenue_garden_landmarks.glb was split on 2026-10-21 so each group carries its own world transform; registry: data/placement_map.json.",
        "provenance": "User's own photos 11.jpg, 13.jpg, 16.jpg, 18.jpg (Mar 2019), Drive folder 'mit', observation only; no photo pixels shipped, no people modelled",
        "generator": "tools/avenue_garden_landmarks.py",
        "outputs": {
            "mit_letters": {
                "glb": "props/mit_letters.glb", "site_enu": SITES["mit_letters"]["site_enu"],
                "yaw_deg": SITES["mit_letters"]["yaw_deg"], "heading_deg": 304.27,
                "site_note": "Avenue lawn inside the Main Gate, east side, ~30 m inside the gate on the avenue axis; long axis aligned to the avenue direction at the gate (OSM node 432468247 geometry). Plinth gained a concrete edging frame.",
                "glb_stats": stats["mit_letters"],
            },
            "golden_statue_garden": {
                "glb": "props/golden_statue_garden.glb", "site_enu": SITES["golden_statue_garden"]["site_enu"],
                "yaw_deg": SITES["golden_statue_garden"]["yaw_deg"], "heading_deg": 34.0,
                "site_note": "7.6 m north-east of the OSM Rajam Statue node (582775241), offset to clear Rajam Hall (west edge x=214) and the Rajam Hall Road bend; front faces the road bend/statue node. A paved spur leaves the pad toward the road, continued by props/connector_paths.glb. Does NOT replace the statue arch in props/landmarks.glb.",
                "glb_stats": stats["golden_statue_garden"],
            },
            "pergola": {
                "glb": "props/pergola.glb", "site_enu": SITES["pergola"]["site_enu"],
                "yaw_deg": 0.0, "heading_deg": 0.0,
                "site_note": "Admin Block lawn garden, west of the Admin Block node box, east of the west service road (photo 18.jpg garden).",
                "glb_stats": stats["pergola"],
            },
            "gazebo": {
                "glb": "props/gazebo.glb", "site_enu": SITES["gazebo"]["site_enu"],
                "yaw_deg": 0.0, "heading_deg": 0.0,
                "site_note": "Same Admin-side garden as the pergola, ~27 m north-west of it (photo 18.jpg).",
                "glb_stats": stats["gazebo"],
            },
        },
        "integration": "All four GLBs are registered in ChromepetSync.Glbs (world-positioned). The retired combined file props/avenue_garden_landmarks.glb was removed from the repo and from the sync list.",
    }
    with open(os.path.join(ROOT, "data", "garden_landmarks_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
