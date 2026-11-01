"""Chrompet station platform details -- additive identity layer.

Adds the furniture the basic roads-layer station (roads/roads_v2.glb
'Chromepet_station' nodes: two 320 m platform slabs with full-length
canopies and centre columns) lacks: platform-edge warning lines, tactile
strips, benches, hanging platform-number boards, under-canopy tube
lights and dustbins. Sits on the existing platforms; nothing is
replaced and no surface duplicates an existing one (all strips stand
2-3 cm proud of the platform top).

Coordinates are baked constants measured from roads/roads_v2.glb on
2026-10-31 (OSM, ODbL; see tools/README.md): platform slab centres
ENU (205.51, 378.77) and (225.40, 365.21), track axis ENU unit vector
(0.5633, 0.8263), slab half-length 160 m, half-width 3.73 m, platform
top y=0.95, canopy underside y=5.10. Platform 1 is the station-office
side (office at ENU (117.1, 235.9), data/identity_meta.json). The
generator itself needs no LFS input.

World frame: metres, x=east, y=up, z=-north, origin 12.9487 N
80.1394 E (same v2 frame as the other layers). WORLD-POSITIONED: load
at the identity transform. Placements are APPROXIMATE (geometry-derived,
not surveyed) and registered in data/placement_map.json.

Run from Chromepet/:  python3 tools/station_details.py
Dependencies: trimesh, numpy, pillow
Output: props/chrompet_station_details.glb + data/station_details_meta.json
"""

import json
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from PIL.features import check as pil_feature_check

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# --- Measured station constants (roads/roads_v2.glb, 2026-10-31) ------
TRACK_U = (0.5633, 0.8263)          # ENU unit vector along the tracks
TRACK_P = (-TRACK_U[1], TRACK_U[0])  # ENU unit vector across the tracks
PLATFORM_TOP = 0.95
CANOPY_UNDER = 5.10
HALF_LENGTH = 160.0
HALF_WIDTH = 3.73
PLATFORMS = {1: (205.51, 378.77), 2: (225.40, 365.21)}

# Foot-overbridge deck (measured from roads_v2.glb Overbridge__0,
# 2026-10-31): slab top y=6.80, overhanging P1 near its centre and
# reaching toward P2. Staircases below plug into it (approximate).
FOB_DECK_TOP = 6.80
STAIRS = {  # platform -> ENU centre of the stair flight (along-track)
    1: PLATFORMS[1],
    2: (219.79, 356.95),  # P2 centre + along -10, near the FOB column row end
}

TRACK_YAW = math.atan2(TRACK_U[1], TRACK_U[0])   # local +x along track
BOARD_YAW = math.atan2(TRACK_P[1], TRACK_P[0])   # local +x across track

COLORS = {
    "line_white": (0.92, 0.92, 0.88),
    "tactile_yellow": (0.85, 0.65, 0.10),
    "bench_blue": (0.16, 0.30, 0.48),
    "steel": (0.58, 0.60, 0.62),
    "board_black": (0.08, 0.08, 0.08),
    "lamp_white": (0.95, 0.95, 0.92),
    "bin_green": (0.13, 0.32, 0.16),
}

LATIN_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def enu_to_gltf():
    return np.array(
        [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float
    )


def box(cx, cy, length, width, height, yaw=0.0, z0=0.0):
    """Box in the ENU build frame: centre (cx, cy), +x rotated by yaw, z0 base."""
    mesh = trimesh.creation.box(extents=[length, width, height])
    mesh.apply_translation([0, 0, height / 2])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([cx, cy, z0])
    return mesh


def cylinder(x, y, radius, height, z0=0.0, sections=10):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation([x, y, z0 + height / 2])
    return mesh


def place(mesh, x, y, z, yaw):
    mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    mesh.apply_translation([x, y, z])
    return mesh


def along(number, offset_along, offset_across):
    """ENU point on platform `number`: along/across offsets from its centre."""
    cx, cy = PLATFORMS[number]
    return (
        cx + TRACK_U[0] * offset_along + TRACK_P[0] * offset_across,
        cy + TRACK_U[1] * offset_along + TRACK_P[1] * offset_across,
    )


class Layer:
    def __init__(self):
        self.parts = []
        self.textured = []

    def add(self, mesh, color, name):
        self.parts.append((name, mesh, COLORS[color]))

    def add_textured(self, mesh, name):
        self.textured.append((name, mesh))

    def export(self, path):
        scene = trimesh.Scene()
        transform = enu_to_gltf()
        for index, (name, mesh, color) in enumerate(self.parts):
            mesh = mesh.copy()
            mesh.visual = trimesh.visual.TextureVisuals(
                material=trimesh.visual.material.PBRMaterial(
                    name=f"{name}_material",
                    baseColorFactor=[*(int(c * 255) for c in color), 255],
                    metallicFactor=0.0,
                    roughnessFactor=0.8,
                )
            )
            mesh.apply_transform(transform)
            scene.add_geometry(mesh, geom_name=f"{name}__{index}", node_name=f"{name}__{index}")
        for index, (name, mesh) in enumerate(self.textured):
            mesh = mesh.copy()
            mesh.apply_transform(transform)
            scene.add_geometry(mesh, geom_name=f"{name}__{index}", node_name=f"{name}__{index}")
        scene.export(path)


def font(size):
    for candidate in LATIN_FONTS:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw_centered(draw, text, y, image_width, font_obj, fill):
    kwargs = {"font": font_obj, "fill": fill}
    if pil_feature_check("raqm"):
        kwargs["direction"] = "ltr"
    measure_kwargs = {k: v for k, v in kwargs.items() if k != "fill"}
    bounds = draw.textbbox((0, 0), text, **measure_kwargs)
    draw.text(((image_width - (bounds[2] - bounds[0])) / 2, y), text, **kwargs)


def number_board_texture(number):
    """White platform-number board; original layout, no copied pixels."""
    image = Image.new("RGB", (512, 288), (245, 244, 238))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 503, 279), outline=(15, 15, 14), width=10)
    draw_centered(draw, str(number), 30, 512, font(150), (15, 15, 14))
    draw_centered(draw, "CHROMPET", 205, 512, font(52), (15, 15, 14))
    return image


def text_plane(image, width, height):
    vertices = np.array(
        [[-width / 2, 0, 0], [width / 2, 0, 0], [width / 2, 0, height], [-width / 2, 0, height]],
        dtype=float,
    )
    faces = np.array([[0, 2, 1], [0, 3, 2], [0, 1, 2], [0, 2, 3]])
    # u runs opposite to +x so a viewer in front sees the text unmirrored
    # (same render-verified mapping as tools/chrompet_identity.py).
    uv = np.array([[1, 0], [0, 0], [0, 1], [1, 1]], dtype=float)
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=uv,
        material=trimesh.visual.material.PBRMaterial(
            name="Station_number_board",
            baseColorTexture=image,
            metallicFactor=0.0,
            roughnessFactor=0.8,
        ),
    )
    return mesh


def add_edge_and_tactile(layer, number):
    """Full-length edge warning line + tactile strip on both platform edges."""
    for side in (-1, 1):
        x, y = along(number, 0.0, side * (HALF_WIDTH - 0.28))
        layer.add(
            box(x, y, (HALF_LENGTH - 2) * 2, 0.40, 0.02, TRACK_YAW, PLATFORM_TOP),
            "line_white",
            f"Station_edge_line_P{number}",
        )
        x, y = along(number, 0.0, side * (HALF_WIDTH - 0.88))
        layer.add(
            box(x, y, (HALF_LENGTH - 2) * 2, 0.30, 0.025, TRACK_YAW, PLATFORM_TOP),
            "tactile_yellow",
            f"Station_tactile_strip_P{number}",
        )


def add_bench(layer, number, offset_along, offset_across):
    """Steel-framed bench, seat toward the platform centre."""
    x, y = along(number, offset_along, offset_across)
    seat = box(x, y, 1.8, 0.45, 0.08, TRACK_YAW, PLATFORM_TOP + 0.42)
    ax, ay = math.cos(TRACK_YAW), math.sin(TRACK_YAW)
    nx, ny = -math.sin(TRACK_YAW), math.cos(TRACK_YAW)
    back_dir = 1 if offset_across < 0 else -1  # backrest away from the edge
    back = box(
        x + nx * back_dir * 0.21, y + ny * back_dir * 0.21,
        1.8, 0.06, 0.55, TRACK_YAW, PLATFORM_TOP + 0.50,
    )
    legs = [
        box(
            x + ax * along_off + nx * lat_off, y + ay * along_off + ny * lat_off,
            0.06, 0.06, 0.42, TRACK_YAW, PLATFORM_TOP,
        )
        for along_off in (-0.78, 0.0, 0.78)
        for lat_off in (-0.16, 0.16)
    ]
    layer.add(trimesh.util.concatenate([seat, back]), "bench_blue", f"Station_bench_seat_P{number}")
    layer.add(trimesh.util.concatenate(legs), "steel", f"Station_bench_frame_P{number}")


def add_number_board(layer, number, offset_along):
    """Double-sided platform-number board hung from the canopy."""
    x, y = along(number, offset_along, 0.0)
    bottom = 3.40
    frame = box(x, y, 1.70, 0.12, 1.00, BOARD_YAW, bottom)
    rods = []
    px, py = -math.sin(BOARD_YAW), math.cos(BOARD_YAW)  # board normal (along track)
    ax, ay = math.cos(BOARD_YAW), math.sin(BOARD_YAW)   # across track
    for side in (-1, 1):
        rods.append(
            cylinder(x + ax * side * 0.6, y + ay * side * 0.6, 0.02, CANOPY_UNDER - bottom - 0.9, bottom + 0.9, 8)
        )
    layer.add(trimesh.util.concatenate([frame, *rods]), "board_black", f"Station_board_P{number}")
    texture = number_board_texture(number)
    front = text_plane(texture, 1.58, 0.90)
    back = text_plane(texture, 1.58, 0.90)
    layer.add_textured(
        place(front, x + px * 0.065, y + py * 0.065, bottom + 0.05, BOARD_YAW),
        f"Station_board_P{number}_front",
    )
    layer.add_textured(
        place(back, x - px * 0.065, y - py * 0.065, bottom + 0.05, BOARD_YAW + math.pi),
        f"Station_board_P{number}_back",
    )


def add_light(layer, number, offset_along):
    """Under-canopy tube light on two drop rods."""
    x, y = along(number, offset_along, 0.0)
    tube = box(x, y, 1.2, 0.12, 0.06, TRACK_YAW, 4.55)
    ax, ay = math.cos(TRACK_YAW), math.sin(TRACK_YAW)
    rods = [
        cylinder(x + ax * side * 0.45, y + ay * side * 0.45, 0.015, CANOPY_UNDER - 4.61, 4.61, 8)
        for side in (-1, 1)
    ]
    layer.add(trimesh.util.concatenate([tube, *rods]), "lamp_white", f"Station_light_P{number}")


def add_stairs(layer, number):
    """Straight stair flight along the platform up to the FOB deck.

    Rise PLATFORM_TOP -> FOB_DECK_TOP over a ~10 m along-track run with a
    central landing; two stringer walls. Approximate: the roads-layer FOB
    deck overhangs the platforms here, exact historic stair geometry is
    not in OSM. Used by the station journey route (data/journey_route.json).
    """
    cx, cy = STAIRS[number]
    rise = FOB_DECK_TOP - PLATFORM_TOP          # 5.85
    steps = 36
    step_h = rise / steps                        # ~0.163
    run = 10.0
    step_d = run / steps
    width = 1.6
    ux, uy = TRACK_U
    base_x = cx - ux * run / 2
    base_y = cy - uy * run / 2
    parts = []
    for i in range(steps):
        sx = base_x + ux * (i + 0.5) * step_d
        sy = base_y + uy * (i + 0.5) * step_d
        parts.append(box(sx, sy, step_d + 0.02, width, step_h, TRACK_YAW, PLATFORM_TOP + i * step_h))
    # Stringer walls (thin boxes following the flight as stacked slabs).
    nx, ny = -uy, ux
    for side in (-1, 1):
        for i in range(0, steps, 4):
            sx = base_x + ux * (i + 2) * step_d + nx * side * (width / 2 + 0.04)
            sy = base_y + uy * (i + 2) * step_d + ny * side * (width / 2 + 0.04)
            h = (i + 4) * step_h + 0.5
            parts.append(box(sx, sy, 4 * step_d + 0.02, 0.08, h, TRACK_YAW, PLATFORM_TOP))
    layer.add(trimesh.util.concatenate(parts), "column" if "column" in COLORS else "steel", f"Station_stairs_P{number}")


def add_dustbin(layer, number, offset_along, offset_across):
    x, y = along(number, offset_along, offset_across)
    body = cylinder(x, y, 0.28, 0.70, PLATFORM_TOP, 12)
    rim = cylinder(x, y, 0.30, 0.06, PLATFORM_TOP + 0.70, 12)
    layer.add(trimesh.util.concatenate([body, rim]), "bin_green", f"Station_dustbin_P{number}")


def main():
    layer = Layer()
    for number in (1, 2):
        add_edge_and_tactile(layer, number)
        add_stairs(layer, number)
        for index, offset_along in enumerate((-140, -100, -60, -20, 20, 60, 100, 140)):
            add_bench(layer, number, offset_along, 1.6 if index % 2 == 0 else -1.6)
        for offset_along in (-100, 0, 100):
            add_number_board(layer, number, offset_along)
        for offset_along in (-140, -100, -60, -20, 20, 60, 100, 140):
            add_light(layer, number, offset_along)
        for index, offset_along in enumerate((-120, -40, 40, 120)):
            add_dustbin(layer, number, offset_along, -2.4 if index % 2 == 0 else 2.4)

    out_path = os.path.join(ROOT, "props", "chrompet_station_details.glb")
    layer.export(out_path)

    loaded = trimesh.load(out_path)
    geometries = list(loaded.geometry.values())
    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres), origin 12.9487N 80.1394E; WORLD-POSITIONED",
        "placement": "SITED (approximate, source: roads_geometry): platform slab centres, axis, top and canopy heights measured from roads/roads_v2.glb 'Chromepet_station' nodes on 2026-10-31; constants baked in the generator docstring.",
        "provenance": "Original procedural geometry; station layout derives from OpenStreetMap data (ODbL) via the repo's own roads layer. Board artwork is original, not copied signage.",
        "generator": "tools/station_details.py",
        "output": "props/chrompet_station_details.glb",
        "station_constants_enu": {
            "platforms": {str(k): list(v) for k, v in PLATFORMS.items()},
            "track_axis_enu": list(TRACK_U),
            "half_length_m": HALF_LENGTH,
            "half_width_m": HALF_WIDTH,
            "platform_top_m": PLATFORM_TOP,
            "canopy_underside_m": CANOPY_UNDER,
        },
        "contents": {
            "edge_warning_lines": 4,
            "tactile_strips": 4,
            "benches": 16,
            "number_boards": 6,
            "tube_lights": 16,
            "dustbins": 8,
            "fob_staircases": 2,
        },
        "glb_stats": {
            "geometries": len(geometries),
            "vertices": int(sum(len(g.vertices) for g in geometries)),
            "faces": int(sum(len(g.faces) for g in geometries)),
            "bounds_gltf": [[round(float(v), 2) for v in row] for row in loaded.bounds.tolist()],
        },
        "integration": "Registered in ChromepetSync.Glbs (world-positioned). Registry: data/placement_map.json (id chrompet_station_details).",
    }
    with open(os.path.join(ROOT, "data", "station_details_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
