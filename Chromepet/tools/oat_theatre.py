"""Detailed Open Air Theatre (OAT), MIT Chromepet -- additive detailed model.

Reference: user's own campus photos 1.jpg and 76.jpg (Mar 2019, Google
Drive folder 'mit', shared 2026-10-20; see ../REFERENCE_VIDEOS.md).
76.jpg is a close view of the stage end: a curved red-brick slatted
screen with a pergola beam behind the raised semicircular stage.
Observation only: no photo pixels are shipped; all textures are
original PIL renderings.

What the photo shows: a large flat circular plaza of concentric paved
rings (alternating light concrete and dark bands), ringed on the far
side by curved brick-red stepped terraces, a low central circular stage
area, black lamp posts around the plaza and a yellow OPEN AIR THEATRE
sign board. People in the photo are not modelled.

Placement: WORLD-POSITIONED (baked at export). The theatre's surveyed
ENU position is not recorded in OSM (no OAT node exists), so the site
was chosen from the model's own road/campus geometry (roads_v2.glb +
data/osm_raw.osm analysis, 2026-10-21): the only clear 63 m circle on
campus ground west of the main avenue, between the avenue and the west
service road, north of the avenue fountain. Centre ENU (-26.0, -116.0),
heading 0 (local north = world north; terraces wrap north/east/west,
entrance opening + sign on the south side, facing the gate). A paved
connector (props/connector_paths.glb) links the avenue's west edge to
the entrance. Recorded in data/placement_map.json (id open_air_theatre).
See data/oat_meta.json for the placement record.

Run from Chromepet/:  python3 tools/oat_theatre.py
Dependencies: trimesh, numpy, pillow
Output: props/open_air_theatre.glb + data/oat_meta.json
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
    "brick_red": (0.62, 0.24, 0.17),
    "brick_dark": (0.50, 0.19, 0.13),
    "concrete": (0.74, 0.72, 0.68),
    "concrete_dark": (0.42, 0.42, 0.44),
    "paving_light": (0.80, 0.78, 0.74),
    "stage_brown": (0.42, 0.27, 0.15),
    "black": (0.05, 0.05, 0.05),
    "sign_yellow": (0.93, 0.72, 0.12),
    "lamp": (0.95, 0.92, 0.70),
    "grass": (0.33, 0.47, 0.22),
}


def box(cx, cy, length, width, height, yaw=0.0, z0=0.0):
    mesh = trimesh.creation.box(extents=[length, width, height])
    mesh.apply_translation([0, 0, z0 + height / 2])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([cx, cy, 0])
    return mesh


def cylinder(x, y, radius, height, z0=0.0, sections=24):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation([x, y, z0 + height / 2])
    return mesh


def annulus(x, y, r_min, r_max, height, z0=0.0, sections=48):
    mesh = trimesh.creation.annulus(r_min=r_min, r_max=r_max, height=height, sections=sections)
    mesh.apply_translation([x, y, z0 + height / 2])
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

    def export(self, path, world_enu=(0.0, 0.0)):
        scene = trimesh.Scene()
        enu_to_gltf = np.array(
            [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float
        )
        # Bake the world site: ENU (x, y) -> glTF translation (x, 0, -y).
        site = np.eye(4)
        site[0, 3], site[2, 3] = world_enu[0], -world_enu[1]
        for index, (name, mesh, color) in enumerate(self.parts):
            mesh = mesh.copy()
            mesh.visual = trimesh.visual.TextureVisuals(material=material(color, f"{name}_material"))
            mesh.apply_transform(enu_to_gltf)
            mesh.apply_transform(site)
            scene.add_geometry(mesh, geom_name=f"{name}__{index}", node_name=f"{name}__{index}")
        for index, (name, mesh) in enumerate(self.textured):
            mesh = mesh.copy()
            mesh.apply_transform(enu_to_gltf)
            mesh.apply_transform(site)
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
    """Yellow OAT board, original rendering (no photo pixels)."""
    image = Image.new("RGB", (1024, 256), (237, 184, 31))
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 10, 1013, 245), outline=(25, 25, 22), width=10)
    text = "OPEN AIR THEATRE"
    fnt = font(104)
    bounds = draw.textbbox((0, 0), text, font=fnt)
    draw.text(((1024 - (bounds[2] - bounds[0])) / 2, 42), text, font=fnt, fill=(25, 25, 22))
    small = font(52)
    text2 = "O A T"
    bounds = draw.textbbox((0, 0), text2, font=small)
    draw.text(((1024 - (bounds[2] - bounds[0])) / 2, 168), text2, font=small, fill=(25, 25, 22))
    return image


def text_plane(image, width, height):
    vertices = np.array(
        [[-width / 2, 0, 0], [width / 2, 0, 0], [width / 2, 0, height], [-width / 2, 0, height]],
        dtype=float,
    )
    faces = np.array([[0, 2, 1], [0, 3, 2], [0, 1, 2], [0, 2, 3]])
    # u runs opposite to +x: a viewer in front of the plane (the +y side) sees +x
    # to their left, so u=0 (start of text) must sit at the +x edge or the sign
    # reads mirrored. Same fix as the department frontage / Navy titles
    # (verified by render 2026-10-21: the OAT sign previously read reversed).
    uv = np.array([[1, 0], [0, 0], [0, 1], [1, 1]], dtype=float)
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=uv,
        material=trimesh.visual.material.PBRMaterial(
            name="OAT_sign", baseColorTexture=image, metallicFactor=0.0, roughnessFactor=0.8
        ),
    )
    return mesh


def place(mesh, x, y, z, yaw):
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([x, y, z])
    return mesh


def main():
    layer = SceneLayer()
    name = "Open_Air_Theatre"

    # Flat circular plaza with concentric paved rings (photo 1.jpg).
    layer.add(cylinder(0, 0, 19.0, 0.18, 0.0, 48), "concrete", name)
    ring_specs = [
        (5.6, 7.2, "concrete_dark"),
        (7.2, 8.6, "paving_light"),
        (8.6, 10.2, "concrete_dark"),
        (10.2, 11.8, "paving_light"),
        (11.8, 13.4, "brick_dark"),
        (13.4, 15.2, "paving_light"),
        (15.2, 17.0, "concrete_dark"),
        (17.0, 19.0, "paving_light"),
    ]
    for r_min, r_max, col in ring_specs:
        layer.add(annulus(0, 0, r_min, r_max, 0.06, 0.18, 48), col, name)

    # Central circular stage platform + short brown centre cylinder.
    layer.add(cylinder(0, 0, 5.6, 0.45, 0.18, 40), "brick_red", f"{name}_stage")
    layer.add(cylinder(0, 0, 5.65, 0.12, 0.18, 40), "stage_brown", f"{name}_stage")
    layer.add(cylinder(0, 0, 1.1, 0.85, 0.63, 20), "stage_brown", f"{name}_stage")
    # Brick-red stepped terraces wrapping north/east/west (entrance gap south).
    # 6 steps, each an arc of tangent wedge boxes.
    steps = 6
    for k in range(steps):
        radius = 20.6 + k * 1.55
        height = 0.55 + k * 0.52
        col = "brick_red" if k % 2 == 0 else "brick_dark"
        n = 22
        for i in range(n):
            theta_deg = -18 + (216 * i) / (n - 1)  # 0 deg = east, 90 = north
            theta = math.radians(theta_deg)
            x, y = radius * math.cos(theta), radius * math.sin(theta)
            chord = 2 * math.pi * radius * (216 / 360) / n * 0.94
            layer.add(box(x, y, chord, 1.5, height, theta + math.pi / 2, 0.0), col, f"{name}_terraces")
    # Curved red-brick slatted screen behind the stage with a pergola beam
    # on brick pillars (photo 76.jpg, close view of the same complex).
    screen_r = 7.4
    for i in range(17):
        theta = math.radians(32 + (116 * i) / 16)
        x, y = screen_r * math.cos(theta), screen_r * math.sin(theta)
        layer.add(box(x, y, 0.52, 0.20, 2.30, theta + math.pi / 2, 0.63), "brick_red", f"{name}_stage_screen")
    for theta_deg in (30, 150):
        theta = math.radians(theta_deg)
        x, y = screen_r * math.cos(theta), screen_r * math.sin(theta)
        layer.add(box(x, y, 0.55, 0.55, 3.15, theta, 0.0), "brick_dark", f"{name}_stage_screen")
    for i in range(8):
        theta = math.radians(36 + (108 * i) / 7)
        x, y = screen_r * math.cos(theta), screen_r * math.sin(theta)
        layer.add(box(x, y, 1.95, 0.42, 0.30, theta + math.pi / 2, 3.15), "concrete", f"{name}_stage_screen")

    # Rectangular stage house behind the slat screen (photos 21.jpg /
    # 30.jpg: a raised rectangular stage block with a maroon slatted
    # backdrop stands behind the circular stage, north side).
    layer.add(box(0, 11.9, 15.0, 5.2, 4.3, 0.0, 0.0), "brick_dark", f"{name}_stage_house")
    layer.add(box(0, 11.9, 15.8, 5.8, 0.30, 0.0, 4.3), "concrete", f"{name}_stage_house")
    for i in range(13):  # maroon vertical slats on the stage-facing wall
        x = -6.0 + i * 1.0
        layer.add(box(x, 9.22, 0.55, 0.16, 3.3, 0.0, 0.63), (0.45, 0.10, 0.13), f"{name}_stage_house")
    for side in (-7.9, 7.9):  # end pillars
        layer.add(box(side, 11.9, 0.6, 0.6, 4.6, 0.0, 0.0), "brick_red", f"{name}_stage_house")

    # Grass bank behind the top terrace.
    layer.add(annulus(0, 0, 29.6, 31.5, 0.25, 0.0, 48), "grass", name)

    # Defined entrance opening on the south side: two brick gate pillars
    # flanking the terrace gap + a paved entrance slab from the plaza
    # edge out to the grounds edge (the connector path meets it here).
    for theta_deg in (219, 339):
        theta = math.radians(theta_deg)
        x, y = 25.5 * math.cos(theta), 25.5 * math.sin(theta)
        layer.add(box(x, y, 0.75, 0.75, 2.6, theta, 0.0), "brick_red", f"{name}_entrance")
        layer.add(box(x, y, 0.95, 0.95, 0.25, theta, 2.6), "concrete", f"{name}_entrance")
    layer.add(box(0, -26.0, 4.4, 11.5, 0.10, 0.0, 0.02), "concrete", f"{name}_entrance")

    # Black lamp posts around the plaza.
    for i in range(8):
        theta = math.radians(i * 45 + 12)
        x, y = 17.8 * math.cos(theta), 17.8 * math.sin(theta)
        layer.add(cylinder(x, y, 0.07, 4.4, 0.18, 8), "black", f"{name}_lamps")
        layer.add(cylinder(x, y, 0.16, 0.28, 4.58, 10), "lamp", f"{name}_lamps")

    # Yellow OAT sign board at the south entrance opening.
    sx, sy = 0.0, -21.5
    for side in (-1.9, 1.9):
        layer.add(cylinder(sx + side, sy, 0.09, 2.9, 0.0, 8), "black", f"{name}_sign")
    layer.add(box(sx, sy, 4.6, 0.18, 1.25, 0.0, 1.55), "sign_yellow", f"{name}_sign")
    texture = sign_texture()
    front = text_plane(texture, 4.4, 1.1)
    back = text_plane(texture, 4.4, 1.1)
    layer.add_textured(place(front, sx, sy - 0.11, 1.62, math.pi), f"{name}_sign_front")
    layer.add_textured(place(back, sx, sy + 0.11, 1.62, 0.0), f"{name}_sign_back")

    site_enu = (-26.0, -116.0)  # baked world site, see docstring + placement_map.json
    out_path = os.path.join(ROOT, "props", "open_air_theatre.glb")
    layer.export(out_path, world_enu=site_enu)

    loaded = trimesh.load(out_path)
    geometries = list(loaded.geometry.values())
    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres), origin 12.9487N 80.1394E; WORLD-POSITIONED (site baked into the GLB)",
        "placement": "SITED (approximate, source: roads_geometry): centre ENU (-26.0, -116.0), heading 0 deg (terraces north/east/west, entrance south). Chosen 2026-10-21 from roads_v2.glb + data/osm_raw.osm geometry: the only clear 63 m circle on campus ground west of the main avenue (avenue centreline 38.4 m east of the centre, west service road centreline 41.2 m west, fountain 48 m south). No OSM node exists for the OAT; not surveyed.",
        "provenance": "User's own photos 1.jpg, 21.jpg, 30.jpg, 76.jpg (Mar 2019), Drive folder 'mit', observation only; no photo pixels shipped, no people modelled",
        "generator": "tools/oat_theatre.py",
        "output": "props/open_air_theatre.glb",
        "contents": {
            "plaza_radius_m": 19.0,
            "paved_rings": len(ring_specs),
            "terrace_steps": steps,
            "lamp_posts": 8,
            "sign_board": 1,
            "stage_screen": "curved red-brick slat screen + pergola beam (photo 76.jpg)",
            "stage_house": "rectangular stage house with maroon slatted backdrop behind the screen (photos 21/30.jpg)",
            "entrance": "brick gate pillars flanking the south terrace gap + paved entrance slab",
        },
        "glb_stats": {
            "geometries": len(geometries),
            "vertices": int(sum(len(g.vertices) for g in geometries)),
            "faces": int(sum(len(g.faces) for g in geometries)),
            "bounds_gltf": [[round(float(v), 2) for v in row] for row in loaded.bounds.tolist()],
        },
        "integration": "Registered in ChromepetSync.Glbs (world-positioned, like props/chrompet_identity.glb); connector path props/connector_paths.glb links the avenue west edge to the south entrance. Registry: data/placement_map.json id open_air_theatre.",
    }
    with open(os.path.join(ROOT, "data", "oat_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
