# tools
`python3 osm_to_mesh.py ../data/osm_raw.osm <outdir>` (needs trimesh shapely scipy matplotlib). Writes buildings/roads/ground .obj, combined .glb, stats.json, preview.png into <outdir>; move them into the area folders.

## v2 (procedural detail, mit_details.py)
Requires `pip install trimesh shapely scipy pillow numpy`. Run from `Chromepet/`: `python3 tools/mit_details.py` (~30 s). Writes `buildings/campus_buildings.glb`, `buildings/outside_buildings.glb`, `roads/roads_v2.glb`, `ground/ground_v2.glb`, `props/landmarks.glb`, `props/trees.glb`, `props/trees_colliders.json`, `data/v2_meta.json` (spawn, building style assignments). Output is standard glTF (+Y up, x=east, z=-north). Features not in OSM are approximate placements from the reference videos.
