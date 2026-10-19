using UnityEngine;
using UnityEngine.InputSystem;

/// On-foot only controller: WASD, mouse look, gravity, jump, sprint (Shift), V toggles 1st/3rd person.
/// No fly / free-cam mode by design.
[RequireComponent(typeof(CharacterController))]
public class PlayerController : MonoBehaviour
{
    public float walkSpeed = 2.0f, sprintSpeed = 5.5f, jumpHeight = 1.1f, gravity = -19.6f;
    public float mouseSensitivity = 2.0f;
    public Transform cameraPivot;          // head height pivot (child)
    public Camera cam;
    public bool thirdPerson = false;
    public float thirdPersonDistance = 3.5f;
    public Renderer[] bodyRenderers;       // hidden in first person
    public Vector3 Velocity { get; private set; }

    CharacterController cc; float yaw, pitch, vy;

    void Awake()
    {
        cc = GetComponent<CharacterController>();
        if (!cam) cam = GetComponentInChildren<Camera>();
        yaw = transform.eulerAngles.y;
        Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false;
    }

    void Update()
    {
        var keyboard = Keyboard.current;
        var mouse = Mouse.current;
        Vector2 look = mouse != null ? mouse.delta.ReadValue() : Vector2.zero;
        yaw += look.x * mouseSensitivity * 0.02f;
        pitch = Mathf.Clamp(pitch - look.y * mouseSensitivity * 0.02f, -80f, 80f);
        transform.rotation = Quaternion.Euler(0, yaw, 0);
        cameraPivot.localRotation = Quaternion.Euler(pitch, 0, 0);
        if (keyboard != null && keyboard.vKey.wasPressedThisFrame) thirdPerson = !thirdPerson;
        if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame)
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        Vector2 moveInput = Vector2.zero;
        if (keyboard != null)
        {
            if (keyboard.aKey.isPressed) moveInput.x -= 1;
            if (keyboard.dKey.isPressed) moveInput.x += 1;
            if (keyboard.sKey.isPressed) moveInput.y -= 1;
            if (keyboard.wKey.isPressed) moveInput.y += 1;
        }
        Vector3 input = new Vector3(moveInput.x, 0, moveInput.y);
        input = Vector3.ClampMagnitude(input, 1f);
        bool sprinting = keyboard != null && (keyboard.leftShiftKey.isPressed || keyboard.rightShiftKey.isPressed);
        float speed = sprinting ? sprintSpeed : walkSpeed;
        Vector3 move = transform.TransformDirection(input) * speed;

        if (cc.isGrounded && vy < 0) vy = -2f;
        if (cc.isGrounded && keyboard != null && keyboard.spaceKey.wasPressedThisFrame)
            vy = Mathf.Sqrt(jumpHeight * -2f * gravity);
        vy += gravity * Time.deltaTime;
        move.y = vy;
        cc.Move(move * Time.deltaTime);
        Velocity = cc.velocity;
    }

    void LateUpdate()
    {
        Vector3 target = thirdPerson ? new Vector3(0.4f, 0.2f, -thirdPersonDistance) : Vector3.zero;
        if (thirdPerson && Physics.Raycast(cameraPivot.position, cameraPivot.TransformDirection(target.normalized),
                out var hit, target.magnitude, ~0, QueryTriggerInteraction.Ignore) && !hit.transform.IsChildOf(transform))
            target = target.normalized * Mathf.Max(0.3f, hit.distance - 0.2f);  // avoid clipping into walls
        cam.transform.localPosition = Vector3.Lerp(cam.transform.localPosition, target, 15f * Time.deltaTime);
        foreach (var r in bodyRenderers) if (r) r.shadowCastingMode = thirdPerson
            ? UnityEngine.Rendering.ShadowCastingMode.On : UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly;
    }
}
