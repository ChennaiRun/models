using UnityEngine;

/// Feeds horizontal speed from the CharacterController into the Animator "Speed" float (Idle/Walk/Run blend tree).
public class PlayerAnimator : MonoBehaviour
{
    public PlayerController player;
    public Animator animator;
    public float damp = 0.1f;
    void Update()
    {
        if (!animator || !player) return;
        Vector3 v = player.Velocity; v.y = 0;
        animator.SetFloat("Speed", v.magnitude, damp, Time.deltaTime);
    }
}
