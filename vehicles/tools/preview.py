"""Render inspection views of a vehicle GLB with a tiny z-buffer rasteriser.

Usage: python3 vehicles/tools/preview.py <asset.glb> <out.png> [--front M] [--width PX]
          [--only PREFIX,...] [--hero HERO.png] [--gif TURNTABLE.gif] [--frames N]
  --front M   only show the front M metres of the asset (useful for long trains)
  --only      only show nodes whose name starts with one of the prefixes (whole cars)
  --hero      also write a large anti-aliased front-3/4 still
  --gif       also write an anti-aliased turntable GIF
Write previews outside the repository (e.g. /tmp); they are not committed.
Orthographic views, Lambert shading, per-pixel texture sampling, COL_* hidden.
Dependencies: trimesh, numpy, pillow.
"""

from __future__ import annotations

import argparse
import math

import numpy as np
import trimesh
from PIL import Image, ImageDraw


def load_triangles(path, front=None, only=None):
    scene = trimesh.load(path, force="scene")
    items = []
    for node in scene.graph.nodes_geometry:
        transform, geom_name = scene.graph[node]
        if node.startswith("COL_") or "COL_" in geom_name:
            continue
        if only and not any(node.startswith(p) for p in only):
            continue
        geom = scene.geometry[geom_name].copy()
        geom.apply_transform(transform)
        mat = getattr(geom.visual, "material", None)
        tex = None
        uv = None
        color = np.array([0.7, 0.7, 0.7])
        if mat is not None and getattr(mat, "baseColorTexture", None) is not None and geom.visual.uv is not None:
            tex = np.asarray(mat.baseColorTexture.convert("RGB"), float) / 255.0
            uv = geom.visual.uv[geom.faces]
        elif mat is not None and getattr(mat, "baseColorFactor", None) is not None:
            c = np.asarray(mat.baseColorFactor[:3], float)
            color = c / 255.0 if c.max() > 1.0 else c
        tris = geom.triangles
        keep = np.ones(len(tris), bool)
        if front is not None:
            zmax = scene.bounds[1][2]
            keep = tris[:, :, 2].max(axis=1) >= zmax - front
        items.append((tris[keep], geom.face_normals[keep], color, tex, None if uv is None else uv[keep]))
    return items


def view_matrix(azimuth_deg, elevation_deg):
    """Rotation taking world -> camera (camera looks along -Zc).

    azimuth 0 = looking at the vehicle front (+Z face), 90 = looking at the +X side.
    """
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    eye = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
    fwd = -eye
    right = np.cross(fwd, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return np.stack([right, up, -fwd]), eye


def rasterise(items, azimuth, elevation, size, bounds_pts, background=(0.93, 0.95, 0.98), fill=0.92):
    rot, eye = view_matrix(azimuth, elevation)
    w, h = size
    pts = bounds_pts @ rot.T
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    scale = fill * min(w / (hi[0] - lo[0]), h / (hi[1] - lo[1]))
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    img = np.ones((h, w, 3)) * np.array(background)
    # Simple ground shadow line for context: none; background gradient instead.
    img *= np.linspace(1.0, 0.86, h)[:, None, None]
    zbuf = np.full((h, w), -np.inf)
    light = np.array([0.4, 0.85, 0.35])
    light /= np.linalg.norm(light)
    for tris, normals, color, tex, uvs in items:
        if len(tris) == 0:
            continue
        cam = tris @ rot.T
        sx = (cam[:, :, 0] - cx) * scale + w / 2
        sy = h / 2 - (cam[:, :, 1] - cy) * scale
        sz = cam[:, :, 2]
        facing = normals @ eye
        shade = 0.38 + 0.62 * np.clip(normals @ light, 0, 1) * 0.8 + 0.12 * np.clip(facing, 0, 1)
        for t in range(len(tris)):
            if facing[t] <= 1e-6:
                continue  # back-face cull (glTF is single-sided by default)
            x, y, z = sx[t], sy[t], sz[t]
            x0, x1 = int(max(0, math.floor(x.min()))), int(min(w - 1, math.ceil(x.max())))
            y0, y1 = int(max(0, math.floor(y.min()))), int(min(h - 1, math.ceil(y.max())))
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(d) < 1e-9:
                continue
            l0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
            l1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
            l2 = 1 - l0 - l1
            inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            if not inside.any():
                continue
            depth = l0 * z[0] + l1 * z[1] + l2 * z[2]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            mask = inside & (depth > sub)
            if not mask.any():
                continue
            sub[mask] = depth[mask]
            if tex is not None:
                uv = uvs[t]
                u = l0 * uv[0, 0] + l1 * uv[1, 0] + l2 * uv[2, 0]
                v = l0 * uv[0, 1] + l1 * uv[1, 1] + l2 * uv[2, 1]
                th, tw = tex.shape[:2]
                px = np.clip((u * (tw - 1)).astype(int), 0, tw - 1)
                py = np.clip(((1 - v) * (th - 1)).astype(int), 0, th - 1)
                col = tex[py, px] * shade[t]
                img[y0:y1 + 1, x0:x1 + 1][mask] = col[mask]
            else:
                img[y0:y1 + 1, x0:x1 + 1][mask] = np.clip(color * shade[t], 0, 1)
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))


VIEWS = [
    (35, 18, "front-left 3/4 (+X side)"),
    (-145, 18, "rear-right 3/4 (-X side)"),
    (90, 0, "left side (+X: doors / platform side)"),
    (-90, 0, "right side (-X)"),
    (0, 0, "front (+Z)"),
    (180, 0, "rear (-Z)"),
]


def corners_of(items):
    all_pts = np.concatenate([t.reshape(-1, 3) for t, *_ in items if len(t)])
    lo, hi = all_pts.min(axis=0), all_pts.max(axis=0)
    return np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])


def fixed_sphere(corners):
    """Bounding points that are rotation-invariant about Y, so a turntable keeps a constant scale."""
    lo, hi = corners.min(axis=0), corners.max(axis=0)
    c = (lo + hi) / 2
    r = float(np.hypot(hi[0] - lo[0], hi[2] - lo[2]) / 2)
    ring = [[c[0] + r * math.cos(a), y, c[2] + r * math.sin(a)] for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)
            for y in (lo[1], hi[1])]
    return np.array(ring)


def antialiased(items, az, el, size, bounds, ss=2, fill=0.92):
    w, h = size
    big = rasterise(items, az, el, (w * ss, h * ss), bounds, fill=fill)
    return big.resize((w, h), Image.LANCZOS)


def hero(items, out, title, size=(1600, 900)):
    corners = corners_of(items)
    img = antialiased(items, 35, 14, size, corners, ss=2, fill=0.9)
    ImageDraw.Draw(img).text((16, 12), title, fill=(25, 25, 25))
    img.save(out)


def turntable(items, out, frames=36, size=(720, 405), elevation=14):
    corners = fixed_sphere(corners_of(items))
    imgs = []
    for k in range(frames):
        az = 35 + 360.0 * k / frames
        imgs.append(antialiased(items, az, elevation, size, corners, ss=2, fill=0.98).convert(
            "P", palette=Image.ADAPTIVE, colors=200))
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=90, loop=0, optimize=True)


def render(path, out, front=None, width=900, only=None):
    items = load_triangles(path, front, only)
    all_pts = np.concatenate([t.reshape(-1, 3) for t, *_ in items if len(t)])
    lo, hi = all_pts.min(axis=0), all_pts.max(axis=0)
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    tile_h = int(width * 0.5)
    panels = []
    for az, el, title in VIEWS:
        panel = rasterise(items, az, el, (width, tile_h), corners)
        ImageDraw.Draw(panel).text((8, 6), title, fill=(20, 20, 20))
        panels.append(panel)
    sheet = Image.new("RGB", (width * 2, tile_h * 3), (255, 255, 255))
    for i, panel in enumerate(panels):
        sheet.paste(panel, ((i % 2) * width, (i // 2) * tile_h))
    sheet.save(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("glb")
    parser.add_argument("out")
    parser.add_argument("--front", type=float, default=None)
    parser.add_argument("--width", type=int, default=900)
    parser.add_argument("--only", default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gif", default=None)
    parser.add_argument("--frames", type=int, default=36)
    parser.add_argument("--title", default="")
    args = parser.parse_args()
    only = args.only.split(",") if args.only else None
    render(args.glb, args.out, args.front, args.width, only)
    if args.hero or args.gif:
        items = load_triangles(args.glb, args.front, only)
        if args.hero:
            hero(items, args.hero, args.title)
        if args.gif:
            turntable(items, args.gif, args.frames)
