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
        var vikram = Path.Combine(PlayersRoot, "Vikram");
        if (Directory.Exists(vikram))
            foreach (var f in Directory.GetFiles(vikram, "*.fbx"))
                CopyPlayer(Path.Combine("Vikram", Path.GetFileName(f)), "Assets/Characters/Vikram/" + Path.GetFileName(f));
        AssetDatabase.Refresh();
        EnableLightmapUvs(Dst);
    }

    // glTF has no dedicated lightmap-UV convention. Ask glTFast to generate Unity's
    // secondary UV channel for every synced environment mesh so baked GI can unwrap it.
    static void EnableLightmapUvs(string assetDirectory)
    {
        var absoluteDirectory = Path.Combine(Path.GetDirectoryName(Application.dataPath), assetDirectory);
        if (!Directory.Exists(absoluteDirectory)) return;

        foreach (var file in Directory.GetFiles(absoluteDirectory, "*.glb", SearchOption.AllDirectories))
        {
            var assetPath = file.Replace('\\', '/');
            assetPath = "Assets/" + assetPath.Substring(Application.dataPath.Replace('\\', '/').Length + 1);
            var importer = AssetImporter.GetAtPath(assetPath);
            if (importer == null) continue;

            var serializedImporter = new SerializedObject(importer);
            var generateUvs = serializedImporter.FindProperty("editorImportSettings.generateSecondaryUVSet");
            bool shouldGenerate = assetPath.Contains("/detailed/");
            if (generateUvs == null || generateUvs.boolValue == shouldGenerate) continue;

            generateUvs.boolValue = shouldGenerate;
            serializedImporter.ApplyModifiedPropertiesWithoutUndo();
            importer.SaveAndReimport();
        }
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
