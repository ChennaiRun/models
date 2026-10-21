"""Detailed Indian Navy aircraft display for the MIT Chromepet aircraft grove.

Reference: user's own campus photo 15.jpg (Mar 2019, Drive folder 'mit',
shared 2026-10-20; see ../REFERENCE_VIDEOS.md). In the photo, taken from
the path past the Mechatronics block, a white fuselage with light-blue
upper surfaces and a dark "NAVY" titles sits on the display ground
behind the trees. Observation only: no photo pixels are shipped; the
NAVY titles are an original PIL rendering.

The aircraft is modelled as a generic naval patrol type (straight high
wing, twin turboprops, blue tail) at display attitude on supports. It is
a detailed additive companion to the crude Sea_Hawk / Gnat shapes in
props/landmarks.glb (tools/mit_details.py), which are NOT edited.

Placement: WORLD-POSITIONED in the v2 frame (origin 12.9487 N,
80.1394 E; glTF x=east, y=up, z=-north; metres). Centre ENU
(154.0, -26.0) is south-east of the aircraft grove centre recorded in
data/v2_meta.json (142.6, -10.2), clear of the existing Sea_Hawk and
Gnat positions there; heading and exact spot are APPROXIMATE (from the
photo viewpoint, not surveyed). Because it is world-positioned it is
registered in ChromepetSync.Glbs like props/chrompet_identity.glb.

Run from Chromepet/:  python3 tools/navy_aircraft.py
Dependencies: trimesh, numpy, pillow
Output: props/navy_aircraft_display.glb + data/navy_aircraft_meta.json
"""

import json
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CENTRE_ENU = (154.0, -26.0)
YAW = 0.55  # ENU radians, nose direction; APPROXIMATE

COLORS = {
    "fuselage_white": (0.90, 0.91, 0.90),
    "navy_blue": (0.16, 0.38, 0.72),
    "navy_dark": (0.07, 0.16, 0.35),
    "glass": (0.08, 0.12, 0.16),
    "steel": (0.50, 0.52, 0.54),
    "dark": (0.10, 0.10, 0.11),
    "concrete": (0.70, 0.70, 0.68),
    "stand_yellow": (0.90, 0.68, 0.10),
}


def material(color, name):
    return trimesh.visual.material.PBRMaterial(
        name=name,
        baseColorFactor=[*(int(c * 255) for c in color), 255],
        metallicFactor=0.0,
        roughnessFactor=0.7,
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


def navy_texture():
    image = Image.new("RGBA", (512, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    fnt = font(96)
    text = "NAVY"
    bounds = draw.textbbox((0, 0), text, font=fnt)
    draw.text(((512 - (bounds[2] - bounds[0])) / 2, 14), text, font=fnt, fill=(18, 42, 88, 255))
    return image


def text_plane(image, width, height):
    vertices = np.array(
        [[-width / 2, 0, 0], [width / 2, 0, 0], [width / 2, 0, height], [-width / 2, 0, height]],
        dtype=float,
    )
    faces = np.array([[0, 2, 1], [0, 3, 2], [0, 1, 2], [0, 2, 3]])
    # u runs opposite to the plane's +x: on both fuselage sides a viewer looking
    # at the plane sees its +x edge on their left, so u=0 (start of "NAVY") must
    # sit there or the titles read mirrored. Verified by renders of both sides.
    uv = np.array([[1, 0], [0, 0], [0, 1], [1, 1]], dtype=float)
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=uv,
        material=trimesh.visual.material.PBRMaterial(
            name="NAVY_titles", baseColorTexture=image, metallicFactor=0.0, roughnessFactor=0.7
        ),
    )
    return mesh


def place(mesh, x, y, z, yaw):
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([x, y, z])
    return mesh


def box_local(length, width, height, x, y, z):
    mesh = trimesh.creation.box(extents=[length, width, height])
    mesh.apply_translation([x, y, z])
    return mesh


def main():
    layer = SceneLayer()
    name = "Navy_aircraft_display"
    cx, cy = CENTRE_ENU
    cos_y, sin_y = math.cos(YAW), math.sin(YAW)

    def to_world(mesh, lx, ly, lz):
        """Local aircraft frame (x=nose, y=left wing, z=up) -> world ENU."""
        mesh.apply_transform(trimesh.transformations.rotation_matrix(YAW, [0, 0, 1]))
        mesh.apply_translation([cx + lx * cos_y - ly * sin_y, cy + lx * sin_y + ly * cos_y, lz])
        return mesh

    # Display plinth strip.
    plinth = box_local(16.5, 6.0, 0.18, 0, 0, 0.09)
    layer.add(to_world(plinth, 0, 0, 0), "concrete", name)

    body_z = 2.35  # fuselage centre height on its supports
    # Fuselage: tapered capsule built from a cylinder + nose/tail cones.
    fus = trimesh.creation.cylinder(radius=1.05, height=9.5, sections=18)
    fus.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    layer.add(to_world(fus, -0.5, 0, body_z), "fuselage_white", name)
    nose = trimesh.creation.cone(radius=1.05, height=2.6, sections=18)
    nose.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    nose.apply_translation([5.55, 0, 0])
    layer.add(to_world(nose, 0, 0, body_z), "fuselage_white", name)
    tailcone = trimesh.creation.cone(radius=1.05, height=3.0, sections=18)
    tailcone.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))
    tailcone.apply_translation([-6.75, 0, 0])
    layer.add(to_world(tailcone, 0, 0, body_z), "fuselage_white", name)
    # Light-blue upper fuselage band / spine.
    spine = box_local(9.8, 1.15, 0.35, -0.4, 0, body_z + 0.95)
    layer.add(to_world(spine, 0, 0, 0), "navy_blue", name)
    # Cockpit glass.
    cockpit = box_local(1.7, 1.55, 0.55, 3.9, 0, body_z + 0.62)
    layer.add(to_world(cockpit, 0, 0, 0), "glass", name)
    # Blue cheatline along both sides.
    for side in (-1, 1):
        stripe = box_local(10.5, 0.06, 0.42, -0.5, side * 1.06, body_z + 0.15)
        layer.add(to_world(stripe, 0, 0, 0), "navy_blue", name)

    # High straight wing + twin turboprop nacelles and propellers.
    wing = box_local(2.1, 14.6, 0.22, 0.6, 0, body_z + 1.12)
    layer.add(to_world(wing, 0, 0, 0), "fuselage_white", name)
    for side in (-1, 1):
        nac = box_local(3.4, 0.85, 0.85, 0.8, side * 3.4, body_z + 0.82)
        layer.add(to_world(nac, 0, 0, 0), "navy_blue", name)
        prop = trimesh.creation.cylinder(radius=1.25, height=0.08, sections=20)
        prop.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        prop.apply_translation([2.65, side * 3.4, 0])
        layer.add(to_world(prop, 0, 0, body_z + 0.82), "dark", name)
        hub = trimesh.creation.cone(radius=0.22, height=0.55, sections=10)
        hub.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        hub.apply_translation([2.95, side * 3.4, 0])
        layer.add(to_world(hub, 0, 0, body_z + 0.82), "steel", name)

    # Tail: blue vertical fin + horizontal stabiliser.
    fin = box_local(1.9, 0.18, 2.1, -6.6, 0, body_z + 1.55)
    layer.add(to_world(fin, 0, 0, 0), "navy_blue", name)
    fin_tip = box_local(1.9, 0.20, 0.35, -6.6, 0, body_z + 2.72)
    layer.add(to_world(fin_tip, 0, 0, 0), "fuselage_white", name)
    stab = box_local(1.3, 5.2, 0.16, -6.7, 0, body_z + 0.85)
    layer.add(to_world(stab, 0, 0, 0), "fuselage_white", name)

    # Display supports + wheels-down suggestion.
    for lx in (-3.5, 2.8):
        support = box_local(0.5, 1.6, 1.15, lx, 0, 0.75)
        layer.add(to_world(support, 0, 0, 0), "stand_yellow", name)
    for side in (-1, 1):
        wheel = trimesh.creation.cylinder(radius=0.42, height=0.22, sections=12)
        wheel.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        wheel.apply_translation([1.4, side * 0.85, 0])
        layer.add(to_world(wheel, 0, 0, 0.60), "dark", name)

    # NAVY titles on both rear fuselage sides (original rendering).
    texture = navy_texture()
    for side in (-1, 1):
        plane = text_plane(texture, 2.6, 0.65)
        yaw = YAW if side == 1 else YAW + math.pi
        lx, ly = -3.4, side * 1.10
        wx = cx + lx * cos_y - ly * sin_y
        wy = cy + lx * sin_y + ly * cos_y
        layer.add_textured(place(plane, wx, wy, body_z + 0.28, yaw), f"{name}_titles_{'L' if side == 1 else 'R'}")

    out_path = os.path.join(ROOT, "props", "navy_aircraft_display.glb")
    layer.export(out_path)

    loaded = trimesh.load(out_path)
    geometries = list(loaded.geometry.values())
    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres), origin 12.9487N 80.1394E; WORLD-POSITIONED",
        "placement": "APPROXIMATE: centre ENU (154.0, -26.0), south-east of the aircraft grove centre (142.6, -10.2) in data/v2_meta.json; heading 0.55 rad ENU; from photo 15.jpg viewpoint, not surveyed",
        "provenance": "User's own photo 15.jpg (Mar 2019), Drive folder 'mit', observation only; no photo pixels shipped, no people modelled",
        "generator": "tools/navy_aircraft.py",
        "output": "props/navy_aircraft_display.glb",
        "contents": {"aircraft": 1, "display_plinth": 1, "supports": 2},
        "glb_stats": {
            "geometries": len(geometries),
            "vertices": int(sum(len(g.vertices) for g in geometries)),
            "faces": int(sum(len(g.faces) for g in geometries)),
            "bounds_gltf": [[round(float(v), 2) for v in row] for row in loaded.bounds.tolist()],
        },
        "integration": "Registered in ChromepetSync.Glbs (world-positioned, like props/chrompet_identity.glb); Unity was not opened/compiled on this machine",
    }
    with open(os.path.join(ROOT, "data", "navy_aircraft_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
