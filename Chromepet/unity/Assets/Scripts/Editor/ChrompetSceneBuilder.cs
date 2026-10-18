#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// Menu: Chrompet > Build MIT Campus Scene
/// Imports the generated OBJ meshes (Assets/Models/Chrompet), adds MeshColliders, a ground BoxCollider,
/// a capsule-placeholder player with PlayerController at the MIT main-entrance spawn point, and saves the scene.
public static class ChrompetSceneBuilder
{
    const string ModelDir = "Assets/Models/Chrompet/";
    // Local metres (X east, Z north) relative to origin 12.9487N, 80.1394E (approx MIT main gate on MIT Road).
    // Spawn = OSM-tagged MIT south gate; North Gate is node 249211141 (12.95160N 80.14132E) ~ (204, 0, 321).
    public static Vector3 SpawnPoint = new Vector3(-77.6f, 1.2f, -258f); // ~5 m inside "MIT South Gaate" (OSM node 432468247, 12.94634N 80.13868E)

    [MenuItem("Chrompet/Build MIT Campus Scene")]
    public static void Build()
    {
        ChromepetSync.Sync();
        var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
        Object.DestroyImmediate(Camera.main.gameObject); // player brings its own camera

        var world = new GameObject("Chrompet_World");
        foreach (var name in new[] { "ground", "roads", "buildings" })
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(ModelDir + name + ".obj");
            if (!prefab) { Debug.LogError("Missing " + ModelDir + name + ".obj - run tools/osm_to_mesh.py"); continue; }
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, world.transform);
            go.name = name; go.isStatic = true;
            foreach (var mf in go.GetComponentsInChildren<MeshFilter>())
            {
                if (name == "ground") { mf.gameObject.AddComponent<BoxCollider>(); continue; }
                var mc = mf.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mf.sharedMesh;
            }
        }

        // Player
        var player = new GameObject("Player");
        player.transform.position = SpawnPoint;
        var cc = player.AddComponent<CharacterController>();
        cc.height = 1.8f; cc.radius = 0.3f; cc.center = new Vector3(0, 0.9f, 0); cc.stepOffset = 0.35f;
        var body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        body.name = "Body_Placeholder"; Object.DestroyImmediate(body.GetComponent<Collider>());
        body.transform.SetParent(player.transform, false); body.transform.localPosition = new Vector3(0, 0.9f, 0);
        var pivot = new GameObject("CameraPivot").transform; pivot.SetParent(player.transform, false);
        pivot.localPosition = new Vector3(0, 1.65f, 0);
        var camGo = new GameObject("PlayerCamera", typeof(Camera), typeof(AudioListener)); camGo.tag = "MainCamera";
        camGo.transform.SetParent(pivot, false); camGo.GetComponent<Camera>().nearClipPlane = 0.05f;
        var pc = player.AddComponent<PlayerController>();
        pc.cameraPivot = pivot; pc.cam = camGo.GetComponent<Camera>();
        pc.bodyRenderers = new[] { body.GetComponent<Renderer>() };
        var anim = player.AddComponent<PlayerAnimator>(); anim.player = pc;
        new GameObject("SpawnPoint_MIT_MainEntrance").transform.position = SpawnPoint;

        System.IO.Directory.CreateDirectory("Assets/Scenes");
        EditorSceneManager.SaveScene(scene, "Assets/Scenes/MIT_Chrompet.unity");
        MixamoSetup.TrySwapAvatar(player); // no-op until Mixamo FBX files exist
    }
}
#endif
