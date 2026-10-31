"""Chennai Metro (CMRL) Phase 1 four-car Alstom Metropolis trainset.

Writes ../cmrl_metro/cmrl_metro_phase1.glb and ../cmrl_metro/cmrl_metro_phase1.json.
Run from the repository root:  python3 vehicles/tools/cmrl_metro.py
Dependencies: trimesh, numpy, pillow.

Frame: metres, +Y up, +Z = leading cab (DMC1), +X = train left, y = 0 top of
rail, origin at trainset centre on the track centreline. Standard gauge.
Each car is a child node whose origin is its own centre at rail level.

Formation per CMRL: DMC1 - TC1 - TC2 - DMC2, stainless-steel bodies, 25 kV AC
overhead supply (pantographs on the trailer cars). Original procedural
geometry interpreted from openly licensed photos in ../REFERENCE_MEDIA.md;
CMRL and Alstom logos are deliberately not reproduced.
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
OUT_DIR = os.path.join(os.path.dirname(HERE), "cmrl_metro")

DMC_LEN = 22.00           # driving motor car incl. nose (approx.)
TC_LEN = 21.64            # trailer car body (CMRL DPR coach size)
HALF_W = 1.45             # 2.9 m wide
SKIRT_Y = 0.95            # bottom of stainless side
FLOOR_Y = 1.13
ROOF_Y = 3.90
ROOF_R = 0.38
STRIPE = (1.93, 2.03)     # blue waist stripe
EAVE_Y = 3.28             # blue eave band from here to the shoulder
GAP = 0.60
BOGIE_CENTRES = 15.0
BOGIE_WHEELBASE = 2.2
WHEEL_R = 0.43
GAUGE = 1.435
DOOR_W, DOOR_TOP = 1.40, 3.08
NOSE_LEN = 2.2
PANTO_HEAD_Y = 4.95
CONSIST = [("DMC1", DMC_LEN, +1, "D101"), ("TC1", TC_LEN, 0, "T101"), ("TC2", TC_LEN, 0, "T102"),
           ("DMC2", DMC_LEN, -1, "D102")]
DESTINATION = "AIRPORT"

PALETTE = Palette({
    "stainless": ((0.76, 0.77, 0.78), 0.45, 0.35),
    "cmrl_blue": ((0.12, 0.36, 0.86), 0.1, 0.35),
    "roof_grey": ((0.55, 0.56, 0.57), 0.4, 0.55),
    "glass_dark": ((0.05, 0.07, 0.09), 0.3, 0.08),
    "black_trim": ((0.03, 0.03, 0.03), 0.0, 0.6),
    "underframe": ((0.10, 0.10, 0.11), 0.2, 0.8),
    "gangway": ((0.16, 0.16, 0.17), 0.0, 0.9),
    "wheel_steel": ((0.36, 0.36, 0.37), 0.8, 0.45),
    "lamp_white": ((0.96, 0.96, 0.92), 0.0, 0.15),
    "tail_red": ((0.80, 0.04, 0.05), 0.0, 0.3),
    "panto_steel": ((0.22, 0.23, 0.24), 0.7, 0.4),
    "insulator": ((0.75, 0.75, 0.72), 0.0, 0.4),
    "collider": ((1.0, 0.0, 1.0), 0.0, 1.0),
})


def rgb255(name):
    return tuple(int(c * 255) for c in PALETTE.rgb(name))


BANDS = [(STRIPE[0], "stainless"), (STRIPE[1], "cmrl_blue"), (EAVE_Y, "stainless"), (ROOF_Y - ROOF_R, "cmrl_blue")]


def profile():
    return side_profile(HALF_W, SKIRT_Y, BANDS, ROOF_Y, ROOF_R, roof_segments=8)


def nose_shape(pts, sx, drop):
    """Shrink width and pull the upper body down/back to form the cab nose."""
    p = pts.copy()
    p[:, 0] *= sx
    pivot = 1.60
    k = 1.0 - drop / (ROOF_Y - pivot)
    p[:, 1] = np.where(p[:, 1] > pivot, pivot + (p[:, 1] - pivot) * k, p[:, 1])
    return p


def cab_front_texture(bounds_lo, bounds_hi):
    """Blue nose face: big windscreen, black lower band, headlamp pods, LED."""
    ppm = 220
    w = int((bounds_hi[0] - bounds_lo[0]) * ppm)
    h = int((bounds_hi[1] - bounds_lo[1]) * ppm)

    def px(x, y):
        return ((x - bounds_lo[0]) * ppm, (bounds_hi[1] - y) * ppm)

    top = bounds_hi[1]
    img = Image.new("RGB", (w, h), rgb255("cmrl_blue"))
    d = ImageDraw.Draw(img)
    x0, y0 = px(-0.98, top - 0.12)
    x1, y1 = px(0.98, 1.98)
    d.rounded_rectangle((x0, y0, x1, y1), radius=40, fill=(18, 22, 26), outline=(10, 10, 10), width=8)
    led = led_board(DESTINATION, (int((x1 - x0) * 0.5), 46), color=(255, 150, 20), bg=(18, 22, 26))
    img.paste(led, (int((x0 + x1) / 2 - led.width / 2), int(y0 + 16)))
    bx0, by0 = px(-0.92, 1.96)
    bx1, by1 = px(0.92, 1.66)
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=24, fill=(14, 14, 16))
    for side in (-1, 1):
        pod = [px(side * 0.55, 1.50), px(side * 1.12, 1.52), px(side * 1.12, 1.12), px(side * 0.62, 1.12)]
        d.polygon(pod, fill=(12, 12, 14))
    return img


def car_number_texture(text):
    img = Image.new("RGB", (320, 96), rgb255("cmrl_blue"))
    d = ImageDraw.Draw(img)
    draw_text(d, (160, 48), text, fit_font(d, text, LATIN_FONTS, 300, 70), (245, 245, 245))
    return img


def resolve(key):
    return {"__bottom__": "underframe", "__shoulder__": "cmrl_blue", "__roof__": "roof_grey"}.get(key, key)


def door_centres(length, cab):
    base = [-7.65, -2.55, 2.55, 7.65]
    shift = -0.25 if cab else 0.0   # doors shift away from the cab
    return [c + shift for c in base]


def bogie(parts, zc):
    for dz in (-BOGIE_WHEELBASE / 2, BOGIE_WHEELBASE / 2):
        z = zc + dz
        for side in (-1, 1):
            parts.append(("wheel_steel", cyl_x(side * GAUGE / 2, WHEEL_R, z, WHEEL_R, 0.13, 18)))
            parts.append(("underframe", box(side * 0.95 - 0.12, side * 0.95 + 0.12, 0.30, 0.56, z - 0.17, z + 0.17)))
        parts.append(("underframe", cyl_x(0, WHEEL_R, z, 0.08, GAUGE + 0.12, 10)))
    for side in (-1, 1):
        parts.append(("underframe", box(side * 0.95 - 0.10, side * 0.95 + 0.10, 0.48, 0.74, zc - 1.6, zc + 1.6)))
        parts.append(("panto_steel", cyl_y(side * 0.95, 0.74, zc, 0.2, 0.18, 12)))   # air spring
    parts.append(("underframe", box(-1.05, 1.05, 0.62, 0.80, zc - 0.3, zc + 0.3)))


def single_arm_pantograph(parts, zc):
    base_y = ROOF_Y + 0.02
    parts.append(("panto_steel", box(-0.55, 0.55, base_y, base_y + 0.12, zc - 1.1, zc + 1.1)))
    for sx in (-0.45, 0.45):
        for sz in (-0.95, 0.95):
            parts.append(("insulator", cyl_y(sx, ROOF_Y - 0.03, zc + sz, 0.06, 0.18, 10)))
    hinge = np.array([0.0, base_y + 0.22, zc - 0.85])
    knee = np.array([0.0, base_y + 0.55, zc + 1.05])
    head = np.array([0.0, PANTO_HEAD_Y - 0.08, zc - 0.15])
    for sx in (-0.22, 0.22):
        parts.append(("panto_steel", beam(hinge + [sx, 0, 0], knee + [sx * 0.3, 0, 0], 0.04, 8)))
    parts.append(("panto_steel", beam(knee, head, 0.03, 8)))
    parts.append(("panto_steel", beam(hinge + [0, -0.05, 0.3], knee + [0, -0.12, -0.3], 0.015, 6)))   # damper link
    parts.append(("panto_steel", beam((-0.7, PANTO_HEAD_Y, zc - 0.15), (0.7, PANTO_HEAD_Y, zc - 0.15), 0.035, 8)))
    parts.append(("panto_steel", beam((-0.35, PANTO_HEAD_Y - 0.08, zc - 0.15), (0.35, PANTO_HEAD_Y - 0.08, zc - 0.15), 0.02, 6)))
    for sx in (-1, 1):   # pan-head horns
        parts.append(("panto_steel", beam((sx * 0.7, PANTO_HEAD_Y, zc - 0.15), (sx * 0.9, PANTO_HEAD_Y - 0.18, zc - 0.15), 0.025, 6)))


def car(name, length, cab, number):
    """Car-local geometry with any cab at +Z; caller flips for cab == -1."""
    parts, tex = [], []
    pts, keys = profile()
    zf, zr = length / 2, -length / 2
    if cab:
        nose = [(0.0, 1.0, 0.0), (0.9, 1.0, 0.08), (1.45, 0.975, 0.22), (1.85, 0.93, 0.40), (2.1, 0.88, 0.56),
                (NOSE_LEN, 0.84, 0.66)]
        z_nose = zf - NOSE_LEN
        sections = [(zr, pts), (z_nose, pts)] + [(z_nose + dz, nose_shape(pts, sx, dr)) for dz, sx, dr in nose[1:]]
        n_body = 1

        def edge_mat(span, edge):
            k = keys[edge]
            if span >= n_body and k not in ("__bottom__", "__roof__"):
                return "cmrl_blue"
            if span >= n_body and k == "__roof__":
                return "cmrl_blue"
            return k

        parts += list(loft(sections, edge_mat, resolve).items())
        lo, hi = sections[-1][1].min(axis=0), sections[-1][1].max(axis=0)
        cap, uv = cap_mesh(sections[-1][1], zf, +1)
        tex.append(("cab_front", textured(cap, uv, cab_front_texture(lo, hi), f"CMRL_cab_front_{number}")))
        # Headlamps, tail lamps, roof-dome marker light, anti-climber/coupler.
        zl = zf + 0.01
        for side in (-1, 1):
            hx = side * 0.88 * 0.84 / 0.84
            parts.append(("lamp_white", cyl_z(side * 0.72, 1.32, zl + 0.02, 0.085, 0.04, 16)))
            parts.append(("lamp_white", cyl_z(side * 0.90, 1.34, zl + 0.02, 0.065, 0.04, 14)))
            parts.append(("tail_red", cyl_z(side * 0.82, 1.20, zl + 0.02, 0.045, 0.04, 12)))
        parts.append(("lamp_white", cyl_z(0, hi[1] - 0.06, zf - 0.02, 0.07, 0.06, 14)))
        parts.append(("black_trim", box(-1.15, 1.15, 0.70, SKIRT_Y + 0.08, zf - 0.6, zf + 0.12)))
        parts.append(("underframe", box(-0.16, 0.16, 0.72, 0.92, zf + 0.12, zf + 0.55)))
        parts.append(("black_trim", box(-0.28, 0.28, 0.66, 0.98, zf + 0.55, zf + 0.62)))
        door_end_limit = z_nose - 0.3
    else:
        sections = [(zr, pts), (zf, pts)]
        parts += list(loft(sections, keys, resolve).items())
        cap, _ = cap_mesh(pts, zf, +1)
        parts.append(("stainless", cap))
        door_end_limit = zf
    rear_cap, _ = cap_mesh(pts, zr, -1)
    parts.append(("stainless", rear_cap))

    # Doors, windows, car numbers on both sides.
    doors = door_centres(length, cab)
    for side in (-1, 1):
        xo = side * HALF_W

        def slab(y0, y1, z0, z1, depth=0.012):
            x0, x1 = sorted((xo, xo + side * depth))
            return box(x0, x1, y0, y1, z0, z1)

        for c in doors:
            parts.append(("black_trim", slab(FLOOR_Y - 0.03, DOOR_TOP + 0.03, c - DOOR_W / 2 - 0.03, c + DOOR_W / 2 + 0.03, 0.008)))
            for l0, l1 in ((c - DOOR_W / 2, c - 0.01), (c + 0.01, c + DOOR_W / 2)):
                parts.append(("stainless", slab(FLOOR_Y, DOOR_TOP, l0, l1, 0.02)))
                parts.append(("cmrl_blue", slab(STRIPE[0], STRIPE[1], l0, l1, 0.024)))
                wc = (l0 + l1) / 2
                parts.append(("glass_dark", slab(2.10, 2.95, wc - 0.17, wc + 0.17, 0.026)))
            parts.append(("black_trim", slab(FLOOR_Y - 0.05, FLOOR_Y, c - DOOR_W / 2, c + DOOR_W / 2, 0.03)))   # threshold
        bays = [(zr + 0.5, doors[0] - DOOR_W / 2 - 0.25)]
        bays += [(a + DOOR_W / 2 + 0.25, b - DOOR_W / 2 - 0.25) for a, b in zip(doors, doors[1:])]
        bays.append((doors[-1] + DOOR_W / 2 + 0.25, min(door_end_limit, zf) - 0.5))
        for b0, b1 in bays:
            span = b1 - b0
            count = 2 if span > 2.6 else 1
            win = min(1.25, (span - 0.25 * (count - 1)) / count)
            for i in range(count):
                c = b0 + span * (i + 0.5) / count
                parts.append(("black_trim", slab(2.06, 3.04, c - win / 2 - 0.03, c + win / 2 + 0.03, 0.008)))
                parts.append(("glass_dark", slab(2.09, 3.01, c - win / 2, c + win / 2, 0.012)))
        nz = (zf - NOSE_LEN - 1.0) if cab else (zf - 1.4)
        tex.append((f"car_number_{'L' if side > 0 else 'R'}",
                    decal(car_number_texture(number), (xo, (EAVE_Y + ROOF_Y - ROOF_R) / 2, nz), 0.62, 0.19,
                          "+x" if side > 0 else "-x", f"CMRL_car_number_{number}")))

    # Underframe, equipment, bogies.
    parts.append(("underframe", box(-1.38, 1.38, 0.62, SKIRT_Y, zr + 0.3, zf - (0.6 if cab else 0.3))))
    for z0, z1 in ((-5.6, -1.2), (1.2, 5.6)):
        parts.append(("underframe", box(-1.25, 1.25, 0.45, 0.62, z0, z1)))
    for zc in (-BOGIE_CENTRES / 2, BOGIE_CENTRES / 2):
        bogie(parts, zc)
    # Roof AC units.
    for zc in (-(length / 2) + 3.2, (length / 2) - (NOSE_LEN + 2.6 if cab else 3.2)):
        parts.append(("roof_grey", box(-0.85, 0.85, ROOF_Y - 0.03, ROOF_Y + 0.28, zc - 1.1, zc + 1.1)))
        parts.append(("black_trim", box(-0.5, 0.5, ROOF_Y + 0.28, ROOF_Y + 0.29, zc - 0.5, zc + 0.5)))
    if not cab:
        single_arm_pantograph(parts, 0.0)
    # Gangway bellows and coupler at every non-cab end (half the gap each).
    for end, sgn in ((zr, -1), (zf, 1)):
        if sgn > 0 and cab:
            continue
        z0, z1 = sorted((end, end + sgn * GAP / 2))
        parts.append(("gangway", box(-0.85, 0.85, FLOOR_Y - 0.05, 3.25, z0, z1)))
        for k in range(1, 4):
            zz = end + sgn * GAP / 2 * k / 4
            parts.append(("black_trim", box(-0.88, 0.88, FLOOR_Y - 0.08, 3.28, zz - 0.012, zz + 0.012)))
        z0, z1 = sorted((end - sgn * 0.3, end + sgn * GAP / 2))
        parts.append(("underframe", box(-0.15, 0.15, 0.72, 0.90, z0, z1)))
    return parts, tex


def build():
    b = VehicleBuilder("CMRL_Metro_Phase1_4car", PALETTE)
    total = sum(length for _, length, _, _ in CONSIST) + GAP * (len(CONSIST) - 1)
    z = total / 2
    flip = trimesh.transformations.rotation_matrix(math.pi, [0, 1, 0])
    placements = []
    for name, length, cab, number in CONSIST:
        zc = z - length / 2
        z -= length + GAP
        node = b.node(f"car_{name}", (0, 0, zc))
        parts, tex = car(name, length, cab, number)
        for mat, mesh in parts:
            if cab < 0:
                mesh.apply_transform(flip)
            b.add(node, mat, mesh)
        for tname, mesh in tex:
            if cab < 0:
                mesh.apply_transform(flip)
            b.add_textured(node, tname, mesh)
        collider_box(b, f"car_{name}", -HALF_W, HALF_W, SKIRT_Y - 0.3, ROOF_Y, -length / 2, length / 2, (0, 0, zc))
        placements.append({"node": f"car_{name}", "length": length, "centre_z": round(zc, 3), "number": number,
                           "cab": {1: "front (+Z)", -1: "rear (-Z)", 0: "none"}[cab],
                           "pantograph": cab == 0})
    return b, placements, total


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    glb = os.path.join(OUT_DIR, "cmrl_metro_phase1.glb")
    builder, placements, total = build()
    builder.export(glb)
    meta = {
        "asset": "cmrl_metro_phase1.glb",
        "description": "Chennai Metro Phase 1 four-car Alstom Metropolis trainset (DMC1-TC1-TC2-DMC2), stainless steel with blue cab and stripes.",
        "frame": "glTF metres, +Y up, +Z = leading cab (DMC1), +X = train left; y=0 top of rail; origin at trainset centre on track centreline",
        "gauge_m": GAUGE,
        "dimensions_m": {
            "car_width": HALF_W * 2, "roof_height_above_rail": ROOF_Y, "floor_height": FLOOR_Y,
            "dmc_length_incl_nose": DMC_LEN, "tc_length": TC_LEN, "inter_car_gap": GAP,
            "train_length_over_bodies": round(total, 3), "bogie_centres": BOGIE_CENTRES,
            "bogie_wheelbase": BOGIE_WHEELBASE, "wheel_radius": WHEEL_R, "pantograph_head_above_rail": PANTO_HEAD_Y,
            "door_clear_width": DOOR_W, "doors_per_side_per_car": 4,
        },
        "consist_front_to_rear": placements,
        "colliders": "COL_car_* box per car; hide renderers in Unity",
        "destination_board": DESTINATION,
        "sources": "See vehicles/REFERENCE_MEDIA.md (CMRL rolling-stock page, Wikimedia Commons CC BY-SA 4.0 photos).",
        "approximations": [
            "Formation, stainless body, 25 kV overhead supply and 2.9 m width follow CMRL/DPR data; car lengths, bogie spacing and roof height are typical Metropolis values, not drawings.",
            "Cab nose is a lofted approximation of the Phase 1 Metropolis front; windscreen and lamp layout are painted onto the end face.",
            "Pantograph placement on the trailer cars is inferred from photos. Phase 2 driverless trainsets (darker livery) are not represented.",
            "No interior; windows are opaque dark glass. Car numbers are illustrative; logos are omitted.",
        ],
        "stats": scene_stats(glb),
    }
    write_meta(os.path.join(OUT_DIR, "cmrl_metro_phase1.json"), meta)
    print(glb, meta["stats"])


if __name__ == "__main__":
    main()
