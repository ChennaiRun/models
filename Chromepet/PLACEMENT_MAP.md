# Chromepet placement map

The registry for every buildable asset in the Chromepet area: where it sits, which way it faces, and what it connects to. The machine-readable source of truth is [`data/placement_map.json`](data/placement_map.json); this document explains it and reproduces the full table. The top-down visual map is [`data/placement_map.png`](data/placement_map.png), generated from the JSON by `tools/placement_map_image.py` (regenerate after any registry change so the picture can never drift from the data).

## Frame and conventions

- Origin: **12.9487 N, 80.1394 E** (MIT Chromepet). All positions are ENU metres from the origin: `position_enu = [east_m, north_m]`.
- glTF: `(x, y, z) = (east, up, -north)`. Unity: `(x, y, z) = (east, up, north)`.
- Convert ENU back to lat/lon: `lat = 12.9487 + degrees(north / 6378137)`; `lon = 80.1394 + degrees(east / (6378137 * cos(12.9487 deg)))`. The table below carries the computed lat/lon per asset.
- `heading_deg` is the compass bearing (clockwise from north) of the asset's local +Y axis after placement. The ENU yaw used when baking a GLB is `(-heading_deg) mod 360`.
- `footprint_m` is `[width along local X, depth along local Y]` before heading rotation; `height_m` is the world up extent.
- `source`: `osm` = OpenStreetMap geometry (`data/osm_raw.osm`, ODbL); `v2_meta` = anchors recorded by the v2 build (`data/v2_meta.json`, `data/identity_meta.json`); `roads_geometry` = measured from `roads/roads_v2.glb` / `buildings/campus_buildings.glb`; `photo_relative` = placed relative to neighbours from the user's campus photos. `confidence: approximate` means geometry-derived, not surveyed — expect metre-level error.

## How a game builder uses the JSON

- **area_layer** — world-baked GLB spanning the area; load once at the identity transform. Individual buildings/landmarks inside a layer also appear as anchor entries (their `glb` points at the layer file).
- **prop / landmark_group (world-baked)** — the GLB already carries its site; load at the identity transform. `position_enu` is the asset's anchor point (usually its centre), `heading_deg` is informational.
- **detailed_building** — world-baked replacements also load at identity, *except* `production_technology_frontage`, whose GLB is origin-centred: place its root at `position_enu` with Unity rotation Y = `-56.29` (from `heading_deg` 303.71). `ChrompetSceneBuilder.Placements` already encodes exactly this — the JSON and the C# must stay in sync.
- **connector** — flat path strips in `props/connector_paths.glb` (world-baked); `connects_to` names the assets each path joins. The road network itself is in `road_network` (centreline polylines + widths) for pathfinding/spawn logic.
- Player spawn (from the v2 build): ENU **(-70.91, -253.28)**, on the avenue 12 m inside the Main Gate, facing into campus.

## Asset table

| id | name | ENU (east, north) | lat, lon | heading | footprint (m) | height | source | conf. | connects to |
|---|---|---|---|---|---|---|---|---|---|
| ground_layer | Ground layer (campus + outside ground, avenue paving) | (0.0, 0.0) | 12.9487, 80.1394 | 0.0 | 2600.0 x 2800.0 | 0.12 | v2_meta | high | - |
| roads_layer | Roads layer (GST Road, MIT Flyover, railway, station, campus roads) | (0.0, 0.0) | 12.9487, 80.1394 | 0.0 | 2600.0 x 2800.0 | 9.4 | v2_meta | high | - |
| campus_buildings_layer | Campus buildings layer (60 procedural MIT buildings) | (0.0, 0.0) | 12.9487, 80.1394 | 0.0 | 511.5 x 733.9 | 19.9 | v2_meta | high | - |
| outside_buildings_layer | Outside buildings layer (8,732 surrounding buildings) | (0.0, 0.0) | 12.9487, 80.1394 | 0.0 | 2600.0 x 2800.0 | 21.0 | v2_meta | high | - |
| landmarks_layer | Landmarks layer (gate, fountain, tank, walkway, grove aircraft, spawn markers) | (0.0, 0.0) | 12.9487, 80.1394 | 0.0 | 560.0 x 740.0 | 27.0 | v2_meta | high | - |
| trees_layer | Trees layer (2,510 trees) | (0.0, 0.0) | 12.9487, 80.1394 | 0.0 | 2600.0 x 2800.0 | 12.0 | v2_meta | high | - |
| chrompet_identity | Chrompet identity layer (station boards, office, EMU, auto-rickshaws) | (156.52, 328.51) | 12.951651, 80.140843 | 0.0 | 366.0 x 636.0 | 6.0 | v2_meta | high | roads_layer |
| main_gate | Main Gate (MIT South Gate) | (-77.67, -263.19) | 12.946336, 80.138684 | 34.3 | 17.5 x 2.2 | 8.4 | osm | high | roads_layer, mit_letters |
| admin_block | Admin Block & Dean Office (procedural) | (25.3, -74.3) | 12.948033, 80.139633 | 0.0 | 28.0 x 18.0 | 14.0 | osm | high | pergola, gazebo |
| charles_babbage_block | Charles Babbage Block (detailed) | (249.5, 168.2) | 12.950211, 80.1417 | 0.0 | 42.9 x 31.8 | 8.8 | v2_meta | high | campus_buildings_layer |
| rajam_statue_arch | Rajam statue arch + pool (landmarks layer) | (217.6, 0.5) | 12.948704, 80.141406 | 303.0 | 8.0 x 5.0 | 6.3 | osm | high | golden_statue_garden, connector_statue |
| avenue_fountain | Avenue fountain + Anna University sign | (-28.2, -163.9) | 12.947228, 80.13914 | 0.0 | 11.4 x 11.4 | 1.9 | v2_meta | high | roads_layer |
| aircraft_grove | Aircraft display grove (Sea Hawk, Gnat, jet engines) | (142.6, -10.2) | 12.948608, 80.140714 | 0.0 | 36.0 x 28.0 | 5.0 | v2_meta | high | navy_aircraft_display, connector_grove |
| open_air_theatre | Open Air Theatre (OAT) | (-26.0, -116.0) | 12.947658, 80.13916 | 0.0 | 63.0 x 63.2 | 4.86 | roads_geometry | approximate | connector_oat, roads_layer |
| mit_letters | MIT letters monument | (-50.1, -245.7) | 12.946493, 80.138938 | 304.27 | 13.2 x 3.7 | 3.38 | osm | approximate | connector_letters, main_gate |
| golden_statue_garden | Golden statue garden (C. Rajam) | (224.0, 10.0) | 12.94879, 80.141465 | 34.0 | 6.8 x 10.5 | 3.54 | osm | approximate | connector_statue, rajam_statue_arch |
| pergola | Garden pergola | (-18.0, -80.0) | 12.947981, 80.139234 | 0.0 | 8.8 x 4.6 | 3.53 | photo_relative | approximate | gazebo, admin_block |
| gazebo | Garden gazebo | (-36.0, -64.0) | 12.948125, 80.139068 | 0.0 | 8.7 x 7.2 | 5.03 | photo_relative | approximate | pergola, admin_block |
| production_technology_frontage | Department of Production Technology frontage (detailed) | (170.42, 75.39) | 12.949377, 80.140971 | 303.71 | 26.5 x 6.9 | 7.18 | osm | approximate | connector_prodtech, campus_buildings_layer |
| navy_aircraft_display | Indian Navy aircraft display | (154.0, -26.0) | 12.948466, 80.14082 | 328.49 | 22.0 x 26.9 | 5.24 | v2_meta | approximate | aircraft_grove, connector_grove |
| connector_oat | Connector path: avenue to OAT entrance | (-19.0, -143.8) | 12.947408, 80.139225 | 0.0 | 32.1 x 2.4 | 0.07 | roads_geometry | approximate | open_air_theatre, roads_layer |
| connector_letters | Connector path: avenue to MIT letters | (-53.8, -243.3) | 12.946514, 80.138904 | 0.0 | 5.8 x 2.2 | 0.07 | roads_geometry | approximate | mit_letters, roads_layer |
| connector_statue | Connector path: Rajam Hall Road to statue garden | (218.4, 5.0) | 12.948745, 80.141413 | 0.0 | 3.7 x 2.2 | 0.07 | roads_geometry | approximate | golden_statue_garden, roads_layer |
| connector_prodtech | Connector path: avenue to Production Technology porch | (161.9, 81.1) | 12.949429, 80.140892 | 0.0 | 8.8 x 2.2 | 0.07 | roads_geometry | approximate | production_technology_frontage, roads_layer |
| connector_grove | Connector paths: service roads to aircraft grove / Navy plinth | (145.0, -21.0) | 12.948511, 80.140737 | 0.0 | 9.2 x 2.2 | 0.07 | roads_geometry | approximate | navy_aircraft_display, aircraft_grove, roads_layer |

## Road network

| id | name | width (m) | OSM source |
|---|---|---|---|
| mit_avenue | MIT Road (campus avenue) | 7.5 | ways named 'MIT Road' |
| rajam_hall_road | Rajam Hall Road | 4.0 | way 25907694 |
| service_west | West service road | 4.0 | way 23092151 |
| service_grove | Grove service road | 4.0 | way 23092148 |
| service_aero | Aero service road | 4.0 | way 23092149 |
| service_prodtech | North-east service road | 4.0 | way 1434524589 |
| service_north | North service road | 4.0 | way 23092383 |

Full centrelines (ENU polylines) are in the JSON under `road_network`.

## Siting rationale (2026-10-21 pass)

- **Open Air Theatre (-26, -116)** — no OSM node exists for the OAT. The site is the only clear 63 m circle on campus ground west of the main avenue: bounded by the avenue paving to the east, the west service road (OSM 23092151) to the west, and clear of all building footprints; the avenue fountain is 48 m south. Terraces face north/east/west and the entrance opens south, linked to the avenue by `connector_oat`. Refinements: rectangular stage house with maroon slatted backdrop (photos 21/30.jpg) added behind the screen; entrance pillars + slab define the south opening.
- **MIT letters (-50.1, -245.7)** — avenue lawn inside the Main Gate, east side, aligned to the avenue direction at the gate (OSM node 432468247). Split out of the former combined garden GLB so it carries its own transform; plinth gained a concrete edging frame.
- **Golden statue garden (224, 10)** — anchored on the OSM Rajam Statue node (582775241) but offset 7.6 m north-east so the garden clears both Rajam Hall and the Rajam Hall Road bend; it faces the bend (photo 16.jpg shows the statue at the end of this road). A paved spur + `connector_statue` join it to the road. The crude statue arch in `landmarks.glb` stays untouched.
- **Pergola (-18, -80) and gazebo (-36, -64)** — the Admin-side garden west of the Admin Block (photo 18.jpg), east of the west service road, ~27 m apart.
- **Production Technology frontage (anchor 170.42, 75.39)** — the department is a no-footprint OSM node (432468201) whose procedural box was measured in `campus_buildings.glb`. The frontage is placed on the box surface along `mit_details.facing()` (146.29 deg ENU, toward the avenue) + 0.35 m, as a ground-floor overlay; the procedural building is not hidden. Two entrance steps were added (photo 14.jpg).
- **Navy aircraft (154, -26, kept)** — the roads survey confirmed the original spot is already road-adjacent (OSM 23092149 passes ~2 m south of the plinth, 23092148 passes the grove), so instead of moving it, it gained a concrete apron and a path pad to the grove centre, joined to the roads by `connector_grove`.

## Known limitations

- All 2026-10-21 sites are `approximate`: derived from OSM geometry and the model's own layers, not from a survey. The OAT in particular has no OSM footprint; its site is the best clear ground west of the avenue, not a measured position.
- Live Overpass was queried on 2026-10-21 and returned no additional campus features; the repo's `data/osm_raw.osm` extract (same ODbL source) was used instead.
- Procedural trees (trees.glb) were not treated as siting obstacles; a tree may stand close to a new prop.
- The Unity scene builder changes are compile-unverified (no Unity editor on the build machine); the placement numbers in `ChrompetSceneBuilder.cs` and this registry were cross-checked programmatically instead.
- GLBs are stored as regular binary blobs in this commit (no git-lfs on the build machine), same as the previous model commits.
