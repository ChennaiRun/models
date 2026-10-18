# Vikram

`Vikram.fbx` is the user-supplied character (FBX 7.3, about 52 MB). It contains a Mixamo humanoid skeleton. The original download remains at `/Users/sivab/Downloads/character.fbx`; this is a renamed copy in the shared player asset folder.

Run **Chrompet > Sync Area Assets** in the Chromepet Unity project to copy it to `Assets/Characters/Vikram/Vikram.fbx`. Build the scene to install Vikram automatically, or run **Chrompet > Setup Vikram Avatar** with `Player` in an open scene. The setup replaces the capsule placeholder with Vikram and configures a Humanoid rig.

For idle/walk/run animation, add these optional files to this folder, then sync and run setup again:

| File | Mixamo export settings |
|---|---|
| `Idle.fbx` | FBX for Unity, Without Skin, 30 fps |
| `Walking.fbx` | FBX for Unity, Without Skin, 30 fps, In Place |
| `Running.fbx` | FBX for Unity, Without Skin, 30 fps, In Place |

The editor setup builds `VikramLocomotion.controller` with a 1D blend tree on `Speed` (0 idle, 2 walk, 5.5 run). Without these clips, Vikram can be displayed but does not yet have locomotion animation. The player controller uses WASD and mouse, Shift to sprint, Space to jump, and V to toggle first and third person.
