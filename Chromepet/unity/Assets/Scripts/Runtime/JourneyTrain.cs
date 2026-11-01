using System;
using UnityEngine;

/// Moves a suburban EMU along a baked rail path (data/journey_route.json,
/// unity-enu frame) with two station stops: approach -> dwell at Chrompet
/// platform 2 -> ride -> dwell at Tambaram Sanatorium -> depart south.
/// The path polyline is loaded by StationJourney/Setup from the JSON;
/// the train orients its local +Z along the tangent (the EMU GLB extends
/// along its local Z axis).
public class JourneyTrain : MonoBehaviour
{
    public enum State { Waiting, Approaching, DwellChrompet, Riding, DwellSanatorium, Departing, Done }

    [Tooltip("Rail path polyline, unity-enu metres.")]
    public Vector3[] path;
    public int chrompetStopIndex;
    public int sanatoriumStopIndex;
    public float speed = 12f;
    public float dwellSeconds = 8f;

    public State state { get; private set; } = State.Waiting;
    public event Action ArrivedChrompet;
    public event Action ArrivedSanatorium;

    int targetIndex;
    float dwellTimer;

    /// Start the run from the beginning of the path.
    public void Begin()
    {
        if (path == null || path.Length < 2) { Debug.LogWarning("JourneyTrain: no path."); return; }
        chrompetStopIndex = Mathf.Clamp(chrompetStopIndex, 0, path.Length - 1);
        sanatoriumStopIndex = Mathf.Clamp(sanatoriumStopIndex, 0, path.Length - 1);
        transform.position = path[0];
        state = State.Approaching;
        targetIndex = 1;
    }

    void Update()
    {
        if (state == State.Waiting || state == State.Done || path == null || path.Length < 2) return;

        if (state == State.DwellChrompet || state == State.DwellSanatorium)
        {
            dwellTimer -= Time.deltaTime;
            if (dwellTimer > 0f) return;
            if (state == State.DwellChrompet)
            {
                state = State.Riding;
                targetIndex = Mathf.Min(chrompetStopIndex + 1, path.Length - 1);
            }
            else
            {
                state = State.Departing;
                targetIndex = Mathf.Min(sanatoriumStopIndex + 1, path.Length - 1);
            }
            return;
        }

        // Move toward the current target path point.
        Vector3 target = path[targetIndex];
        Vector3 delta = target - transform.position;
        float step = speed * Time.deltaTime;
        if (delta.magnitude <= step)
        {
            transform.position = target;
            if (targetIndex >= path.Length - 1) { state = State.Done; return; }
            if (state == State.Approaching && targetIndex == chrompetStopIndex)
            {
                state = State.DwellChrompet;
                dwellTimer = dwellSeconds;
                ArrivedChrompet?.Invoke();
                return;
            }
            if (state == State.Riding && targetIndex == sanatoriumStopIndex)
            {
                state = State.DwellSanatorium;
                dwellTimer = dwellSeconds;
                ArrivedSanatorium?.Invoke();
                return;
            }
            targetIndex++;
        }
        else
        {
            transform.position += delta.normalized * step;
        }

        Vector3 look = path[Mathf.Min(targetIndex, path.Length - 1)] - transform.position;
        look.y = 0f;
        if (look.sqrMagnitude > 0.01f)
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(look), 8f * Time.deltaTime);
    }
}
