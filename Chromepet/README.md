# Chromepet – MIT Chromepet (Anna University), Chennai
Area starter centred on the MIT campus, Chromepet (bbox 12.935–12.960 N, 80.128–80.152 E; includes Chromepet station, GST Road, MIT flyover). Real extruded meshes from OpenStreetMap (no voxels).

| Folder | Contents |
|---|---|
| `data/` | `osm_raw.osm`, `preview.png`, `stats.json`, `v2_meta.json`, `identity_meta.json`, per-model metadata for the Drive-photo models (`oat_meta.json`, `garden_landmarks_meta.json`, `production_frontage_meta.json`, `navy_aircraft_meta.json`, `connector_paths_meta.json`), the station furniture and rail corridor metadata (`station_details_meta.json`, `rail_corridor_meta.json`) + corridor OSM provenance (`rail_corridor.osm`), and the placement registry `placement_map.json` + visual `placement_map.png` (see [`PLACEMENT_MAP.md`](PLACEMENT_MAP.md)) |
| `buildings/` | v2 area layers plus additive replacements in `detailed/` (Charles Babbage Block; Production Technology frontage overlay); v1: `buildings.obj` |
| `roads/` | v2: `roads_v2.glb` (GST Road, MIT Flyover, railway, station, overbridge, subway, poles); v1: `roads.obj` |
| `ground/` | v2: `ground_v2.glb` (campus ground, interlock paving, tactile strips); v1: `ground.obj` |
| `combined/` | `chrompet_mit.glb` — LEGACY v1 combined export (`tools/osm_to_mesh.py`, z=north frame, mirrored vs v2). Stale: not regenerated and not used by Unity sync; the v2 layers above are canonical. |
| `props/` | `landmarks.glb`, `chrompet_identity.glb`, `trees.glb`, `trees_colliders.json`, plus additive Drive-photo models, all world-positioned and sited (2026-10-21): `open_air_theatre.glb`, `mit_letters.glb`, `golden_statue_garden.glb`, `pergola.glb`, `gazebo.glb`, `navy_aircraft_display.glb`, and `connector_paths.glb` linking them to the road network; `chrompet_station_details.glb` (2026-10-31) adds platform furniture on the station |
| `tools/` | Area, identity and detailed-building generators; see `tools/README.md` |
| `unity/` | Unity 2022.3 project (controller, scene builder, Vikram avatar setup) |

Coordinates (v2 GLB): standard glTF, metres, x=east, y=up, z=-north, origin 12.9487 N 80.1394 E. v1 OBJs used z=north and appear mirrored east-west in Unity; use v2.
Spawn: on the campus avenue 12 m inside the Main Gate (OSM node 432468247, MIT Road right after the MIT Flyover). Video sources: `REFERENCE_VIDEOS.md`.
Asset positions: [`PLACEMENT_MAP.md`](PLACEMENT_MAP.md) / `data/placement_map.json` is the registry of every asset's ENU coordinates, heading, footprint and connections — consult it before moving or adding models.

The separate identity layer adds four current-style Chrompet station nameboards, a station office, a three-car Chennai suburban EMU and four auto-rickshaws. Browser/map and CC image references are recorded in `REFERENCE_MEDIA.md`; the meshes are original procedural geometry and do not contain Google or source-photo pixels.

Player models are shared across areas in [`../players/`](../players/).

New contributors and coding agents should follow the repository-level [`MODEL_STANDARDS.md`](../MODEL_STANDARDS.md), [`CONTRIBUTING.md`](../CONTRIBUTING.md) and [`AGENTS.md`](../AGENTS.md). Prefer new identity layers or `buildings/detailed/` replacements so concurrent work does not regenerate the shared area GLBs.

## Approach
* **Gameplay (offline):** procedural OSM meshes – ODbL; refine MIT buildings by hand in Blender (BlenderOSM / Blender GIS).
* **Optional online backdrop:** Cesium for Unity + Google Photorealistic 3D Tiles. Streaming only; no caching/offline, no tracing/deriving models; credits on screen (https://developers.google.com/maps/documentation/tile/policies). Chennai photoreal coverage is unconfirmed – Google's country table lists India as 2D only (https://developers.google.com/maps/coverage).
* Gaps: OSM has 0 height tags / 17 levels tags here; MIT campus outline not mapped in OSM; no DEM yet.

Data © OpenStreetMap contributors (ODbL).

## Improvement pass (2026-10-21)

Generator-level photo corrections, all render-verified before/after (backups kept outside the repo):
`mit_details.py` — Production Technology no longer shares the Automobile 'auto' style: new 'prodtech' style (cream + mustard bands + blue sign band, photos 14/45.jpg); RLHC split from 'lhc' into 'rlhc' (white block, round-column portico, red doors, photos 52/53.jpg; the pale-green LHC of photo 31.jpg is unchanged); Aeronautical restyled maroon/cream (photo 22.jpg); the avenue fountain's ANNA UNIVERSITY sign moved to the avenue-facing side of its block, where it reads correctly (it was mirrored and unreadable). `chrompet_identity.py` — station nameboard text UVs fixed (Tamil/Hindi/English read correctly on both faces now) and Linux Noto font fallbacks added. Regeneration is deterministic: roads/ground/trees/outside-buildings outputs are byte-identical; only campus_buildings, landmarks and chrompet_identity changed. The Charles Babbage detailed block was assessed and left unchanged (its generator needs Blender, unavailable on the build machine; the 2026-10-21 magenta fix is intact).

## Improvement pass (2026-10-31)

Additive station and garden work, no shared layers regenerated (roads/ground/trees/outside-buildings outputs untouched):
`tools/station_details.py` (new) — platform furniture layer `props/chrompet_station_details.glb` on the two existing roads-layer platforms: edge warning lines, tactile strips, 16 benches, 6 double-sided hanging number boards (original artwork, Latin text), 16 under-canopy tube lights, 8 dustbins. Slab centres/axis/heights were measured from `roads/roads_v2.glb` and baked as documented constants, so the generator needs no LFS input. `tools/connector_paths.py` — added the Admin garden loop (west service road -> gazebo -> pergola -> Admin Block west face); the pergola, gazebo and Admin Block previously had no paved connection to the road network. `tools/rail_corridor.py` (new) — suburban rail corridor `props/rail_corridor.glb` from Guindy to Vandalur along the OSM station-node alignment (Overpass 2026-10-31, ODbL, provenance `data/rail_corridor.osm`): two broad-gauge tracks with ballast and OHE on a ground strip, clipped out of the area bbox where roads_v2 already carries the railway; detailed stations at Guindy, Pallavaram, Tambaram Sanatorium and Vandalur, minor platforms at the six intermediate suburban stations; Chrompet itself is untouched (the corridor threads through the existing station). Registry, `PLACEMENT_MAP.md` and `placement_map.png` updated; both new GLBs added to `ChromepetSync.Glbs` (world-baked, load at identity). Unity scene-builder change is compile-unverified (no Unity editor on the build machine), same caveat as the 2026-10-21 pass.
