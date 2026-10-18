# Chromepet – MIT Chromepet (Anna University), Chennai
Area starter centred on the MIT campus, Chromepet (bbox 12.935–12.960 N, 80.128–80.152 E; includes Chromepet station, GST Road, MIT flyover). Real extruded meshes from OpenStreetMap (no voxels).

| Folder | Contents |
|---|---|
| `data/` | `osm_raw.osm`, `preview.png`, `stats.json` |
| `buildings/` | `buildings.obj` (8,792 OSM footprints, heights estimated) |
| `roads/` | `roads.obj` |
| `ground/` | `ground.obj` (flat) |
| `combined/` | `chrompet_mit.glb` (all layers) |
| `props/` | placeholder |
| `tools/` | `osm_to_mesh.py` |
| `unity/` | Unity 2022.3 project (controller, scene builder, Mixamo setup) |
| `characters/` | Mixamo drop folder + instructions |

Coordinates: metres, X=east, Z=north, Y=up, origin 12.9487 N 80.1394 E. Spawn: MIT South Gate.

## Approach
* **Gameplay (offline):** procedural OSM meshes – ODbL; refine MIT buildings by hand in Blender (BlenderOSM / Blender GIS).
* **Optional online backdrop:** Cesium for Unity + Google Photorealistic 3D Tiles. Streaming only; no caching/offline, no tracing/deriving models; credits on screen (https://developers.google.com/maps/documentation/tile/policies). Chennai photoreal coverage is unconfirmed – Google's country table lists India as 2D only (https://developers.google.com/maps/coverage).
* Gaps: OSM has 0 height tags / 17 levels tags here; MIT campus outline not mapped in OSM; no DEM yet.

Data © OpenStreetMap contributors (ODbL).
