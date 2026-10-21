"""Top-down visual map for the Chromepet placement registry.

Reads ONLY data/placement_map.json (the single source of truth) and
draws: road centrelines from its road_network section, a rotated
footprint rectangle + label per asset, the origin marker, a north
arrow and a 100 m scale bar. Because the image is generated from the
JSON, it cannot drift from the registry -- regenerate it whenever the
registry changes.

Run from Chromepet/:  python3 tools/placement_map_image.py [out.png]
Default output: data/placement_map.png
Dependencies: matplotlib
"""

import json
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

COLORS = {
    "area_layer": "#b8bec4",
    "detailed_building": "#2f6db3",
    "prop": "#d98a29",
    "landmark_group": "#3d9970",
    "connector": "#8e44ad",
}


def rect_corners(asset):
    """Footprint rectangle corners in ENU, rotated by the heading.

    heading_deg is the bearing of the local +Y axis; the ENU yaw of the
    local frame is theta = -heading (CCW from east)."""
    cx, cy = asset["position_enu"]
    w, d = asset["footprint_m"]
    theta = math.radians(-asset["heading_deg"])
    corners = []
    for lx, ly in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        corners.append((cx + lx * math.cos(theta) - ly * math.sin(theta),
                        cy + lx * math.sin(theta) + ly * math.cos(theta)))
    return corners


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "placement_map.png")
    with open(os.path.join(ROOT, "data", "placement_map.json"), encoding="utf-8") as handle:
        doc = json.load(handle)

    fig, ax = plt.subplots(figsize=(13, 13))
    ax.set_facecolor("#eef2e6")

    # Campus-scope assets only (layers spanning the whole bbox are noted, not drawn).
    drawn = [a for a in doc["assets"] if max(a["footprint_m"]) < 500]

    for road in doc["road_network"]:
        pts = road["polyline_enu"]
        ax.plot([p[0] for p in pts], [p[1] for p in pts],
                color="#666666", linewidth=max(1.0, road["width_m"] * 0.55), solid_capstyle="round", zorder=1)
        mid = pts[len(pts) // 2]
        ax.annotate(road["name"], mid, fontsize=6.5, color="#444444", zorder=5,
                    xytext=(3, 3), textcoords="offset points")

    for asset in drawn:
        color = COLORS.get(asset["type"], "#333333")
        corners = rect_corners(asset)
        ax.add_patch(MplPolygon(corners, closed=True, facecolor=color, edgecolor="#222222",
                                linewidth=0.7, alpha=0.75, zorder=3))
        x, y = asset["position_enu"]
        ax.plot([x], [y], marker=".", color="#222222", markersize=3, zorder=4)
        ax.annotate(asset["id"], (x, y), fontsize=7, zorder=6,
                    xytext=(4, 4), textcoords="offset points")

    # Origin marker + spawn.
    ax.plot([0], [0], marker="+", color="#c0392b", markersize=14, markeredgewidth=2, zorder=6)
    ax.annotate("origin 12.9487N 80.1394E", (0, 0), fontsize=7, color="#c0392b",
                xytext=(5, -11), textcoords="offset points", zorder=6)
    ax.plot([-70.91], [-253.28], marker="*", color="#c0392b", markersize=13, zorder=6)
    ax.annotate("player spawn", (-70.91, -253.28), fontsize=7, color="#c0392b",
                xytext=(5, 4), textcoords="offset points", zorder=6)

    xs = [a["position_enu"][0] for a in drawn] + [p[0] for r in doc["road_network"] for p in r["polyline_enu"]]
    ys = [a["position_enu"][1] for a in drawn] + [p[1] for r in doc["road_network"] for p in r["polyline_enu"]]
    x0, x1 = min(xs) - 45, max(xs) + 55
    y0, y1 = min(ys) - 40, max(ys) + 40
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xlabel("east (m from origin)")
    ax.set_ylabel("north (m from origin)")
    ax.set_title("Chromepet / MIT campus -- placement map (from data/placement_map.json, v1, 2026-10-21)")
    ax.grid(True, color="#cccccc", linewidth=0.4, zorder=0)

    # North arrow + scale bar (axes fraction anchors).
    ax.annotate("N", xy=(0.965, 0.93), xytext=(0.965, 0.865), xycoords="axes fraction",
                fontsize=13, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", lw=1.8))
    bar_x = x0 + 25
    ax.plot([bar_x, bar_x + 100], [y0 + 18, y0 + 18], color="#222222", linewidth=3, zorder=7)
    ax.annotate("100 m", (bar_x + 50, y0 + 18), fontsize=8, ha="center",
                xytext=(0, 5), textcoords="offset points", zorder=7)

    handles = [plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=c, markersize=9, label=t)
               for t, c in COLORS.items()]
    ax.legend(handles=handles, loc="lower right", fontsize=8, title="asset type")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"wrote {out_path} with {len(drawn)} assets and {len(doc['road_network'])} roads")


if __name__ == "__main__":
    main()
