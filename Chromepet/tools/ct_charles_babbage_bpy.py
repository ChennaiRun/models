"""Detailed Charles Babbage Block / Department of Computer Technology (MIT Chromepet), scripted in Blender.
Reference: two user photos (2026-10-18): street view from the road + front 3/4 view. Dimensions are plausible estimates, not surveyed.
Run:  blender -b -P tools/ct_charles_babbage_bpy.py      (from Chromepet/)
Placement: replaces the approximate 'Charles Babbage Block' footprint of mit_details.py
(OBB centre ENU (249.45, 167.68) m, 44.9 x 10.4 m, entrance facing 142.15 deg (toward the campus avenue)).
Output: buildings/detailed/ct_charles_babbage.glb (glTF +Y up). Nodes named COL_* are simple collision boxes."""
import bpy, math, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in dir() else os.getcwd()
OUT = os.path.join(os.getcwd(), 'buildings', 'detailed', 'ct_charles_babbage.glb')
CX, CY, FACE = 249.45, 167.68, 142.15
L, D, SH, FLOORS = 44.0, 10.4, 3.8, 2   # 2 storeys + parapet (photo 2)
H = SH*FLOORS; FRONT = D/2; PLINTH = 0.9  # 5 steps x 0.18 m

bpy.ops.wm.read_factory_settings(use_empty=True)
root = bpy.data.objects.new('CT_Charles_Babbage', None); bpy.context.scene.collection.objects.link(root)
root.location = (CX, CY, 0); root.rotation_euler = (0, 0, math.radians(FACE-90))  # local +Y = entrance direction
MATS = {}
def mat(name, rgb, rough=0.8, metal=0.0, alpha=1.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    MATS[name] = m; return m
CREAM = mat('peach_wall', (0.90, 0.76, 0.66)); CREAM2 = mat('cream_trim', (0.93, 0.86, 0.78)); SALMON = mat('salmon_band', (0.78, 0.52, 0.42))
GLASS = mat('window_glass', (0.06, 0.08, 0.10), 0.15, 0.3); FRAME = mat('window_frame', (0.55, 0.50, 0.42))
WOOD = mat('orange_wood', (0.72, 0.36, 0.12), 0.6); DARK = mat('doorway_dark', (0.03, 0.03, 0.03))
LATT = mat('jali_lattice', (0.82, 0.70, 0.52)); BROWN = mat('sign_brown', (0.30, 0.17, 0.08), 0.5)
STEEL = mat('steel_rail', (0.75, 0.76, 0.78), 0.3, 1.0); STEP = mat('black_granite', (0.05, 0.05, 0.06), 0.25)
PAVE = mat('terracotta_hex_pavers', (0.62, 0.30, 0.24)); POT = mat('pot', (0.45, 0.22, 0.12)); LEAF = mat('plant', (0.18, 0.45, 0.15)); LIGHT = mat('tube_light', (1, 1, 1), 0.2); GREY = mat('concrete', (0.62, 0.61, 0.58))
COLM = mat('collision', (1, 0, 1))

def box(name, cx, cy, cz, sx, sy, sz, m, parent=root):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz)); o = bpy.context.object
    o.scale = (sx, sy, sz); o.name = name; o.data.materials.append(m); o.parent = parent
    bpy.ops.object.transform_apply(scale=True); return o
def cyl(name, x, y, z0, z1, r, m, rot=None, length=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length or (z1-z0), vertices=10, location=(x, y, (z0+z1)/2))
    o = bpy.context.object; o.name = name; o.data.materials.append(m); o.parent = root
    if rot: o.rotation_euler = rot
    return o
def text(name, s, x, y, z, size, m, extrude=0.06):
    bpy.ops.object.text_add(location=(x, y, z)); o = bpy.context.object; o.data.body = s; o.data.size = size
    o.data.align_x = 'CENTER'; o.data.align_y = 'CENTER'; o.data.extrude = extrude; o.rotation_euler = (math.radians(90), 0, math.radians(180))  # face local +Y (toward the road)
    o.data.materials.append(m); o.parent = root; o.name = name
    bpy.ops.object.convert(target='MESH'); return o

# --- main block, right-end return wing (steps forward at the right end), plinth, parapet
box('Main_block', 0, 0, H/2, L, D, H, CREAM)
WX = L/2 - 4.0; WD = 4.5   # return wing at +x end projecting toward the road
box('End_wing', WX, FRONT+WD/2, H/2, 8.0, WD, H, CREAM)
box('Plinth', 0, 0, 0.3, L+0.4, D+0.4, 0.6, SALMON)
for (x, y, sx, sy) in [(0, FRONT-0.1, L, 0.25), (0, -FRONT+0.1, L, 0.25), (L/2-0.1, 0, 0.25, D), (-L/2+0.1, 0, 0.25, D)]:
    box('Parapet', x, y, H+0.6, sx, sy, 1.2, CREAM)
box('Parapet_wing', WX, FRONT+WD-0.1, H+0.6, 8.0, 0.25, 1.2, CREAM)
box('Roof_coping', 0, 0, H+1.22, L+0.3, D+0.3, 0.06, CREAM2)
# --- salmon horizontal bands (floor + sill levels), salmon pilasters between bays, continuous sunshade ledges,
#     one dark-framed 3-panel grilled window per bay (front, back, wing face)
BAY = 4.0
def facade(x0, x1, yface, sgn, skip=None):
    n = int((x1-x0)/BAY); xs = [x0 + BAY/2 + i*BAY for i in range(n)]
    for z in [0.95] + [f*SH + 0.9 for f in range(1, FLOORS)] + [f*SH for f in range(1, FLOORS)] + [H-0.15]:
        box('Salmon_band', (x0+x1)/2, yface+sgn*0.04, z, x1-x0, 0.1, 0.22, SALMON)
    for i in range(n+1):
        px = x0 + i*BAY
        if skip and skip[0] < px < skip[1]: continue
        box('Pilaster', px, yface+sgn*0.08, H/2, 0.35, 0.16, H, SALMON)
    for f in range(FLOORS):
        zc = f*SH + 2.0
        box('Sunshade_ledge', (x0+x1)/2, yface+sgn*0.45, zc+1.0, x1-x0, 0.9, 0.1, CREAM2)
        for x in xs:
            if skip and skip[0] < x < skip[1]: continue
            box('Window_frame', x, yface+sgn*0.03, zc, 2.5, 0.08, 1.6, DARK)
            box('Window_glass', x, yface+sgn*0.06, zc, 2.3, 0.05, 1.45, GLASS)
            for k in (-0.4, 0.4): box('Window_divider', x+k*1.9, yface+sgn*0.09, zc, 0.07, 0.05, 1.45, DARK)
            for k in range(6): box('Window_grille', x, yface+sgn*0.11, zc-0.6+k*0.24, 2.3, 0.03, 0.03, DARK)
facade(-L/2, WX-4.0, FRONT, 1, skip=(-4.3, 4.3))
facade(-L/2, L/2, -FRONT, -1)
facade(WX-4.0, WX+4.0, FRONT+WD, 1)
for f in range(FLOORS):
    for sx in (1, -1):
        for yy in (-2.5, 2.5): box('Window_end', sx*(L/2+0.03), yy, f*SH+2.0, 0.06, 1.6, 1.4, GLASS)
# --- entrance: teak frames with glass lattice panels, dark doorway
EW = 6.6
box('Entrance_wall', 0, FRONT+0.04, PLINTH + 2.6, EW, 0.1, 5.2, WOOD)
box('Doorway', 0, FRONT+0.1, PLINTH + 1.4, 2.6, 0.08, 2.8, DARK)
for sx in (-1, 1):
    for zz, hh in ((PLINTH+1.4, 2.8), (PLINTH+3.9, 1.8)):
        xc = sx*2.25; box('Lattice_glass', xc, FRONT+0.1, zz, 1.7, 0.05, hh, GLASS)
        for i in range(5): box('Lattice_v', xc-0.68+i*0.34, FRONT+0.14, zz, 0.05, 0.05, hh, WOOD)
        for j in range(int(hh/0.3)+1): box('Lattice_h', xc, FRONT+0.15, zz-hh/2+j*0.3, 1.7, 0.05, 0.05, WOOD)
box('Transom_lattice', 0, FRONT+0.1, PLINTH+3.9, 2.6, 0.05, 1.8, GLASS)
for i in range(9): box('Lattice_v', -1.2+i*0.3, FRONT+0.14, PLINTH+3.9, 0.05, 0.05, 1.8, WOOD)
# --- portico: two square cream pillars, flat slab roof carrying the sign, recessed ceiling with tube light
PD = 4.2; PW = 7.6; PH = H + 1.2
for sx in (-1, 1):
    box('Portico_pillar', sx*PW/2, FRONT+PD, PH/2, 0.75, 0.75, PH, CREAM2)
box('Portico_fascia', 0, FRONT+PD-0.2, PH-1.6, PW+1.0, 0.9, 3.2, CREAM)
for sx in (-1, 1): box('Portico_side', sx*(PW/2+0.4), FRONT+PD/2, PH-1.6, 0.25, PD, 3.2, CREAM)
box('Portico_ceiling', 0, FRONT+PD/2, PH-3.0, PW+0.6, PD, 0.25, CREAM2)
box('Tube_light', 0, FRONT+PD-1.6, PH-3.15, 1.2, 0.12, 0.06, LIGHT)
SY = FRONT+PD+0.27
text('Sign_line1', 'CHARLES BABBAGE BLOCK', 0, SY, PH-0.55, 0.55, BROWN)
text('Sign_line2', 'DEPARTMENT OF', 0, SY, PH-1.35, 0.4, BROWN)
text('Sign_line3', 'COMPUTER TECHNOLOGY', 0, SY, PH-1.9, 0.4, BROWN)
# --- landing + 5 black granite steps + handrail (left)
box('Landing', 0, FRONT+PD/2, PLINTH/2, PW+0.6, PD, PLINTH, STEP)
SW = 4.6; T = 0.32
for k in range(5):
    h = PLINTH - k*0.18; box(f'Step_{k}', -0.8, FRONT+PD+T/2+k*T, h/2, SW, T, h, STEP)
SL = 5*T; y0, y1 = FRONT+PD, FRONT+PD+SL
for x in (-0.8-SW/2+0.1,):
    for yy, zz in ((y0+0.1, PLINTH), (y1-0.15, 0.18)): cyl('Handrail_post', x, yy, zz, zz+0.95, 0.03, STEEL)
    ln = math.hypot(SL, PLINTH-0.18); ang = math.atan2(PLINTH-0.18, SL)
    cyl('Handrail', x, (y0+y1)/2, 0, 0, 0.025, STEEL, rot=(math.pi/2+ang, 0, 0), length=ln).location.z = (PLINTH+0.18)/2+0.95
# --- ramp on the right, descending along the building (1:12), steel railings both sides
RL = PLINTH*10; RW = 1.6; rx0 = PW/2+0.3
bpy.ops.mesh.primitive_cube_add(size=1); ramp = bpy.context.object; ramp.name = 'Ramp'; ramp.parent = root; ramp.data.materials.append(PAVE)
for p in ramp.data.vertices:
    x = rx0 + (p.co.x+0.5)*RL; y = FRONT+1.0 + p.co.y*RW; z = 0 if p.co.z < 0 else PLINTH*(1-(p.co.x+0.5))
    p.co = (x, y, z)
box('Ramp_kerb', rx0+RL/2, FRONT+1.0+RW/2+0.1, 0.25, RL, 0.2, 0.5, GREY)
for i in range(0, 11):
    x = rx0 + i*RL/10; z = PLINTH*(1-i/10)
    for yy in (FRONT+1.0-RW/2+0.05, FRONT+1.0+RW/2-0.05): cyl('Ramp_post', x, yy, z, z+0.95, 0.03, STEEL)
for yy in (FRONT+1.0-RW/2+0.05, FRONT+1.0+RW/2-0.05):
    for dz in (0.95, 0.5):
        ln = math.hypot(RL, PLINTH); ang = math.atan2(PLINTH, RL)
        r = cyl('Ramp_rail', rx0+RL/2, yy, 0, 0, 0.025, STEEL, rot=(0, math.pi/2+ang, 0), length=ln); r.location.z = PLINTH/2+dz
# --- terracotta hexagonal-paver forecourt (hex pattern as slightly raised tiles) + potted plants along the wall
box('Forecourt', 0, FRONT+PD+SL+4.5, 0.03, 16, 9.0+0.01, 0.06, PAVE)
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.2, depth=0.02); hexo = bpy.context.object; hexo.name = 'Hex_pavers'; hexo.data.materials.append(GREY)
hexo.parent = root; hexo.location = (-7.6, FRONT+PD+SL+0.2, 0.065)
arr = hexo.modifiers.new('a', 'ARRAY'); arr.count = 38; arr.relative_offset_displace = (1.0, 0, 0); arr.use_relative_offset = True
arr2 = hexo.modifiers.new('b', 'ARRAY'); arr2.count = 21; arr2.use_relative_offset = True; arr2.relative_offset_displace = (0.5, 0.87, 0)
hexo.scale = (1, 1, 1); hexo.data.materials[0] = mat('hex_joint', (0.50, 0.24, 0.19))
for i in range(7):
    x = rx0 + 1.0 + i*1.3; y = FRONT + 2.6 + (i % 2)*0.4
    cyl('Pot', x, y, 0, 0.45, 0.22, POT)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.45 + (i % 3)*0.12, location=(x, y, 0.9 + (i % 3)*0.15))
    o = bpy.context.object; o.name = 'Plant'; o.data.materials.append(LEAF); o.parent = root
# --- collision proxies (simple boxes; renderers disabled in Unity)
for n, a in [('COL_main', (0, 0, (H+1.2)/2, L+0.4, D+0.4, H+1.2)), ('COL_wing', (WX, FRONT+WD/2, (H+1.2)/2, 8.0, WD, H+1.2)), ('COL_landing', (0, FRONT+PD/2, PLINTH/2, PW+0.6, PD, PLINTH)),
             ('COL_pillar_L', (-PW/2, FRONT+PD, PH/2, 0.9, 0.9, PH)), ('COL_pillar_R', (PW/2, FRONT+PD, PH/2, 0.9, 0.9, PH))]:
    box(n, *a, COLM)
# steps collision as a smooth ramp (walkable), ramp collision = ramp mesh copy
bpy.ops.mesh.primitive_cube_add(size=1); cs = bpy.context.object; cs.name = 'COL_steps'; cs.parent = root; cs.data.materials.append(COLM)
for p in cs.data.vertices:
    y = y0 + (p.co.y+0.5)*SL; x = p.co.x*SW; z = 0 if p.co.z < 0 else PLINTH*(1-(p.co.y+0.5)) + 0.01
    p.co = (x, y, z)
cr = ramp.copy(); cr.data = ramp.data.copy(); cr.name = 'COL_ramp'; bpy.context.scene.collection.objects.link(cr); cr.data.materials[0] = COLM
# Mirror the layout in local X so the ramp, plants and return wing sit to the RIGHT of the entrance as seen
# from the forecourt (photo 2). Sign text is not mirrored.
import bmesh, mathutils
for o in list(bpy.data.objects):
    if o.type != 'MESH' or o.name.startswith('Sign_'): continue
    if o.data.users > 1: o.data = o.data.copy()
    o.data.transform(mathutils.Matrix.Scale(-1, 4, (1, 0, 0)))
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    o.location.x *= -1; o.rotation_euler.y *= -1; o.rotation_euler.z *= -1
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_apply=True)
print('WROTE', OUT)
