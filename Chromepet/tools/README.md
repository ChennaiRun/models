# tools
`python3 osm_to_mesh.py ../data/osm_raw.osm <outdir>` (needs trimesh shapely scipy matplotlib). Writes buildings/roads/ground .obj, combined .glb, stats.json, preview.png into <outdir>; move them into the area folders.

## v2 (procedural detail, mit_details.py)
Requires `pip install trimesh shapely scipy pillow numpy`. Run from `Chromepet/`: `python3 tools/mit_details.py` (~30 s). Writes `buildings/campus_buildings.glb`, `buildings/outside_buildings.glb`, `roads/roads_v2.glb`, `ground/ground_v2.glb`, `props/landmarks.glb`, `props/trees.glb`, `props/trees_colliders.json`, `data/v2_meta.json` (spawn, building style assignments). Output is standard glTF (+Y up, x=east, z=-north). Features not in OSM are approximate placements from the reference videos.

## Chrompet identity layer (chrompet_identity.py)

Requires `pip install trimesh pillow numpy`. Run from `Chromepet/`: `python3 tools/chrompet_identity.py`. This script does not require `data/osm_raw.osm`, so it works before Git LFS data is fetched. It writes `props/chrompet_identity.glb` and `data/identity_meta.json` in the same v2 coordinate frame. See `../REFERENCE_MEDIA.md` for the observation sources and licensing notes.

## Detailed buildings

`ct_charles_babbage_bpy.py` runs inside Blender: `blender -b -P tools/ct_charles_babbage_bpy.py`. It writes `buildings/detailed/ct_charles_babbage.glb`. Detailed generators should remain additive and own exactly one output where practical so separate agents can work without regenerating the area-wide building layer.
