#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEngine;

/// Menu: Chrompet > Sync Area Assets
/// Copies meshes from the repo area folders (Chromepet/buildings, roads, ground) into Assets/Models/Chrompet and
/// Mixamo FBX files from Chromepet/characters/Mixamo into Assets/Characters/Mixamo (copies are git-ignored).
public static class ChromepetSync
{
    static string AreaRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));

    [MenuItem("Chrompet/Sync Area Assets")]
    public static void Sync()
    {
        Copy("buildings/buildings.obj", "Assets/Models/Chrompet/buildings.obj");
        Copy("roads/roads.obj", "Assets/Models/Chrompet/roads.obj");
        Copy("ground/ground.obj", "Assets/Models/Chrompet/ground.obj");
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
