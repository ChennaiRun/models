"""MIT Chromepet detailed procedural model (v2).
Builds per-area GLBs with PBR materials from OSM + video-reference notes (see ../REFERENCE_VIDEOS.md).
Usage (from Chromepet/):  python3 tools/mit_details.py
Coordinates: built in ENU metres (x=east, y=north, z=up), origin 12.9487N 80.1394E, then exported to glTF
convention (+Y up, right-handed): glTF (x, y, z) = (east, up, -north). Blender's glTF importer maps that back
to (east, north, up); Unity glTF importers convert handedness without mirroring the map.
Heights: ~3.5 m per storey. Everything not in OSM is APPROXIMATE (placed from video notes, not surveyed)."""
import math, json, random, os, xml.etree.ElementTree as ET
import numpy as np, trimesh
from shapely.geometry import Polygon, LineString, Point, MultiPolygon, box as sbox
from shapely.ops import unary_union, nearest_points
from shapely import affinity
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
LAT0, LON0, RE = 12.9487, 80.1394, 6378137.0
def P(la, lo): return ((lo-LON0)*math.radians(1)*RE*math.cos(math.radians(LAT0)), (la-LAT0)*math.radians(1)*RE)
SH = 3.5  # storey height
rng = random.Random(42)

# ---------------------------------------------------------------- OSM
root = ET.parse(os.path.join(ROOT, 'data', 'osm_raw.osm')).getroot()
NODES = {n.get('id'): P(float(n.get('lat')), float(n.get('lon'))) for n in root.iter('node')}
def tags(e): return {t.get('k'): t.get('v') for t in e.findall('tag')}
NTAGS = {n.get('id'): tags(n) for n in root.iter('node') if n.find('tag') is not None}
WAYS = []
for w in root.iter('way'):
    pts = [NODES[x.get('ref')] for x in w.findall('nd') if x.get('ref') in NODES]
    if len(pts) >= 2: WAYS.append((w.get('id'), tags(w), pts, [x.get('ref') for x in w.findall('nd')]))
BBOX = sbox(-1300, -1450, 1300, 1350)  # local extent of the OSM bbox (approx)

# ---------------------------------------------------------------- mesh collector
C = dict(  # palette (sRGB 0-1)
 grass=(0.33,0.47,0.22), wood_floor=(0.26,0.36,0.17), outside_ground=(0.55,0.52,0.42), asphalt=(0.17,0.17,0.18),
 asphalt_light=(0.30,0.30,0.31), median=(0.75,0.74,0.70), tile_red=(0.62,0.22,0.18), tile_black=(0.16,0.15,0.15),
 tactile=(0.95,0.80,0.10), white=(0.93,0.93,0.90), grey=(0.62,0.62,0.62), dark_grey=(0.30,0.30,0.32),
 glass_blue=(0.20,0.42,0.68), gold=(0.85,0.65,0.20), pale_yg=(0.84,0.86,0.58), light_green=(0.66,0.82,0.62),
 red=(0.75,0.12,0.10), yellow=(0.95,0.78,0.15), orange_brick=(0.78,0.38,0.20), brown=(0.42,0.27,0.15),
 pale_yellow=(0.94,0.89,0.62), concrete=(0.70,0.70,0.68), rust=(0.55,0.28,0.15), roof_grey=(0.50,0.52,0.54),
 brick=(0.65,0.25,0.18), green_win=(0.40,0.62,0.40), atm_green=(0.20,0.55,0.25), atm_blue=(0.15,0.30,0.70),
 black=(0.06,0.06,0.06), pink=(0.88,0.58,0.70), purple=(0.58,0.42,0.68), blue_band=(0.25,0.40,0.75),
 hostel_green=(0.55,0.75,0.50), beige=(0.88,0.80,0.66), silver=(0.80,0.82,0.85), water=(0.15,0.45,0.75),
 trunk=(0.38,0.27,0.17), canopy=(0.20,0.40,0.14), canopy2=(0.27,0.47,0.17), coconut_leaf=(0.35,0.55,0.18),
 navy=(0.18,0.30,0.60), camo=(0.42,0.46,0.35), steel=(0.55,0.56,0.58), ballast=(0.45,0.42,0.38),
 green_bridge=(0.20,0.55,0.30), billboard=(0.90,0.90,0.90), stripe_blue=(0.20,0.35,0.75), pole=(0.55,0.55,0.55),
 wire=(0.08,0.08,0.08), shelter_blue=(0.20,0.40,0.70), maroon=(0.48,0.18,0.16),
 prod_cream=(0.93,0.87,0.74), prod_mustard=(0.78,0.58,0.16), prod_blue=(0.10,0.25,0.55))
PASTELS = [(0.95,0.85,0.70),(0.80,0.90,0.95),(0.95,0.80,0.85),(0.85,0.95,0.80),(0.98,0.95,0.75),(0.90,0.85,0.95),(0.96,0.90,0.85),(0.85,0.92,0.88),(0.93,0.93,0.93)]

class Layer:
    def __init__(s): s.parts = {}; s.named = []; s.textured = []; s.nodes = []
    def add(s, mesh, col, name=None):
        if mesh is None or len(mesh.faces) == 0: return
        key = col if isinstance(col, tuple) else C[col]
        if name: s.named.append((name, mesh, key))
        else: s.parts.setdefault(key, []).append(mesh)
    def export(s, path):
        sc = trimesh.Scene()
        def mat(c, n): return trimesh.visual.material.PBRMaterial(name=n, baseColorFactor=[*(int(v*255) for v in c), 255], metallicFactor=0.0, roughnessFactor=0.85)
        M = np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]], float)  # ENU -> glTF
        for i, (c, ms) in enumerate(s.parts.items()):
            m = trimesh.util.concatenate(ms); m.visual = trimesh.visual.TextureVisuals(material=mat(c, f'mat_{i}'))
            m.apply_transform(M); sc.add_geometry(m, geom_name=f'part_{i}', node_name=f'part_{i}')
        groups = {}
        for n, m, c in s.named: groups.setdefault(n, []).append((m, c))
        for n, lst in groups.items():
            for j, (m, c) in enumerate(lst):
                m = m.copy(); m.visual = trimesh.visual.TextureVisuals(material=mat(c, f'{n}_m{j}')); m.apply_transform(M)
                sc.add_geometry(m, geom_name=f'{n}__{j}', node_name=f'{n}__{j}')
        for n, m in s.textured:
            m = m.copy(); m.apply_transform(M); sc.add_geometry(m, geom_name=n, node_name=n)
        for n, (x, y, z) in s.nodes:  # empty marker nodes (spawn etc.) -> tiny invisible-ish geometry
            mk = trimesh.creation.box(extents=[0.01,0.01,0.01]); mk.apply_translation([x, y, z]); mk.apply_transform(M)
            mk.visual = trimesh.visual.TextureVisuals(material=mat((1,0,0), n)); sc.add_geometry(mk, geom_name=n, node_name=n)
        sc.export(path); return path

# ---------------------------------------------------------------- primitives (ENU, z up)
def obox(cx, cy, l, w, h, yaw=0.0, z0=0.0):
    m = trimesh.creation.box(extents=[l, w, h]); m.apply_translation([0, 0, h/2 + z0])
    m.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0,0,1])); m.apply_translation([cx, cy, 0]); return m
def extrude(poly, h, z0=0.0):
    out = []
    for g in getattr(poly, 'geoms', [poly]):
        if g.area < 0.5: continue
        try: m = trimesh.creation.extrude_polygon(g, h); m.apply_translation([0,0,z0]); out.append(m)
        except Exception: pass
    return trimesh.util.concatenate(out) if out else None
def cyl(x, y, r, h, z0=0.0, sec=12):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sec); m.apply_translation([x, y, z0+h/2]); return m
def sphere(x, y, z, r, sub=1):
    m = trimesh.creation.icosphere(subdivisions=sub, radius=r); m.apply_translation([x, y, z]); return m
def cone(x, y, r, h, z0=0.0, sec=10):
    m = trimesh.creation.cone(radius=r, height=h, sections=sec); m.apply_translation([x, y, z0]); return m
def beam(p0, p1, w, h, z0=0.0):  # box between two 2D points
    (x0, y0), (x1, y1) = p0, p1; L = math.hypot(x1-x0, y1-y0)
    return obox((x0+x1)/2, (y0+y1)/2, L, w, h, math.atan2(y1-y0, x1-x0), z0) if L > 0.01 else None
def obb(poly):
    r = poly.minimum_rotated_rectangle; xy = np.array(r.exterior.coords)[:4]
    e1, e2 = xy[1]-xy[0], xy[2]-xy[1]
    if np.linalg.norm(e1) < np.linalg.norm(e2): e1, e2 = e2, e1
    c = xy.mean(0); return c, np.linalg.norm(e1), np.linalg.norm(e2), math.atan2(e1[1], e1[0])
def ribbon(line, width, z=0.0, th=0.08):
    return extrude(line.buffer(width/2, cap_style=2, join_style=2), th, z)
def text_quad(text, w, h, fg, bg, px=1024):
    img = Image.new('RGB', (px, max(16, int(px*h/w))), tuple(int(v*255) for v in bg)); d = ImageDraw.Draw(img)
    fs = int(img.height*0.6)
    try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', fs)
    except Exception: f = ImageFont.load_default()
    while d.textlength(text, font=f) > img.width*0.94 and fs > 8:
        fs -= 2
        try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', fs)
        except Exception: break
    tw = d.textlength(text, font=f); d.text(((img.width-tw)/2, (img.height-fs)/2 - fs*0.1), text, font=f, fill=tuple(int(v*255) for v in fg))
    v = np.array([[-w/2,0,0],[w/2,0,0],[w/2,0,h],[-w/2,0,h]], float); f_ = np.array([[0,2,1],[0,3,2],[0,1,2],[0,2,3]])
    uv = np.array([[0,0],[1,0],[1,1],[0,1]], float)
    m = trimesh.Trimesh(v, f_, process=False)
    m.visual = trimesh.visual.TextureVisuals(uv=uv, material=trimesh.visual.material.PBRMaterial(baseColorTexture=img, metallicFactor=0, roughnessFactor=0.8))
    return m
def place(m, x, y, z, yaw):
    m.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0,0,1])); m.apply_translation([x, y, z]); return m

# ---------------------------------------------------------------- key OSM features
def node(i): return np.array(NODES[i])
MAIN_GATE = node('432468247')     # OSM "MIT South Gaate" = main gate on MIT Road, right after MIT Flyover (GST side)
NORTH_GATE = node('249211141'); HOSTEL_GATE = node('432468204'); TANK = node('566538797'); RAJAM_STATUE = node('582775241')
BACK_GATE = node('593999547')
mit_road = [p for i, t, p, r in WAYS if t.get('name') == 'MIT Road']
avenue = unary_union([LineString(p) for p in mit_road])
avenue = avenue if avenue.geom_type == 'LineString' else max(getattr(avenue, 'geoms', [avenue]), key=lambda g: g.length)
from shapely.ops import linemerge
avenue = linemerge(unary_union([LineString(p) for p in mit_road]))
if avenue.geom_type != 'LineString': avenue = max(avenue.geoms, key=lambda g: g.length)
# orient avenue to start at main gate
if Point(avenue.coords[0]).distance(Point(MAIN_GATE)) > Point(avenue.coords[-1]).distance(Point(MAIN_GATE)):
    avenue = LineString(list(avenue.coords)[::-1])
d0 = avenue.project(Point(MAIN_GATE)); a1 = np.array(avenue.interpolate(d0+1).coords[0]); a0 = np.array(avenue.interpolate(d0).coords[0])
GATE_DIR = (a1-a0)/np.linalg.norm(a1-a0); GATE_YAW = math.atan2(GATE_DIR[1], GATE_DIR[0])
SPAWN = np.array(avenue.interpolate(d0+12).coords[0])  # 12 m inside the main gate, on the avenue centreline
rails = [LineString(p) for i, t, p, r in WAYS if t.get('railway') == 'rail']
rail_local = unary_union([g.intersection(BBOX) for g in rails])
CAMPUS_NAMED = {k: node(k) for k in ['432468191','432468195','432468196','432468198','432468199','432468200','432468201','432468205','432468225','432468226','432468246','5964208543']}
named_pts = [Point(*v) for v in CAMPUS_NAMED.values()] + [Point(*TANK), Point(*HOSTEL_GATE), Point(*NORTH_GATE), Point(*RAJAM_STATUE)]
campus = unary_union([avenue.buffer(110), unary_union(named_pts).convex_hull.buffer(45), Point(*HOSTEL_GATE).buffer(90)])
campus = campus.difference(rail_local.buffer(18)).buffer(-5).buffer(5)
if campus.geom_type == 'MultiPolygon': campus = max(campus.geoms, key=lambda g: g.area)

# ---------------------------------------------------------------- buildings
BUILD, OUTB, LAND, GROUND, ROADS, TREES = Layer(), Layer(), Layer(), Layer(), Layer(), Layer()
foot = []
for wid, t, pts, refs in WAYS:
    if 'building' in t and len(pts) >= 4:
        p = Polygon(pts).buffer(0)
        if p.is_valid and p.area > 6: foot.append((wid, t, p))
campus_fp = [(w, t, p) for w, t, p in foot if campus.contains(p.representative_point())]
outside_fp = [(w, t, p) for w, t, p in foot if not campus.contains(p.representative_point())]

NAME_STYLE = [  # keyword in OSM name -> style ('RLHC' must precede 'Lecture Hall Complex': the RLHC
 # name contains both, and photos 52/53.jpg show it white, unlike the pale-green LHC of photo 31.jpg)
 ('Admin', 'admin'), ('RLHC', 'rlhc'), ('Lecture Hall Complex', 'lhc'), ('Aeronautical', 'aero'), ('Rajam Hall', 'rajam'),
 ('Electonics', 'green3'), ('Electronics', 'green3'), ('Instrumentation', 'green3'), ('Mechatronics', 'green3'),
 ('Production', 'prodtech'), ('Automobile', 'auto'), ('DCOE', 'green3'), ('Golden Jub', 'library'), ('KBC', 'cs'),
 ('Micsat', 'white2'), ('Hostel', 'hostel'), ('Alumini', 'white2'), ('Birla', 'hostel')]
def facing(c):  # yaw pointing from building centre toward the avenue
    q = nearest_points(avenue, Point(*c))[0]; return math.atan2(q.y-c[1], q.x-c[0])

def facade_bands(c, L, W, yaw, floors, col, z_every=SH, depth=0.25, th=0.3, front_only=False):
    out = []
    for k in range(1, floors):  # floor bands (not at roof level, avoids coplanar roof faces)
        out.append(obox(c[0], c[1], L+depth*2, W+depth*2, th, yaw, k*z_every-th/2))
    out.append(obox(c[0], c[1], L+depth*2, W+depth*2, 0.5, yaw, floors*z_every-0.6))  # roof coping band, top 10 cm below roof
    return trimesh.util.concatenate(out)

def portico(c, L, W, yaw, face, h, col_p, col_s, n=4, depth=6.0, width=None):
    """columns + slab on the side facing the avenue"""
    width = width or min(L, 18); fx, fy = math.cos(face), math.sin(face)
    # distance from centre to facade along face direction (approx using obb dims)
    rel = (face - yaw) % math.pi; half = abs(math.cos(rel))*L/2 + abs(math.sin(rel))*W/2
    bx, by = c[0]+fx*(half+depth/2), c[1]+fy*(half+depth/2); px, py = -fy, fx
    cols = [cyl(bx+fx*depth/2*0.7+px*s, by+fy*depth/2*0.7+py*s, 0.35, h) for s in np.linspace(-width/2, width/2, n)]
    slab = obox(bx, by, depth, width+1.5, 0.6, face, h)
    return trimesh.util.concatenate(cols), slab, (bx+fx*depth, by+fy*depth), (px, py)

assigned = {}
for key, pt in CAMPUS_NAMED.items():
    name = NTAGS[key]['name']; best = None
    for w, t, p in campus_fp:
        d = p.distance(Point(*pt))
        if d < 25 and (best is None or d < best[0]) and w not in assigned: best = (d, w)
    style = next((s for kw, s in NAME_STYLE if kw in name), 'green3')
    if best: assigned[best[1]] = (name, style)
    else: assigned['node_'+key] = (name, style)  # no footprint -> procedural box at node
for w, t, p in campus_fp:
    n = t.get('name', '')
    if w not in assigned and n:
        s = next((s for kw, s in NAME_STYLE if kw in n), None)
        if s: assigned[w] = (n, s)
# heuristic placement for blocks described in videos but not tagged in OSM (APPROXIMATE)
unn = sorted([(p, w) for w, t, p in campus_fp if w not in assigned], key=lambda q: -q[0].area)
def take(pred, name, style):
    for i, (p, w) in enumerate(unn):
        if pred(p): assigned[w] = (name, style); unn.pop(i); return True
    return False
rail_d = lambda p: p.distance(rail_local)
c_, L_, W_, _ = (None,)*4
take(lambda p: obb(p)[1] > 3.5*obb(p)[2] and obb(p)[1] > 50, 'Central Workshop (approx)', 'workshop')
take(lambda p: rail_d(p) < 90 and p.area > 900, 'Hangar I (approx)', 'hangar1')
take(lambda p: p.area > 700, 'Hangar II / Exam Hall (approx)', 'hangar2')
for nm, st in [('Computer Technology (approx)', 'cs'), ('Rubber & Plastics Technology (approx)', 'rpt'), ('Library (approx)', 'library'),
               ('Applied Sciences (approx)', 'applied'), ('Charles Babbage Block (approx)', 'babbage'), ('Information Technology (approx)', 'green3'),
               ('Electronics & Instrumentation (approx)', 'green3')]:
    take(lambda p: p.area > 300, nm, st)
take(lambda p: p.area < 60, 'Indian Bank ATM (approx)', 'atm')

def style_building(name, style, poly, seed):
    lay = BUILD; tag = ''.join(ch if ch.isalnum() else '_' for ch in name)[:40]
    c, L, W, yaw = obb(poly); face = facing(c)
    def body(h, col): lay.add(extrude(poly, h), col, tag)
    if style == 'admin':
        h = 4*SH; body(h, 'glass_blue'); lay.add(facade_bands(c, L, W, yaw, 4, 'white'), 'white', tag)
        for s in np.linspace(-L/2, L/2, max(3, int(L/6))):  # white vertical frame fins
            lay.add(obox(c[0]+math.cos(yaw)*s, c[1]+math.sin(yaw)*s, 0.4, W+0.6, h, yaw), 'white', tag)
        cols, slab, front, perp = portico(c, L, W, yaw, face, 2*SH, 'grey', 'white', n=6, depth=7)
        lay.add(cols, 'grey', tag); lay.add(slab, 'white', tag)
        LAND.add(obox(front[0], front[1], 2.2, 2.2, 1.6, face), 'dark_grey', 'Kalam_statue')   # plinth
        LAND.add(cyl(front[0], front[1], 0.45, 1.8, 1.6), 'gold', 'Kalam_statue'); LAND.add(sphere(front[0], front[1], 3.65, 0.3), 'gold', 'Kalam_statue')
    elif style == 'lhc':
        f = 4 if seed % 2 else 3; h = f*SH; body(h, 'pale_yg'); lay.add(facade_bands(c, L, W, yaw, f, 'concrete', depth=0.7, th=0.15), 'concrete', tag)
        cols, slab, *_ = portico(c, L, W, yaw, face, SH, 'concrete', 'concrete', n=4, depth=5); lay.add(cols, 'concrete', tag); lay.add(slab, 'concrete', tag)
    elif style == 'green3':
        f = 2 + seed % 2; body(f*SH, 'light_green'); lay.add(facade_bands(c, L, W, yaw, f, 'white', th=0.25), 'white', tag)
    elif style == 'aero':
        h = 2*SH; body(h, 'maroon'); lay.add(facade_bands(c, L, W, yaw, 2, 'beige', th=0.6, depth=0.15), 'beige', tag)
        cols, slab, front, perp = portico(c, L, W, yaw, face, SH*1.2, 'beige', 'maroon', n=4, depth=5); lay.add(cols, 'beige', tag); lay.add(slab, 'maroon', tag)
        ex, ey = front[0]+math.cos(face)*4, front[1]+math.sin(face)*4   # Rolls-Royce Pegasus engine on yellow stand
        LAND.add(obox(ex, ey, 3.2, 1.6, 0.9, face+math.pi/2), 'yellow', 'Pegasus_engine')
        eng = trimesh.creation.cylinder(radius=0.62, height=3.4, sections=16); eng.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0,1,0]))
        LAND.add(place(eng, ex, ey, 1.55, face+math.pi/2), 'steel', 'Pegasus_engine')
    elif style == 'rajam':
        h = 2*SH; body(h, 'white'); w2 = min(L, 10)
        lay.add(obox(c[0]+math.cos(face)*(W/2+0.1), c[1]+math.sin(face)*(W/2+0.1), 0.4, w2, h+1.5, face), 'orange_brick', tag)
    elif style == 'cs':
        f = 4; h = f*SH; body(h, 'white'); lay.add(extrude(poly.buffer(0.3), 1.0), 'brown', tag)
        cols, slab, front, perp = portico(c, L, W, yaw, face, h-1, 'white', 'white', n=6, depth=4); lay.add(cols, 'white', tag); lay.add(slab, 'white', tag)
        lay.add(obox(c[0]+math.cos(face)*(W/2+0.2), c[1]+math.sin(face)*(W/2+0.2), 0.3, 6, 2*SH, face), 'glass_blue', tag)
        rx, ry = front; lay.add(obox(rx, ry, 8, 1.6, 0.5, face+math.pi/2), 'concrete', tag)   # ramp (simplified)
    elif style == 'babbage': body(3*SH, 'pale_yellow'); lay.add(facade_bands(c, L, W, yaw, 3, 'white'), 'white', tag)
    elif style == 'applied':
        h = 3*SH; body(h, 'concrete')
        for s in np.linspace(-L/2, L/2, max(4, int(L/2.5))): lay.add(obox(c[0]+math.cos(yaw)*s, c[1]+math.sin(yaw)*s, 0.35, W+1.0, h, yaw), 'white', tag)
        lay.add(facade_bands(c, L, W, yaw, 3, 'white', depth=0.5), 'white', tag)
        bx, by = c[0]+math.cos(face)*(W/2+8), c[1]+math.sin(face)*(W/2+8)   # pink circular bench with conical roof
        ring = trimesh.creation.annulus(r_min=2.2, r_max=3.0, height=0.45, sections=24); ring.apply_translation([bx, by, 0.225]); LAND.add(ring, 'pink', 'Pink_bench')
        LAND.add(cyl(bx, by, 0.2, 3.0), 'pink', 'Pink_bench'); LAND.add(cone(bx, by, 3.4, 1.4, 3.0), 'pink', 'Pink_bench')
    elif style == 'workshop': body(7.0, 'white'); lay.add(extrude(poly.buffer(0.15), 1.2, 5.0), 'yellow', tag)
    elif style == 'hangar1':
        h = 9.0; body(h, 'rust'); rx = trimesh.creation.extrude_polygon(Polygon([(-W/2-0.5, 0), (W/2+0.5, 0), (0, 4.5)]), L+1)
        rx.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0,1,0])); rx.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [1,0,0]))
        rx.apply_translation([-(L+1)/2, 0, 0]); lay.add(place(rx, c[0], c[1], h, yaw), 'roof_grey', tag)
    elif style == 'hangar2':
        h = 6.0; body(h, 'white'); vault = trimesh.creation.cylinder(radius=W/2+0.4, height=L+0.5, sections=24)
        vault.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0,1,0]))
        vault = vault.slice_plane([0,0,0], [0,0,1], cap=True); lay.add(place(vault, c[0], c[1], h, yaw), 'roof_grey', tag)
    elif style == 'rpt':
        body(3*SH, 'white'); fx, fy = math.cos(face), math.sin(face); px, py = -fy, fx; bx, by = c[0]+fx*(W/2+4), c[1]+fy*(W/2+4)
        for s in np.linspace(-6, 6, 5):
            for d in (-2.5, 2.5): lay.add(obox(bx+px*s+fx*d, by+py*s+fy*d, 0.6, 0.6, 3.0), 'brick', tag)
        for s in np.linspace(-6, 6, 9): lay.add(obox(bx+px*s, by+py*s, 0.25, 6.0, 0.3, face, 3.0), 'brick', tag)
    elif style == 'auto':
        f = 2 + seed % 2; body(f*SH, 'white'); lay.add(facade_bands(c, L, W, yaw, f, 'light_green', th=0.8, depth=0.1), 'light_green', tag)
        lay.add(facade_bands(c, L, W, yaw, f, 'yellow', z_every=SH, th=0.15, depth=0.2), 'yellow', tag)
    elif style == 'prodtech':
        # Photos 14/45.jpg: cream walls, mustard lower band, blue department sign band.
        f = 2 + seed % 2; body(f*SH, 'prod_cream'); lay.add(facade_bands(c, L, W, yaw, f, 'prod_mustard', th=0.8, depth=0.1), 'prod_mustard', tag)
        lay.add(facade_bands(c, L, W, yaw, f, 'prod_blue', z_every=SH, th=0.15, depth=0.2), 'prod_blue', tag)
    elif style == 'rlhc':
        # Photos 52/53.jpg (Rajam Lecture Hall Complex): white block, round-column portico, red doors.
        f = 3; h = f*SH; body(h, 'white'); lay.add(facade_bands(c, L, W, yaw, f, 'concrete', depth=0.7, th=0.15), 'concrete', tag)
        cols, slab, *_ = portico(c, L, W, yaw, face, SH, 'concrete', 'concrete', n=5, depth=5); lay.add(cols, 'concrete', tag); lay.add(slab, 'concrete', tag)
        lay.add(obox(c[0]+math.cos(face)*(W/2+0.2), c[1]+math.sin(face)*(W/2+0.2), 0.3, 4.5, 2.4, face), 'red', tag)
    elif style == 'library': body(3*SH, 'white'); lay.add(facade_bands(c, L, W, yaw, 3, 'grey', th=0.2), 'grey', tag)
    elif style == 'atm': body(3.2, 'atm_green'); lay.add(obox(c[0]+math.cos(face)*(W/2+0.05), c[1]+math.sin(face)*(W/2+0.05), 0.2, max(2, L*0.8), 2.6, face), 'atm_blue', tag)
    elif style == 'hostel':
        pal = [('pink', 'purple'), ('pale_yellow', 'blue_band'), ('hostel_green', 'pink')][seed % 3]; f = 4 + seed % 2
        body(f*SH, pal[0]); lay.add(facade_bands(c, L, W, yaw, f, pal[1], th=0.6, depth=0.12), pal[1], tag)
    elif style == 'store': body(SH, 'pink'); lay.add(extrude(poly.buffer(0.1), 1.2), 'green_win', tag)
    else:
        f = 2 + seed % 2; body(f*SH, ['light_green', 'white', 'pale_yellow'][seed % 3])

hostel_zone = Point(*HOSTEL_GATE).buffer(110)
for w, t, p in campus_fp:
    if w in assigned: nm, st = assigned[w]
    elif hostel_zone.contains(p.representative_point()) and p.area > 250 and Point(*HOSTEL_GATE).distance(Point(*SPAWN)) < p.representative_point().distance(Point(*SPAWN)): nm, st = 'Hostel block', 'hostel'
    elif hostel_zone.contains(p.representative_point()) and p.area < 250: nm, st = 'Hostel store', 'store'
    else: nm, st = 'Campus block', 'generic'
    style_building(nm + ('' if nm in ('Campus block', 'Hostel block', 'Hostel store') else ''), st, p, int(w) % 97)
for k, (nm, st) in list(assigned.items()):
    if k.startswith('node_'):
        x, y = NODES[k[5:]]; style_building(nm, st, sbox(x-14, y-9, x+14, y+9), int(k[5:]) % 97)
log_assign = {v[0]: v[1] for v in assigned.values()}

# outside buildings: 2-6 storeys pastel; 1-3 storeys near station / Radha Nagar market streets
STATION = np.array(NODES[next(k for k, t in NTAGS.items() if t.get('railway') == 'station' and t.get('name') == 'Chromepet')])
for w, t, p in outside_fp:
    s = int(w); r_ = random.Random(s); cpt = p.representative_point()
    near_market = cpt.distance(Point(*STATION)) < 300
    if 'building:levels' in t:
        try: f = max(1, int(float(t['building:levels'])))
        except Exception: f = 2
    elif near_market: f = r_.choice([1, 2, 2, 3])
    else: f = r_.choice([2, 2, 3, 3, 4, 5, 6]) if p.area > 120 else r_.choice([1, 2, 2, 3])
    col = PASTELS[s % len(PASTELS)]; OUTB.add(extrude(p, f*SH), col)
    OUTB.add(extrude(p.exterior.buffer(0.25).intersection(p.buffer(0.25)), 0.9, f*SH), 'white')  # parapet
    if near_market and p.area > 30:  # shop awning / signboard on the ground floor
        c, L, W, yaw = obb(p); OUTB.add(obox(c[0], c[1], L+0.8, W+0.8, 0.6, yaw, 3.0), PASTELS[(s+3) % len(PASTELS)])

# ---------------------------------------------------------------- roads & surroundings
gst_lines, flyover, ramps, other = [], [], [], []
WIDTH = {'trunk': 11.0, 'trunk_link': 7.0, 'primary': 10, 'secondary': 9, 'tertiary': 7.5, 'residential': 6, 'living_street': 5,
         'unclassified': 6, 'service': 4, 'footway': 2, 'path': 1.8, 'pedestrian': 4, 'steps': 2, 'cycleway': 2, 'track': 3}
road_union = []
for wid, t, pts, refs in WAYS:
    hw = t.get('highway')
    if not hw or hw not in WIDTH: continue
    ln = LineString(pts).intersection(BBOX)
    if ln.is_empty: continue
    if t.get('name') == 'MIT Road': continue  # built as campus avenue
    if t.get('bridge') == 'yes' and hw != 'footway': flyover.append((ln, WIDTH[hw] if hw != 'tertiary' else 8.5)); continue
    if t.get('bridge') == 'yes' and hw == 'footway': continue
    if t.get('layer') == '-1': continue  # Radha Nagar subway handled separately
    if hw == 'trunk': gst_lines.append(ln)
    w = WIDTH[hw]; road_union.append(ln.buffer(w/2, cap_style=2, join_style=2))
roads_poly = unary_union(road_union)
ROADS.add(extrude(roads_poly, 0.08, 0.0), 'asphalt')
for g in gst_lines:  # GST Road: OSM maps each carriageway (3 lanes each side -> 6 lanes) + concrete median
    ROADS.add(ribbon(g, 0.8, 0.08, 0.35), 'median')
# MIT Flyover: elevated 4-lane deck on tall pillars with blue/white striped parapet walls
FLY_Z = 7.5
for ln, w in flyover:
    for g in getattr(ln, 'geoms', [ln]):
        ROADS.add(ribbon(g, w, FLY_Z, 0.9), 'asphalt_light', 'MIT_Flyover')
        for side in (-1, 1):
            par = g.parallel_offset(w/2, 'left' if side > 0 else 'right')
            for pg in getattr(par, 'geoms', [par]):
                if pg.length < 1: continue
                ROADS.add(ribbon(pg, 0.3, FLY_Z+0.9, 0.55), 'white', 'MIT_Flyover'); ROADS.add(ribbon(pg, 0.32, FLY_Z+1.45, 0.4), 'stripe_blue', 'MIT_Flyover')
        for d in np.arange(10, g.length, 25):
            q = g.interpolate(d); ROADS.add(obox(q.x, q.y, 1.6, 1.6, FLY_Z), 'concrete', 'MIT_Flyover')
# Radha Nagar subway: 2-lane underpass below railway, retaining walls, 3.0 m height bar
for wid, t, pts, refs in WAYS:
    if 'Radha Nagar' in t.get('name', '') and t.get('layer') == '-1':
        ln = LineString(pts); ROADS.add(ribbon(ln, 7.5, -4.0, 0.1), 'asphalt', 'Radha_Nagar_Subway')
        for side in ('left', 'right'):
            pg = ln.parallel_offset(4.0, side)
            for g in getattr(pg, 'geoms', [pg]):
                if g.length > 1: ROADS.add(ribbon(g, 0.5, -4.0, 5.0), 'concrete', 'Radha_Nagar_Subway')
        a, b = np.array(pts[0]), np.array(pts[-1]); dvec = (b-a)/max(1e-6, np.linalg.norm(b-a)); yaw = math.atan2(dvec[1], dvec[0])
        for e in (a, b):  # height bars at both ends, 3.0 m clearance above road (road at -4 m)
            ROADS.add(obox(e[0], e[1], 0.3, 8.5, 0.35, yaw, -4.0+3.0), 'yellow', 'Subway_height_bar')
            for s in (-4.2, 4.2): ROADS.add(obox(e[0]-dvec[1]*s, e[1]+dvec[0]*s, 0.3, 0.3, 3.4, yaw, -4.0), 'yellow', 'Subway_height_bar')
# railway: ballast bed, rails, OHE masts + contact wire; station platforms + roofs
for g in getattr(rail_local, 'geoms', [rail_local]):
    if g.length < 2: continue
    ROADS.add(ribbon(g, 3.2, 0.0, 0.35), 'ballast', 'Railway')
    for s in (-0.76, 0.76):
        rg = g.parallel_offset(abs(s), 'left' if s > 0 else 'right')
        for q in getattr(rg, 'geoms', [rg]):
            if q.length > 1: ROADS.add(ribbon(q, 0.08, 0.35, 0.16), 'steel', 'Railway')
    for d in np.arange(0, g.length, 50):
        q = g.interpolate(d); ROADS.add(obox(q.x+3.0, q.y, 0.3, 0.3, 7.0), 'steel', 'Railway_OHE')
    ROADS.add(ribbon(g, 0.04, 5.6, 0.04), 'wire', 'Railway_OHE')
# Chromepet station platforms near the station node
near_rail = [g for g in getattr(rail_local, 'geoms', [rail_local]) if g.distance(Point(*STATION)) < 60]
if near_rail:
    allr = unary_union(near_rail); d = None
    ref = max(near_rail, key=lambda g: g.length); dc = ref.project(Point(*STATION))
    seg = LineString([ref.interpolate(max(0, dc-160)), ref.interpolate(dc), ref.interpolate(dc+160)])
    for off in (12.0, -12.0):
        pg = seg.parallel_offset(abs(off), 'left' if off > 0 else 'right')
        for g in getattr(pg, 'geoms', [pg]):
            ROADS.add(ribbon(g, 7.0, 0, 0.95), 'concrete', 'Chromepet_station')
            for dd in np.arange(5, g.length, 12):
                q = g.interpolate(dd); ROADS.add(obox(q.x, q.y, 0.3, 0.3, 4.2, 0, 0.95), 'steel', 'Chromepet_station')
            ROADS.add(ribbon(g, 7.5, 5.1, 0.2), 'roof_grey', 'Chromepet_station')
# pedestrian overbridge (OSM bridge footway at the station) - green/white covered
for wid, t, pts, refs in WAYS:
    if t.get('bridge') == 'yes' and t.get('highway') == 'footway' and Point(pts[0]).distance(Point(*STATION)) < 150:
        ln = LineString(pts); ROADS.add(ribbon(ln, 3.0, 6.5, 0.3), 'white', 'Overbridge')
        for side in ('left', 'right'):
            pg = ln.parallel_offset(1.5, side)
            for g in getattr(pg, 'geoms', [pg]):
                if g.length > 1: ROADS.add(ribbon(g, 0.12, 6.8, 1.1), 'green_bridge', 'Overbridge')
        ROADS.add(ribbon(ln, 3.6, 9.4, 0.15), 'green_bridge', 'Overbridge')
        for q in [ln.interpolate(d) for d in np.arange(0, ln.length+0.1, 8)]:
            for s in (-1.6, 1.6): ROADS.add(obox(q.x+s*0.7, q.y+s*0.7, 0.25, 0.25, 9.4), 'white', 'Overbridge')
        for e in (pts[0], pts[-1]): ROADS.add(obox(e[0], e[1], 8, 2.4, 0.3, 0, 3.2), 'concrete', 'Overbridge')  # landing (stairs simplified)
# utility poles + wires along residential streets, bus shelters + billboards along GST Road
for wid, t, pts, refs in WAYS:
    if t.get('highway') in ('residential', 'tertiary') and not campus.intersects(LineString(pts)):
        ln = LineString(pts).intersection(BBOX)
        for g in getattr(ln, 'geoms', [ln]):
            if g.is_empty or g.length < 40: continue
            off = g.parallel_offset(3.6, 'left')
            if off.is_empty or off.geom_type != 'LineString': continue
            prev = None
            for d in np.arange(0, off.length, 35):
                q = off.interpolate(d); ROADS.add(cyl(q.x, q.y, 0.13, 8.0, 0, 6), 'pole')
                if prev is not None: ROADS.add(beam(prev, (q.x, q.y), 0.04, 0.04, 7.6), 'wire')
                prev = (q.x, q.y)
for g in gst_lines:
    for gg in getattr(g, 'geoms', [g]):
        for d in np.arange(60, gg.length, 260):
            q = gg.interpolate(d); q2 = gg.interpolate(min(gg.length, d+1)); yaw = math.atan2(q2.y-q.y, q2.x-q.x)
            ox, oy = -math.sin(yaw)*9, math.cos(yaw)*9
            ROADS.add(obox(q.x+ox, q.y+oy, 6, 2, 0.15, yaw, 2.6), 'shelter_blue', 'Bus_shelter')
            for s in (-2.8, 2.8): ROADS.add(obox(q.x+ox+math.cos(yaw)*s, q.y+oy+math.sin(yaw)*s, 0.12, 0.12, 2.6), 'steel', 'Bus_shelter')
            bx, by = q.x-ox*1.6, q.y-oy*1.6
            ROADS.add(cyl(bx, by, 0.25, 7, 0, 8), 'steel', 'Billboard'); ROADS.add(obox(bx, by, 9, 0.4, 4, yaw, 7), PASTELS[int(d) % 9], 'Billboard')

# ---------------------------------------------------------------- campus ground, avenue, paving
GROUND.add(extrude(BBOX.difference(campus), 0.05, -0.06), 'outside_ground')
GROUND.add(extrude(campus, 0.06, -0.05), 'wood_floor', 'Campus_ground')
av = avenue.intersection(campus.buffer(5))
AV_W = 7.5
ROADS.add(ribbon(av, AV_W, 0.0, 0.1), 'asphalt', 'MIT_Avenue')
ROADS.add(ribbon(av, 0.15, 0.1, 0.01), 'white', 'MIT_Avenue')
for side in ('left', 'right'):
    for off, wdt, col in ((AV_W/2+1.0, 2.0, 'tile_red'), (AV_W/2+0.15, 0.3, 'tactile')):
        pg = av.parallel_offset(off, side)
        for g in getattr(pg, 'geoms', [pg]):
            if g.length > 1: GROUND.add(ribbon(g, wdt, 0.0, 0.14 if col == 'tile_red' else 0.16), col, 'Avenue_paving')
# interlocking block courtyards in front of every styled academic building + paths to avenue (red/black pattern)
court_red, court_black = [], []
for w, t, p in campus_fp:
    if w not in assigned: continue
    c, L, W, yaw = obb(p); face = facing(c); q = nearest_points(avenue, Point(*c))[0]
    path = LineString([c, (q.x, q.y)])
    court = path.buffer(2.0).union(Point(c[0]+math.cos(face)*(W/2+7), c[1]+math.sin(face)*(W/2+7)).buffer(9)).difference(p.buffer(0.3)).difference(avenue.buffer(AV_W/2+0.3))
    cells = [sbox(x, y, x+1.2, y+1.2) for x in np.arange(court.bounds[0], court.bounds[2], 1.2) for y in np.arange(court.bounds[1], court.bounds[3], 1.2)]
    for k, cel in enumerate(cells):
        i_ = int((cel.bounds[0]-court.bounds[0])/1.2) + int((cel.bounds[1]-court.bounds[1])/1.2)
        (court_black if (i_ % 5 == 0) else court_red).append(cel.intersection(court))
GROUND.add(extrude(unary_union(court_red), 0.12), 'tile_red', 'Interlock_paving')
GROUND.add(extrude(unary_union(court_black), 0.12), 'tile_black', 'Interlock_paving')

# ---------------------------------------------------------------- landmarks
gx, gy = MAIN_GATE; fx, fy = GATE_DIR; px, py = -fy, fx
# Main Gate: 4 square grey/white pillars, red canopy beam across the 2-lane road, white lettering
for s in (-7.2, -4.6, 4.6, 7.2):
    LAND.add(obox(gx+px*s, gy+py*s, 1.2, 1.2, 7.0, GATE_YAW), 'grey', 'Main_Gate'); LAND.add(obox(gx+px*s, gy+py*s, 1.3, 1.3, 0.5, GATE_YAW, 6.6), 'white', 'Main_Gate')
LAND.add(obox(gx, gy, 2.2, 17.5, 1.4, GATE_YAW, 7.0), 'red', 'Main_Gate')
sign = text_quad('MADRAS INSTITUTE OF TECHNOLOGY', 15.5, 1.0, (1, 1, 1), (0.75, 0.12, 0.10))
LAND.textured.append(('Main_Gate_text_out', place(sign, gx-fx*1.12, gy-fy*1.12, 7.2, GATE_YAW+math.pi/2+math.pi)))
sign2 = text_quad('MADRAS INSTITUTE OF TECHNOLOGY', 15.5, 1.0, (1, 1, 1), (0.75, 0.12, 0.10))
LAND.textured.append(('Main_Gate_text_in', place(sign2, gx+fx*1.12, gy+fy*1.12, 7.2, GATE_YAW+math.pi/2)))
bx, by = gx-fx*3+px*11, gy-fy*3+py*11
LAND.add(obox(bx, by, 0.2, 0.2, 2.0, GATE_YAW), 'steel', 'MIT_board'); LAND.add(obox(bx+px*3, by+py*3, 0.2, 0.2, 2.0, GATE_YAW), 'steel', 'MIT_board')
board = text_quad('ANNA UNIVERSITY  MIT CAMPUS', 3.6, 1.0, (0.05, 0.05, 0.05), (0.95, 0.78, 0.15), 768)
LAND.textured.append(('MIT_board_text', place(board, bx+px*1.5-fx*0.12, by+py*1.5-fy*0.12, 2.0, GATE_YAW+math.pi/2+math.pi)))
# Monument of Success (ANUSAT): black base, golden ball, silver cube with antennas, low fence
mx, my = gx+fx*16+px*12, gy+fy*16+py*12
LAND.add(obox(mx, my, 3, 3, 1.2, GATE_YAW), 'black', 'Monument_of_Success'); LAND.add(sphere(mx, my, 2.4, 1.2, 2), 'gold', 'Monument_of_Success')
LAND.add(obox(mx, my, 1.4, 1.4, 1.4, GATE_YAW+0.4, 3.4), 'silver', 'Monument_of_Success')
for a in range(4): LAND.add(beam((mx, my), (mx+math.cos(a*1.57+0.4)*2.0, my+math.sin(a*1.57+0.4)*2.0), 0.06, 0.06, 4.6), 'silver', 'Monument_of_Success')
fence = Point(mx, my).buffer(4.5, 4).exterior; LAND.add(ribbon(fence, 0.08, 0.0, 0.7), 'black', 'Monument_of_Success')
# C. Rajam statue arch over a rectangular blue pool (OSM node "Rajam Statue")
rx, ry = RAJAM_STATUE; ryaw = facing((rx, ry))
LAND.add(obox(rx, ry, 8, 5, 0.5, ryaw), 'concrete', 'Rajam_statue'); LAND.add(obox(rx, ry, 7, 4, 0.1, ryaw, 0.42), 'water', 'Rajam_statue')
for s in (-3.2, 3.2): LAND.add(obox(rx+math.cos(ryaw+math.pi/2)*s, ry+math.sin(ryaw+math.pi/2)*s, 0.8, 0.8, 5.5, ryaw), 'dark_grey', 'Rajam_statue')
LAND.add(obox(rx, ry, 1.0, 7.6, 0.8, ryaw, 5.5), 'red', 'Rajam_statue')
LAND.add(obox(rx, ry, 1.4, 1.4, 1.2, ryaw, 0.5), 'dark_grey', 'Rajam_statue'); LAND.add(obox(rx, ry, 0.9, 0.8, 0.9, ryaw, 1.7), 'gold', 'Rajam_statue'); LAND.add(sphere(rx, ry, 2.9, 0.3), 'gold', 'Rajam_statue')
# circular fountain around brown ANNA UNIVERSITY sign (approx: by the avenue, ~110 m inside the gate)
q = avenue.interpolate(d0+110); qq = avenue.interpolate(d0+111); ay = math.atan2(qq.y-q.y, qq.x-q.x)
fxp, fyp = q.x-math.sin(ay)*14, q.y+math.cos(ay)*14
ring = trimesh.creation.annulus(r_min=5.2, r_max=5.7, height=0.6, sections=32); ring.apply_translation([fxp, fyp, 0.3]); LAND.add(ring, 'concrete', 'Fountain')
LAND.add(cyl(fxp, fyp, 5.2, 0.35, 0, 32), 'water', 'Fountain'); LAND.add(obox(fxp, fyp, 4.0, 0.5, 1.6, ay, 0.3), 'brown', 'Fountain')
au = text_quad('ANNA UNIVERSITY', 3.8, 0.6, (0.95, 0.85, 0.5), (0.42, 0.27, 0.15), 512)
LAND.textured.append(('Fountain_sign_text', place(au, fxp+math.sin(ay)*0.27, fyp-math.cos(ay)*0.27, 0.8, ay)))
# water tank on stilts (OSM node "MIT water tank") + circular umbrella seating in CS courtyard
tx, ty = TANK
for a in range(8): LAND.add(cyl(tx+math.cos(a*math.pi/4)*4.5, ty+math.sin(a*math.pi/4)*4.5, 0.4, 18), 'concrete', 'Water_tank')
LAND.add(cyl(tx, ty, 2.2, 18), 'concrete', 'Water_tank'); LAND.add(cyl(tx, ty, 6.5, 7, 18, 24), 'concrete', 'Water_tank'); LAND.add(cone(tx, ty, 6.7, 2.0, 25, 24), 'concrete', 'Water_tank')
for k in range(4):
    ux, uy = tx+12+k%2*7, ty-8+k//2*7; LAND.add(cyl(ux, uy, 0.08, 2.6), 'steel', 'Umbrella_seating'); LAND.add(cone(ux, uy, 1.8, 0.6, 2.4), 'red', 'Umbrella_seating')
    r_ = trimesh.creation.annulus(r_min=1.0, r_max=1.4, height=0.45); r_.apply_translation([ux, uy, 0.22]); LAND.add(r_, 'concrete', 'Umbrella_seating')
# aircraft display grove: Sea Hawk (blue/white), Gnat (grey-green camo), jet engines (approx. near Aero dept)
ae = CAMPUS_NAMED['432468196']; gq = nearest_points(avenue, Point(*ae))[0]
grove = (gq.x*0.4+ae[0]*0.6+8, gq.y*0.4+ae[1]*0.6-12)
def aircraft(x, y, yaw, L, span, body_col, wing_col, name):
    fus = trimesh.creation.capsule(height=L-1.2, radius=0.6, count=[10, 10]); fus.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0,1,0]))
    LAND.add(place(fus, x, y, 2.2, yaw), body_col, name)
    LAND.add(place(trimesh.creation.box(extents=[2.4, span, 0.18]), x, y, 2.0, yaw), wing_col, name)
    tail = trimesh.creation.box(extents=[1.4, 0.15, 1.8]); tail.apply_translation([-(L/2-0.8), 0, 0.9]); LAND.add(place(tail, x, y, 2.4, yaw), wing_col, name)
    tp = trimesh.creation.box(extents=[1.0, span*0.35, 0.12]); tp.apply_translation([-(L/2-0.8), 0, 0]); LAND.add(place(tp, x, y, 2.4, yaw), wing_col, name)
    for s in (-1, 1): LAND.add(cyl(x+math.cos(yaw)*s*2-math.sin(yaw)*0, y+math.sin(yaw)*s*2, 0.12, 1.6), 'dark_grey', name)
aircraft(grove[0], grove[1], 0.3, 12.0, 11.9, 'navy', 'white', 'Sea_Hawk')
aircraft(grove[0]+18, grove[1]+6, 0.9, 9.0, 6.7, 'camo', 'camo', 'Gnat')
for k in range(2):
    e = trimesh.creation.cylinder(radius=0.5, height=2.8, sections=14); e.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0,1,0]))
    LAND.add(place(e, grove[0]+6+k*5, grove[1]-9, 1.2, 0.2), 'steel', 'Jet_engine'); LAND.add(obox(grove[0]+6+k*5, grove[1]-9, 2.4, 1.0, 0.7, 0.2), 'yellow', 'Jet_engine')
# covered walkway: curved corrugated roof on white pillars, parallel to the avenue (approx 60-260 m inside gate)
wk = LineString([avenue.interpolate(d) for d in np.arange(d0+60, min(avenue.length, d0+260), 5)]).parallel_offset(AV_W/2+5, 'right')
for g in getattr(wk, 'geoms', [wk]):
    if g.length < 5: continue
    for d in np.arange(0, g.length, 5):
        q = g.interpolate(d)
        for s in (-1.4, 1.4):
            q2 = g.interpolate(min(g.length, d+0.5)); yy = math.atan2(q2.y-q.y, q2.x-q.x)
            LAND.add(cyl(q.x-math.sin(yy)*s, q.y+math.cos(yy)*s, 0.12, 2.8, 0, 8), 'white', 'Covered_walkway')
    for k, (off, z) in enumerate([(-1.6, 2.8), (-0.8, 3.15), (0, 3.3), (0.8, 3.15), (1.6, 2.8)]):
        pg = g.parallel_offset(abs(off), 'left' if off >= 0 else 'right') if off != 0 else g
        for gg in getattr(pg, 'geoms', [pg]):
            if gg.length > 1: LAND.add(ribbon(gg, 0.9, z, 0.06), 'roof_grey', 'Covered_walkway')
# hostel gate: black iron gate between yellow pillars + 'MIT HOSTEL'
hx, hy = HOSTEL_GATE; hyaw = facing((hx, hy)) + math.pi/2
for s in (-4, 4): LAND.add(obox(hx+math.cos(hyaw)*s, hy+math.sin(hyaw)*s, 1.0, 1.0, 3.5, hyaw), 'yellow', 'Hostel_gate')
for s in np.linspace(-3.4, 3.4, 18): LAND.add(obox(hx+math.cos(hyaw)*s, hy+math.sin(hyaw)*s, 0.06, 0.06, 2.4, hyaw), 'black', 'Hostel_gate')
LAND.add(obox(hx, hy, 7.0, 0.1, 0.12, hyaw, 2.3), 'black', 'Hostel_gate'); LAND.add(obox(hx, hy, 7.0, 0.1, 0.12, hyaw, 0.3), 'black', 'Hostel_gate')
ht = text_quad('MIT HOSTEL', 3.0, 0.5, (1, 1, 1), (0.05, 0.05, 0.05), 512); LAND.textured.append(('Hostel_gate_text', place(ht, hx, hy, 3.0, hyaw)))
# back gate: white metal gate in a yellow wall (OSM gate node 593999547)
bx, by = BACK_GATE; byaw = facing((bx, by)) + math.pi/2
for s in (-9, 9): LAND.add(obox(bx+math.cos(byaw)*s*0.75, by+math.sin(byaw)*s*0.75, 6, 0.3, 2.4, byaw), 'yellow', 'Back_gate')
for s in np.linspace(-2.6, 2.6, 14): LAND.add(obox(bx+math.cos(byaw)*s, by+math.sin(byaw)*s, 0.05, 0.05, 2.0, byaw), 'white', 'Back_gate')
LAND.add(obox(bx, by, 5.4, 0.08, 0.1, byaw, 1.95), 'white', 'Back_gate')
LAND.nodes.append(('Spawn_MainGate', (SPAWN[0], SPAWN[1], 0.2)))
LAND.nodes.append(('SpawnLook', (SPAWN[0]+GATE_DIR[0]*10, SPAWN[1]+GATE_DIR[1]*10, 1.6)))

# ---------------------------------------------------------------- trees (merged per chunk; positions exported for colliders)
def neem(x, y, s):
    return [(cyl(x, y, 0.22*s, 3.2*s, 0, 6), 'trunk'), (sphere(x, y, 4.6*s, 2.8*s, 1), 'canopy' if (int(x*7+y*3) % 2) else 'canopy2')]
def coconut(x, y, s):
    out = [(cyl(x, y, 0.16*s, 9*s, 0, 6), 'trunk')]
    for a in range(6):
        lf = trimesh.creation.box(extents=[3.2*s, 0.5*s, 0.08]); lf.apply_translation([1.5*s, 0, 0])
        lf.apply_transform(trimesh.transformations.rotation_matrix(-0.45, [0,1,0])); out.append((place(lf, x, y, 9*s, a*math.pi/3), 'coconut_leaf'))
    return out
tree_pts = []
blocked = unary_union([p.buffer(2.5) for _, _, p in foot] + [roads_poly.buffer(1.0), av.buffer(AV_W/2+2.2)] + [rail_local.buffer(6)])
landmark_clear = unary_union([Point(*MAIN_GATE).buffer(14), Point(*TANK).buffer(22), Point(*RAJAM_STATUE).buffer(9), Point(*grove).buffer(22), Point(fxp, fyp).buffer(8), Point(mx, my).buffer(6), Point(*SPAWN).buffer(8)])
blocked = blocked.union(landmark_clear)
# avenue arch: both sides every 9 m
for d in np.arange(d0+20, avenue.length, 9):
    q = avenue.interpolate(d); q2 = avenue.interpolate(min(avenue.length, d+1)); yy = math.atan2(q2.y-q.y, q2.x-q.x)
    for s in (-1, 1):
        x, y = q.x-math.sin(yy)*s*(AV_W/2+3.4), q.y+math.cos(yy)*s*(AV_W/2+3.4)
        if campus.contains(Point(x, y)) and not landmark_clear.contains(Point(x, y)): tree_pts.append((x, y, 1.25, 'neem'))
# dense campus canopy: jittered grid 9 m
minx, miny, maxx, maxy = campus.bounds
for x in np.arange(minx, maxx, 9):
    for y in np.arange(miny, maxy, 9):
        xx, yy = x+rng.uniform(-3, 3), y+rng.uniform(-3, 3); pt = Point(xx, yy)
        if campus.contains(pt) and not blocked.contains(pt): tree_pts.append((xx, yy, rng.uniform(0.8, 1.3), 'neem' if rng.random() > 0.15 else 'coconut'))
# sparse outside: along residential streets (neem / coconut)
for wid, t, pts, refs in WAYS:
    if t.get('highway') == 'residential':
        ln = LineString(pts).intersection(BBOX)
        for g in getattr(ln, 'geoms', [ln]):
            if g.is_empty: continue
            for d in np.arange(rng.uniform(5, 30), g.length, 38):
                q = g.interpolate(d); off = g.parallel_offset(4.8, rng.choice(['left', 'right']))
                if off.is_empty or off.geom_type != 'LineString': continue
                q = off.interpolate(off.project(q)); pt = Point(q.x, q.y)
                if not blocked.contains(pt) and not campus.contains(pt) and rng.random() < 0.6: tree_pts.append((q.x, q.y, rng.uniform(0.7, 1.0), rng.choice(['neem', 'neem', 'coconut'])))
chunks = {}
for x, y, s, kind in tree_pts:
    k = (int(x//150), int(y//150))
    for m, col in (neem(x, y, s) if kind == 'neem' else coconut(x, y, s)): chunks.setdefault((k, col), []).append(m)
for (k, col), ms in chunks.items(): TREES.add(trimesh.util.concatenate(ms), col, f'Trees_{k[0]}_{k[1]}')
# collider data in glTF/Unity-ready frame: x=east, y=up, z=-north (same as glb vertices)
tree_json = [{'x': round(x, 2), 'y': 0.0, 'z': round(-y, 2), 'r': round((0.22 if kind == 'neem' else 0.16)*s+0.05, 2), 'h': round((3.2 if kind == 'neem' else 9)*s, 2), 'kind': kind} for x, y, s, kind in tree_pts]

# ---------------------------------------------------------------- export
outs = {
 'buildings/campus_buildings.glb': BUILD, 'buildings/outside_buildings.glb': OUTB, 'roads/roads_v2.glb': ROADS,
 'ground/ground_v2.glb': GROUND, 'props/landmarks.glb': LAND, 'props/trees.glb': TREES}
for rel, lay in outs.items(): lay.export(os.path.join(ROOT, rel))
json.dump({'frame': 'glTF: x=east, y=up, z=-north (metres), origin 12.9487N 80.1394E', 'trees': tree_json}, open(os.path.join(ROOT, 'props', 'trees_colliders.json'), 'w'))
meta = {'spawn_enu': [round(float(SPAWN[0]), 2), round(float(SPAWN[1]), 2)], 'spawn_gltf': [round(float(SPAWN[0]), 2), 0.2, round(float(-SPAWN[1]), 2)],
        'gate_heading_deg_from_north_cw': round((90 - math.degrees(GATE_YAW)) % 360, 1), 'main_gate_osm_node': 432468247,
        'campus_area_m2': round(campus.area), 'campus_buildings': len(campus_fp), 'outside_buildings': len(outside_fp), 'trees': len(tree_pts),
        'assigned_styles': log_assign, 'no_footprint_procedural': [v[0] for k, v in assigned.items() if k.startswith('node_')], 'aircraft_grove_enu': [round(grove[0],1), round(grove[1],1)], 'fountain_enu': [round(fxp,1), round(fyp,1)]}
json.dump(meta, open(os.path.join(ROOT, 'data', 'v2_meta.json'), 'w'), indent=1); print(json.dumps(meta, indent=1))
