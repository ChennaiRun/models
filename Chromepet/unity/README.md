# unity – Unity 2022.3 LTS project (MIT Chromepet, on-foot)
Open this folder (`Chromepet/unity`) in Unity Hub. Packages: glTFast (imports the .glb files) + Cesium for Unity (optional backdrop) – verify versions in Package Manager.
1. **Chrompet > Build MIT Campus Scene** – syncs the v2 GLBs from `../buildings`, `../roads`, `../ground`, `../props` into `Assets/Models/Chrompet` (git-ignored), instantiates them static, adds MeshColliders (buildings, roads, ground, landmarks), CapsuleColliders on tree trunks (`trees_colliders.json`), a sun, and the Player.
2. **Spawn**: on the campus avenue (MIT Road), 12 m inside the Main Gate (OSM node 432468247, right after the MIT Flyover on the GST Road side), facing into campus. Position is read from the `Spawn_MainGate` marker inside `landmarks.glb`, so it is always consistent with the meshes.
3. Controls: WASD, mouse, Space jump, Shift sprint, V toggle 1st/3rd person. No fly camera.
4. Avatar: see `../characters/README.md`.

**Orientation note:** the v1 OBJs (`../buildings/buildings.obj` etc.) used x=east, y=up, z=north (a left-handed frame); Unity's OBJ importer negates X, so v1 appeared **mirrored east-west** in Unity and the v1 spawn coordinate was off the road. v2 GLBs use standard glTF (x=east, y=up, z=-north) and were verified in Blender (glTF import → north = +Y); the builder no longer uses the OBJs.
Scripts are not yet compiled/tested inside Unity.
