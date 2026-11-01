"""Station journey route: MIT back gate -> Chrompet station -> FOB stairs
-> southbound EMU -> Tambaram Sanatorium -- route data generator.

Writes data/journey_route.json, the waypoint/train-path data consumed by
the Unity journey scripts (unity/Assets/Scripts/Runtime/StationJourney.cs,
JourneyTrain.cs; setup via ChrompetJourneySetup.cs).

Route (all positions baked from the repo's own measured layers):

1. backgate_walk    -- MIT back gate (OSM node 593999547, ENU
   (141.04, -186.29)) north along the east service roads to the
   station's south-west forecourt (approximate, follows the service
   road centrelines in data/placement_map.json road_network).
2. platform_walk    -- onto platform 1 (top y=0.95) and along it to the
   foot of the P1 FOB staircase (Station_stairs_P1 in
   props/chrompet_station_details.glb).
3. stairs_up        -- climbs the P1 staircase to the FOB deck (top
   y=6.80, measured from roads_v2.glb Overbridge__0).
4. bridge_cross     -- across the deck toward platform 2.
5. stairs_down      -- down the P2 staircase (centre ENU (219.79,
   356.95), near the FOB column-row end) to platform 2.
6. platform_wait    -- to the boarding point on platform 2, then WAIT
   for the train.
7. board/ride/alight -- the train runs the southbound rail corridor
   (tools/rail_corridor.py alignment, offset +2.35 m to the P2-side
   track) from north of Chrompet, dwells at platform 2, rides to
   Tambaram Sanatorium, dwells; the player alights on the Sanatorium
   platform and walks to the platform centre.

Frame: "unity-enu" -- x=east, y=up, z=north (metres), origin 12.9487 N
80.1394 E. This is the frame ChrompetSceneBuilder placements use, so
Unity code can consume the numbers directly.

Run from Chromepet/:  python3 tools/journey_route.py
Dependencies: none beyond stdlib + the sibling generator modules.
"""

import json
import math
import os

import numpy as np

from rail_corridor import STATIONS, TRACK_HALF, catmull_rom, local_xy
from station_details import PLATFORM_TOP, PLATFORMS, STAIRS, TRACK_P, TRACK_U, FOB_DECK_TOP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

BACK_GATE_ENU = (141.04, -186.29)  # OSM node 593999547
PLATFORM2_CENTER = PLATFORMS[2]
SANATORIUM = next(s for s in STATIONS if s["name"] == "Tambaram Sanatorium")

WALK_SPEED = 2.0
STAIR_SPEED = 1.2
TRAIN_SPEED = 12.0        # ~43 km/h suburban
TRAIN_DWELL = 8.0


def enu(x, z, y):
    """ENU (east, north) + height -> unity-enu point {x=east, y=up, z=north}.

    Objects (not [x,y,z] arrays) because Unity JsonUtility cannot parse
    jagged arrays; the C# side maps these onto a [Serializable] class.
    """
    return {"x": round(float(x), 2), "y": round(float(y), 2), "z": round(float(z), 2)}


def main():
    ux, uy = TRACK_U
    stairs1 = STAIRS[1]
    stairs2 = STAIRS[2]
    run_half = 5.0

    stages = [
        {
            "name": "backgate_walk",
            "type": "walk",
            "speed": WALK_SPEED,
            "points": [
                enu(*BACK_GATE_ENU, 0.0),
                enu(143.5, -100.0, 0.0),
                enu(145.0, -21.0, 0.0),     # aircraft grove service road
                enu(150.0, 60.0, 0.0),
                enu(140.0, 140.0, 0.0),
                enu(132.9, 210.6, 0.0),     # north service road (OSM 23092383)
                enu(120.0, 250.0, 0.0),     # station forecourt, office side
            ],
        },
        {
            "name": "platform_walk",
            "type": "walk",
            "speed": WALK_SPEED,
            "points": [
                enu(117.0, 250.0, PLATFORM_TOP),   # P1 south-west end
                enu(stairs1[0] - ux * run_half, stairs1[1] - uy * run_half, PLATFORM_TOP),
            ],
        },
        {
            "name": "stairs_up",
            "type": "walk",
            "speed": STAIR_SPEED,
            "points": [
                enu(stairs1[0] - ux * run_half, stairs1[1] - uy * run_half, PLATFORM_TOP),
                enu(stairs1[0] + ux * run_half, stairs1[1] + uy * run_half, FOB_DECK_TOP),
            ],
        },
        {
            "name": "bridge_cross",
            "type": "walk",
            "speed": WALK_SPEED,
            "points": [
                enu(stairs1[0] + ux * run_half, stairs1[1] + uy * run_half, FOB_DECK_TOP),
                enu(stairs2[0] + ux * run_half, stairs2[1] + uy * run_half, FOB_DECK_TOP),
            ],
        },
        {
            "name": "stairs_down",
            "type": "walk",
            "speed": STAIR_SPEED,
            "points": [
                enu(stairs2[0] + ux * run_half, stairs2[1] + uy * run_half, FOB_DECK_TOP),
                enu(stairs2[0] - ux * run_half, stairs2[1] - uy * run_half, PLATFORM_TOP),
            ],
        },
        {
            "name": "platform_wait",
            "type": "walk",
            "speed": WALK_SPEED,
            "points": [
                enu(stairs2[0] - ux * run_half, stairs2[1] - uy * run_half, PLATFORM_TOP),
                enu(PLATFORM2_CENTER[0], PLATFORM2_CENTER[1], PLATFORM_TOP),
            ],
        },
        {"name": "wait_train", "type": "wait_train", "points": []},
        {"name": "ride", "type": "board", "points": []},
        {
            "name": "alight_walk",
            "type": "walk",
            "speed": WALK_SPEED,
            "points": [],  # filled from the alight point at runtime data below
        },
    ]

    # Train path: corridor spline, southbound track (P2 side, +TRACK_HALF),
    # from ~600 m north of Chrompet to ~400 m south of Sanatorium.
    # Through the station zone the corridor spline sits ~40 m from the
    # measured roads_v2 platforms (the OSM station node is on the office
    # building, not platform 2), so blend the path onto the exact
    # platform-2 track line (P2 centre shifted toward P1 to the rail).
    chain = [local_xy(s["lat"], s["lon"]) for s in STATIONS]
    spline = catmull_rom(chain, samples_per_seg=60)
    p2 = np.array(PLATFORM2_CENTER)
    tp = np.array(TRACK_P)
    tu = np.array(TRACK_U)
    track_anchor = p2 - 5.65 * tp  # rail line beside platform 2 (toward P1)

    def station_line_at(north):
        s = (north - track_anchor[1]) / tu[1]
        return track_anchor + tu * s

    def blend_weight(north):
        if 260.0 <= north <= 490.0:
            return 1.0
        if 490.0 < north <= 540.0:
            return (540.0 - north) / 50.0
        if 210.0 <= north < 260.0:
            return (north - 210.0) / 50.0
        return 0.0

    path = []
    for i, p in enumerate(spline):
        north = p[1]
        if north > 1100.0 or north < -1900.0:
            continue
        a = spline[max(0, i - 1)]
        b = spline[min(len(spline) - 1, i + 1)]
        t = b - a
        t = t / np.linalg.norm(t)
        n = np.array([-t[1], t[0]])
        q = p + n * TRACK_HALF
        w = blend_weight(north)
        if w > 0.0:
            q = q + (station_line_at(north) - q) * w
        path.append({"x": round(float(q[0]), 2), "y": 0.45, "z": round(float(q[1]), 2)})

    def nearest(target_enu):
        d = [math.hypot(pt["x"] - target_enu[0], pt["z"] - target_enu[1]) for pt in path]
        return int(np.argmin(d))

    chrompet_stop = nearest(PLATFORM2_CENTER)
    san_enu = local_xy(SANATORIUM["lat"], SANATORIUM["lon"])
    # Sanatorium boarding-side platform: offset +8 m across (same side as P2).
    san_stop = nearest((san_enu[0], san_enu[1]))

    def vec(pt):
        return np.array([pt["x"], pt["y"], pt["z"]], dtype=float)

    tvec = vec(path[min(san_stop + 1, len(path) - 1)]) - vec(path[max(san_stop - 1, 0)])
    tvec[1] = 0
    tvec = tvec / np.linalg.norm(tvec)
    nvec = np.array([-tvec[2], 0.0, tvec[0]])
    plat_pt = vec(path[san_stop]) + nvec * (8.0 - TRACK_HALF)
    plat_pt[1] = PLATFORM_TOP
    door_pt = vec(path[chrompet_stop])
    door_pt[1] = PLATFORM_TOP

    stages[8]["points"] = [
        {"x": round(float(plat_pt[0]), 2), "y": PLATFORM_TOP, "z": round(float(plat_pt[2]), 2)},
        {"x": round(float(plat_pt[0] + tvec[0] * 30), 2), "y": PLATFORM_TOP, "z": round(float(plat_pt[2] + tvec[2] * 30), 2)},
    ]

    route = {
        "frame": "unity-enu: x=east, y=up, z=north (metres), origin 12.9487N 80.1394E",
        "generator": "tools/journey_route.py",
        "notes": "Walk waypoints follow the campus service roads (approximate); station geometry from roads_v2.glb / chrompet_station_details.glb measurements; train path is the rail_corridor.py OSM alignment offset to the platform-2 track.",
        "start": {"position": enu(*BACK_GATE_ENU, 0.1), "name": "MIT back gate (OSM 593999547)"},
        "stages": stages,
        "train": {
            "vehicle_glb": "vehicles/chennai_emu/chennai_suburban_emu.glb",
            "path": path,
            "chrompetStopIndex": chrompet_stop,
            "sanatoriumStopIndex": san_stop,
            "speed": TRAIN_SPEED,
            "dwellSeconds": TRAIN_DWELL,
            "boardPoint": {"x": round(float(door_pt[0]), 2), "y": PLATFORM_TOP, "z": round(float(door_pt[2]), 2)},
            "alightPoint": {"x": round(float(plat_pt[0]), 2), "y": PLATFORM_TOP, "z": round(float(plat_pt[2]), 2)},
        },
    }
    out = os.path.join(ROOT, "data", "journey_route.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(route, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print("stages:", [s["name"] for s in stages])
    print("path points:", len(path), "stops:", chrompet_stop, san_stop)
    print("board:", route["train"]["boardPoint"], "alight:", route["train"]["alightPoint"])


if __name__ == "__main__":
    main()
