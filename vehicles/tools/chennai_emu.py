"""Chennai Suburban 9-car EMU rake (ICF-built WAU-4 type, cream-and-green livery).

Writes ../chennai_emu/chennai_suburban_emu.glb and ../chennai_emu/chennai_suburban_emu.json.
Run from the repository root:  python3 vehicles/tools/chennai_emu.py
Dependencies: trimesh, numpy, pillow.

Frame: metres, +Y up, +Z = leading cab, +X = train left, y = 0 top of rail,
origin at the rake centre on the track centreline. Broad gauge (1676 mm).
Each coach is a child node whose origin is its own centre at rail level.

Original procedural geometry interpreted from openly licensed photos listed
in ../REFERENCE_MEDIA.md; no photo pixels are used.
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transit_common import (  # noqa: E402
    LATIN_FONTS, Palette, VehicleBuilder, beam, box, cap_mesh, collider_box, cyl_x, cyl_y,
    cyl_z, decal, draw_text, fit_font, led_board, loft, scene_stats, side_profile, textured,
    write_meta,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "chennai_emu")

CAR_LEN = 20.73          # ICF EMU body length
HALF_W = 1.83            # 3.66 m wide EMU body
SOLE_Y = 1.05            # bottom of body side (solebar)
FLOOR_Y = 1.27
ROOF_Y = 3.88            # roof height above rail
ROOF_R = 0.62
GREEN_TOP = 1.95
GAP = 0.75               # coupled gap between bodies
BOGIE_CENTRES = 14.63
BOGIE_WHEELBASE = 2.896
WHEEL_R = 0.476          # 952 mm new wheel
GAUGE = 1.676
CONSIST = ["MC", "TC", "TC", "MC", "TC", "TC", "TC", "TC", "MC"]
CAB_DIR = [+1, 0, 0, +1, 0, 0, 0, 0, -1]
DESTINATION = "TAMBARAM"
UNIT_NUMBERS = ["12201", "12202", "12203", "12204", "12205", "12206", "12207", "12208", "12209"]

PALETTE = Palette({
    "emu_cream": ((0.89, 0.85, 0.58), 0.05, 0.55),
    "emu_green": ((0.06, 0.29, 0.21), 0.05, 0.5),
    "roof_grey": ((0.60, 0.61, 0.60), 0.3, 0.6),
    "interior_dark": ((0.07, 0.07, 0.06), 0.0, 0.9),
    "window_dark": ((0.10, 0.12, 0.12), 0.2, 0.2),
    "bar_grey": ((0.70, 0.70, 0.66), 0.5, 0.5),
    "underframe": ((0.07, 0.07, 0.07), 0.2, 0.85),
    "wheel_steel": ((0.36, 0.36, 0.37), 0.8, 0.45),
    "buffer_white": ((0.92, 0.92, 0.90), 0.0, 0.5),
    "lamp_white": ((0.96, 0.96, 0.90), 0.0, 0.2),
    "tail_red": ((0.75, 0.05, 0.04), 0.0, 0.3),
    "insulator": ((0.55, 0.30, 0.18), 0.0, 0.4),
    "panto_steel": ((0.25, 0.26, 0.27), 0.7, 0.4),
    "collider": ((1.0, 0.0, 1.0), 0.0, 1.0),
})


def rgb255(name):
    return tuple(int(c * 255) for c in PALETTE.rgb(name))


def cab_front_texture(number):
    """Cream cab front with the characteristic green 'V', windscreen and number."""
    ppm = 200
    w, h = int(2 * HALF_W * ppm), int((ROOF_Y - SOLE_Y) * ppm)

    def px(x, y):
        return ((x + HALF_W) * ppm, (ROOF_Y - y) * ppm)

    img = Image.new("RGB", (w, h), rgb255("emu_cream"))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, px(0, 3.50)[1]), fill=rgb255("roof_grey"))  # roof dome
    d.polygon([px(-HALF_W, GREEN_TOP + 0.1), px(0, 1.42), px(HALF_W, GREEN_TOP + 0.1),
               px(HALF_W, SOLE_Y), px(-HALF_W, SOLE_Y)], fill=rgb255("emu_green"))
    # Windscreen with red LED destination in its upper part.
    x0, y0 = px(-1.42, 3.32)
    x1, y1 = px(1.42, 2.62)
    d.rounded_rectangle((x0, y0, x1, y1), radius=10, fill=(22, 26, 26), outline=(40, 40, 36), width=6)
    led = led_board(DESTINATION, (int((x1 - x0) * 0.55), 44), color=(255, 40, 30), bg=(22, 26, 26))
    img.paste(led, (int((x0 + x1) / 2 - led.width / 2), int(y0 + 10)))
    # Unit number plate.
    nx0, ny0 = px(-0.48, 2.50)
    nx1, ny1 = px(0.48, 2.24)
    d.rectangle((nx0, ny0, nx1, ny1), fill=(230, 214, 160), outline=(120, 100, 60), width=3)
    draw_text(d, ((nx0 + nx1) / 2, (ny0 + ny1) / 2), number,
              fit_font(d, number, LATIN_FONTS, int(nx1 - nx0 - 16), int(ny1 - ny0 - 10)), (150, 40, 30))
    return img


def coach_number_texture(text):
    img = Image.new("RGB", (384, 96), rgb255("emu_cream"))
    d = ImageDraw.Draw(img)
    draw_text(d, (192, 48), text, fit_font(d, text, LATIN_FONTS, 360, 64), (25, 25, 22))
    return img


def body_sections(cab):
    pts, keys = side_profile(HALF_W, SOLE_Y, [(GREEN_TOP, "emu_green"), (ROOF_Y - ROOF_R, "emu_cream")],
                             ROOF_Y, ROOF_R, roof_segments=8)
    zf, zr = CAR_LEN / 2, -CAR_LEN / 2

    def rounded_end(scale):
        p = pts.copy()
        p[:, 0] *= scale
        return p

    front = [(zf - 0.10, pts), (zf, rounded_end(0.985))]
    rear = [(zr, rounded_end(0.985)), (zr + 0.10, pts)]
    return rear + front, keys


def resolve(key):
    return {"__bottom__": "underframe", "__shoulder__": "roof_grey", "__roof__": "roof_grey"}.get(key, key)


def bogie(parts, zc):
    """ICF-style bogie: two wheelsets, side frames, bolster."""
    for dz in (-BOGIE_WHEELBASE / 2, BOGIE_WHEELBASE / 2):
        z = zc + dz
        for side in (-1, 1):
            parts.append(("wheel_steel", cyl_x(side * (GAUGE / 2 - 0.0), WHEEL_R, z, WHEEL_R, 0.13, 18)))
        parts.append(("underframe", cyl_x(0, WHEEL_R, z, 0.09, GAUGE + 0.2, 10)))
        for side in (-1, 1):  # axle boxes
            parts.append(("underframe", box(side * 1.0 - 0.12, side * 1.0 + 0.12, 0.33, 0.62, z - 0.18, z + 0.18)))
    for side in (-1, 1):
        parts.append(("underframe", box(side * 1.0 - 0.09, side * 1.0 + 0.09, 0.55, 0.85, zc - 2.0, zc + 2.0)))
        # Coil springs represented as short cylinders.
        for dz in (-0.9, 0.9):
            parts.append(("panto_steel", cyl_y(side * 1.0, 0.85, zc + dz, 0.12, 0.18, 10)))
    parts.append(("underframe", box(-1.1, 1.1, 0.80, 1.0, zc - 0.35, zc + 0.35)))


def diamond_pantograph(parts, z):
    base_y = ROOF_Y + 0.05
    parts.append(("panto_steel", box(-0.9, 0.9, ROOF_Y - 0.02, base_y, z - 0.9, z + 0.9)))
    for sx in (-0.75, 0.75):
        for sz in (-0.75, 0.75):
            parts.append(("insulator", cyl_y(sx, ROOF_Y - 0.02, z + sz, 0.07, 0.30, 10)))
    top = ROOF_Y + 1.55
    mid = ROOF_Y + 0.85
    frame_y = base_y + 0.30
    for sx in (-0.55, 0.55):
        lo_a, lo_b = (sx, frame_y, z - 0.75), (sx, frame_y, z + 0.75)
        mid_a, mid_b = (sx * 0.85, mid, z - 0.55), (sx * 0.85, mid, z + 0.55)
        top_p = (sx * 0.6, top, z)
        for a, b in ((lo_a, mid_b), (lo_b, mid_a), (mid_b, top_p), (mid_a, top_p), (lo_a, lo_b)):
            parts.append(("panto_steel", beam(a, b, 0.025, 6)))
    parts.append(("panto_steel", beam((-0.95, top + 0.02, z), (0.95, top + 0.02, z), 0.035, 8)))   # pan head
    parts.append(("panto_steel", beam((-0.55, top, z), (0.55, top, z), 0.02, 6)))


def coach(kind, cab_dir, number):
    """Return (solid parts [(mat, mesh)], textured parts [(name, mesh)]) in car-local frame
    built with the cab (if any) at +Z; caller rotates for cab_dir == -1."""
    parts, tex = [], []
    sections, keys = body_sections(cab_dir != 0)
    for mat, mesh in loft(sections, keys, resolve).items():
        parts.append((mat, mesh))
    zf, zr = CAR_LEN / 2, -CAR_LEN / 2
    front_pts, rear_pts = sections[-1][1], sections[0][1]
    rear_cap, _ = cap_mesh(rear_pts, zr, -1)
    parts.append(("emu_cream", rear_cap))
    if cab_dir:
        cap, uv = cap_mesh(front_pts, zf, +1)
        tex.append(("cab_front", textured(cap, uv, cab_front_texture(number), f"EMU_cab_front_{number}")))
    else:
        cap, _ = cap_mesh(front_pts, zf, +1)
        parts.append(("emu_cream", cap))

    # Side openings: open doorways (no doors on these EMUs), barred windows.
    if kind == "MC":
        doors = [(-7.6, 1.25), (1.2, 1.25)]
        crew = [(zf - 1.55, 0.70)]
        louvre = (zf - 6.2, zf - 2.2)
    else:
        doors = [(-7.6, 1.25), (0.0, 1.25), (7.6, 1.25)]
        crew, louvre = [], None
    windows = []
    door_spans = [(c - w / 2, c + w / 2) for c, w in doors + crew]
    z = zr + 1.2
    while z < zf - 0.9:
        blocked = any(a - 0.85 < z < b + 0.85 for a, b in door_spans)
        if louvre and louvre[0] - 0.6 < z < louvre[1] + 0.6:
            blocked = True
        if not blocked:
            windows.append(z)
        z += 1.55
    for side in (-1, 1):
        xo = side * HALF_W

        def slab(y0, y1, z0, z1, depth=0.012):
            x0, x1 = sorted((xo, xo + side * depth))
            return box(x0, x1, y0, y1, z0, z1)

        for c, w in doors:
            parts.append(("interior_dark", slab(FLOOR_Y - 0.12, 3.18, c - w / 2, c + w / 2)))
            parts.append(("bar_grey", slab(1.30, 3.12, c - 0.025, c + 0.025, 0.03)))   # centre grab pole
            parts.append(("emu_green", slab(SOLE_Y - 0.25, SOLE_Y, c - 0.35, c + 0.35, 0.05)))  # footstep
        for c, w in crew:
            parts.append(("emu_green", slab(SOLE_Y + 0.05, 3.10, c - w / 2, c + w / 2, 0.016)))
            parts.append(("window_dark", slab(2.45, 3.0, c - w / 2 + 0.1, c + w / 2 - 0.1, 0.022)))
        for c in windows:
            parts.append(("window_dark", slab(2.22, 3.17, c - 0.52, c + 0.52)))
            for by in (2.45, 2.70, 2.95):
                parts.append(("bar_grey", slab(by - 0.012, by + 0.012, c - 0.52, c + 0.52, 0.02)))
        if louvre:
            for ly in np.arange(2.30, 3.2, 0.09):
                parts.append(("emu_green", slab(ly, ly + 0.04, louvre[0], louvre[1], 0.02)))
        # Rain gutter over the cream panel.
        parts.append(("roof_grey", slab(ROOF_Y - ROOF_R + 0.02, ROOF_Y - ROOF_R + 0.06, zr + 0.1, zf - 0.1, 0.035)))
        nx = (HALF_W + 0.007) * side
        tex.append((f"coach_number_{'L' if side > 0 else 'R'}",
                    decal(coach_number_texture(number), (nx, 2.17, zr + 2.0),
                          0.75, 0.19, "+x" if side > 0 else "-x", f"EMU_coach_number_{number}")))

    # Underframe, equipment, bogies, couplers.
    parts.append(("underframe", box(-1.35, 1.35, 0.78, SOLE_Y, zr + 0.4, zf - 0.4)))
    if kind == "MC":
        for z0, z1 in ((-4.5, -1.0), (1.8, 4.6)):
            parts.append(("underframe", box(-1.2, 1.2, 0.48, 0.80, z0, z1)))
    for zc in (-BOGIE_CENTRES / 2, BOGIE_CENTRES / 2):
        bogie(parts, zc)
    # Couplers at non-cab ends reach half the inter-coach gap.
    for end, sgn in ((zr, -1), (zf, 1)):
        if sgn > 0 and cab_dir:
            continue
        z0, z1 = sorted((end - sgn * 0.3, end + sgn * GAP / 2))
        parts.append(("underframe", box(-0.2, 0.2, 0.98, 1.18, z0, z1)))

    if kind == "MC":
        diamond_pantograph(parts, zf - 4.2)
        parts.append(("roof_grey", box(-0.5, 0.5, ROOF_Y - 0.05, ROOF_Y + 0.25, zf - 7.2, zf - 5.6)))
        for i in range(4):  # roof insulators / bus-bar
            parts.append(("insulator", cyl_y(0.0, ROOF_Y - 0.02, zf - 9.0 - i * 1.6, 0.06, 0.24, 8)))
        parts.append(("panto_steel", beam((0, ROOF_Y + 0.22, zf - 5.0), (0, ROOF_Y + 0.22, zf - 13.8), 0.025, 6)))
    if cab_dir:
        # Cab-end details: twin marker headlamp on the dome, buffers, centre lamp, cattle guard, tail lamps.
        zfc = zf + 0.01
        parts.append(("underframe", box(-0.32, 0.32, 3.52, 3.78, zf - 0.25, zfc + 0.12)))
        for sx in (-0.13, 0.13):
            parts.append(("lamp_white", cyl_z(sx, 3.65, zfc + 0.13, 0.10, 0.03, 16)))
        parts.append(("lamp_white", cyl_z(0, 1.62, zfc + 0.03, 0.09, 0.06, 14)))
        for sx in (-0.95, 0.95):
            parts.append(("underframe", cyl_z(sx, 1.105, zfc + 0.20, 0.07, 0.40, 10)))
            parts.append(("buffer_white", cyl_z(sx, 1.105, zfc + 0.42, 0.22, 0.05, 20)))
            parts.append(("tail_red", cyl_z(sx * 1.35, 1.40, zfc + 0.02, 0.07, 0.04, 12)))
        parts.append(("underframe", box(-1.2, 1.2, 0.62, SOLE_Y, zf - 0.3, zf + 0.12)))   # headstock
        for gx in np.arange(-1.05, 1.1, 0.21):                                            # cattle guard bars
            parts.append(("underframe", box(gx - 0.025, gx + 0.025, 0.16, 0.66, zf + 0.04, zf + 0.10)))
        parts.append(("underframe", box(-1.1, 1.1, 0.16, 0.24, zf + 0.02, zf + 0.12)))
        parts.append(("underframe", box(-0.26, 0.26, 0.85, 1.20, zf, zf + 0.55)))      # screw coupling hook
    return parts, tex


def build():
    b = VehicleBuilder("Chennai_suburban_EMU_9car", PALETTE)
    pitch = CAR_LEN + GAP
    n = len(CONSIST)
    flip = trimesh.transformations.rotation_matrix(math.pi, [0, 1, 0])
    for i, (kind, cab, number) in enumerate(zip(CONSIST, CAB_DIR, UNIT_NUMBERS)):
        zc = ((n - 1) / 2 - i) * pitch
        node = b.node(f"coach_{i + 1:02d}_{kind}", (0, 0, zc))
        parts, tex = coach(kind, cab, number)
        for mat, mesh in parts:
            if cab < 0:
                mesh.apply_transform(flip)
            b.add(node, mat, mesh)
        for name, mesh in tex:
            if cab < 0:
                mesh.apply_transform(flip)
            b.add_textured(node, name, mesh)
        collider_box(b, f"coach_{i + 1:02d}", -HALF_W, HALF_W, SOLE_Y - 0.3, ROOF_Y, -CAR_LEN / 2, CAR_LEN / 2,
                     translation=(0, 0, zc))
    return b


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    glb = os.path.join(OUT_DIR, "chennai_suburban_emu.glb")
    build().export(glb)
    pitch = CAR_LEN + GAP
    meta = {
        "asset": "chennai_suburban_emu.glb",
        "description": "Chennai Suburban Railway 9-car EMU rake, ICF WAU-4 type in the cream-and-green Southern Railway suburban livery.",
        "frame": "glTF metres, +Y up, +Z = leading cab, +X = train left; y=0 top of rail; origin at rake centre on track centreline",
        "gauge_m": GAUGE,
        "dimensions_m": {
            "coach_body_length": CAR_LEN, "body_width": HALF_W * 2, "roof_height_above_rail": ROOF_Y,
            "pantograph_head_above_rail": round(ROOF_Y + 1.57, 3), "floor_height": FLOOR_Y,
            "bogie_centres": BOGIE_CENTRES, "bogie_wheelbase": BOGIE_WHEELBASE, "wheel_radius": WHEEL_R,
            "coach_pitch": round(pitch, 3), "rake_length_over_bodies": round(len(CONSIST) * CAR_LEN + (len(CONSIST) - 1) * GAP, 3),
        },
        "consist_front_to_rear": [
            {"node": f"coach_{i + 1:02d}_{k}", "type": k, "cab": {1: "front (+Z)", -1: "rear (-Z)", 0: "none"}[c],
             "centre_z": round(((len(CONSIST) - 1) / 2 - i) * pitch, 3), "number": num}
            for i, (k, c, num) in enumerate(zip(CONSIST, CAB_DIR, UNIT_NUMBERS))
        ],
        "colliders": "COL_coach_NN box per coach; hide renderers in Unity",
        "destination_board": DESTINATION,
        "sources": "See vehicles/REFERENCE_MEDIA.md (Wikimedia Commons CC BY / CC BY-SA photos, IRIMEE EMU handbook, Wikipedia).",
        "approximations": [
            "Body length/width/height use typical ICF broad-gauge EMU values (20.73 m x 3.66 m x 3.88 m); not from a drawing.",
            "Door/window counts and spacing are estimated from photos; interiors are not modelled (doorways are dark panels).",
            "Middle motor coach is shown with its cab facing forward; real rake formations vary (9-car = three MC+2TC units).",
            "Unit numbers are illustrative. Advertising wraps and the newer stainless-steel MEDHA/AC EMUs are not represented.",
        ],
        "stats": scene_stats(glb),
    }
    write_meta(os.path.join(OUT_DIR, "chennai_suburban_emu.json"), meta)
    print(glb, meta["stats"])


if __name__ == "__main__":
    main()
