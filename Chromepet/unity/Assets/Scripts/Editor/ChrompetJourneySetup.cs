#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEngine;

/// Menu: Chrompet > Setup Station Journey
/// Run AFTER "Chrompet > Build MIT Campus Scene". Wires the scripted
/// journey (MIT back gate -> FOB stairs -> EMU -> Tambaram Sanatorium):
/// instantiates the shared Chennai EMU on the rail path, attaches a
/// JourneyTrain, and adds a StationJourney to the Player with the route
/// JSON from data/journey_route.json (synced into Assets/Models/Chrompet).
public static class ChrompetJourneySetup
{
    const string EmuAsset = "Assets/Models/Vehicles/chennai_suburban_emu.glb";
    const string RouteAsset = ChromepetSync.Dst + "journey_route.json";

    [MenuItem("Chrompet/Setup Station Journey")]
    public static void Setup()
    {
        ChromepetSync.Sync();

        var routeJson = AssetDatabase.LoadAssetAtPath<TextAsset>(RouteAsset);
        if (!routeJson) { Debug.LogError("Missing " + RouteAsset + " (run Chrompet > Sync Area Assets)."); return; }

        var playerGo = GameObject.Find("Player");
        if (!playerGo || !playerGo.GetComponent<PlayerController>())
        {
            Debug.LogError("No Player with PlayerController in the scene. Run Chrompet > Build MIT Campus Scene first.");
            return;
        }

        // Train
        var trainGo = GameObject.Find("JourneyTrain");
        if (!trainGo)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(EmuAsset);
            if (!prefab) { Debug.LogError("Missing " + EmuAsset + " (is glTFast installed?)."); return; }
            trainGo = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            trainGo.name = "JourneyTrain";
        }
        var train = trainGo.GetComponent<JourneyTrain>();
        if (!train) train = trainGo.AddComponent<JourneyTrain>();

        // Journey on the player
        var journey = playerGo.GetComponent<StationJourney>();
        if (!journey) journey = playerGo.AddComponent<StationJourney>();
        journey.routeJson = routeJson;
        journey.player = playerGo.GetComponent<PlayerController>();
        journey.train = train;

        // Park the player at the back gate start for convenience.
        var route = JsonUtility.FromJson<StationJourney.JRoute>(routeJson.text);
        if (route != null && route.start != null)
            playerGo.transform.position = route.start.position.V + Vector3.up * 0.1f;

        Selection.activeGameObject = playerGo;
        EditorUtility.SetDirty(playerGo);
        EditorUtility.SetDirty(trainGo);
        Debug.Log("Station journey set up. Press Play to ride (auto-starts; J replays from the back gate). Save the scene to keep it.");
    }
}
#endif
