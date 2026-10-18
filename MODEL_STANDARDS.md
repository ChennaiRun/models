# Model standards

## Runtime format and coordinates

- Prefer glTF 2.0 binary (`.glb`) for environments, props and non-authoring character delivery.
- Use metres and +Y up.
- Georeferenced v2 layers use `x=east`, `y=up`, `z=-north`. Record latitude/longitude origin and any local rotation in metadata.
- Keep transforms applied unless a meaningful reusable pivot is required. Document that pivot.
- Use UTF-8 JSON with stable key ordering and two-space indentation for placement metadata.

Legacy v1 OBJ files may use older conventions. Do not copy their axis behavior into new assets.

## Area layout

```text
AreaName/
  README.md
  REFERENCE_MEDIA.md       Optional; required when external visual sources are used
  buildings/
    detailed/              Additive replacements for coarse procedural buildings
  roads/
  ground/
  props/
  data/
  tools/
  unity/
```

Name files with lowercase ASCII and underscores. Name scene nodes semantically; avoid Blender defaults such as `Cube.001`. Prefix dedicated collision meshes with `COL_`.

## Modelling levels

- **Area base:** low-complexity footprints, roads and ground designed for broad coverage.
- **Identity layer:** recognisable signs, transit, vegetation and landmarks that can be added without rebuilding the base.
- **Detailed replacement:** a focused building or landmark with its own file and generator. Unity should hide or disable the corresponding coarse node.

Prefer additive identity and replacement layers for parallel work. They reduce merge conflicts and allow selective loading.

## Geometry and materials

- Optimise for real-time use: instance repeated parts, merge static material groups and avoid unseen internal faces.
- Report vertex/triangle counts and world bounds. Treat large increases as a review item rather than relying on a single universal triangle cap.
- Use a small material palette and texture atlases where practical.
- Embed textures in GLB unless there is a documented streaming reason not to.
- Use collision proxies for detailed/concave assets. Do not generate expensive mesh colliders for vegetation or decorative micro-geometry.
- Keep transparent surfaces limited and explicitly named.

## Reproducibility

Generated assets must have a committed generator, fixed random seed where randomness is used, deterministic ordering and documented dependencies. A generator must not require a Git LFS source unless that dependency is stated clearly.

Metadata should describe:

- coordinate frame and origin;
- asset contents and counts;
- placement coordinates and heading;
- source/reference notes;
- approximations or survey gaps;
- generator version or command when useful.

## References and licensing

Record the source page rather than a search-results URL. Include author and licence for reusable media. Original geometry inspired by a reference must not imply endorsement by the reference creator.

Google Maps, Street View and similar restricted services are observation-only for this repository: do not copy textures, download tiles, trace geometry or use them as photogrammetry input. Prefer OpenStreetMap for map geometry and openly licensed/user-authorised photos for visual detail.

## Git LFS

The repository tracks `.obj`, `.glb`, `.gltf`, `.fbx`, `.png`, `.tif`, `.osm` and `.pbf` through Git LFS. A three-line LFS pointer in a checkout is not a corrupt model; run `git lfs pull` to materialise it. Never replace a pointer with arbitrary text.

## Acceptance checks

- Runtime file parses and has plausible bounds.
- No unintended external buffers or textures.
- Units, axes and placement match the area contract.
- Materials and text are visually checked.
- Collision strategy is documented.
- Generator reruns successfully and deterministically when applicable.
- Reference and licence notes are present.
- Unity registry/build code includes the asset when required.
- `python3 scripts/validate_repo.py` and `git diff --check` pass.
