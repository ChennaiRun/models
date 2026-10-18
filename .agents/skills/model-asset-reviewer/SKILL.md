---
name: model-asset-reviewer
description: Review ChennaiRun 3D asset changes for geometry validity, coordinates, provenance, reproducibility, Git LFS handling, performance, collisions, and Unity readiness. Use for audits and pull-request review, not for creating new models unless fixes are requested.
---

# Model Asset Reviewer

Read `AGENTS.md`, `MODEL_STANDARDS.md`, and the changed area's documentation. Review the diff and generated outputs; do not regenerate or edit assets unless the user asks for fixes.

## Review priorities

1. **Correctness:** GLB parses, bounds and scale are plausible, axes/origin match the area, textures are embedded or intentionally external, and placement metadata agrees with geometry.
2. **Provenance:** reference URLs and licences are recorded, approximations are labelled, and no restricted imagery or unauthorised attachment is shipped.
3. **Reproducibility:** generator/source exists where feasible, dependencies and commands are documented, randomness/order are deterministic, and output ownership does not overlap another active asset.
4. **Runtime behavior:** semantic node names, sensible material/mesh counts, collider proxies, replacement behavior and Unity registry changes are present where needed.
5. **Repository hygiene:** binaries are under Git LFS, generated Unity/cache files are absent, documentation is updated, and validation passes.

Run `python3 scripts/validate_repo.py`, `git diff --check`, `git status --short`, and `git lfs ls-files`. When dependencies are available, load each materialized GLB and report meshes, vertices, triangles, materials, textures and bounds. Return actionable findings ordered by severity with exact file paths; say explicitly when no blocking issues are found.
