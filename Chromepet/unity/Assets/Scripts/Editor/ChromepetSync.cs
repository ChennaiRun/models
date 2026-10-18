#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEngine;

/// Menu: Chrompet > Sync Area Assets
/// Copies the per-area v2 GLBs (Chromepet/buildings, roads, ground, props), tree collider data and v2 metadata into
/// Assets/Models/Chrompet, and Mixamo FBX from Chromepet/characters/Mixamo into Assets/Characters/Mixamo.
/// Copies are git-ignored; the sources of truth are the area folders. GLBs are imported by glTFast (com.unity.cloud.gltfast).
public static class ChromepetSync
{
    public static string AreaRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));
    public const string Dst = "Assets/Models/Chrompet/";
    public static readonly string[] Glbs = {
        "ground/ground_v2.glb", "roads/roads_v2.glb", "buildings/campus_buildings.glb",
        "buildings/outside_buildings.glb", "props/landmarks.glb", "props/trees.glb" };

    [MenuItem("Chrompet/Sync Area Assets")]
    public static void Sync()
    {
        foreach (var g in Glbs) Copy(g, Dst + Path.GetFileName(g));
        Copy("props/trees_colliders.json", Dst + "trees_colliders.json");
        Copy("data/v2_meta.json", Dst + "v2_meta.json");
        var mix = Path.Combine(AreaRoot, "characters", "Mixamo");
        if (Directory.Exists(mix))
            foreach (var f in Directory.GetFiles(mix, "*.fbx"))
                Copy(Path.Combine("characters", "Mixamo", Path.GetFileName(f)), "Assets/Characters/Mixamo/" + Path.GetFileName(f));
        AssetDatabase.Refresh();
    }

    static void Copy(string rel, string dst)
    {
        var src = Path.Combine(AreaRoot, rel);
        if (!File.Exists(src)) { Debug.LogWarning("Missing " + src); return; }
        Directory.CreateDirectory(Path.GetDirectoryName(dst));
        if (!File.Exists(dst) || File.GetLastWriteTimeUtc(src) > File.GetLastWriteTimeUtc(dst)) File.Copy(src, dst, true);
    }
}
#endif
