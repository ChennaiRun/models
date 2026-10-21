"""Paved connector paths for the sited Chromepet props -- additive layer.

Links the models sited on 2026-10-21 (Open Air Theatre, MIT letters,
golden statue garden, Production Technology frontage, Navy aircraft /
aircraft grove) to the existing road network with flat concrete path
strips in the v2 world frame (metres, x=east, y=up, z=-north, origin
12.9487 N 80.1394 E).

Every polyline endpoint was snapped to road geometry extracted from
roads/roads_v2.glb and data/osm_raw.osm (OSM, ODbL):

* Connector_OAT      -- MIT Avenue west paving edge (-4.96, -144.0)
  around the south side to the OAT south entrance (-26.0, -138.5);
  the theatre centre is ENU (-26.0, -116.0).
* Connector_letters  -- MIT Avenue east paving edge (-56.27, -241.82)
  to the MIT letters plinth (-51.4, -244.8).
* Connector_statue   -- Rajam Hall Road edge (216.75, 5.88) to the end
  of the statue garden's own path spur (220.0, 4.1).
* Connector_prodtech -- MIT Avenue east paving edge (158.3, 83.5) to
  the Production Technology porch front (165.59, 78.61).
* Connector_grove    -- two short links: service road (OSM 23092148)
  edge (141.5, -9.5) to the aircraft grove centre / Navy apron end
  (143.4, -10.6), and service road (OSM 23092149) edge (148.4, -33.8)
  to the Navy plinth south edge (148.5, -32.2).

Strips are 2.2-2.4 m wide, 0.07 m thick, top at z=0.07 (above the
campus ground top ~0.01, below the avenue road top 0.10), in the
repo's concrete tone. Placements are APPROXIMATE (geometry-derived,
not surveyed) and registered in data/placement_map.json.

Run from Chromepet/:  python3 tools/connector_paths.py
Dependencies: trimesh, numpy
Output: props/connector_paths.glb + data/connector_paths_meta.json
"""

import json
import math
import os

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CONCRETE = (0.70, 0.70, 0.68)
TILE_RED = (0.62, 0.22, 0.18)

# name -> (polyline ENU points, width m)
PATHS = {
    "Connector_OAT": ([(-4.96, -144.0), (-26.0, -149.0), (-26.0, -138.5)], 2.4),
    "Connector_letters": ([(-56.27, -241.82), (-51.4, -244.8)], 2.2),
    "Connector_statue": ([(216.75, 5.88), (220.0, 4.1)], 2.2),
    "Connector_prodtech": ([(158.3, 83.5), (165.59, 78.61)], 2.2),
    "Connector_grove": ([(141.5, -9.5), (143.4, -10.6)], 2.2),
    "Connector_grove_plinth": ([(148.4, -33.8), (148.5, -32.2)], 2.2),
}


def material(color, name):
    return trimesh.visual.material.PBRMaterial(
        name=name,
        baseColorFactor=[*(int(c * 255) for c in color), 255],
        metallicFactor=0.0,
        roughnessFactor=0.9,
    )


def strip_segment(p0, p1, width, height=0.07):
    """Flat box between two ENU points (built in ENU: x east, y north, z up)."""
    (x0, y0), (x1, y1) = p0, p1
    length = math.hypot(x1 - x0, y1 - y0) + width * 0.8  # overlap joints/caps
    mesh = trimesh.creation.box(extents=[length, width, height])
    mesh.apply_translation([0, 0, height / 2])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.atan2(y1 - y0, x1 - x0), [0, 0, 1]))
    mesh.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, 0])
    return mesh


def main():
    scene = trimesh.Scene()
    enu_to_gltf = np.array(
        [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float
    )
    index = 0
    for name, (points, width) in PATHS.items():
        for p0, p1 in zip(points, points[1:]):
            mesh = strip_segment(p0, p1, width)
            mesh.visual = trimesh.visual.TextureVisuals(material=material(CONCRETE, f"{name}_material"))
            mesh.apply_transform(enu_to_gltf)
            scene.add_geometry(mesh, geom_name=f"{name}__{index}", node_name=f"{name}__{index}")
            index += 1

    out_path = os.path.join(ROOT, "props", "connector_paths.glb")
    scene.export(out_path)

    loaded = trimesh.load(out_path)
    geometries = list(loaded.geometry.values())
    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres), origin 12.9487N 80.1394E; WORLD-POSITIONED",
        "placement": "SITED (approximate, source: roads_geometry): endpoints snapped to avenue / Rajam Hall Road / service-road edges extracted from roads/roads_v2.glb + data/osm_raw.osm on 2026-10-21; see generator docstring for the per-path endpoints.",
        "provenance": "Original procedural geometry; endpoint coordinates derive from OpenStreetMap data (ODbL) via data/osm_raw.osm and the repo's own roads layer.",
        "generator": "tools/connector_paths.py",
        "output": "props/connector_paths.glb",
        "paths": {
            name: {"polyline_enu": [list(p) for p in points], "width_m": width}
            for name, (points, width) in PATHS.items()
        },
        "glb_stats": {
            "geometries": len(geometries),
            "vertices": int(sum(len(g.vertices) for g in geometries)),
            "faces": int(sum(len(g.faces) for g in geometries)),
            "bounds_gltf": [[round(float(v), 2) for v in row] for row in loaded.bounds.tolist()],
        },
        "integration": "Registered in ChromepetSync.Glbs (world-positioned). Registry: data/placement_map.json (ids connector_oat, connector_letters, connector_statue, connector_prodtech, connector_grove).",
    }
    with open(os.path.join(ROOT, "data", "connector_paths_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
