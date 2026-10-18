#!/usr/bin/env python3
"""Dependency-free structural validation for ChennaiRun model repositories."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path


LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"
LFS_EXTENSIONS = {".fbx", ".glb", ".gltf", ".obj", ".osm", ".pbf", ".png", ".tif"}
REQUIRED_DOCS = ("README.md", "AGENTS.md", "CONTRIBUTING.md", "MODEL_STANDARDS.md")


def is_lfs_pointer(path: Path) -> bool:
    with path.open("rb") as handle:
        return handle.read(len(LFS_PREFIX)) == LFS_PREFIX


def validate_glb(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("file is too short for a GLB header")
    magic, version, declared = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2:
        raise ValueError(f"expected glTF 2.0 header, found {magic!r} version {version}")
    if declared != len(data):
        raise ValueError(f"declared length {declared} differs from file length {len(data)}")

    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise ValueError("first GLB chunk is not JSON")
    document = json.loads(data[20 : 20 + json_length].rstrip(b" \0"))
    if document.get("asset", {}).get("version") != "2.0":
        raise ValueError("JSON asset.version is not 2.0")
    external = [
        entry["uri"]
        for entry in document.get("buffers", []) + document.get("images", [])
        if entry.get("uri") and not entry["uri"].startswith("data:")
    ]
    if external:
        raise ValueError(f"contains external resources: {external}")
    return {
        "nodes": len(document.get("nodes", [])),
        "meshes": len(document.get("meshes", [])),
        "materials": len(document.get("materials", [])),
        "images": len(document.get("images", [])),
    }


def validate_skill(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\nname:" not in text or "\ndescription:" not in text:
        raise ValueError("missing YAML frontmatter name/description")
    if "TODO" in text:
        raise ValueError("contains unfinished TODO scaffold text")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-materialized", action="store_true", help="fail when a GLB is only an LFS pointer")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    glbs = pointers = 0

    for name in REQUIRED_DOCS:
        if not (root / name).is_file():
            errors.append(f"missing required document: {name}")

    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(root)
        try:
            if path.suffix.lower() in LFS_EXTENSIONS and is_lfs_pointer(path):
                pointers += 1
                if args.require_materialized and path.suffix.lower() == ".glb":
                    raise ValueError("GLB is an LFS pointer; run git lfs pull")
            elif path.suffix.lower() == ".glb":
                stats = validate_glb(path)
                glbs += 1
                print(f"GLB {rel}: {stats['meshes']} meshes, {stats['materials']} materials, {stats['images']} images")
            elif path.suffix.lower() == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            elif path.name == "SKILL.md" and ".agents" in path.parts:
                validate_skill(path)
        except Exception as exc:
            errors.append(f"{rel}: {exc}")

    for child in sorted(root.iterdir()):
        if child.is_dir() and not child.name.startswith(".") and child.name not in {"players", "scripts"}:
            if not (child / "README.md").is_file():
                errors.append(f"{child.name}: area directory has no README.md")

    print(f"Checked {glbs} materialized GLBs and {pointers} Git LFS pointers.")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
