using System.Collections;
using UnityEngine;

/// Scripted journey: MIT back gate -> campus service roads -> Chrompet
/// platform 1 -> FOB stairs -> platform 2 -> board the southbound EMU ->
/// Tambaram Sanatorium -> alight and walk to the platform centre.
/// Route data comes from data/journey_route.json (tools/journey_route.py;
/// unity-enu frame: x=east, y=up, z=north). Disables the PlayerController
/// and CharacterController for the duration, then hands control back.
public class StationJourney : MonoBehaviour
{
    [System.Serializable] public class JPoint { public float x, y, z; public Vector3 V => new Vector3(x, y, z); }
    [System.Serializable] public class JStage { public string name; public string type; public float speed; public JPoint[] points; }
    [System.Serializable] public class JTrain { public string vehicle_glb; public JPoint[] path; public int chrompetStopIndex; public int sanatoriumStopIndex; public float speed; public float dwellSeconds; public JPoint boardPoint; public JPoint alightPoint; }
    [System.Serializable] public class JStart { public JPoint position; public string name; }
    [System.Serializable] public class JRoute { public JStart start; public JStage[] stages; public JTrain train; }

    public TextAsset routeJson;
    public PlayerController player;
    public JourneyTrain train;
    [Tooltip("Start the journey automatically after this many seconds.")]
    public bool autoStart = true;
    public float autoStartDelay = 2f;

    JRoute route;
    CharacterController cc;
    bool running;

    void Start()
    {
        if (routeJson == null) { Debug.LogWarning("StationJourney: no route JSON assigned."); return; }
        route = JsonUtility.FromJson<JRoute>(routeJson.text);
        if (route == null || route.stages == null) { Debug.LogWarning("StationJourney: route JSON failed to parse."); return; }
        if (player == null) player = FindFirstObjectByType<PlayerController>();
        if (train != null)
        {
            train.path = System.Array.ConvertAll(route.train.path, p => p.V);
            train.chrompetStopIndex = route.train.chrompetStopIndex;
            train.sanatoriumStopIndex = route.train.sanatoriumStopIndex;
            train.speed = route.train.speed;
            train.dwellSeconds = route.train.dwellSeconds;
        }
        if (autoStart) StartCoroutine(RunDelayed(autoStartDelay));
    }

    void Update()
    {
        // Manual trigger: J starts the journey again from the back gate.
        if (!running && UnityEngine.InputSystem.Keyboard.current != null &&
            UnityEngine.InputSystem.Keyboard.current.jKey.wasPressedThisFrame && route != null)
            StartCoroutine(RunDelayed(0f));
    }

    IEnumerator RunDelayed(float delay)
    {
        yield return new WaitForSeconds(delay);
        yield return Run();
    }

    IEnumerator Run()
    {
        if (running || player == null) yield break;
        running = true;
        cc = player.GetComponent<CharacterController>();
        player.enabled = false;
        if (cc) cc.enabled = false;

        player.transform.position = route.start.position.V + Vector3.up * 0.1f;

        foreach (var stage in route.stages)
        {
            switch (stage.type)
            {
                case "walk":
                    foreach (var p in stage.points)
                        yield return MoveTo(p.V, stage.speed > 0 ? stage.speed : 2f);
                    break;
                case "wait_train":
                    if (train == null) break;
                    bool arrived = false;
                    void OnArrive() => arrived = true;
                    train.ArrivedChrompet += OnArrive;
                    train.Begin();
                    while (!arrived) yield return null;
                    train.ArrivedChrompet -= OnArrive;
                    break;
                case "board":
                    if (train == null) break;
                    yield return MoveTo(route.train.boardPoint.V, 1.2f);
                    player.transform.SetParent(train.transform, true);
                    bool arrivedB = false;
                    void OnArriveB() => arrivedB = true;
                    train.ArrivedSanatorium += OnArriveB;
                    while (!arrivedB) yield return null;
                    train.ArrivedSanatorium -= OnArriveB;
                    player.transform.SetParent(null, true);
                    player.transform.position = route.train.alightPoint.V + Vector3.up * 0.05f;
                    break;
            }
        }

        if (cc) cc.enabled = true;
        player.enabled = true;
        running = false;
        Debug.Log("StationJourney: arrived at Tambaram Sanatorium. Control returned.");
    }

    IEnumerator MoveTo(Vector3 target, float speed)
    {
        while (Vector3.Distance(player.transform.position, target) > 0.15f)
        {
            Vector3 pos = player.transform.position;
            player.transform.position = Vector3.MoveTowards(pos, target, speed * Time.deltaTime);
            Vector3 face = target - pos;
            face.y = 0f;
            if (face.sqrMagnitude > 0.04f)
                player.transform.rotation = Quaternion.Slerp(player.transform.rotation,
                    Quaternion.LookRotation(face), 10f * Time.deltaTime);
            yield return null;
        }
    }
}
