# Mixamo avatar (download manually – needs an Adobe login at https://www.mixamo.com)
Put these files in `Chromepet/characters/Mixamo/`, exact names (they are synced into the Unity project by **Chrompet > Sync Area Assets**):
| File | Mixamo export settings |
|---|---|
| Character.fbx | any character, Format: **FBX for Unity**, **With Skin**, T-pose |
| Idle.fbx | "Idle" anim, FBX for Unity, **Without Skin**, 30 fps |
| Walking.fbx | "Walking" (tick **In Place**), FBX for Unity, Without Skin, 30 fps |
| Running.fbx | "Running" (tick **In Place**), FBX for Unity, Without Skin, 30 fps |

Then in Unity: menu **Chrompet > Setup Mixamo Avatar** (Player must be in the open scene).
It sets Humanoid rigs, builds `PlayerLocomotion.controller` (1D blend on `Speed`: 0 idle, 2 walk, 5.5 run),
replaces the capsule placeholder and wires `PlayerAnimator`. Until then a capsule is used.
First person: body renders shadows only; press **V** for third person.
