# ChennaiRun Models

Open 3D environment, landmark, transport and character assets for ChennaiRun. The repository combines procedural GIS generation with focused hand-authored models, then integrates the results into Unity as standard glTF assets.

## Current coverage

| Area | Included assets | Status |
|---|---|---|
| [Chromepet](Chromepet/) | MIT campus, 8,700+ surrounding buildings, GST Road, MIT Flyover, Chrompet railway station, suburban train, local props, vegetation and detailed campus buildings | Active |
| [Shared players](players/) | Baymax GLB and Vikram FBX character sources | Active |

Chromepet uses an offline OpenStreetMap-derived base plus original procedural and hand-modelled detail. Google Maps and other online imagery may be used only for observation where their terms permit it; restricted imagery is never copied, cached, traced or shipped.

## Repository layout

```text
<area>/
  buildings/       Area and detailed building GLBs
  roads/           Roads, rail and transport infrastructure
  ground/          Terrain and surface layers
  props/           Landmarks, vegetation and local identity assets
  data/            Source extracts and generated placement metadata
  tools/           Reproducible generators
  unity/           Area-specific Unity integration
players/           Reusable character assets
.agents/skills/    Repo-local Codex workflows
scripts/           Repository validation
```

Read [MODEL_STANDARDS.md](MODEL_STANDARDS.md) before producing an asset and [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Coding agents must also follow [AGENTS.md](AGENTS.md).

## Quick start

```bash
git lfs install
git clone https://github.com/ChennaiRun/models.git
cd models
git lfs pull
python3 scripts/validate_repo.py
```

Area generators list their own dependencies. For example, the lightweight Chrompet identity layer needs `trimesh`, `numpy` and `Pillow`:

```bash
python3 -m venv .venv
.venv/bin/pip install trimesh numpy pillow
cd Chromepet
../.venv/bin/python tools/chrompet_identity.py
```

Open [Chromepet/unity](Chromepet/unity/) in Unity 2022.3 LTS and run **Chrompet → Build MIT Campus Scene** to sync source GLBs into the generated Unity asset folders.

## Repo-local agent skills

Codex-compatible skills live in `.agents/skills/`:

- `area-model-builder` — creates or extends geospatial areas, buildings, landmarks and street props.
- `unity-model-integrator` — imports source assets, preserves orientation and configures scenes/colliders.
- `model-asset-reviewer` — audits geometry, provenance, metadata, Git LFS and runtime suitability.

These skills are deliberately separated so parallel agents can own different outputs without sharing a mutable generator or binary.

## Asset contract

- Runtime meshes use glTF 2.0 binary (`.glb`), metres and +Y up.
- Georeferenced v2 area assets use `x=east`, `y=up`, `z=-north` and document their origin.
- Every derived asset must retain a generator or clear source notes, placement metadata and licensing/provenance.
- Large binaries are Git LFS tracked. Never hand-edit an LFS pointer.
- Generated Unity imports, caches and builds are not committed.

Run `python3 scripts/validate_repo.py --require-materialized` when all LFS objects are available locally; ordinary CI accepts valid LFS pointers and validates every materialized GLB.

## Data and licensing

OpenStreetMap-derived data is © OpenStreetMap contributors and distributed under ODbL. Third-party visual references retain their original licences and attribution. Each area records source-specific notes beside its assets. Code and original model licensing should be reviewed before redistribution outside ChennaiRun.
