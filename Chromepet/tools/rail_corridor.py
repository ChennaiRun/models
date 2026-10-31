"""Chennai suburban rail corridor: Guindy <-> Vandalur -- additive layer.

Builds the Beach-Chengalpattu south-line corridor through the Chromepet
area: two broad-gauge running tracks with ballast bed and OHE masts, a
ground strip under the corridor outside the area bbox, and station
models (side platforms, canopy, trilingual nameboards) at:

* Guindy (OSM node 13.0086685 N, 80.2126063 E)                -- detailed
* Pallavaram (12.96757, 80.15205)                             -- detailed
* Tambaram Sanatorium (12.93696, 80.13070)                    -- detailed
* Vandalur (12.89161, 80.08497)                               -- detailed
* Minor platforms + board at the intermediate suburban stations:
  Saint Thomas Mount, Palavanthangal, Meenambakkam, Tirusulam,
  Tambaram, Perungalattur.

Chrompet itself is NOT rebuilt -- it already exists in roads_v2.glb +
chrompet_identity.glb; the corridor tracks thread through it.

Alignment: Catmull-Rom spline through the OSM railway=station node
coordinates (the line passes every station; station chain documented in
STATIONS below, fetched from Overpass 2026-10-31, ODbL -- provenance
copy at data/rail_corridor.osm). Rails/ballast/OHE are clipped out of
the area bbox (north -1526..+1258 m) because roads_v2.glb already
carries the railway there; stations inside the bbox (Sanatorium) still
get platforms since roads_v2 models none.

Track: 2 running lines, centres +-2.35 m, broad gauge 1.676 m, rails
0.17 m tall on a 0.25 m ballast bed (rail top ~0.42 m, matching the
roads-layer railway). OHE masts ~7 m, alternating sides every 60 m
(existing roads-layer OHE height is 7.0 m).

World frame: metres, x=east, y=up, z=-north, origin 12.9487 N
80.1394 E (v2 frame). WORLD-POSITIONED: load at identity. All
placements derive from OSM node coordinates (ODbL); station
architecture is an original low-poly interpretation, not surveyed.

Run from Chromepet/:  python3 tools/rail_corridor.py
Dependencies: trimesh, numpy, pillow
Output: props/rail_corridor.glb + data/rail_corridor_meta.json
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

ORIGIN_LAT, ORIGIN_LON = 12.9487, 80.1394
EARTH_R = 6378137.0

# Area bbox in ENU metres (12.935-12.960 N): roads_v2.glb already
# carries railway + OHE inside this band, so corridor rails skip it.
AREA_NORTH_MIN, AREA_NORTH_MAX = -1526.0, 1258.0

# Suburban station chain, north to south (OSM railway=station nodes,
# Overpass 2026-10-31). kind: detailed = platforms+canopy+boards,
# minor = platforms+one board, none = alignment only (already modelled).
STATIONS = [
    {"name": "Guindy", "ta": "கிண்டி", "hi": "गिंडी", "lat": 13.0086685, "lon": 80.2126063, "kind": "detailed"},
    {"name": "Saint Thomas Mount", "ta": "பரங்கிமலை", "hi": "सेंट थॉमस माउंट", "lat": 12.9947654, "lon": 80.1993715, "kind": "minor"},
    {"name": "Palavanthangal", "ta": "பழவந்தாங்கல்", "hi": "पलवन्तंगल", "lat": 12.9906385, "lon": 80.1879401, "kind": "minor"},
    {"name": "Meenambakkam", "ta": "மீனம்பாக்கம்", "hi": "मीनम्बाक्कम", "lat": 12.98767, "lon": 80.17648, "kind": "minor"},
    {"name": "Tirusulam", "ta": "திருசூலம்", "hi": "तिरसूलम", "lat": 12.98046, "lon": 80.16579, "kind": "minor"},
    {"name": "Pallavaram", "ta": "பல்லாவரம்", "hi": "पल्लावरम", "lat": 12.96757, "lon": 80.15205, "kind": "detailed"},
    {"name": "Chrompet", "ta": "குரோம்பேட்டை", "hi": "क्रोमपेट", "lat": 12.95219, "lon": 80.14117, "kind": "none"},
    {"name": "Tambaram Sanatorium", "ta": "தாம்பரம் சானடோரியம்", "hi": "टाम्बरम सैनेटोरियम", "lat": 12.93696, "lon": 80.13070, "kind": "detailed"},
    {"name": "Tambaram", "ta": "தாம்பரம்", "hi": "टाम्बरम", "lat": 12.92579, "lon": 80.11792, "kind": "minor"},
    {"name": "Perungalattur", "ta": "பெருங்களத்தூர்", "hi": "पेरूंगलत्तूर", "lat": 12.90524, "lon": 80.09505, "kind": "minor"},
    {"name": "Vandalur", "ta": "வண்டலூர்", "hi": "वंडलूर", "lat": 12.89161, "lon": 80.08497, "kind": "detailed"},
]

TRACK_HALF = 2.35        # running-line centre offset from corridor axis
GAUGE = 1.676
RAIL_W, RAIL_H = 0.075, 0.17
BALLAST_W, BALLAST_H = 11.0, 0.25
PLATFORM_TOP = 0.95
PLATFORM_LEN, PLATFORM_W = 240.0, 7.5
PLATFORM_EDGE = TRACK_HALF + 1.9   # inner edge offset from axis
OHE_H = 7.0

COLORS = {
    "ballast": (0.42, 0.40, 0.38),
    "rail": (0.55, 0.55, 0.58),
    "ground_strip": (0.32, 0.36, 0.26),
    "platform": (0.62, 0.60, 0.56),
    "platform_edge_white": (0.92, 0.92, 0.88),
    "canopy": (0.55, 0.16, 0.14),
    "column": (0.75, 0.73, 0.70),
    "ohe": (0.35, 0.35, 0.38),
    "board_post": (0.08, 0.08, 0.08),
    "station_yellow": (0.91, 0.66, 0.16),
}

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


def local_xy(lat, lon):
    x = math.radians(lon - ORIGIN_LON) * EARTH_R * math.cos(math.radians(ORIGIN_LAT))
    y = math.radians(lat - ORIGIN_LAT) * EARTH_R
    return np.array([x, y])


def catmull_rom(points, samples_per_seg=14):
    """Uniform Catmull-Rom spline through ENU points."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = (np.array(p) for p in (pts[i - 1], pts[i], pts[i + 1], pts[i + 2]))
        for t in np.linspace(0, 1, samples_per_seg, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(
                0.5
                * (
                    (2 * p1)
                    + (-p0 + p2) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
                )
            )
    out.append(np.array(points[-1]))
    return out


def enu_to_gltf():
    return np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)


def box_between(p0, p1, width, height, z0):
    """Box beam between two ENU points, base at z0 (built z-up)."""
    (x0, y0), (x1, y1) = p0, p1
    length = math.hypot(x1 - x0, y1 - y0) + width * 0.5  # slight overlap at joints
    mesh = trimesh.creation.box(extents=[length, width, height])
    mesh.apply_translation([0, 0, height / 2])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.atan2(y1 - y0, x1 - x0), [0, 0, 1]))
    mesh.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, z0])
    return mesh


def offset_point(p, u, off):
    return (p[0] + u[0] * off, p[1] + u[1] * off)


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
                    metallicFactor=0.1 if color == COLORS["rail"] else 0.0,
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


def font(candidates, size):
    for candidate in candidates:
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


def station_sign_texture(tamil, hindi, latin):
    """Yellow suburban nameboard; original layout, no copied pixels."""
    image = Image.new("RGB", (1024, 512), (232, 168, 41))
    draw = ImageDraw.Draw(image)
    draw.rectangle((12, 12, 1011, 499), outline=(20, 20, 18), width=18)
    draw_centered(draw, tamil, 25, 1024, font(TAMIL_FONTS, 110), (15, 15, 14))
    draw_centered(draw, hindi, 170, 1024, font(DEVANAGARI_FONTS, 100), (15, 15, 14))
    draw_centered(draw, latin.upper(), 312, 1024, font(LATIN_FONTS, 100), (15, 15, 14))
    return image


def text_plane(image, width, height):
    vertices = np.array(
        [[-width / 2, 0, 0], [width / 2, 0, 0], [width / 2, 0, height], [-width / 2, 0, height]],
        dtype=float,
    )
    faces = np.array([[0, 2, 1], [0, 3, 2], [0, 1, 2], [0, 2, 3]])
    # u runs opposite to +x so a viewer in front sees the text unmirrored
    # (render-verified mapping from tools/chrompet_identity.py).
    uv = np.array([[1, 0], [0, 0], [0, 1], [1, 1]], dtype=float)
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=uv,
        material=trimesh.visual.material.PBRMaterial(
            name="Corridor_station_sign",
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


def add_name_board(layer, x, y, yaw, station, name):
    """Freestanding yellow trilingual board on striped posts (identity style)."""
    board_w, board_h, bottom = 4.6, 2.05, PLATFORM_TOP + 1.6
    frame = trimesh.creation.box(extents=[board_w + 0.18, 0.20, board_h + 0.18])
    frame.apply_translation([0, 0, bottom + board_h / 2])
    parts = [frame]
    for side in (-1, 1):
        post = trimesh.creation.cylinder(radius=0.12, height=bottom + board_h + 0.1, sections=10)
        post.apply_translation([side * (board_w / 2 - 0.3), 0, (bottom + board_h + 0.1) / 2])
        parts.append(post)
    group = trimesh.util.concatenate(parts)
    group.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
    group.apply_translation([x, y, 0])
    layer.add(group, "board_post", name)

    texture = station_sign_texture(station["ta"], station["hi"], station["name"])
    px, py = -math.sin(yaw), math.cos(yaw)
    front = text_plane(texture, board_w - 0.16, board_h - 0.16)
    back = text_plane(texture, board_w - 0.16, board_h - 0.16)
    layer.add_textured(place(front, x + px * 0.126, y + py * 0.126, bottom + 0.06, yaw), f"{name}_front")
    layer.add_textured(place(back, x - px * 0.126, y - py * 0.126, bottom + 0.06, yaw + math.pi), f"{name}_back")


def build_station(layer, station, centre, tangent):
    """Two side platforms aligned to the local tangent; canopy + boards."""
    name_key = station["name"].replace(" ", "_")
    u = tangent / np.linalg.norm(tangent)
    n = np.array([-u[1], u[0]])
    yaw = math.atan2(u[1], u[0])
    half = PLATFORM_LEN / 2
    board_count = 0
    for side in (-1, 1):
        off = PLATFORM_EDGE + PLATFORM_W / 2
        c = centre + n * (side * off)
        slab = trimesh.creation.box(extents=[PLATFORM_LEN, PLATFORM_W, PLATFORM_TOP])
        slab.apply_translation([0, 0, PLATFORM_TOP / 2])
        slab.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
        slab.apply_translation([c[0], c[1], 0])
        layer.add(slab, "platform", f"Corridor_platform_{name_key}")
        # White edge line on the track side (local -y is the track side for
        # side=+1 and +y for side=-1 because the platform centre is offset out).
        line = trimesh.creation.box(extents=[PLATFORM_LEN - 4, 0.4, 0.02])
        line.apply_translation([0, -side * (PLATFORM_W / 2 - 0.28), PLATFORM_TOP + 0.01])
        line.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
        line.apply_translation([c[0], c[1], 0])
        layer.add(line, "platform_edge_white", f"Corridor_edge_line_{name_key}")

        if station["kind"] == "detailed":
            # Canopy over the middle 140 m on a centre column row.
            canopy_len = 140.0
            roof = trimesh.creation.box(extents=[canopy_len, PLATFORM_W - 0.6, 0.2])
            roof.apply_translation([0, 0, 5.1])
            columns = []
            for k in range(-6, 7):
                col = trimesh.creation.cylinder(radius=0.15, height=5.0, sections=10)
                col.apply_translation([k * canopy_len / 13, 0, PLATFORM_TOP + 2.5])
                columns.append(col)
            canopy = trimesh.util.concatenate([roof] + columns)
            canopy.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]))
            canopy.apply_translation([c[0], c[1], 0])
            layer.add(canopy, "canopy", f"Corridor_canopy_{name_key}")
            # One nameboard per platform at opposite quarter points.
            quarter = half / 2 * side
            bx, by = c[0] + u[0] * quarter, c[1] + u[1] * quarter
            add_name_board(layer, bx, by, yaw, station, f"Corridor_board_{name_key}_{board_count}")
            board_count += 1
        else:
            # Minor station: single board on the south-bound platform.
            if side == 1:
                add_name_board(layer, c[0], c[1], yaw, station, f"Corridor_board_{name_key}")


def in_area_band(north):
    return AREA_NORTH_MIN <= north <= AREA_NORTH_MAX


def main():
    layer = Layer()
    chain = [local_xy(s["lat"], s["lon"]) for s in STATIONS]
    spline = catmull_rom(chain, samples_per_seg=14)

    # Tangent/normal per spline point.
    tangents = []
    for i, p in enumerate(spline):
        a = spline[max(0, i - 1)]
        b = spline[min(len(spline) - 1, i + 1)]
        t = b - a
        tangents.append(t / np.linalg.norm(t))

    # Corridor furniture: rails, ballast, ground strip, OHE masts.
    rails, ballast, ground, ohes = [], [], [], []
    ohe_acc = 0.0
    for i in range(len(spline) - 1):
        p0, p1 = spline[i], spline[i + 1]
        mid_north = (p0[1] + p1[1]) / 2
        if in_area_band(mid_north):
            continue  # roads_v2.glb already carries the railway here
        u = tangents[i]
        n = np.array([-u[1], u[0]])
        ground.append(box_between(p0, p1, 30.0, 0.1, -0.12))
        ballast.append(box_between(p0, p1, BALLAST_W, BALLAST_H, 0.0))
        for track_off in (-TRACK_HALF, TRACK_HALF):
            for rail_off in (-GAUGE / 2, GAUGE / 2):
                off = track_off + rail_off
                rails.append(
                    box_between(offset_point(p0, n, off), offset_point(p1, n, off), RAIL_W, RAIL_H, BALLAST_H)
                )
        seg_len = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        ohe_acc += seg_len
        if ohe_acc >= 60.0:
            ohe_acc = 0.0
            side = 1 if len(ohes) % 2 == 0 else -1
            base = offset_point(p0, n, side * (TRACK_HALF + 3.2))
            mast = trimesh.creation.cylinder(radius=0.14, height=OHE_H, sections=8)
            mast.apply_translation([base[0], base[1], OHE_H / 2])
            # Cantilever boom over the nearest track.
            boom = trimesh.creation.box(extents=[0.12, TRACK_HALF + 3.2 + 1.0, 0.12])
            boom.apply_translation([0, (-side) * (TRACK_HALF + 3.2 + 1.0) / 2, OHE_H - 0.4])
            boom.apply_transform(
                trimesh.transformations.rotation_matrix(math.atan2(u[1], u[0]), [0, 0, 1])
            )
            boom.apply_translation([base[0], base[1], 0])
            ohes.append(trimesh.util.concatenate([mast, boom]))

    layer.add(trimesh.util.concatenate(ground), "ground_strip", "Corridor_ground_strip")
    layer.add(trimesh.util.concatenate(ballast), "ballast", "Corridor_ballast")
    layer.add(trimesh.util.concatenate(rails), "rail", "Corridor_rails")
    if ohes:
        layer.add(trimesh.util.concatenate(ohes), "ohe", "Corridor_OHE")

    # Stations: nearest spline index gives the local tangent.
    spline_arr = np.array(spline)
    for station in STATIONS:
        if station["kind"] == "none":
            continue
        centre = local_xy(station["lat"], station["lon"])
        idx = int(np.argmin(np.linalg.norm(spline_arr - centre, axis=1)))
        build_station(layer, station, spline_arr[idx], tangents[idx])

    out_path = os.path.join(ROOT, "props", "rail_corridor.glb")
    layer.export(out_path)

    loaded = trimesh.load(out_path)
    geometries = list(loaded.geometry.values())
    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres), origin 12.9487N 80.1394E; WORLD-POSITIONED",
        "placement": "OSM-derived: Catmull-Rom alignment through the railway=station node chain listed in the generator (Overpass 2026-10-31, ODbL; provenance data/rail_corridor.osm). Rails/ballast/OHE clipped out of north -1526..+1258 m where roads_v2.glb already carries the railway.",
        "provenance": "Geometry from OpenStreetMap data (ODbL). Station architecture and board artwork are original procedural interpretations, not surveyed and not copied signage.",
        "generator": "tools/rail_corridor.py",
        "output": "props/rail_corridor.glb",
        "stations": [
            {
                "name": s["name"],
                "lat_lon": [s["lat"], s["lon"]],
                "enu": [round(float(v), 2) for v in local_xy(s["lat"], s["lon"])],
                "kind": s["kind"],
            }
            for s in STATIONS
        ],
        "track": {
            "running_lines": 2,
            "track_centres_m": [-TRACK_HALF, TRACK_HALF],
            "gauge_m": GAUGE,
            "ballast_width_m": BALLAST_W,
            "ohe_height_m": OHE_H,
        },
        "glb_stats": {
            "geometries": len(geometries),
            "vertices": int(sum(len(g.vertices) for g in geometries)),
            "faces": int(sum(len(g.faces) for g in geometries)),
            "bounds_gltf": [[round(float(v), 2) for v in row] for row in loaded.bounds.tolist()],
        },
        "integration": "Registered in ChromepetSync.Glbs (world-positioned). Registry: data/placement_map.json (id rail_corridor).",
    }
    with open(os.path.join(ROOT, "data", "rail_corridor_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(meta["glb_stats"], indent=2))
    print("stations:", len([s for s in STATIONS if s["kind"] != "none"]))


if __name__ == "__main__":
    main()
