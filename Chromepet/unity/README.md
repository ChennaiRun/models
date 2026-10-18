# unity – Unity 2022.3 LTS project (MIT Chromepet, on-foot)
Open this folder (`Chromepet/unity`) in Unity Hub. Packages: Cesium for Unity (scoped registry) + glTFast – verify versions in Package Manager.
1. **Chrompet > Build MIT Campus Scene** – syncs `../buildings`, `../roads`, `../ground` meshes into `Assets/Models/Chrompet` (ignored by git), adds MeshColliders / ground BoxCollider, capsule Player at MIT South Gate (OSM node 432468247), saves `Assets/Scenes/MIT_Chrompet.unity`.
2. Controls: WASD, mouse, Space jump, Shift sprint, V toggle 1st/3rd person. No fly camera.
3. Avatar: see `../characters/README.md`.
Scripts are not yet compiled/tested in Unity.
