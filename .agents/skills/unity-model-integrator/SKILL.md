---
name: unity-model-integrator
description: Integrate ChennaiRun GLB or FBX source assets into an area's Unity project, including sync registries, placement, replacement nodes, colliders, spawn behavior, and import verification. Do not use for modelling-only or review-only tasks.
---

# Unity Model Integrator

Read `AGENTS.md`, `MODEL_STANDARDS.md`, the area's README, and its Unity README first.

Treat top-level area/player assets as sources of truth. Sync them into git-ignored Unity folders; do not commit imported copies, `.meta` files from ignored generated folders, Library caches, builds, or editor state.

## Integration invariants

- Preserve glTF +Y-up orientation and the area's documented east/north mapping.
- Register additive GLBs without removing existing layers.
- When a detailed asset replaces coarse procedural geometry, hide the named coarse node deterministically rather than deleting source geometry.
- Use `COL_*` meshes or simple proxy colliders for detailed assets. Avoid mesh colliders on vegetation and decorative micro-geometry.
- Keep spawn and look markers derived from model/metadata coordinates rather than duplicated magic numbers.
- Make repeated scene builds idempotent.

Verify source paths, imports, bounds, materials, colliders, hidden replacements and player spawn. Compile or open the project in the supported Unity version when possible. If Unity cannot be run, perform static validation and state the remaining verification clearly. Finish with `python3 scripts/validate_repo.py` and `git diff --check`.
