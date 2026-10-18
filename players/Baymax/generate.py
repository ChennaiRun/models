#!/usr/bin/env python3
"""Build a lightweight, poseable Baymax-inspired inflatable character as glTF 2.0.

No external dependencies. Run `python3 generate.py` to rebuild baymax.glb and preview.png.
The model uses metres, Y up, and faces +Z. The root sits on the ground.
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path


OUT = Path(__file__).resolve().parent
WHITE = (0.91, 0.945, 0.95)
FACE = (0.025, 0.035, 0.045)
SEAM = (0.68, 0.73, 0.75)
ACCENT = (0.23, 0.69, 0.76)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(a, s):
    return tuple(x * s for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    length = math.sqrt(dot(a, a))
    return mul(a, 1 / length) if length else (0, 1, 0)


def ellipsoid(center, radii, rings=20, sides=32, pear=0.0):
    """An analytic, smooth sphere; pear widens its lower half."""
    vertices = []
    indices = []
    for i in range(rings + 1):
        theta = -math.pi / 2 + math.pi * i / rings
        y = math.sin(theta)
        radial = math.cos(theta)
        factor = 1 - pear * y
        for j in range(sides + 1):
            phi = 2 * math.pi * j / sides
            vertices.append((center[0] + radii[0] * radial * math.cos(phi) * factor,
                             center[1] + radii[1] * y,
                             center[2] + radii[2] * radial * math.sin(phi) * factor))
    for i in range(rings):
        for j in range(sides):
            a = i * (sides + 1) + j
            b = a + sides + 1
            indices.extend((a, b, a + 1, a + 1, b, b + 1))
    return vertices, indices


def oriented_ellipsoid(start, end, radii, rings=16, sides=24):
    center = mul(add(start, end), .5)
    axis = unit(sub(end, start))
    across = unit(cross((0, 0, 1), axis))
    forward = unit(cross(axis, across))
    length = math.sqrt(dot(sub(end, start), sub(end, start)))
    vertices, indices = ellipsoid((0, 0, 0), (radii[0], length / 2 + radii[1], radii[2]), rings, sides)
    return [add(center, add(mul(across, p[0]), add(mul(axis, p[1]), mul(forward, p[2])))) for p in vertices], indices


def tube(points, radius=.008, sides=10):
    vertices = []
    indices = []
    for k, point in enumerate(points):
        tangent = unit(sub(points[min(k + 1, len(points) - 1)], points[max(k - 1, 0)]))
        across = unit(cross((0, 1, 0), tangent))
        up = unit(cross(tangent, across))
        for j in range(sides):
            phi = 2 * math.pi * j / sides
            vertices.append(add(point, mul(add(mul(across, math.cos(phi)), mul(up, math.sin(phi))), radius)))
    for k in range(len(points) - 1):
        for j in range(sides):
            a = k * sides + j
            b = k * sides + (j + 1) % sides
            c = (k + 1) * sides + j
            d = (k + 1) * sides + (j + 1) % sides
            indices.extend((a, c, b, b, c, d))
    return vertices, indices


class Builder:
    def __init__(self):
        self.binary = bytearray()
        self.views = []
        self.accessors = []
        self.meshes = []
        self.nodes = []
        self.parts = []
        self.materials = []

    def material(self, name, rgb, roughness=.72):
        self.materials.append({"name": name, "pbrMetallicRoughness": {
            "baseColorFactor": [*rgb, 1], "metallicFactor": 0, "roughnessFactor": roughness},
            "doubleSided": True})
        return len(self.materials) - 1

    def accessor(self, payload, component, kind, count, minimum=None, maximum=None, target=None):
        while len(self.binary) % 4:
            self.binary.append(0)
        offset = len(self.binary)
        self.binary.extend(payload)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(payload)}
        if target:
            view["target"] = target
        self.views.append(view)
        accessor = {"bufferView": len(self.views) - 1, "componentType": component,
                    "count": count, "type": kind}
        if minimum is not None:
            accessor["min"] = minimum
            accessor["max"] = maximum
        self.accessors.append(accessor)
        return len(self.accessors) - 1

    def node(self, name, translation=(0, 0, 0), parent=None):
        node = {"name": name, "translation": list(translation)}
        self.nodes.append(node)
        index = len(self.nodes) - 1
        if parent is not None:
            self.nodes[parent].setdefault("children", []).append(index)
        return index

    def mesh(self, name, geometry, material, parent):
        positions, indices = geometry
        normals = [(0.0, 0.0, 0.0) for _ in positions]
        for k in range(0, len(indices), 3):
            a, b, c = (positions[indices[k + q]] for q in range(3))
            n = cross(sub(b, a), sub(c, a))
            for q in range(3):
                idx = indices[k + q]
                normals[idx] = add(normals[idx], n)
        # UV seams and the two poles have duplicate vertices. Share their normal
        # so game renderers do not show a hard stripe down otherwise soft surfaces.
        shared = {}
        for vertex, normal in zip(positions, normals):
            key = tuple(round(x, 6) for x in vertex)
            shared[key] = add(shared.get(key, (0, 0, 0)), normal)
        normals = [unit(shared[tuple(round(x, 6) for x in vertex)]) for vertex in positions]
        flat_p = [x for p in positions for x in p]
        flat_n = [x for n in normals for x in n]
        p = self.accessor(struct.pack('<' + 'f' * len(flat_p), *flat_p), 5126, "VEC3", len(positions),
                          [min(v[i] for v in positions) for i in range(3)],
                          [max(v[i] for v in positions) for i in range(3)], 34962)
        n = self.accessor(struct.pack('<' + 'f' * len(flat_n), *flat_n), 5126, "VEC3", len(positions), target=34962)
        ind = self.accessor(struct.pack('<' + 'H' * len(indices), *indices), 5123, "SCALAR", len(indices),
                            [min(indices)], [max(indices)], 34963)
        self.meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": p, "NORMAL": n},
                                                            "indices": ind, "material": material}]})
        child = self.node(name, parent=parent)
        self.nodes[child]["mesh"] = len(self.meshes) - 1
        self.parts.append((parent, positions, indices, material))
        return child

    def save(self, path):
        while len(self.binary) % 4:
            self.binary.append(0)
        doc = {"asset": {"version": "2.0", "generator": "ChennaiRun Baymax procedural model"},
               "scene": 0, "scenes": [{"name": "Baymax", "nodes": [0]}], "nodes": self.nodes,
               "meshes": self.meshes, "materials": self.materials,
               "buffers": [{"byteLength": len(self.binary)}], "bufferViews": self.views,
               "accessors": self.accessors}
        encoded = json.dumps(doc, separators=(',', ':')).encode('utf8')
        encoded += b' ' * ((-len(encoded)) % 4)
        size = 12 + 8 + len(encoded) + 8 + len(self.binary)
        path.write_bytes(struct.pack('<4sII', b'glTF', 2, size) +
                         struct.pack('<I4s', len(encoded), b'JSON') + encoded +
                         struct.pack('<I4s', len(self.binary), b'BIN\x00') + self.binary)


def build():
    b = Builder()
    white = b.material("Soft warm white vinyl", WHITE)
    face = b.material("Graphite face markings", FACE, .55)
    seam = b.material("Soft grey seams", SEAM)
    accent = b.material("Medical badge blue", ACCENT, .45)
    root = b.node("Baymax_ROOT")

    b.mesh("Torso_inflatable", ellipsoid((0, 1.17, 0), (.56, .78, .43), pear=.16), white, root)
    b.mesh("Neck_collar", ellipsoid((0, 1.88, 0), (.25, .14, .23)), white, root)
    head = b.node("Head_PIVOT", (0, 1.88, 0), root)
    b.mesh("Head", ellipsoid((0, .24, .035), (.43, .235, .26)), white, head)
    for side, label in ((-1, "Left"), (1, "Right")):
        b.mesh(f"Eye_{label}", ellipsoid((side * .194, .253, .271), (.055, .063, .026), 16, 24), face, head)
    # The thin, gently dipping line is a defining feature of the soft robot's face.
    b.mesh("Eye_connector", tube([(-.193 + i * .386 / 24, .251 - .012 * math.sin(math.pi * i / 24),
                                   .318 - .036 * abs(2 * i / 24 - 1)) for i in range(25)], .008), face, head)

    # Very restrained seam and badge detail, kept flush with the front of the body.
    b.mesh("Chest_badge_rim", ellipsoid((-.24, 1.68, .301), (.075, .105, .017), 16, 24), seam, root)
    b.mesh("Chest_badge", ellipsoid((-.24, 1.68, .314), (.055, .078, .014), 16, 24), accent, root)
    b.mesh("Chest_badge_center", ellipsoid((-.24, 1.68, .327), (.018, .025, .009), 12, 16), white, root)

    for side, label in ((-1, "Left"), (1, "Right")):
        arm = b.node(f"Arm_{label}_PIVOT", (side * .49, 1.68, 0), root)
        b.mesh(f"Arm_{label}", oriented_ellipsoid((0, .02, 0), (side * .36, -.68, .035), (.205, .065, .215)), white, arm)
        hand = b.node(f"Hand_{label}_PIVOT", (side * .36, -.68, .035), arm)
        b.mesh(f"Palm_{label}", ellipsoid((0, -.035, .02), (.19, .20, .205)), white, hand)
        # Four rounded fingers and a short thumb; all are individual parts for posing.
        for finger in range(4):
            spread = (finger - 1.5) * .079
            b.mesh(f"{label}_finger_{finger + 1}",
                   oriented_ellipsoid((spread, -.14, .065), (spread + side * .01, -.28, .098),
                                      (.043, .035, .051), 12, 16), white, hand)
        b.mesh(f"{label}_thumb", oriented_ellipsoid((-side * .16, -.055, .09),
                                                      (-side * .25, -.19, .16), (.069, .033, .073), 12, 16), white, hand)

        leg = b.node(f"Leg_{label}_PIVOT", (side * .245, .67, 0), root)
        b.mesh(f"Leg_{label}", ellipsoid((0, -.21, 0), (.25, .37, .245)), white, leg)
        b.mesh(f"Foot_{label}", ellipsoid((0, -.52, .125), (.27, .15, .355)), white, leg)

    path = OUT / "baymax.glb"
    b.save(path)
    return b, path


def preview(b):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    colors = [WHITE, FACE, SEAM, ACCENT]
    # Scene graph world offsets; all poses are neutral translations in this export.
    parents = {}
    for idx, node in enumerate(b.nodes):
        for child in node.get("children", []):
            parents[child] = idx

    def offset(idx):
        t = tuple(b.nodes[idx].get("translation", (0, 0, 0)))
        return add(t, offset(parents[idx])) if idx in parents else t

    width, height = 1024, 560
    canvas = Image.new("RGB", (width, height), (225, 235, 239))
    draw = ImageDraw.Draw(canvas)
    for view_idx, angle in enumerate((0, math.radians(35))):
        triangles = []
        camera = (math.sin(angle), .10, math.cos(angle))
        light = unit((-.45, .8, 1))
        for parent, vertices, indices, mat in b.parts:
            world = [add(v, offset(parent)) for v in vertices]
            projected = []
            for x, y, z in world:
                x2 = x * math.cos(angle) - z * math.sin(angle)
                depth = x * math.sin(angle) + z * math.cos(angle)
                projected.append((x2, y, depth))
            for k in range(0, len(indices), 3):
                p = [projected[indices[k + q]] for q in range(3)]
                w = [world[indices[k + q]] for q in range(3)]
                normal = unit(cross(sub(w[1], w[0]), sub(w[2], w[0])))
                if dot(normal, camera) <= 0:
                    continue
                shade = .66 + .34 * max(0, dot(normal, light))
                rgb = tuple(round(255 * min(1, c * shade)) for c in colors[mat])
                cx = 256 + view_idx * 512
                points = [(cx + v[0] * 188, 490 - v[1] * 188) for v in p]
                triangles.append((sum(v[2] for v in p) / 3, points, rgb))
        for _, points, rgb in sorted(triangles):
            draw.polygon(points, fill=rgb)
        draw.text((view_idx * 512 + 24, 20), "FRONT" if view_idx == 0 else "THREE-QUARTER", fill=(39, 58, 70))
    draw.text((24, 529), "BAYMAX  |  2.36 m  |  +Z forward  |  separate poseable parts", fill=(39, 58, 70))
    output = OUT / "preview.png"
    canvas.save(output)
    return output


if __name__ == "__main__":
    builder, model_path = build()
    preview_path = preview(builder)
    print(f"Wrote {model_path} ({model_path.stat().st_size:,} bytes)")
    if preview_path:
        print(f"Wrote {preview_path}")
