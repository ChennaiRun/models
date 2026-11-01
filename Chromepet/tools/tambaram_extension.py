"""Tambaram extension: ground, water, roads and buildings south of the
Chromepet area down to Tambaram station -- additive area layer.

Extends the Chromepet area (bbox south edge 12.935 N) to just south of
Tambaram station, covering the GST Road (NH45) corridor, the Tambaram
Flyover, Camp Road / Gandhi Road market streets, Tambaram town and the
Chitlapakkam / Tambaram Sanatorium lakes east of the tracks.

Geometry source: OpenStreetMap via Overpass (ODbL), extract committed at
data/tambaram_extension.osm (fetched 2026-10-31; buildings, highways,
water, no relations). Google Earth/Maps imagery was used for general
layout observation only -- no pixels, tracing or photogrammetry from it,
per MODEL_STANDARDS.md.

Outputs (all world-positioned in the v2 frame: metres, x=east, y=up,
z=-north, origin 12.9487 N 80.1394 E):

* ground/tambaram_ground.glb    -- earth base quad + lake polygons
* roads/tambaram_roads.glb      -- road strips by OSM highway class
                                   (GST Road trunk, Tambaram Flyover
                                   elevated with piers, market streets)
* buildings/tambaram_buildings.glb -- 10.8k extruded footprints
                                   (levels*3 m where tagged, else 7 m;
                                   simple style palette, merged meshes)

Buildings/roads/water north of 12.9353 N are dropped -- the v2 area
layers already cover that band. Heights are generic (OSM has almost no
levels tags here: 41/10868), so blocks are approximate massing, not
surveyed architecture.

Requires data/tambaram_extension.osm (Git LFS source, like mit_details.py
requires osm_raw.osm). Run from Chromepet/:
    python3 tools/tambaram_extension.py
Dependencies: trimesh, shapely, numpy, mapbox-earcut
"""

import json
import math
import os
import xml.etree.ElementTree as ET

import numpy as np
import trimesh
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OSM_PATH = os.path.join(ROOT, "data", "tambaram_extension.osm")

ORIGIN_LAT, ORIGIN_LON = 12.9487, 80.1394
EARTH_R = 6378137.0
NORTH_CLIP = 12.9353  # v2 area layers cover north of this

# (width m, height m, color) per OSM highway class.
ROAD_STYLES = {
    "trunk": (14.0, 0.06, (0.24, 0.24, 0.26)),
    "trunk_link": (10.0, 0.06, (0.24, 0.24, 0.26)),
    "primary": (12.0, 0.06, (0.26, 0.26, 0.28)),
    "primary_link": (8.0, 0.06, (0.26, 0.26, 0.28)),
    "secondary": (9.0, 0.05, (0.30, 0.30, 0.31)),
    "secondary_link": (7.0, 0.05, (0.30, 0.30, 0.31)),
    "tertiary": (7.0, 0.05, (0.32, 0.32, 0.33)),
    "tertiary_link": (6.0, 0.05, (0.32, 0.32, 0.33)),
    "residential": (4.5, 0.04, (0.36, 0.36, 0.36)),
    "unclassified": (4.5, 0.04, (0.36, 0.36, 0.36)),
    "living_street": (4.5, 0.04, (0.36, 0.36, 0.36)),
    "service": (3.5, 0.04, (0.40, 0.40, 0.39)),
    "busway": (5.0, 0.04, (0.34, 0.34, 0.35)),
    "track": (3.0, 0.03, (0.45, 0.42, 0.36)),
    "footway": (2.0, 0.03, (0.55, 0.53, 0.48)),
    "path": (2.0, 0.03, (0.55, 0.53, 0.48)),
    "pedestrian": (3.0, 0.03, (0.55, 0.53, 0.48)),
    "steps": (2.0, 0.03, (0.55, 0.53, 0.48)),
}
FLYOVER_NAME = "Tambaram Flyover"
FLYOVER_H = 6.0

BUILDING_STYLES = {
    "commercial": (0.78, 0.68, 0.55),
    "retail": (0.78, 0.68, 0.55),
    "office": (0.72, 0.72, 0.75),
    "apartments": (0.80, 0.78, 0.72),
    "residential": (0.85, 0.83, 0.76),
    "house": (0.85, 0.83, 0.76),
    "detached": (0.85, 0.83, 0.76),
    "industrial": (0.62, 0.66, 0.70),
    "warehouse": (0.62, 0.66, 0.70),
    "school": (0.82, 0.75, 0.62),
    "college": (0.82, 0.75, 0.62),
    "hospital": (0.88, 0.88, 0.88),
    "train_station": (0.75, 0.62, 0.50),
    "church": (0.88, 0.86, 0.80),
    "temple": (0.85, 0.60, 0.35),
}
DEFAULT_BUILDING_COLOR = (0.82, 0.80, 0.74)
GROUND_COLOR = (0.42, 0.46, 0.34)
WATER_COLOR = (0.20, 0.38, 0.55)


def local_xy(lat, lon):
    x = math.radians(lon - ORIGIN_LON) * EARTH_R * math.cos(math.radians(ORIGIN_LAT))
    y = math.radians(lat - ORIGIN_LAT) * EARTH_R
    return (x, y)


def enu_to_gltf():
    return np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)


class Layer:
    def __init__(self):
        self.parts = []

    def add(self, mesh, color, name):
        mesh.visual = trimesh.visual.TextureVisuals(
            material=trimesh.visual.material.PBRMaterial(
                name=f"{name}_material",
                baseColorFactor=[*(int(c * 255) for c in color), 255],
                metallicFactor=0.0,
                roughnessFactor=0.9,
            )
        )
        self.parts.append((name, mesh))

    def export(self, path):
        scene = trimesh.Scene()
        transform = enu_to_gltf()
        for index, (name, mesh) in enumerate(self.parts):
            mesh = mesh.copy()
            mesh.apply_transform(transform)
            scene.add_geometry(mesh, geom_name=f"{name}__{index}", node_name=f"{name}__{index}")
        scene.export(path)


def parse_osm(path):
    nodes, ways = {}, []
    for event, el in ET.iterparse(path, events=("end",)):
        if el.tag == "node":
            nodes[int(el.get("id"))] = (float(el.get("lat")), float(el.get("lon")))
            el.clear()
        elif el.tag == "way":
            tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
            refs = [int(nd.get("ref")) for nd in el.findall("nd")]
            ways.append((tags, refs))
            el.clear()
    return nodes, ways


def way_points(refs, nodes):
    pts = [local_xy(*nodes[r]) for r in refs if r in nodes]
    return pts if len(pts) >= 2 else None


def centroid_north(pts):
    return sum(p[1] for p in pts) / len(pts)


def build_ground_water(nodes, ways, bbox_enu):
    layer = Layer()
    (x0, y0), (x1, y1) = bbox_enu
    quad = trimesh.creation.box(extents=[x1 - x0, y1 - y0, 0.1])
    quad.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, -0.06])
    layer.add(quad, GROUND_COLOR, "Tambaram_ground")

    waters = []
    for tags, refs in ways:
        if tags.get("natural") != "water" and tags.get("landuse") not in ("reservoir", "basin"):
            continue
        pts = way_points(refs, nodes)
        if not pts or len(pts) < 3:
            continue
        if centroid_north(pts) > local_xy(NORTH_CLIP, ORIGIN_LON)[1]:
            continue
        poly = Polygon(pts)
        if not poly.is_valid or poly.area < 50:
            continue
        waters.append(poly)
    water_count = 0
    for poly in waters:
        try:
            mesh = trimesh.creation.extrude_polygon(poly, 0.04)
        except Exception:
            continue
        mesh.apply_translation([0, 0, 0.0])
        layer.add(mesh, WATER_COLOR, "Tambaram_water")
        water_count += 1
    layer.export(os.path.join(ROOT, "ground", "tambaram_ground.glb"))
    return water_count


def build_roads(nodes, ways):
    layer = Layer()
    by_class = {}
    flyover_lines = []
    for tags, refs in ways:
        hw = tags.get("highway")
        if hw not in ROAD_STYLES or hw == "construction":
            continue
        pts = way_points(refs, nodes)
        if not pts or centroid_north(pts) > local_xy(NORTH_CLIP, ORIGIN_LON)[1]:
            continue
        if tags.get("name") == FLYOVER_NAME or (hw == "trunk_link" and "Flyover" in (tags.get("name") or "")):
            flyover_lines.append(pts)
            continue
        by_class.setdefault(hw, []).append(pts)

    stats = {}
    for hw, lines in sorted(by_class.items()):
        width, height, color = ROAD_STYLES[hw]
        buffered = []
        for pts in lines:
            line = LineString(pts)
            if line.length < 1.0:
                continue
            buffered.append(line.buffer(width / 2, cap_style="flat", join_style="mitre"))
        if not buffered:
            continue
        merged = unary_union(buffered)
        polys = list(merged.geoms) if merged.geom_type == "MultiPolygon" else [merged]
        meshes = []
        for poly in polys:
            if poly.area < 2:
                continue
            try:
                meshes.append(trimesh.creation.extrude_polygon(poly, height))
            except Exception:
                continue
        if meshes:
            group = trimesh.util.concatenate(meshes)
            group.apply_translation([0, 0, 0.02])
            layer.add(group, color, f"Tambaram_roads_{hw}")
            stats[hw] = {"ways": len(lines), "polygons": len(polys)}

    # Tambaram Flyover: elevated strip with piers.
    if flyover_lines:
        width, _, color = ROAD_STYLES["trunk_link"]
        deck_parts, pier_parts = [], []
        for pts in flyover_lines:
            line = LineString(pts)
            deck = line.buffer(width / 2, cap_style="flat", join_style="mitre")
            try:
                mesh = trimesh.creation.extrude_polygon(deck, 0.5)
                mesh.apply_translation([0, 0, FLYOVER_H])
                deck_parts.append(mesh)
            except Exception:
                pass
            step = max(1, int(line.length / 30))
            for i in range(0, len(pts) - 1, step):
                pier = trimesh.creation.cylinder(radius=0.9, height=FLYOVER_H, sections=10)
                pier.apply_translation([pts[i][0], pts[i][1], FLYOVER_H / 2])
                pier_parts.append(pier)
        if deck_parts:
            layer.add(trimesh.util.concatenate(deck_parts), color, "Tambaram_flyover_deck")
        if pier_parts:
            layer.add(trimesh.util.concatenate(pier_parts), (0.55, 0.55, 0.55), "Tambaram_flyover_piers")
        stats["flyover"] = {"ways": len(flyover_lines), "piers": len(pier_parts)}

    layer.export(os.path.join(ROOT, "roads", "tambaram_roads.glb"))
    return stats


def build_buildings(nodes, ways):
    layer = Layer()
    by_color = {}
    stats = {"total": 0, "with_levels": 0, "skipped": 0}
    for tags, refs in ways:
        if "building" not in tags:
            continue
        pts = way_points(refs, nodes)
        if not pts or len(pts) < 3:
            stats["skipped"] += 1
            continue
        if centroid_north(pts) > local_xy(NORTH_CLIP, ORIGIN_LON)[1]:
            continue
        poly = Polygon(pts)
        if not poly.is_valid or poly.area < 4:
            stats["skipped"] += 1
            continue
        levels = tags.get("building:levels")
        try:
            height = max(2.5, min(60.0, float(levels) * 3.0)) if levels else 7.0
            if levels:
                stats["with_levels"] += 1
        except ValueError:
            height = 7.0
        color = BUILDING_STYLES.get(tags["building"], DEFAULT_BUILDING_COLOR)
        try:
            mesh = trimesh.creation.extrude_polygon(poly, height)
        except Exception:
            stats["skipped"] += 1
            continue
        by_color.setdefault(color, []).append(mesh)
        stats["total"] += 1
    for index, (color, meshes) in enumerate(sorted(by_color.items())):
        layer.add(trimesh.util.concatenate(meshes), color, f"Tambaram_buildings_{index}")
    layer.export(os.path.join(ROOT, "buildings", "tambaram_buildings.glb"))
    stats["styles"] = len(by_color)
    return stats


def glb_stats(path):
    loaded = trimesh.load(path)
    geometries = list(loaded.geometry.values())
    return {
        "geometries": len(geometries),
        "vertices": int(sum(len(g.vertices) for g in geometries)),
        "faces": int(sum(len(g.faces) for g in geometries)),
        "bounds_gltf": [[round(float(v), 2) for v in row] for row in loaded.bounds.tolist()],
    }


def main():
    nodes, ways = parse_osm(OSM_PATH)
    lats = [lat for lat, lon in nodes.values()]
    lons = [lon for lat, lon in nodes.values()]
    south, west = min(lats), min(lons)
    bbox_enu = (local_xy(south, west), local_xy(NORTH_CLIP, max(lons)))

    water_count = build_ground_water(nodes, ways, bbox_enu)
    road_stats = build_roads(nodes, ways)
    building_stats = build_buildings(nodes, ways)

    meta = {
        "frame": "glTF: x=east, y=up, z=-north (metres), origin 12.9487N 80.1394E; WORLD-POSITIONED",
        "extent": "OSM extract south of 12.9353 N to just past Tambaram station (the v2 area layers cover the band north of it)",
        "source": "OpenStreetMap via Overpass, 2026-10-31 (ODbL); extract at data/tambaram_extension.osm. Google Earth/Maps used for layout observation only (no pixels/tracing), per MODEL_STANDARDS.md.",
        "approximations": "Building heights generic (levels*3 m where tagged, else 7 m); flyover deck at a constant 6 m; road widths by highway class. Massing, not surveyed architecture.",
        "generator": "tools/tambaram_extension.py",
        "outputs": {
            "ground/tambaram_ground.glb": glb_stats(os.path.join(ROOT, "ground", "tambaram_ground.glb")),
            "roads/tambaram_roads.glb": glb_stats(os.path.join(ROOT, "roads", "tambaram_roads.glb")),
            "buildings/tambaram_buildings.glb": glb_stats(os.path.join(ROOT, "buildings", "tambaram_buildings.glb")),
        },
        "water_bodies": water_count,
        "roads": road_stats,
        "buildings": building_stats,
        "integration": "Registered in ChromepetSync.Glbs (world-positioned). Registry: data/placement_map.json (id tambaram_extension).",
    }
    with open(os.path.join(ROOT, "data", "tambaram_extension_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({k: meta[k] for k in ("water_bodies", "roads", "buildings")}, indent=2))


if __name__ == "__main__":
    main()
