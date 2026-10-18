---
name: area-model-builder
description: Build or extend ChennaiRun geospatial areas, detailed buildings, landmarks, transport elements, vegetation, or local identity props. Use for model generation and source research; use unity-model-integrator for Unity-only wiring and model-asset-reviewer for review-only work.
---

# Area Model Builder

Read `AGENTS.md`, `MODEL_STANDARDS.md`, and the target area's README before changing files.

## Choose the smallest ownership boundary

Prefer a standalone identity layer, detailed replacement, or prop GLB with its own generator. Modify an area-wide generator only when the task genuinely owns every output it rewrites. State the generator/output pair in progress updates so other agents can avoid it.

## Build from permitted sources

Use OpenStreetMap or other licensed geodata for map geometry. Record reference URLs, author, date, licence, coordinates, and which details are approximate. Maps and Street View may be observed, but do not copy their pixels, trace restricted imagery, cache tiles, or use them for photogrammetry. Do not commit user-provided media without explicit permission.

## Preserve the area contract

Use metres and +Y up. For georeferenced v2 layers, use x=east, y=up, z=-north and the area's documented origin. Keep coordinate conversion in one named function. Record placements/headings in JSON when they are not obvious from the generator.

Commit the runtime GLB and reproducible generator together where feasible. Use deterministic seeds and stable iteration order. Give meshes semantic node names and prefix dedicated colliders with `COL_`.

## Hand off cleanly

Update the area's README and reference tracker. If the asset belongs in the game scene, leave explicit integration information or invoke `unity-model-integrator`. Run `python3 scripts/validate_repo.py`, compile changed Python generators, inspect GLB counts/bounds, visually inspect the output, and run `git diff --check`.
