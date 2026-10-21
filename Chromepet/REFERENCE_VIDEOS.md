# Chromepet reference videos and model tracker

Status values: `pending` (no model yet), `in progress` (being reconstructed), `done` (output received), `merged` (merged into the main Chromepet model and committed).

Drop each user-generated 3D output in `Chromepet/incoming/<video-id>/` (preferred: metre-scale, Y-up `.glb`; splats as `.ply`), then update its row here.

## Campus videos (user-provided)

| # | Video | Title / channel | Models generated | Status | Notes |
|---|-------|-----------------|------------------|--------|-------|
| 1 | [7ukD24Afw44](https://www.youtube.com/watch?v=7ukD24Afw44) | Inside MIT Chennai: Campus Tour, Canteen & Student Life / Suman Mpm | none | pending | Informed the procedural v2 model (campus buildings/colours, canteen & hostel zone; tools/mit_details.py) |
| 2 | [Lxfu7Ca0t1g](https://www.youtube.com/watch?v=Lxfu7Ca0t1g) | MIT Campus Anna University, Campus Tour (TNEA 0004) / Shree Creations World | none | pending | Informed the procedural v2 model (main gate, avenue, department blocks; tools/mit_details.py) |
| 3 | [Lnbh9o4DO_w](https://www.youtube.com/watch?v=Lnbh9o4DO_w) | MIT Anna University Full Campus Tour 2026 / Naveen Speaks | none | pending | Informed the procedural v2 model (full tour: avenue, landmarks, aircraft grove, water tank; tools/mit_details.py) |
| 4 | [9puuqORQ9jA](https://www.youtube.com/watch?v=9puuqORQ9jA) | MIT CHENNAI CAMPUS, Anna University / Aadarsh Kumar | none | pending | Informed the procedural v2 model (Admin block, LHC, Rajam Hall, statues; tools/mit_details.py) |

## Supplementary reference (visual only)

| Video | What it shows | Status | Notes |
|-------|---------------|--------|-------|
| [UiqrwMtWw90](https://www.youtube.com/watch?v=UiqrwMtWw90) | MIT bird view (drone) | pending | Informed the procedural v2 model (campus layout: wooded strip, avenue spine, hangars) |
| [pU7IlCqgIkU](https://www.youtube.com/watch?v=pU7IlCqgIkU) | GST Road drive, Pallavaram to Tambaram | pending | Informed the procedural v2 model (GST Road 6 lanes + median, MIT Flyover, overbridge, bus shelters/billboards) |
| [QKCAmu_7zfg](https://www.youtube.com/watch?v=QKCAmu_7zfg) | Chromepet railway station road drive | pending | Informed the procedural v2 model (station road; main gate right after the flyover (spawn)) |
| [yWtKV24QGR4](https://www.youtube.com/watch?v=yWtKV24QGR4) | Radha Nagar walking tour | pending | Informed the procedural v2 model (Radha Nagar 2-3 storey shops, poles/wires) |
| [J_mGzeckHCw](https://www.youtube.com/watch?v=J_mGzeckHCw) | Radha Nagar subway night drive | pending | Informed the procedural v2 model (Radha Nagar subway, 3.0 m height bar) |
| [qhQ7aS-qETw](https://www.youtube.com/watch?v=qhQ7aS-qETw) | Chromepet drone shots | pending | Informed the procedural v2 model (outside building heights/colours, trees) |

## Photo references (user-provided)

| Photo | What it shows | Status | Notes |
|-------|---------------|--------|-------|
| CT photo 1 (2026-10-18, chat attachment 01M5857J7HR5C543N93F7TC1DS) | Charles Babbage Block / Dept. of Computer Technology from the road: portico, sign, steps, ramp, forecourt | merged | Modelled in `buildings/detailed/ct_charles_babbage.glb` (tools/ct_charles_babbage_bpy.py) |
| CT photo 2 (2026-10-18, chat attachment 01M585AECX15DAQKGEZ2XEAJEG) | Same building, front 3/4: 2 storeys, salmon bands/pilasters, sunshade ledges, teak lattice entrance, 5 granite steps, ramp, hex pavers, potted plants | merged | Same model; replaces the approximate procedural Charles Babbage box |

### Drive photo set (user-provided, 2026-10-20)

The user's own Mar 2019 campus photos from his Google Drive folder 'mit'
(https://drive.google.com/drive/folders/1Vs_RHFa1Daip6N2LwohIy9BYGBcaeGDO).
The folder contains 87 JPGs (1.jpg-87.jpg, 294 MB; the web listing only
shows the first 50). All 87 were downloaded and viewed on 2026-10-20.
Observation only: no photo pixels are shipped in any model; people in
the photos are not modelled. New models are additive (own generator +
GLB + `data/*_meta.json`); placements marked APPROXIMATE are unsurveyed.

| Photo | What it shows | Status | Notes |
|-------|---------------|--------|-------|
| 1.jpg | Open Air Theatre (OAT): flat circular plaza of concentric paved rings, brick-red stepped terraces around the far side, low central stage, black lamp posts, yellow OPEN AIR THEATRE sign | modelled | `props/open_air_theatre.glb` (tools/oat_theatre.py), origin-centred, siting outstanding |
| 2.jpg | Main building facade (white/blue glass) with tiled forecourt and brown "MADRAS INSTITUTE OF TECHNOLOGY ANNA UNIVERSITY" signboard | reference | Facade/signage reference only |
| 3.jpg | Tree trunk close-up, avenue and signboard behind | reference | No model |
| 4.jpg | Tree-lined campus road, painted mural/notice wall left, cycle shelter right | reference | No model |
| 5.jpg | Tree-lined road, painted mural wall panels left | reference | No model |
| 6.jpg | M.I.T. Hostel Store shopfront (xerox/snacks) by the road | reference | No model |
| 7.jpg | Campus road with painted mural wall, second view of the 5.jpg stretch | reference | No model |
| 8.jpg | "Mitafest '19" mural painted on a rusty hangar side wall | reference | No model |
| 9.jpg | Ribbed conical temple gopuram (vimana) with golden finials, seen over the grove outside the campus wall, maroon bus in front | reference | Identifies the tower in 10.jpg: a temple outside the wall, not a campus structure; not modelled |
| 10.jpg | The same ribbed conical temple gopuram on its circular stepped platform, closer view from the grove | reference | See 9.jpg; not a campus building, not modelled |
| 11.jpg | MIT letters monument: large black 3D letters M I T on the avenue lawn | modelled | `props/avenue_garden_landmarks.glb` group `MIT_letters` (tools/avenue_garden_landmarks.py); low stone plinth added as mount |
| 12.jpg | Rajam Hall interior stage (red curtain, wood panelling, RAJAM HALL sign) | reference | Interior only; no model |
| 13.jpg | Golden standing statue on bright-blue pedestal in a garden: globe lamp posts, green benches, blue railing | modelled | `props/avenue_garden_landmarks.glb` group `Golden_statue_garden`; detailed additive version, landmarks.glb not edited. The figure is Sri C. Rajam, MIT founder (identified by the gate statue plaque in 81.jpg) |
| 14.jpg | Department of Production Technology entrance close-up: big blue sign, square-grid jali above, oval-hole lattice screens, cream walls, yellow lower band, maroon doors | modelled | `buildings/detailed/production_technology_frontage.glb` (tools/production_technology_frontage.py), origin-centred additive overlay |
| 15.jpg | Campus path past Mechatronics; white/blue Indian NAVY aircraft display behind the trees | modelled | `props/navy_aircraft_display.glb` (tools/navy_aircraft.py), world-positioned at the aircraft grove (APPROXIMATE), registered in ChromepetSync |
| 16.jpg | Tree-lined internal road, hangar-like white building left, mustard building right, golden statue at the far end | reference | Supports the statue garden siting |
| 17.jpg | White multi-storey tower block from below, brown-framed paired windows, stilted ground floor | reference | Same block as 27.jpg (Computer Technology) |
| 18.jpg | Garden with red-brick pergola and round tiled-roof gazebo with circular bench | modelled | `props/avenue_garden_landmarks.glb` groups `Pergola` + `Gazebo` |
| 19.jpg | Gazebo garden at sunset, glass-fronted building behind | reference | Supports the gazebo model |
| 20.jpg | Camouflage Tamil Nadu government van (vehicle) | reference | Vehicle; not modelled |
| 21.jpg | OAT / stage complex from the stage end: raised rectangular stage, maroon slatted backdrop, paver plaza, blue benches | reference | The OAT model's stage is simplified to the circular stage of 1.jpg |
| 22.jpg | Department of Aerospace Engineering frontage: maroon/cream, eagle sign | reference | Future detailed candidate; cf. 'aero' style in mit_details.py |
| 23.jpg | Aircraft grove close-up: light blue/white Sea Hawk and grey Gnat on tiled plinths, blue info boards | reference | Validates the existing landmarks.glb grove |
| 24.jpg | Library entrance: cream block, white round-column portico | reference | No model |
| 25.jpg | Aerospace Engineering from across the channel/path | reference | Context for 22.jpg |
| 26.jpg | Gazebo garden at sunset, wider view of the 19.jpg scene | reference | Supports the gazebo model |
| 27.jpg | Department of Computer Technology entrance of the white tower block (17.jpg): glass front, steps, ramp | reference | Future detailed candidate (distinct from Charles Babbage Block) |
| 28.jpg | Central Workshop facade: white/cream, dark-blue letters, green trim | reference | No model |
| 29.jpg | Department of Information Technology entrance: cream, raised letters, wooden doors, grey porch frame | reference | No model |
| 30.jpg | OAT plaza at sunset: stage/pergola left, glass building right | reference | Context for 1.jpg / 21.jpg |
| 31.jpg | Abdul Kalam Lecture Hall Complex: light green + white band, big black letters | reference | Validates the 'lhc' pale yellow-green style |
| 32.jpg | Information Technology entrance, evening view | reference | Second view of 29.jpg |
| 33.jpg | Main avenue looking along the campus, pergola/stage area left | reference | No model |
| 34.jpg | Green direction signpost: Administrative Block, Automobile Engineering, Electronics Engineering, AU-KBC Centre | reference | No model |
| 35.jpg | Rajam Hall exterior (white/orange brick) with seated golden C. Rajam statue on plaque pedestal in a railed forecourt | reference | Note: the landmarks.glb Rajam statue is an arch over a pool -- a detailed forecourt statue is a future candidate |
| 36.jpg | Golden statue garden, second view: blue pedestal with gold emblem, red-tiled surround | modelled | Same item as 13.jpg; emblem added to the model |
| 37.jpg | Main Gate from inside the campus: pillars, red beam, MIT name + emblem | reference | Validates landmarks.glb Main Gate |
| 38.jpg | Weathered hangar/exam-hall gable end with maroon "...INSTITUTE OF TECHNOLOGY" letters | reference | No model |
| 39.jpg | Golden statue close-up: standing figure with staff and book, blue pedestal with gold emblem | modelled | Same item as 13.jpg; staff added to the model |
| 40.jpg | Newer Production Technology block: 4-storey cream block, teal trim/sunshades, tiled porch roof | reference | Future detailed candidate (distinct from the 14.jpg entrance) |
| 41.jpg | Newer Production Technology block, long side view | reference | Context for 40.jpg |
| 42.jpg | End wall of the newer block: ANNA UNIVERSITY / MADRAS INSTITUTE OF TECHNOLOGY letters + emblem, teal fins | reference | No model |
| 43.jpg | Same end wall, second view | reference | Context for 42.jpg |
| 44.jpg | Garden seating in front of Mechatronics: stone benches, oval-lattice wall, blue MECHATRONICS sign | reference | Lattice language shared with the Production Technology frontage |
| 45.jpg | Production Technology entrance, wide view of the 14.jpg building, with Division of Applied Sciences & Humanities banner above | modelled | Same frontage as 14.jpg; frontage is the ground floor of a taller pale-green lattice block |
| 46.jpg | Central Workshop & Division of Mechatronics sign; Robotics & Automation Lab link bridge | reference | Context for 28.jpg / 44.jpg |
| 47.jpg | Hangar-II front: cream, lattice jali walls, large mesh gates | reference | Future detailed candidate |
| 48.jpg | Hangar-II side: coloured-glass panel windows, exam-hall signage | reference | Context for 47.jpg |
| 49.jpg | Department of Electronics Engineering entrance: blue portico frame, stone-clad tower, wooden doors | reference | No model |
| 50.jpg | Electronics Engineering block, wider view (white/blue) | reference | Context for 49.jpg |
| 51.jpg | Internal road by the Electronics block, paved footpaths | reference | No model |
| 52.jpg | Rajam Lecture Hall Complex entrance: white block, round columns, red doors, tiled path | reference | Distinct from Rajam Hall (35.jpg) |
| 53.jpg | Rajam Lecture Hall Complex from under a tree, second view | reference | Context for 52.jpg |
| 54.jpg | Old Department of Electronics Engineering block: light green, black department sign board | reference | Distinct from the newer blue block in 49/50.jpg |
| 55.jpg | Main avenue tree canopy looking along the road | reference | No model |
| 56.jpg | Department of Automobile Engineering (red/white) courtyard, generator set | reference | No model |
| 57.jpg | Vintage Ambassador car parked by a block (vehicle) | reference | Vehicle; not modelled |
| 58.jpg | Golden Jubilee Complex tower with Computer Technology sign at ground level | reference | Same complex as 17/27/60/61.jpg |
| 59.jpg | Charles Babbage Block entrance close-up: lattice doors, sign, steps | reference | Validates buildings/detailed/ct_charles_babbage.glb |
| 60.jpg | Department of Computer Technology entrance of the tower block, rotated view | reference | Second view of 27.jpg |
| 61.jpg | Computer Technology tower block from below, clearer view of 17.jpg | reference | Future detailed candidate |
| 62.jpg | AU-KBC Research Centre side view behind trees | reference | Context for 63.jpg |
| 63.jpg | AU-KBC Research Centre front: cream/gold portico | reference | Future detailed candidate |
| 64.jpg | Electronics Engineering Block-2 / Rubber & Plastics Technology (pink/white); a red-brick pergola stands at the right | reference | The pergola type of 18.jpg also stands alone here |
| 65.jpg | From inside a gazebo across the garden: second tiled-roof gazebo + pergola, Admin glass building behind | reference | Supports the P2 gazebo/pergola grouping |
| 66.jpg | Main avenue with covered walkway on the left | reference | Supports landmarks.glb covered walkway |
| 67.jpg | Instrumentation Engineering block front: cream/green, 4 storeys | reference | Future detailed candidate |
| 68.jpg | Instrumentation block side + covered walkway | reference | Context for 67.jpg |
| 69.jpg | Umbrella seating close-up: hexagonal stone table/benches under a big umbrella roof with hanging lamps, checker tiles | reference | Validates the landmarks.glb umbrella seating by the water tank |
| 70.jpg | Covered walkway interior: barrel roof, interlocking pavers | reference | Validates landmarks.glb covered walkway |
| 71.jpg | Instrumentation Engineering older block front: 2 storeys, cream, department letters on the band | reference | Distinct from Block-1 (72.jpg) |
| 72.jpg | "INSTRUMENTATION ENGINEERING BLOCK-1" sign band close-up | reference | Context for 71.jpg |
| 73.jpg | Administrative Block glass facade from the avenue | reference | Validates the 'admin' style in mit_details.py |
| 74.jpg | Main avenue; a red-brick pergola end stands at the right | reference | Pergolas also line the avenue (cf. 18.jpg) |
| 75.jpg | Administrative Block facade: ANNA UNIVERSITY / MADRAS INSTITUTE OF TECHNOLOGY header letters | reference | Context for 73.jpg |
| 76.jpg | OAT stage close view: semicircular raised stage, curved red-brick slatted screen, pergola beam, Instrumentation block behind | modelled | Screen + pergola beam added to `props/open_air_theatre.glb` (tools/oat_theatre.py) |
| 77.jpg | OAT plaza ground-level view across the pavers: stage screen left, gazebo right, Admin block behind | reference | Context for 1.jpg / 76.jpg |
| 78.jpg | OAT plaza at sunset, wider view of the 77.jpg scene | reference | Context for 1.jpg |
| 79.jpg | Camouflage Tamil Nadu government van, front 3/4 (Mobile Command and Control Station) | reference | Same vehicle as 20.jpg; not modelled |
| 80.jpg | Camouflage government van, second photo in the set ordering (front quarter) | reference | Vehicle; not modelled |
| 81.jpg | Golden statue of Sri C. Rajam (plaque: "STATUE OF SRI C RAJAM - MIT FOUNDER") standing with a walking stick under the Main Gate arch, over the pool | reference | This is the statue the landmarks.glb Rajam arch represents; also identifies the garden statue in 13/36/39.jpg |
| 82.jpg | Campus security checkpoint on the avenue: boom barrier, yellow barricades, campus map board | reference | No model |
| 83.jpg | Side gate: brick name wall with Anna University emblem and Tamil campus name, grey gate pillars, white gate | reference | Gate furniture reference |
| 84.jpg | Main Gate exterior and forecourt: red canopy beam, ANUSAT "Monument of Success" cube, brick ANNA UNIVERSITY name wall, yellow barricades | reference | Validates landmarks.glb Main Gate + Monument of Success |
| 85.jpg | Main avenue, empty tree-lined stretch | reference | No model |
| 86.jpg | Administrative Block close-up: header letters + ADMINISTRATIVE BLOCK portico band, flagpole | reference | Context for 73/75.jpg |
| 87.jpg | Administrative Block portico entrance: red-tiled porch, steps, ramp, flagpole | reference | Portico matches the Kalam-statue portico in landmarks.glb |

## Merge log

| Date | Video | Model file | Commit | Notes |
|------|-------|------------|--------|-------|
| 2026-10-20 | Drive photo set (all 87 photos viewed) | tools/oat_theatre.py, tools/avenue_garden_landmarks.py, tools/production_technology_frontage.py, tools/navy_aircraft.py; props/open_air_theatre.glb, props/avenue_garden_landmarks.glb, buildings/detailed/production_technology_frontage.glb, props/navy_aircraft_display.glb; data/oat_meta.json, data/garden_landmarks_meta.json, data/production_frontage_meta.json, data/navy_aircraft_meta.json | branch mit-drive-models | Additive models from the user's own campus photos; no area GLBs regenerated (OSM input is an LFS pointer on the build machine) |
| 2026-10-18 | 7ukD24Afw44, Lxfu7Ca0t1g, Lnbh9o4DO_w, 9puuqORQ9jA, UiqrwMtWw90, pU7IlCqgIkU, QKCAmu_7zfg, yWtKV24QGR4, J_mGzeckHCw, qhQ7aS-qETw | tools/mit_details.py, data/v2_meta.json | 259b9f9 | Procedural v2 generator (notes from videos, not reconstructions) |
| 2026-10-18 | 7ukD24Afw44, Lxfu7Ca0t1g, Lnbh9o4DO_w, 9puuqORQ9jA, UiqrwMtWw90 | buildings/campus_buildings.glb, buildings/outside_buildings.glb | 85b9484 | Styled campus blocks + pastel surroundings |
| 2026-10-18 | 7ukD24Afw44, Lxfu7Ca0t1g, Lnbh9o4DO_w, 9puuqORQ9jA, UiqrwMtWw90 | ground/ground_v2.glb, props/landmarks.glb, props/trees.glb | a360d9b | Paving, landmarks, trees |
| 2026-10-18 | pU7IlCqgIkU, QKCAmu_7zfg, yWtKV24QGR4, J_mGzeckHCw, qhQ7aS-qETw | roads/roads_v2.glb | dabaf4a | GST Road, flyover, overbridge, station, railway, subway |
| 2026-10-18 | QKCAmu_7zfg, 7ukD24Afw44, Lnbh9o4DO_w | unity/Assets/Scripts/Editor/*.cs | 5fdb94d | Spawn inside Main Gate, GLB import + colliders |
| 2026-10-18 | CT photos 1-2 | buildings/detailed/ct_charles_babbage.glb | 8d12e9c | Detailed Charles Babbage Block (bpy), Unity imports detailed buildings + hides procedural box |
| 2026-10-21 | Drive photos 14/22/31/45/52.jpg (style cross-check) | tools/mit_details.py, tools/chrompet_identity.py; buildings/campus_buildings.glb, props/landmarks.glb, props/chrompet_identity.glb | branch improve-existing-models | Improvement pass: 'prodtech' + 'rlhc' styles, Aero maroon/cream, fountain sign to avenue side, station board text UV fix |
