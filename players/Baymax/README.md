# Baymax character model

`baymax.glb` is a lightweight, unrigged 3D character for the ChennaiRun Unity game. It is 2.36 m tall, uses metres with Y up, faces +Z, and has its root at ground level. Head, arms, hands, legs, eyes, and badge are separate named meshes. The head, arms, hands, and legs have pivot nodes for simple transform animation, but there is no humanoid skeleton or animation clips yet.

Run `python3 generate.py` to regenerate the model. The script needs only Python's standard library for the `.glb`; Pillow is optional for `preview.png`.

## Unity 2022.3

The Chromepet Unity project includes glTFast. In Unity, run **Chrompet > Sync Area Assets** to copy the model into `Chromepet/unity/Assets/Characters/Baymax/`; glTFast imports `.glb` files in `Assets` as prefabs. Place the resulting prefab as a child of `Player`, keeping its local position and rotation at zero. Deactivate `Body_Vikram` (or `Body_Placeholder` if Vikram was not installed), then populate `PlayerController.bodyRenderers` with the imported renderers. The model is unrigged, so Vikram's Humanoid animation setup does not apply; animate the named pivot nodes directly or rig it separately.

This model is a depiction of Disney's Baymax. Obtain the relevant rights before distributing it in a game.
