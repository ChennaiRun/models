# tools
`python3 osm_to_mesh.py ../data/osm_raw.osm <outdir>` (needs trimesh shapely scipy matplotlib). Writes buildings/roads/ground .obj, combined .glb, stats.json, preview.png into <outdir>; move them into the area folders.

## v2 (procedural detail, mit_details.py)
Requires `pip install trimesh shapely scipy pillow numpy`. Run from `Chromepet/`: `python3 tools/mit_details.py` (~30 s). Writes `buildings/campus_buildings.glb`, `buildings/outside_buildings.glb`, `roads/roads_v2.glb`, `ground/ground_v2.glb`, `props/landmarks.glb`, `props/trees.glb`, `props/trees_colliders.json`, `data/v2_meta.json` (spawn, building style assignments). Output is standard glTF (+Y up, x=east, z=-north). Features not in OSM are approximate placements from the reference videos.

## Chrompet identity layer (chrompet_identity.py)

Requires `pip install trimesh pillow numpy`. Run from `Chromepet/`: `python3 tools/chrompet_identity.py`. This script does not require `data/osm_raw.osm`, so it works before Git LFS data is fetched. It writes `props/chrompet_identity.glb` and `data/identity_meta.json` in the same v2 coordinate frame. See `../REFERENCE_MEDIA.md` for the observation sources and licensing notes.

## Detailed buildings

`ct_charles_babbage_bpy.py` runs inside Blender: `blender -b -P tools/ct_charles_babbage_bpy.py`. It writes `buildings/detailed/ct_charles_babbage.glb`. Detailed generators should remain additive and own exactly one output where practical so separate agents can work without regenerating the area-wide building layer.

## Drive-photo models (2026-10-20)

Standalone trimesh generators from the user's own MIT campus photos (Drive folder 'mit'; full catalogue in `../REFERENCE_VIDEOS.md`). Like the identity layer they need no OSM/LFS input: `pip install trimesh numpy pillow`, run from `Chromepet/` as `python3 tools/<name>.py`. Each writes one additive GLB plus a metadata JSON in `../data/`.

* `oat_theatre.py` -> `../props/open_air_theatre.glb` + `oat_meta.json` (origin-centred)
* `avenue_garden_landmarks.py` -> `../props/avenue_garden_landmarks.glb` + `garden_landmarks_meta.json` (origin-centred set)
* `production_technology_frontage.py` -> `../buildings/detailed/production_technology_frontage.glb` + `production_frontage_meta.json` (origin-centred)
* `navy_aircraft.py` -> `../props/navy_aircraft_display.glb` + `navy_aircraft_meta.json` (world-positioned, registered in ChromepetSync)
