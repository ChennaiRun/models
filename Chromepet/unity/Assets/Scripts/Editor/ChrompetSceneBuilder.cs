#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// Menu: Chrompet > Build MIT Campus Scene
/// 1. Syncs per-area GLBs into Assets/Models/Chrompet (ChromepetSync).
/// 2. Instantiates ground / roads / campus + outside buildings / landmarks / trees, marks them static,
///    adds MeshColliders to every mesh (simple extruded geometry; tree meshes get NO mesh collider).
/// 3. Adds CapsuleColliders on tree trunks from trees_colliders.json.
/// 4. Places an on-foot Player (capsule placeholder) at "Spawn_MainGate" on the campus avenue just inside the
///    Main Gate (OSM node 432468247, MIT Road right after the MIT Flyover), facing into campus.
/// Orientation: GLBs are standard glTF (+Y up, right-handed; x=east, z=-north). The spawn and tree colliders are
/// derived from marker geometry inside the imported GLB, so they stay consistent whatever axis conversion the importer uses.
public static class ChrompetSceneBuilder
{
    const string Dir = ChromepetSync.Dst;

    [System.Serializable] class Tree { public float x, y, z, r, h; public string kind; }
    [System.Serializable] class TreeFile { public string frame; public Tree[] trees; }

    [MenuItem("Chrompet/Build MIT Campus Scene")]
    public static void Build()
    {
        ChromepetSync.Sync();
        var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
        if (Camera.main) Object.DestroyImmediate(Camera.main.gameObject); // player brings its own camera

        var world = new GameObject("Chromepet_World");
        GameObject landmarks = null;
        foreach (var g in ChromepetSync.Glbs)
        {
            var file = Path.GetFileName(g);
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Dir + file);
            if (!prefab) { Debug.LogError("Missing/unimported " + Dir + file + " (is glTFast installed?)"); continue; }
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, world.transform);
            go.name = Path.GetFileNameWithoutExtension(file);
            foreach (var t in go.GetComponentsInChildren<Transform>()) t.gameObject.isStatic = true;
            if (file == "landmarks.glb") landmarks = go;
            if (file == "trees.glb") continue; // trees: capsule colliders only
            foreach (var mf in go.GetComponentsInChildren<MeshFilter>())
            {
                if (mf.name.StartsWith("Spawn")) continue;
                var mc = mf.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mf.sharedMesh;
            }
        }

        // Detailed hand/bpy-modelled buildings (Chromepet/buildings/detailed/*.glb). Each replaces a procedural box:
        // nodes named COL_* become invisible MeshColliders, visual meshes get no collider, and the procedural
        // building whose node name starts with the mapped prefix is disabled.
        var replaces = new System.Collections.Generic.Dictionary<string, string> {
            { "ct_charles_babbage", "Charles_Babbage_Block" } };
        var detRoot = new GameObject("Detailed_Buildings"); detRoot.transform.SetParent(world.transform);
        foreach (var path in Directory.Exists(Dir + "detailed") ? Directory.GetFiles(Dir + "detailed", "*.glb") : new string[0])
        {
            var p = AssetDatabase.LoadAssetAtPath<GameObject>(path.Replace('\\', '/'));
            if (!p) continue;
            var go = (GameObject)PrefabUtility.InstantiatePrefab(p, detRoot.transform);
            go.name = Path.GetFileNameWithoutExtension(path);
            foreach (var t in go.GetComponentsInChildren<Transform>()) t.gameObject.isStatic = true;
            foreach (var mf in go.GetComponentsInChildren<MeshFilter>())
            {
                if (!mf.name.StartsWith("COL_")) continue;
                var mc = mf.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mf.sharedMesh;
                var r = mf.GetComponent<Renderer>(); if (r) r.enabled = false;
            }
            if (replaces.TryGetValue(go.name, out var prefix))
                foreach (var t in world.GetComponentsInChildren<Transform>(true))
                    if (t.name.StartsWith(prefix) && !t.IsChildOf(detRoot.transform)) t.gameObject.SetActive(false);
        }

        // Spawn markers: tiny meshes baked at the spawn / look-at points (vertex data, so use renderer bounds).
        Vector3 spawn = new Vector3(0, 0.2f, 0), look = Vector3.forward * 10;
        Transform spawnT = landmarks ? FindDeep(landmarks.transform, "Spawn_MainGate") : null;
        Transform lookT = landmarks ? FindDeep(landmarks.transform, "SpawnLook") : null;
        if (spawnT) { spawn = spawnT.GetComponentInChildren<Renderer>().bounds.center; spawnT.GetComponentInChildren<Renderer>().enabled = false; }
        else Debug.LogWarning("Spawn_MainGate marker not found; using origin.");
        if (lookT) { look = lookT.GetComponentInChildren<Renderer>().bounds.center; lookT.GetComponentInChildren<Renderer>().enabled = false; }

        // Tree trunk capsules. JSON is in glTF frame; detect the importer's axis signs from the spawn marker.
        var metaPath = Dir + "v2_meta.json"; float sx = 1, sz = 1;
        if (File.Exists(metaPath) && spawnT)
        {
            var meta = JsonUtility.FromJson<Meta>(File.ReadAllText(metaPath));
            if (meta.spawn_gltf != null && meta.spawn_gltf.Length == 3)
            {
                sx = Mathf.Sign(spawn.x) == Mathf.Sign(meta.spawn_gltf[0]) ? 1 : -1;
                sz = Mathf.Sign(spawn.z) == Mathf.Sign(meta.spawn_gltf[2]) ? 1 : -1;
            }
        }
        var treeJson = Dir + "trees_colliders.json";
        if (File.Exists(treeJson))
        {
            var tf = JsonUtility.FromJson<TreeFile>(File.ReadAllText(treeJson));
            var root = new GameObject("TreeColliders"); root.transform.SetParent(world.transform); root.isStatic = true;
            foreach (var t in tf.trees)
            {
                var go = new GameObject("Trunk_" + t.kind); go.isStatic = true; go.transform.SetParent(root.transform);
                go.transform.position = new Vector3(t.x * sx, 0, t.z * sz);
                var cc = go.AddComponent<CapsuleCollider>(); cc.radius = Mathf.Max(0.15f, t.r); cc.height = t.h; cc.center = new Vector3(0, t.h / 2, 0);
            }
        }

        // Sun
        var sun = new GameObject("Sun", typeof(Light)); var l = sun.GetComponent<Light>(); l.type = LightType.Directional; l.shadows = LightShadows.Soft;
        sun.transform.rotation = Quaternion.Euler(50, 140, 0);

        // Player (on foot only)
        var player = new GameObject("Player");
        player.transform.position = spawn + Vector3.up * 0.1f;
        var dir = look - spawn; dir.y = 0; if (dir.sqrMagnitude > 0.01f) player.transform.rotation = Quaternion.LookRotation(dir);
        var ccon = player.AddComponent<CharacterController>();
        ccon.height = 1.8f; ccon.radius = 0.3f; ccon.center = new Vector3(0, 0.9f, 0); ccon.stepOffset = 0.35f;
        var body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        body.name = "Body_Placeholder"; Object.DestroyImmediate(body.GetComponent<Collider>());
        body.transform.SetParent(player.transform, false); body.transform.localPosition = new Vector3(0, 0.9f, 0);
        var pivot = new GameObject("CameraPivot").transform; pivot.SetParent(player.transform, false);
        pivot.localPosition = new Vector3(0, 1.65f, 0);
        var camGo = new GameObject("PlayerCamera", typeof(Camera), typeof(AudioListener)); camGo.tag = "MainCamera";
        camGo.transform.SetParent(pivot, false); var cam = camGo.GetComponent<Camera>(); cam.nearClipPlane = 0.05f; cam.farClipPlane = 4000f;
        var pc = player.AddComponent<PlayerController>();
        pc.cameraPivot = pivot; pc.cam = cam; pc.bodyRenderers = new[] { body.GetComponent<Renderer>() };
        var anim = player.AddComponent<PlayerAnimator>(); anim.player = pc;
        var sp = new GameObject("SpawnPoint_MIT_MainGate"); sp.transform.SetPositionAndRotation(player.transform.position, player.transform.rotation);

        Directory.CreateDirectory("Assets/Scenes");
        EditorSceneManager.SaveScene(scene, "Assets/Scenes/MIT_Chrompet.unity");
        VikramSetup.TrySwapAvatar(player); // no-op until Vikram.fbx has been synced
        Debug.Log($"MIT Chromepet scene built. Spawn {spawn}, axis signs x{sx} z{sz}.");
    }

    [System.Serializable] class Meta { public float[] spawn_gltf; }

    static Transform FindDeep(Transform t, string prefix)
    {
        if (t.name.StartsWith(prefix)) return t;
        foreach (Transform c in t) { var r = FindDeep(c, prefix); if (r) return r; }
        return null;
    }
}
#endif
