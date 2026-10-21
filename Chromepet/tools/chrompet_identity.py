"""Build recognisable Chrompet identity props as one world-positioned GLB.

This generator is intentionally independent of the large OSM input so the small
identity layer can be rebuilt even when Git LFS objects have not been fetched.

Reference frame matches the v2 area assets:
  origin 12.9487 N, 80.1394 E
  glTF x=east, y=up, z=-north, units=metres

Visual references and licensing are recorded in ../REFERENCE_MEDIA.md.
Run from Chromepet/:  python3 tools/chrompet_identity.py
Dependencies: trimesh, numpy, pillow
"""

import json
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont, features


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAT0, LON0, EARTH_R = 12.9487, 80.1394, 6378137.0


def local_xy(lat, lon):
    """Latitude/longitude to local ENU metres."""
    x = (lon - LON0) * math.radians(1) * EARTH_R * math.cos(math.radians(LAT0))
    y = (lat - LAT0) * math.radians(1) * EARTH_R
    return np.array([x, y], dtype=float)


COLORS = {
    "station_yellow": (0.91, 0.66, 0.16),
    "black": (0.045, 0.045, 0.04),
    "cream": (0.91, 0.86, 0.69),
    "maroon": (0.48, 0.12, 0.17),
    "train_white": (0.82, 0.83, 0.80),
    "train_band": (0.42, 0.16, 0.28),
    "window_blue": (0.12, 0.28, 0.38),
    "steel": (0.48, 0.50, 0.50),
    "dark_steel": (0.20, 0.21, 0.21),
    "auto_yellow": (0.95, 0.70, 0.08),
    "auto_green": (0.12, 0.30, 0.16),
    "tail_red": (0.76, 0.05, 0.04),
    "lamp": (0.92, 0.90, 0.65),
}


def box(cx, cy, length, width, height, yaw=0.0, z0=0.0):
    mesh = trimesh.creation.box(extents=[length, width, height])
    mesh.apply_translation([0, 0, z0 + height / 2])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([cx, cy, 0])
    return mesh


def cylinder(x, y, radius, height, z0=0.0, sections=12):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation([x, y, z0 + height / 2])
    return mesh


def place(mesh, x, y, z, yaw):
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([x, y, z])
    return mesh


def beam3(a, b, radius=0.04, sections=8):
    """Cylinder between 3D points."""
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
        roughnessFactor=0.78,
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
            [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]],
            dtype=float,
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


def font(candidates, size):
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


LATIN_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
TAMIL_FONTS = [
    "/System/Library/Fonts/Supplemental/Tamil Sangam MN.ttc",
    "/System/Library/Fonts/Supplemental/Tamil MN.ttc",
    "/System/Library/Fonts/SFIndia.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf",
]
DEVANAGARI_FONTS = [
    "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
    "/System/Library/Fonts/Supplemental/DevanagariMT.ttc",
    "/System/Library/Fonts/SFIndia.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
]


def draw_centered(draw, text, y, image_width, font_obj, fill):
    kwargs = {"font": font_obj, "fill": fill}
    if features.check("raqm"):
        kwargs["direction"] = "ltr"
    measure_kwargs = {"font": font_obj}
    if "direction" in kwargs:
        measure_kwargs["direction"] = kwargs["direction"]
    bounds = draw.textbbox((0, 0), text, **measure_kwargs)
    width = bounds[2] - bounds[0]
    draw.text(((image_width - width) / 2, y), text, **kwargs)


def station_sign_texture():
    """Recreate the current yellow Chrompet nameboard without copying pixels."""
    image = Image.new("RGB", (1024, 512), (232, 168, 41))
    draw = ImageDraw.Draw(image)
    draw.rectangle((12, 12, 1011, 499), outline=(20, 20, 18), width=18)
    draw_centered(draw, "குரோம்பேட்டை", 25, 1024, font(TAMIL_FONTS, 116), (15, 15, 14))
    draw_centered(draw, "क्रोमपेट", 170, 1024, font(DEVANAGARI_FONTS, 105), (15, 15, 14))
    draw_centered(draw, "CHROMPET", 312, 1024, font(LATIN_FONTS, 118), (15, 15, 14))
    return image


def text_plane(image, width, height):
    vertices = np.array(
        [[-width / 2, 0, 0], [width / 2, 0, 0], [width / 2, 0, height], [-width / 2, 0, height]],
        dtype=float,
    )
    faces = np.array([[0, 2, 1], [0, 3, 2], [0, 1, 2], [0, 2, 3]])
    # u runs opposite to +x so a viewer in front of the plane sees the text
    # unmirrored (same fix as the department frontage; the station boards read
    # reversed with the old mapping, render-verified 2026-10-21).
    uv = np.array([[1, 0], [0, 0], [0, 1], [1, 1]], dtype=float)
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=uv,
        material=trimesh.visual.material.PBRMaterial(
            name="Chrompet_station_sign",
            baseColorTexture=image,
            metallicFactor=0.0,
            roughnessFactor=0.80,
        ),
    )
    return mesh


def add_station_board(layer, x, y, yaw, name):
    """Yellow trilingual nameboard with black/yellow striped posts and black feet."""
    board_w, board_h, bottom = 4.2, 2.05, 2.0
    layer.add(box(x, y, board_w + 0.18, 0.20, board_h + 0.18, yaw, bottom - 0.09), "black", name)
    layer.add(box(x, y, board_w, 0.24, board_h, yaw, bottom), "station_yellow", name)

    px, py = -math.sin(yaw), math.cos(yaw)
    along_x, along_y = math.cos(yaw), math.sin(yaw)
    for side in (-1, 1):
        sx, sy = x + along_x * side * 1.75, y + along_y * side * 1.75
        layer.add(cylinder(sx, sy, 0.12, 3.95, 0, 10), "black", name)
        for z0 in (0.62, 1.34):
            layer.add(cylinder(sx, sy, 0.135, 0.36, z0, 10), "station_yellow", name)
        layer.add(cylinder(sx, sy, 0.28, 0.28, 0, 12), "black", name)

    texture = station_sign_texture()
    front = text_plane(texture, board_w - 0.16, board_h - 0.16)
    back = text_plane(texture, board_w - 0.16, board_h - 0.16)
    layer.add_textured(place(front, x + px * 0.126, y + py * 0.126, bottom + 0.08, yaw), f"{name}_front")
    layer.add_textured(place(back, x - px * 0.126, y - py * 0.126, bottom + 0.08, yaw + math.pi), f"{name}_back")


def add_station_office(layer, x, y, yaw):
    """Small cream-and-maroon platform office based on the station overview."""
    name = "Chrompet_station_office"
    layer.add(box(x, y, 26.0, 10.5, 5.9, yaw), "cream", name)
    layer.add(box(x, y, 26.4, 10.9, 0.58, yaw, 4.85), "maroon", name)
    layer.add(box(x, y, 27.2, 11.5, 0.35, yaw, 5.9), "cream", name)
    # Platform-facing dark windows and ticket openings.
    nx, ny = -math.sin(yaw), math.cos(yaw)
    ax, ay = math.cos(yaw), math.sin(yaw)
    for offset in (-8.0, -3.0, 3.0, 8.0):
        layer.add(
            box(x + ax * offset + nx * 5.31, y + ay * offset + ny * 5.31, 2.8, 0.12, 1.45, yaw, 2.25),
            "window_blue",
            name,
        )
    # Shallow platform canopy.
    layer.add(box(x + nx * 7.3, y + ny * 7.3, 22.0, 4.2, 0.25, yaw, 4.05), "maroon", name)
    for offset in (-9.5, -4.8, 0, 4.8, 9.5):
        layer.add(cylinder(x + ax * offset + nx * 8.8, y + ay * offset + ny * 8.8, 0.09, 4.1, 0, 8), "steel", name)


def add_emu_car(layer, x, y, yaw, index, cab=False):
    name = f"Chennai_suburban_EMU_car_{index}"
    length, width, height = 19.2, 3.45, 3.65
    layer.add(box(x, y, length, width, height, yaw, 1.15), "train_white", name)
    layer.add(box(x, y, length + 0.06, width + 0.04, 0.48, yaw, 2.05), "train_band", name)
    layer.add(box(x, y, length - 0.3, width + 0.08, 0.18, yaw, 4.80), "steel", name)
    ax, ay = math.cos(yaw), math.sin(yaw)
    nx, ny = -math.sin(yaw), math.cos(yaw)
    # Dark side windows and doors on both faces.
    for face in (-1, 1):
        for offset in (-6.5, -3.9, -1.3, 1.3, 3.9, 6.5):
            layer.add(
                box(x + ax * offset + nx * face * 1.74, y + ay * offset + ny * face * 1.74, 1.55, 0.10, 1.05, yaw, 3.05),
                "window_blue",
                name,
            )
        for offset in (-8.25, 8.25):
            layer.add(
                box(x + ax * offset + nx * face * 1.76, y + ay * offset + ny * face * 1.76, 1.05, 0.11, 2.15, yaw, 1.38),
                "train_band",
                name,
            )
    # Wheelsets: cylinders are rotated so their axles cross the coach.
    for offset in (-6.6, 6.6):
        wx, wy = x + ax * offset, y + ay * offset
        axle = trimesh.creation.cylinder(radius=0.44, height=3.58, sections=14)
        axle.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        layer.add(place(axle, wx, wy, 0.62, yaw), "dark_steel", name)
    if cab:
        ex, ey = x + ax * (length / 2 + 0.04), y + ay * (length / 2 + 0.04)
        layer.add(box(ex, ey, 0.10, width * 0.72, 1.25, yaw + math.pi / 2, 3.15), "window_blue", name)
        for side in (-1, 1):
            layer.add(cylinder(ex + nx * side * 0.95, ey + ny * side * 0.95, 0.16, 0.10, 2.18, 12), "lamp", name)


def add_suburban_emu(layer, x, y, yaw):
    """Static three-car low-poly train; enough detail for station context."""
    ax, ay = math.cos(yaw), math.sin(yaw)
    for index, offset in enumerate((-20.0, 0.0, 20.0)):
        add_emu_car(layer, x + ax * offset, y + ay * offset, yaw, index + 1, cab=index in (0, 2))
    # One diamond pantograph on the centre motor car.
    base_a = np.array([x - ax * 2.2, y - ay * 2.2, 5.0])
    base_b = np.array([x + ax * 2.2, y + ay * 2.2, 5.0])
    nx, ny = -math.sin(yaw), math.cos(yaw)
    top_a = np.array([x - ax * 1.0 + nx * 0.15, y - ay * 1.0 + ny * 0.15, 6.45])
    top_b = np.array([x + ax * 1.0 + nx * 0.15, y + ay * 1.0 + ny * 0.15, 6.45])
    for a, b in ((base_a, top_b), (base_b, top_a), (top_a, top_b)):
        layer.add(beam3(a, b, 0.055), "dark_steel", "Chennai_suburban_EMU_pantograph")


def add_auto(layer, x, y, yaw, index):
    """Compact Chennai-style yellow/green auto-rickshaw."""
    name = f"Chrompet_auto_rickshaw_{index}"
    ax, ay = math.cos(yaw), math.sin(yaw)
    layer.add(box(x, y, 2.65, 1.38, 0.52, yaw, 0.42), "auto_yellow", name)
    layer.add(box(x - ax * 0.24, y - ay * 0.24, 1.62, 1.42, 1.18, yaw, 0.90), "auto_green", name)
    layer.add(box(x - ax * 0.18, y - ay * 0.18, 1.78, 1.48, 0.16, yaw, 2.05), "black", name)
    # Slanted-looking windscreen represented by a dark front panel.
    layer.add(box(x + ax * 0.77, y + ay * 0.77, 0.10, 1.16, 0.70, yaw + math.pi / 2, 1.22), "window_blue", name)
    for longitudinal, lateral in ((0.78, 0), (-0.74, -0.62), (-0.74, 0.62)):
        wx = x + ax * longitudinal - math.sin(yaw) * lateral
        wy = y + ay * longitudinal + math.cos(yaw) * lateral
        wheel = trimesh.creation.cylinder(radius=0.28, height=0.16, sections=12)
        wheel.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        layer.add(place(wheel, wx, wy, 0.30, yaw), "black", name)
    layer.add(cylinder(x + ax * 1.30, y + ay * 1.30, 0.10, 0.10, 0.78, 12), "lamp", name)
    layer.add(box(x - ax * 1.34, y - ay * 1.34, 0.08, 0.72, 0.16, yaw + math.pi / 2, 0.62), "tail_red", name)


def main():
    layer = SceneLayer()
    station = local_xy(12.9514922, 80.1408089)
    rail_yaw = math.radians(73.5)  # ~16.5 degrees east of north, measured from map alignment.
    ax, ay = math.cos(rail_yaw), math.sin(rail_yaw)
    nx, ny = -math.sin(rail_yaw), math.cos(rail_yaw)

    # Four platforms are documented for CMP; boards are staggered so each is visible.
    board_positions = []
    for index, (along, across) in enumerate(((-58, -12), (45, -4), (-22, 5), (66, 13)), 1):
        x = station[0] + ax * along + nx * across
        y = station[1] + ay * along + ny * across
        add_station_board(layer, x, y, rail_yaw, f"Chrompet_station_board_P{index}")
        board_positions.append([round(x, 2), round(y, 2)])

    # Office and train are slightly offset along/across the station centre.
    office_xy = station - np.array([ax, ay]) * 82 + np.array([nx, ny]) * 13
    add_station_office(layer, office_xy[0], office_xy[1], rail_yaw)
    train_xy = station + np.array([ax, ay]) * 18 + np.array([nx, ny]) * 1.5
    add_suburban_emu(layer, train_xy[0], train_xy[1], rail_yaw)

    # A small auto stand on Station Road and one auto near the MIT main gate.
    auto_positions = []
    station_road = local_xy(12.95070, 80.14200)
    for index, offset in enumerate((-3.2, 0, 3.2), 1):
        p = station_road + np.array([0, offset])
        add_auto(layer, p[0], p[1], math.radians(165), index)
        auto_positions.append([round(float(p[0]), 2), round(float(p[1]), 2)])
    gate_auto = local_xy(12.94647, 80.13863)
    add_auto(layer, gate_auto[0], gate_auto[1], math.radians(35), 4)
    auto_positions.append([round(float(gate_auto[0]), 2), round(float(gate_auto[1]), 2)])

    out_path = os.path.join(ROOT, "props", "chrompet_identity.glb")
    layer.export(out_path)
    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres), origin 12.9487N 80.1394E",
        "source_notes": "See REFERENCE_MEDIA.md; geometry is an original low-poly interpretation, not a photogrammetry extraction.",
        "station_coordinates": [12.9514922, 80.1408089],
        "rail_yaw_enu_degrees": 73.5,
        "station_board_enu": board_positions,
        "station_office_enu": [round(float(office_xy[0]), 2), round(float(office_xy[1]), 2)],
        "train_centre_enu": [round(float(train_xy[0]), 2), round(float(train_xy[1]), 2)],
        "auto_rickshaw_enu": auto_positions,
        "contents": {
            "station_boards": 4,
            "station_office": 1,
            "suburban_emu_cars": 3,
            "auto_rickshaws": 4,
        },
    }
    with open(os.path.join(ROOT, "data", "identity_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
