"""Extrude OSM building footprints + road ribbons into OBJ/GLB meshes centred on MIT Chrompet.
Usage: python3 osm_to_mesh.py data/osm_raw.osm out_dir
Local coords: X=east, Z=north (metres), Y=up; origin = MIT main gate approx (12.9487, 80.1394)."""
import sys, math, json, xml.etree.ElementTree as ET
import numpy as np, trimesh
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
LAT0, LON0 = 12.9487, 80.1394
R = 6378137.0
def proj(lat, lon):
    return ((lon-LON0)*math.radians(1)*R*math.cos(math.radians(LAT0)), (lat-LAT0)*math.radians(1)*R)
src, out = sys.argv[1], sys.argv[2]
root = ET.parse(src).getroot()
nodes = {n.get('id'): proj(float(n.get('lat')), float(n.get('lon'))) for n in root.iter('node')}
def tags(e): return {t.get('k'): t.get('v') for t in e.findall('tag')}
def height(t):
    for k in ('height', 'building:height'):
        try: return float(t[k].split()[0])
        except Exception: pass
    try: return float(t['building:levels'])*3.2
    except Exception: pass
    pass
    return {"house":6,'residential':9,'apartments':15,'university':12,'school':9,'commercial':9,'train_station':8}.get(t.get('building'), 6.0)
def to_y_up(m):  # trimesh extrude is Z-up in (x,y)=(east,north) -> Unity Y-up, Z=north
    m.apply_transform(np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])); m.invert(); return m
blds, roads, stats = [], [], {'buildings':0,'with_height':0,'with_levels':0,'roads':0}
mit = None
for w in root.iter('way'):
    t = tags(w); ref = [nd.get('ref') for nd in w.findall('nd')]
    pts = [nodes[r] for r in ref if r in nodes]
    if t.get('amenity') == 'university' and 'Madras Institute' in t.get('name', ''):
        mit = Polygon(pts)
    if 'building' in t and len(pts) >= 4:
        p = Polygon(pts).buffer(0)
        if p.is_empty or p.area < 4: continue
        stats['buildings'] += 1; stats['with_height'] += 'height' in t; stats['with_levels'] += 'building:levels' in t
        h = height(t)
        if not h or h <= 0: h = 6.0
        for g in getattr(p, "geoms", [p]):
            blds.append(to_y_up(trimesh.creation.extrude_polygon(g, h)))
    elif 'highway' in t and len(pts) >= 2:
        wdt = {'trunk':14,'primary':12,'secondary':10,'tertiary':8,'residential':6,'service':4,'footway':2,'path':2}.get(t['highway'], 5)
        roads.append(LineString(pts).buffer(wdt/2, cap_style=2)); stats['roads'] += 1
rd = unary_union(roads)
rmeshes = [to_y_up(trimesh.creation.extrude_polygon(g, 0.05)) for g in getattr(rd, 'geoms', [rd]) if g.area > 1]
xs = [v[0] for v in nodes.values()]; zs = [v[1] for v in nodes.values()]
ground = trimesh.creation.box(extents=[max(xs)-min(xs), 0.2, max(zs)-min(zs)])
ground.apply_translation([(max(xs)+min(xs))/2, -0.1, (max(zs)+min(zs))/2])
B = trimesh.util.concatenate(blds); Rm = trimesh.util.concatenate(rmeshes)
B.visual.face_colors = [225, 205, 170, 255]; Rm.visual.face_colors = [70, 70, 70, 255]; ground.visual.face_colors = [120, 150, 90, 255]
for name, m in (('buildings', B), ('roads', Rm), ('ground', ground)):
    m.export(f'{out}/{name}.obj')
sc = trimesh.Scene(); [sc.add_geometry(m, node_name=n) for n, m in (('buildings', B), ('roads', Rm), ('ground', ground))]
sc.export(f'{out}/chrompet_mit.glb')
stats['mit_campus_found'] = mit is not None
if mit is not None: stats['mit_centroid_local_m'] = [round(mit.centroid.x,1), round(mit.centroid.y,1)]
json.dump(stats, open(f'{out}/stats.json', 'w'), indent=1); print(stats)
# preview
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig = plt.figure(figsize=(12, 10)); ax = fig.add_subplot(projection='3d')
for m, c in ((Rm, '#444444'), (B, '#e0c9a0')):
    tri = m.vertices[m.faces][:, :, [0, 2, 1]]
    ax.add_collection3d(Poly3DCollection(tri, facecolor=c, edgecolor='none', linewidth=0))
if mit is not None:
    x, y = mit.exterior.xy; ax.plot(x, y, 0.5, color='red', lw=2, label='MIT campus (OSM)'); ax.legend()
L = 900; ax.set_xlim(-L, L); ax.set_ylim(-L, L); ax.set_zlim(0, 300); ax.view_init(45, -60)
ax.set_title('Chrompet / MIT campus - OSM extruded buildings (© OpenStreetMap contributors)')
plt.savefig(f'{out}/preview.png', dpi=110, bbox_inches='tight')
