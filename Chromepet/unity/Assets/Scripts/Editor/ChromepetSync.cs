#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEngine;

/// Menu: Chrompet > Sync Area Assets
/// Copies the per-area v2 GLBs (Chromepet/buildings, roads, ground, props), tree collider data and v2 metadata into
/// Assets/Models/Chrompet, and shared player assets from models/players into Assets/Characters.
/// Copies are git-ignored; GLBs are imported by glTFast (com.unity.cloud.gltfast).
public static class ChromepetSync
{
    public static string AreaRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));
    static string PlayersRoot => Path.GetFullPath(Path.Combine(AreaRoot, "..", "players"));
    public const string Dst = "Assets/Models/Chrompet/";
    public static readonly string[] Glbs = {
        "ground/ground_v2.glb", "roads/roads_v2.glb", "buildings/campus_buildings.glb",
        "buildings/outside_buildings.glb", "props/landmarks.glb", "props/chrompet_identity.glb",
        "props/trees.glb" };

    [MenuItem("Chrompet/Sync Area Assets")]
    public static void Sync()
    {
        foreach (var g in Glbs) Copy(g, Dst + Path.GetFileName(g));
        var det = Path.Combine(AreaRoot, "buildings", "detailed");
        if (Directory.Exists(det))
            foreach (var f in Directory.GetFiles(det, "*.glb"))
                Copy(Path.Combine("buildings", "detailed", Path.GetFileName(f)), Dst + "detailed/" + Path.GetFileName(f));
        Copy("props/trees_colliders.json", Dst + "trees_colliders.json");
        Copy("data/v2_meta.json", Dst + "v2_meta.json");
        Copy("data/identity_meta.json", Dst + "identity_meta.json");
        CopyPlayer("Baymax/baymax.glb", "Assets/Characters/Baymax/baymax.glb");
        var vikram = Path.Combine(PlayersRoot, "Vikram");
        if (Directory.Exists(vikram))
            foreach (var f in Directory.GetFiles(vikram, "*.fbx"))
                CopyPlayer(Path.Combine("Vikram", Path.GetFileName(f)), "Assets/Characters/Vikram/" + Path.GetFileName(f));
        AssetDatabase.Refresh();
    }

    static void Copy(string rel, string dst) => CopyFrom(AreaRoot, rel, dst);
    static void CopyPlayer(string rel, string dst) => CopyFrom(PlayersRoot, rel, dst);

    static void CopyFrom(string root, string rel, string dst)
    {
        var src = Path.Combine(root, rel);
        if (!File.Exists(src)) { Debug.LogWarning("Missing " + src); return; }
        Directory.CreateDirectory(Path.GetDirectoryName(dst));
        if (!File.Exists(dst) || File.GetLastWriteTimeUtc(src) > File.GetLastWriteTimeUtc(dst)) File.Copy(src, dst, true);
    }
}
#endif
