# Chromepet – MIT Chromepet (Anna University), Chennai
Area starter centred on the MIT campus, Chromepet (bbox 12.935–12.960 N, 80.128–80.152 E; includes Chromepet station, GST Road, MIT flyover). Real extruded meshes from OpenStreetMap (no voxels).

| Folder | Contents |
|---|---|
| `data/` | `osm_raw.osm`, `preview.png`, `stats.json`, `v2_meta.json`, `identity_meta.json`, plus per-model metadata for the Drive-photo models (`oat_meta.json`, `garden_landmarks_meta.json`, `production_frontage_meta.json`, `navy_aircraft_meta.json`) |
| `buildings/` | v2 area layers plus additive replacements in `detailed/` (currently Charles Babbage Block); v1: `buildings.obj` |
| `roads/` | v2: `roads_v2.glb` (GST Road, MIT Flyover, railway, station, overbridge, subway, poles); v1: `roads.obj` |
| `ground/` | v2: `ground_v2.glb` (campus ground, interlock paving, tactile strips); v1: `ground.obj` |
| `combined/` | `chrompet_mit.glb` (all layers) |
| `props/` | `landmarks.glb`, `chrompet_identity.glb`, `trees.glb`, `trees_colliders.json`, plus additive Drive-photo models: `open_air_theatre.glb`, `avenue_garden_landmarks.glb`, `navy_aircraft_display.glb` |
| `tools/` | Area, identity and detailed-building generators; see `tools/README.md` |
| `unity/` | Unity 2022.3 project (controller, scene builder, Vikram avatar setup) |

Coordinates (v2 GLB): standard glTF, metres, x=east, y=up, z=-north, origin 12.9487 N 80.1394 E. v1 OBJs used z=north and appear mirrored east-west in Unity; use v2.
Spawn: on the campus avenue 12 m inside the Main Gate (OSM node 432468247, MIT Road right after the MIT Flyover). Video sources: `REFERENCE_VIDEOS.md`.

The separate identity layer adds four current-style Chrompet station nameboards, a station office, a three-car Chennai suburban EMU and four auto-rickshaws. Browser/map and CC image references are recorded in `REFERENCE_MEDIA.md`; the meshes are original procedural geometry and do not contain Google or source-photo pixels.

Player models are shared across areas in [`../players/`](../players/).

New contributors and coding agents should follow the repository-level [`MODEL_STANDARDS.md`](../MODEL_STANDARDS.md), [`CONTRIBUTING.md`](../CONTRIBUTING.md) and [`AGENTS.md`](../AGENTS.md). Prefer new identity layers or `buildings/detailed/` replacements so concurrent work does not regenerate the shared area GLBs.

## Approach
* **Gameplay (offline):** procedural OSM meshes – ODbL; refine MIT buildings by hand in Blender (BlenderOSM / Blender GIS).
* **Optional online backdrop:** Cesium for Unity + Google Photorealistic 3D Tiles. Streaming only; no caching/offline, no tracing/deriving models; credits on screen (https://developers.google.com/maps/documentation/tile/policies). Chennai photoreal coverage is unconfirmed – Google's country table lists India as 2D only (https://developers.google.com/maps/coverage).
* Gaps: OSM has 0 height tags / 17 levels tags here; MIT campus outline not mapped in OSM; no DEM yet.

Data © OpenStreetMap contributors (ODbL).
