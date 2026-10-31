"""MTC Chennai 12 m low-floor city bus (Ashok Leyland, 2024-25 purple/cyan livery).

Writes ../mtc_bus/mtc_low_floor_bus.glb and ../mtc_bus/mtc_low_floor_bus.json.
Run from the repository root:  python3 vehicles/tools/mtc_bus.py
Dependencies: trimesh, numpy, pillow (+ libraqm for Tamil shaping).

Frame: metres, +Y up, +Z = bus front, +X = bus left (kerb/door side, India
drives on the left), origin on the road surface at the bus centre.

The geometry is original procedural work interpreted from openly licensed
photos listed in ../REFERENCE_MEDIA.md; no photo pixels or logos are used.
"""

from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transit_common import (  # noqa: E402
    LATIN_FONTS, TAMIL_FONTS, Palette, VehicleBuilder, beam, box, cap_mesh, collider_box,
    cyl_x, cyl_z, decal, draw_text, fit_font, led_board, loft, scene_stats, side_profile,
    tamil_supported, warn, write_meta,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "mtc_bus")

# Principal dimensions (metres). Sources/assumptions in the metadata JSON.
LENGTH = 12.0
HALF_W = 1.275            # 2.55 m body; mirrors add ~0.2 m each side
ROOF_Y = 3.10
SKIRT_Y = 0.32            # bottom of side skirt
ARCH_TOP = 1.00           # top of wheel-arch opening
FRONT_AXLE_Z = 3.40       # 2.60 m front overhang
REAR_AXLE_Z = -2.80       # 6.20 m wheelbase, 3.20 m rear overhang
WHEEL_R = 0.48            # 275/70 R22.5 tyre
ARCH_HALF = 0.62
FRONT_DOOR = (4.35, 5.55)
MIDDLE_DOOR = (-0.60, 0.60)
ROUTE = "21G"
DESTINATION = "TAMBARAM"

PALETTE = Palette({
    "mtc_purple": ((0.34, 0.19, 0.62), 0.1, 0.45),
    "mtc_cyan": ((0.42, 0.78, 0.88), 0.1, 0.45),
    "mtc_orange": ((0.96, 0.60, 0.12), 0.1, 0.45),
    "livery_white": ((0.93, 0.93, 0.91), 0.1, 0.45),
    "roof_white": ((0.84, 0.85, 0.85), 0.0, 0.7),
    "glass_dark": ((0.05, 0.07, 0.09), 0.3, 0.08),
    "black_trim": ((0.03, 0.03, 0.03), 0.0, 0.6),
    "underbody": ((0.09, 0.09, 0.09), 0.0, 0.9),
    "tyre": ((0.035, 0.035, 0.035), 0.0, 0.92),
    "hub_steel": ((0.62, 0.63, 0.64), 0.8, 0.35),
    "lamp_white": ((0.95, 0.95, 0.90), 0.0, 0.2),
    "tail_red": ((0.72, 0.03, 0.02), 0.0, 0.3),
    "indicator_amber": ((0.95, 0.55, 0.05), 0.0, 0.3),
    "step_yellow": ((0.95, 0.78, 0.10), 0.0, 0.6),
    "collider": ((1.0, 0.0, 1.0), 0.0, 1.0),
})


def tamil_side_text():
    """Operator name on the cyan band, as painted on current MTC buses."""
    w, h = 1024, 224
    img = Image.new("RGB", (w, h), tuple(int(c * 255) for c in PALETTE.rgb("mtc_cyan")))
    draw = ImageDraw.Draw(img)
    ink = (52, 24, 110)
    if tamil_supported():
        line1, line2, fonts = "மாநகர் போக்குவரத்துக் கழகம்", "சென்னை", TAMIL_FONTS
    else:
        warn("libraqm or a Tamil font is missing; using English side text")
        line1, line2, fonts = "METROPOLITAN TRANSPORT CORPORATION", "CHENNAI", LATIN_FONTS
    f1 = fit_font(draw, line1, fonts, int(w * 0.96), 104)
    f2 = fit_font(draw, line2, fonts, int(w * 0.5), 84)
    draw_text(draw, (w / 2, 62), line1, f1, ink)
    draw_text(draw, (w / 2, 170), line2, f2, ink)
    return img


def fleet_number(text="CPT 2121"):
    w, h = 512, 96
    img = Image.new("RGB", (w, h), tuple(int(c * 255) for c in PALETTE.rgb("mtc_cyan")))
    draw = ImageDraw.Draw(img)
    draw_text(draw, (w / 2, h / 2), text, fit_font(draw, text, LATIN_FONTS, w - 20, 70), (52, 24, 110))
    return img


def number_plate(text="TN 01 AN 2121"):
    w, h = 512, 112
    img = Image.new("RGB", (w, h), (240, 196, 30))
    draw = ImageDraw.Draw(img)
    draw.rectangle((4, 4, w - 5, h - 5), outline=(20, 20, 20), width=6)
    draw_text(draw, (w / 2, h / 2), text, fit_font(draw, text, LATIN_FONTS, w - 40, 76), (15, 15, 15))
    return img


def body_profile():
    """Upper body cross-section: from the arch line to the roof."""
    bands = [
        (1.50, "mtc_cyan"),
        (1.54, "mtc_orange"),
        (2.72, "glass_dark"),
        (2.96, "mtc_purple"),
    ]
    return side_profile(HALF_W, ARCH_TOP, bands, ROOF_Y, 0.14, roof_segments=6)


def build():
    b = VehicleBuilder("MTC_low_floor_bus", PALETTE)
    body = b.node("body")
    pts, keys = body_profile()

    def resolve(key):
        return {"__bottom__": "black_trim", "__shoulder__": "mtc_purple", "__roof__": "roof_white"}.get(key, key)

    # Upper body: straight loft with slightly tucked front/rear faces.
    def tucked(scale_x, drop):
        p = pts.copy()
        p[:, 0] *= scale_x
        p[:, 1] = np.where(p[:, 1] > 2.9, p[:, 1] - drop, p[:, 1])
        return p

    zf, zr = LENGTH / 2, -LENGTH / 2
    sections = [
        (zr, tucked(0.965, 0.05)),
        (zr + 0.12, tucked(0.99, 0.01)),
        (zf - 0.14, pts),
        (zf, tucked(0.965, 0.06)),
    ]
    b.add_many(body, loft(sections, keys, resolve))
    front_cap, _ = cap_mesh(sections[-1][1], zf, +1)
    rear_cap, _ = cap_mesh(sections[0][1], zr, -1)
    b.add(body, "mtc_purple", front_cap)
    b.add(body, "mtc_purple", rear_cap)

    # Lower body/skirt, cut around the wheel arches. Bands: purple, white stripe, cyan.
    lower_bands = [(SKIRT_Y, 0.90, "mtc_purple"), (0.90, 0.95, "livery_white"), (0.95, ARCH_TOP, "mtc_cyan")]
    cuts = [zr + 0.02]
    for axle in (REAR_AXLE_Z, FRONT_AXLE_Z):
        cuts += [axle - ARCH_HALF, axle + ARCH_HALF]
    cuts.append(zf - 0.02)
    for z0, z1 in zip(cuts[0::2], cuts[1::2]):
        for y0, y1, mat in lower_bands:
            b.add(body, mat, box(-HALF_W, HALF_W, y0, y1, z0, z1))
    # Wheel wells and underfloor.
    for axle in (REAR_AXLE_Z, FRONT_AXLE_Z):
        z0, z1 = axle - ARCH_HALF, axle + ARCH_HALF
        b.add(body, "underbody", box(-HALF_W + 0.42, HALF_W - 0.42, SKIRT_Y, ARCH_TOP, z0, z1))
        for side in (-1, 1):
            # Black rubber arch trim around the opening.
            x0, x1 = sorted((side * (HALF_W - 0.02), side * (HALF_W + 0.012)))
            b.add(body, "black_trim", box(x0, x1, ARCH_TOP - 0.04, ARCH_TOP + 0.03, z0 - 0.03, z1 + 0.03))
            for zz in (z0, z1):
                b.add(body, "black_trim", box(x0, x1, SKIRT_Y + 0.05, ARCH_TOP, zz - 0.03, zz + 0.03))

    # Window pillars and the sliding-window rail on both sides.
    door_zones = [FRONT_DOOR, MIDDLE_DOOR]
    pillar_z = np.arange(zr + 0.45, zf - 0.9, 1.22)
    for side in (-1, 1):
        x0, x1 = sorted((side * HALF_W, side * (HALF_W + 0.012)))
        for z in pillar_z:
            if side > 0 and any(d0 - 0.1 < z < d1 + 0.1 for d0, d1 in door_zones):
                continue
            b.add(body, "black_trim", box(x0, x1, 1.54, 2.72, z - 0.045, z + 0.045))
        b.add(body, "black_trim", box(x0, x1, 2.17, 2.21, zr + 0.2, zf - 0.2))

    # Doors on the +X (kerb) side: black frame, two glass leaves, yellow step nosing.
    xo = HALF_W
    for d0, d1 in door_zones:
        b.add(body, "black_trim", box(xo - 0.02, xo + 0.018, SKIRT_Y + 0.02, 2.76, d0, d1))
        mid = (d0 + d1) / 2
        for l0, l1 in ((d0 + 0.05, mid - 0.015), (mid + 0.015, d1 - 0.05)):
            b.add(body, "glass_dark", box(xo + 0.018, xo + 0.026, 0.48, 2.66, l0, l1))
            b.add(body, "black_trim", box(xo + 0.018, xo + 0.03, 1.38, 1.44, l0, l1))  # leaf mid rail
        b.add(body, "step_yellow", box(xo - 0.35, xo + 0.02, SKIRT_Y, SKIRT_Y + 0.04, d0 + 0.02, d1 - 0.02))

    # Front face (+Z).
    zface = zf + 0.002
    b.add(body, "black_trim", box(-1.20, 1.20, 1.00, 2.96, zf - 0.05, zface + 0.012))
    b.add(body, "glass_dark", box(-1.15, 1.15, 1.06, 2.62, zface + 0.012, zface + 0.022))
    b.add(body, "black_trim", box(-0.03, 0.03, 1.06, 2.62, zface + 0.022, zface + 0.03))  # windscreen split
    b.add(body, "mtc_cyan", box(-1.22, 1.22, 0.64, 1.00, zf - 0.05, zface + 0.03))
    b.add(body, "livery_white", box(-1.22, 1.22, 0.98, 1.02, zf - 0.05, zface + 0.034))
    b.add(body, "mtc_purple", box(-1.25, 1.25, SKIRT_Y, 0.64, zf - 0.05, zf + 0.07))  # bumper
    for side in (-1, 1):
        cx = side * 0.92
        b.add(body, "black_trim", box(cx - 0.24, cx + 0.24, 0.66, 0.86, zface + 0.03, zface + 0.05))
        b.add(body, "lamp_white", cyl_z(cx - side * 0.09, 0.76, zface + 0.06, 0.065, 0.03, 14))
        b.add(body, "lamp_white", cyl_z(cx + side * 0.06, 0.76, zface + 0.06, 0.055, 0.03, 14))
        b.add(body, "indicator_amber", box(cx + side * 0.13, cx + side * 0.22, 0.70, 0.82, zface + 0.05, zface + 0.06))
        # Wiper and wing mirrors.
        b.add(body, "black_trim", beam((side * 0.15, 1.12, zface + 0.03), (side * 0.95, 1.65, zface + 0.03), 0.012, 6))
        arm_a = (side * (HALF_W - 0.02), 2.55, zf - 0.20)
        arm_b = (side * (HALF_W + 0.22), 2.62, zf + 0.22)
        b.add(body, "black_trim", beam(arm_a, arm_b, 0.022, 6))
        mx = side * (HALF_W + 0.24)
        b.add(body, "black_trim", box(mx - 0.05, mx + 0.05, 2.05, 2.62, zf + 0.17, zf + 0.29))
    b.add_textured(body, "front_destination_led",
                   decal(led_board(f"{ROUTE}  {DESTINATION}", (768, 96)), (0, 2.79, zface + 0.012), 1.90, 0.24, "+z",
                         "MTC_front_led"))
    b.add_textured(body, "front_number_plate",
                   decal(number_plate(), (0, 0.49, zf + 0.07), 0.50, 0.11, "+z", "MTC_number_plate_front"))

    # Rear face (-Z): rear-engine grille, rear window, route LED, tail lamps.
    zb = zr - 0.002
    b.add(body, "glass_dark", box(-1.05, 1.05, 1.95, 2.62, zb - 0.012, zr + 0.02))
    b.add(body, "black_trim", box(-1.0, 1.0, 0.70, 1.55, zb - 0.012, zr + 0.02))   # engine grille
    for gy in np.arange(0.78, 1.52, 0.09):
        b.add(body, "underbody", box(-0.95, 0.95, gy, gy + 0.035, zb - 0.02, zb - 0.012))
    b.add(body, "mtc_purple", box(-1.25, 1.25, SKIRT_Y, 0.62, zr - 0.06, zr + 0.05))
    for side in (-1, 1):
        cx = side * 1.12
        b.add(body, "tail_red", box(cx - 0.1, cx + 0.1, 0.70, 1.20, zb - 0.02, zr + 0.02))
        b.add(body, "indicator_amber", box(cx - 0.1, cx + 0.1, 1.22, 1.36, zb - 0.02, zr + 0.02))
    b.add_textured(body, "rear_route_led",
                   decal(led_board(ROUTE, (256, 96)), (0, 2.79, zb - 0.012), 0.70, 0.24, "-z", "MTC_rear_led"))
    b.add_textured(body, "rear_number_plate",
                   decal(number_plate(), (0, 0.47, zr - 0.06), 0.50, 0.11, "-z", "MTC_number_plate_rear"))

    # Side lettering on the cyan band, both sides.
    side_text = tamil_side_text()
    b.add_textured(body, "side_operator_left",
                   decal(side_text, (HALF_W, 1.25, 1.65), 2.25, 0.46, "+x", "MTC_side_operator_text"))
    b.add_textured(body, "side_operator_right",
                   decal(side_text, (-HALF_W, 1.25, -0.6), 2.25, 0.46, "-x", "MTC_side_operator_text"))
    fleet = fleet_number()
    b.add_textured(body, "fleet_number_left",
                   decal(fleet, (HALF_W, 1.25, 3.25), 0.60, 0.12, "+x", "MTC_fleet_number"))

    # Roof hatches and the rooftop route board housing.
    for z in (2.2, -1.6):
        b.add(body, "roof_white", box(-0.45, 0.45, ROOF_Y, ROOF_Y + 0.09, z - 0.45, z + 0.45))

    # Wheels: single front tyres, dual rear tyres.
    wheels = b.node("wheels")
    for axle, width in ((FRONT_AXLE_Z, 0.30), (REAR_AXLE_Z, 0.56)):
        for side in (-1, 1):
            outer = side * (HALF_W - 0.06)
            cx = outer - side * width / 2
            b.add(wheels, "tyre", cyl_x(cx, WHEEL_R, axle, WHEEL_R, width, 20))
            b.add(wheels, "hub_steel", cyl_x(outer + side * 0.004, WHEEL_R, axle, 0.28, 0.012, 16))
            b.add(wheels, "black_trim", cyl_x(outer + side * 0.012, WHEEL_R, axle, 0.09, 0.012, 10))
    b.add(wheels, "underbody", box(-0.9, 0.9, 0.36, 0.44, REAR_AXLE_Z - 0.06, REAR_AXLE_Z + 0.06))

    collider_box(b, "MTC_low_floor_bus", -HALF_W, HALF_W, SKIRT_Y - 0.02, ROOF_Y + 0.09, zr - 0.06, zf + 0.08)
    return b


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    builder = build()
    glb = os.path.join(OUT_DIR, "mtc_low_floor_bus.glb")
    builder.export(glb)
    meta = {
        "asset": "mtc_low_floor_bus.glb",
        "description": "MTC Chennai 12 m low-floor city bus (Ashok Leyland body style), current purple/cyan MTC livery, route 21G Tambaram.",
        "frame": "glTF metres, +Y up, +Z = bus front, +X = bus left (door/kerb side), origin on road at bus centre",
        "dimensions_m": {
            "length": LENGTH, "body_width": round(HALF_W * 2, 3), "height_incl_roof_hatches": round(ROOF_Y + 0.09, 3),
            "wheelbase": round(FRONT_AXLE_Z - REAR_AXLE_Z, 3), "front_overhang": round(LENGTH / 2 - FRONT_AXLE_Z, 3),
            "wheel_radius": WHEEL_R, "entry_step_height": SKIRT_Y,
        },
        "doors": {"side": "+X (left/kerb)", "front_z": list(FRONT_DOOR), "middle_z": list(MIDDLE_DOOR)},
        "nodes": {
            "body": "painted body, glazing, doors, lamps, decals",
            "wheels": "tyres and hubs (static; separate node for optional spin)",
            "COL_MTC_low_floor_bus": "single box collider; hide its renderer in Unity",
        },
        "tamil_text_shaped": tamil_supported(),
        "sources": "See vehicles/REFERENCE_MEDIA.md (Wikimedia Commons CC BY-SA 4.0 / CC0 photos, Ashok Leyland order notices).",
        "approximations": [
            "12 m length, 2.55 m width, 6.2 m wheelbase and 0.32 m skirt height are typical Ashok Leyland 12 m low-floor values, not measured from a specific bus.",
            "Livery band heights are estimated from photos; the white diagonal swoosh and small stickers are omitted.",
            "No interior; side glazing is opaque dark glass. Logos are deliberately not reproduced.",
            "Fleet number and registration plate are fictitious.",
        ],
        "stats": scene_stats(glb),
    }
    write_meta(os.path.join(OUT_DIR, "mtc_low_floor_bus.json"), meta)
    print(glb, meta["stats"])


if __name__ == "__main__":
    main()
