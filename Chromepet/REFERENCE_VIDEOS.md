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

## Merge log

| Date | Video | Model file | Commit | Notes |
|------|-------|------------|--------|-------|
| 2026-10-18 | 7ukD24Afw44, Lxfu7Ca0t1g, Lnbh9o4DO_w, 9puuqORQ9jA, UiqrwMtWw90, pU7IlCqgIkU, QKCAmu_7zfg, yWtKV24QGR4, J_mGzeckHCw, qhQ7aS-qETw | tools/mit_details.py, data/v2_meta.json | 259b9f9 | Procedural v2 generator (notes from videos, not reconstructions) |
| 2026-10-18 | 7ukD24Afw44, Lxfu7Ca0t1g, Lnbh9o4DO_w, 9puuqORQ9jA, UiqrwMtWw90 | buildings/campus_buildings.glb, buildings/outside_buildings.glb | 85b9484 | Styled campus blocks + pastel surroundings |
| 2026-10-18 | 7ukD24Afw44, Lxfu7Ca0t1g, Lnbh9o4DO_w, 9puuqORQ9jA, UiqrwMtWw90 | ground/ground_v2.glb, props/landmarks.glb, props/trees.glb | a360d9b | Paving, landmarks, trees |
| 2026-10-18 | pU7IlCqgIkU, QKCAmu_7zfg, yWtKV24QGR4, J_mGzeckHCw, qhQ7aS-qETw | roads/roads_v2.glb | dabaf4a | GST Road, flyover, overbridge, station, railway, subway |
| 2026-10-18 | QKCAmu_7zfg, 7ukD24Afw44, Lnbh9o4DO_w | unity/Assets/Scripts/Editor/*.cs | 5fdb94d | Spawn inside Main Gate, GLB import + colliders |
| 2026-10-18 | CT photos 1-2 | buildings/detailed/ct_charles_babbage.glb | (this commit) | Detailed Charles Babbage Block (bpy), Unity imports detailed buildings + hides procedural box |
