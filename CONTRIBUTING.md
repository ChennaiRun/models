# Contributing

ChennaiRun models are built by people and coding agents working in parallel. Contributions should be independently reviewable, reproducible and safe to merge without replacing another asset accidentally.

## Setup

```bash
git lfs install
git lfs pull
python3 scripts/validate_repo.py
```

Use a task-specific branch or worktree. Suggested branch prefixes are `area/`, `building/`, `props/`, `player/`, `unity/` and `docs/`.

## Choose an ownership boundary

Before modelling, identify the files the task owns. The best parallel units are standalone detailed buildings, prop packs, transport elements, character assets, or a new area folder. Avoid two tasks writing the same generated GLB or the same placement metadata.

If work must modify a shared generator, keep the output set small and announce the owned functions and generated files in the pull request. Integrate documentation and Unity registry changes after asset work has stabilised.

## Contribution types

### New area

Create the standard area folders described in [MODEL_STANDARDS.md](MODEL_STANDARDS.md), document the coordinate origin and add a small reproducible first layer before expanding coverage.

### Detailed building or landmark

Prefer an additive file under `<area>/buildings/detailed/` or `<area>/props/`. Include the generator/source, placement, replacement behavior and collider strategy. Do not overwrite the coarse area layer unless the task explicitly owns its generator.

### Procedural layer

Commit both generator and output. Fixed seeds, stable ordering and explicit coordinate conversions are required so another contributor can reproduce the binary.

### Character

Place reusable characters under `players/<name>/`. Record licence, scale, rig, animation compatibility and Unity setup requirements.

## Sources and provenance

- Record URLs, creator, date observed and licence for external references.
- Distinguish surveyed facts from estimates and visual approximations.
- Do not commit source media without redistribution permission.
- Do not use restricted map imagery for texture extraction, tracing or photogrammetry.
- Keep user-provided attachments private unless the user explicitly authorises repository inclusion.

## Validation and pull requests

Run:

```bash
python3 scripts/validate_repo.py
git diff --check
git lfs ls-files
```

In the pull request, list generated outputs, source/generator pairs, coordinate frame, triangle/vertex counts, visual checks, Unity status and known approximations. The provided pull-request template includes the full checklist.

Small focused commits are easier to integrate than a single commit that mixes source research, multiple assets and unrelated Unity changes.
