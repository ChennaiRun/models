#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

/// Menu: Chrompet > Setup Mixamo Avatar
/// Sets Humanoid rig on Assets/Characters/Mixamo/*.fbx, builds an AnimatorController with a 1D "Speed" blend tree
/// (Idle 0, Walking 2, Running 5.5 m/s), and swaps the character onto the Player (replacing the capsule).
public static class MixamoSetup
{
    const string Dir = "Assets/Characters/Mixamo/";
    const string CtrlPath = Dir + "PlayerLocomotion.controller";

    [MenuItem("Chrompet/Setup Mixamo Avatar")]
    public static void Menu() { var p = GameObject.Find("Player"); if (p) TrySwapAvatar(p); else Debug.LogError("No Player in scene"); }

    static bool SetHumanoid(string path, bool loop, Avatar source)
    {
        var imp = AssetImporter.GetAtPath(path) as ModelImporter;
        if (imp == null) return false;
        imp.animationType = ModelImporterAnimationType.Human;
        if (source == null) imp.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
        else { imp.avatarSetup = ModelImporterAvatarSetup.CopyFromOther; imp.sourceAvatar = source; }
        var clips = imp.defaultClipAnimations;
        foreach (var c in clips) { c.loopTime = loop; c.lockRootPositionXZ = true; c.keepOriginalPositionXZ = true;
            c.lockRootRotation = true; c.lockRootHeightY = true; }
        if (clips.Length > 0) imp.clipAnimations = clips;
        imp.SaveAndReimport(); return true;
    }

    static AnimationClip Clip(string path)
    {
        foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path))
            if (o is AnimationClip c && !c.name.StartsWith("__preview")) return c;
        return null;
    }

    public static void TrySwapAvatar(GameObject player)
    {
        string charPath = Dir + "Character.fbx";
        if (!SetHumanoid(charPath, false, null)) { Debug.Log("Mixamo Character.fbx not found; keeping capsule placeholder."); return; }
        var avatar = AssetDatabase.LoadAssetAtPath<Avatar>(charPath);
        foreach (var n in new[] { "Idle", "Walking", "Running" }) SetHumanoid(Dir + n + ".fbx", true, avatar);

        var ctrl = AnimatorController.CreateAnimatorControllerAtPath(CtrlPath);
        ctrl.AddParameter("Speed", AnimatorControllerParameterType.Float);
        var tree = new BlendTree { name = "Locomotion", blendParameter = "Speed", blendType = BlendTreeType.Simple1D, useAutomaticThresholds = false };
        AssetDatabase.AddObjectToAsset(tree, ctrl);
        var idle = Clip(Dir + "Idle.fbx"); var walk = Clip(Dir + "Walking.fbx"); var run = Clip(Dir + "Running.fbx");
        if (idle) tree.AddChild(idle, 0f); if (walk) tree.AddChild(walk, 2f); if (run) tree.AddChild(run, 5.5f);
        var state = ctrl.layers[0].stateMachine.AddState("Locomotion"); state.motion = tree;
        ctrl.layers[0].stateMachine.defaultState = state;

        var old = player.transform.Find("Body_Placeholder"); if (old) Object.DestroyImmediate(old.gameObject);
        var model = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(charPath), player.transform);
        model.name = "Body_Mixamo"; model.transform.localPosition = Vector3.zero;
        var animator = model.GetComponent<Animator>() ?? model.AddComponent<Animator>();
        animator.avatar = avatar; animator.runtimeAnimatorController = ctrl; animator.applyRootMotion = false;
        var pc = player.GetComponent<PlayerController>();
        pc.bodyRenderers = model.GetComponentsInChildren<Renderer>(); // first person: shadows only (body hidden)
        var pa = player.GetComponent<PlayerAnimator>() ?? player.AddComponent<PlayerAnimator>();
        pa.player = pc; pa.animator = animator;
        AssetDatabase.SaveAssets();
        Debug.Log("Mixamo avatar installed on Player.");
    }
}
#endif
