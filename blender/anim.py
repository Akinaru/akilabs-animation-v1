# Aki Labs intro animation (Blender 5.x, EEVEE + Freestyle). Run:
#   Blender -b -P anim.py -- <frames_dir> [first] [last]
import bpy, bmesh, math, sys, random

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUTDIR = argv[0] if argv else '/tmp/aki_frames'
F0 = int(argv[1]) if len(argv) > 1 else 1
F1 = int(argv[2]) if len(argv) > 2 else 120
random.seed(11)

FPS = 30
INK = (0.006, 0.002, 0.018, 1)
VIOLET = [(0.060, 0.005, 0.42, 1), (0.170, 0.022, 0.88, 1), (0.36, 0.15, 1.0, 1)]
A_COL = [(0.20, 0.06, 0.85, 1), (0.36, 0.16, 1.0, 1), (0.55, 0.36, 1.0, 1)]
GLASS = [(0.36, 0.30, 0.70, 1), (0.66, 0.60, 0.92, 1), (0.95, 0.92, 1.0, 1)]
WHITE = [(0.62, 0.58, 0.85, 1), (0.92, 0.90, 1.0, 1), (1, 1, 1, 1)]
LABS = [(0.20, 0.06, 0.90, 1), (0.42, 0.22, 1.0, 1), (0.70, 0.55, 1.0, 1)]
BUB = [(0.20, 0.06, 0.90, 1), (0.42, 0.22, 1.0, 1), (0.85, 0.78, 1.0, 1)]
INBUB = [(0.10, 0.012, 0.55, 1), (0.24, 0.05, 0.98, 1), (0.32, 0.10, 1.0, 1)]

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x, scn.render.resolution_y = 800, 1000
scn.render.fps = FPS
scn.frame_start, scn.frame_end = F0, F1
scn.view_settings.view_transform = 'Standard'
scn.render.image_settings.file_format = 'PNG'
try:
    scn.eevee.taa_render_samples = 32
except Exception:
    pass

# ---------------- materials ----------------
def toon(name, cols, stops=(0.30, 0.66), alpha=1.0, gloss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; l = nt.links; n.clear()
    out = n.new('ShaderNodeOutputMaterial')
    dif = n.new('ShaderNodeBsdfDiffuse'); s2r = n.new('ShaderNodeShaderToRGB'); ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, cols[0]
    e[1].position, e[1].color = stops[0], cols[1]
    e.new(stops[1]).color = cols[2]
    l.new(dif.outputs[0], s2r.inputs[0]); l.new(s2r.outputs[0], ramp.inputs[0])
    col = ramp.outputs[0]; hl = None
    if gloss:
        g = n.new('ShaderNodeBsdfGlossy'); g.inputs['Roughness'].default_value = gloss
        g2 = n.new('ShaderNodeShaderToRGB'); r2 = n.new('ShaderNodeValToRGB')
        r2.color_ramp.interpolation = 'CONSTANT'
        r2.color_ramp.elements[0].color = (0, 0, 0, 1)
        r2.color_ramp.elements[1].position = 0.55; r2.color_ramp.elements[1].color = (1, 1, 1, 1)
        l.new(g.outputs[0], g2.inputs[0]); l.new(g2.outputs[0], r2.inputs[0])
        mix = n.new('ShaderNodeMix'); mix.data_type = 'RGBA'
        l.new(r2.outputs[0], mix.inputs['Factor']); l.new(col, mix.inputs['A'])
        mix.inputs['B'].default_value = (1, 1, 1, 1)
        col = mix.outputs['Result']; hl = r2.outputs[0]
    em = n.new('ShaderNodeEmission'); l.new(col, em.inputs['Color'])
    if alpha < 1.0:
        tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
        a = n.new('ShaderNodeMath'); a.operation = 'MAXIMUM'
        lw = n.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.35
        fr = n.new('ShaderNodeValToRGB'); fr.color_ramp.interpolation = 'CONSTANT'
        fr.color_ramp.elements[0].color = (alpha * 0.25,) * 3 + (1,)
        fr.color_ramp.elements[1].position = 0.55; fr.color_ramp.elements[1].color = (alpha,) * 3 + (1,)
        l.new(lw.outputs['Facing'], fr.inputs[0]); l.new(fr.outputs[0], a.inputs[0])
        if hl is not None: l.new(hl, a.inputs[1])
        else: a.inputs[1].default_value = alpha
        l.new(a.outputs[0], mx.inputs[0]); l.new(tr.outputs[0], mx.inputs[1]); l.new(em.outputs[0], mx.inputs[2])
        l.new(mx.outputs[0], out.inputs[0])
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    else:
        l.new(em.outputs[0], out.inputs[0])
    return m

# ---------------- helpers ----------------
def link(ob, coll=None):
    (coll or scn.collection).objects.link(ob); return ob

def lathe(name, prof, steps=96):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=steps, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return link(bpy.data.objects.new(name, me))

def radius_at(z):
    pts = [(0.00, 1.02), (0.12, 1.08), (0.28, 1.05), (1.42, 0.36), (1.60, 0.28), (3.0, 0.28)]
    for (z0, r0), (z1, r1) in zip(pts, pts[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 0.28

def key(ob, path, frame, value, interp='BEZIER'):
    setattr(ob, path, value); ob.keyframe_insert(path, frame=frame)
    for fc in (ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, 'fcurves') else []):
        pass

def ease(t):  # smoothstep
    return t * t * (3 - 2 * t)

# ---------------- rig (everything that drops) ----------------
rig = link(bpy.data.objects.new('rig', None))

glass_prof = [(0.001, 0.0), (0.86, 0.0), (1.07, 0.04), (1.17, 0.15), (1.15, 0.31),
              (0.44, 1.45), (0.35, 1.63), (0.34, 2.20), (0.37, 2.24), (0.47, 2.27),
              (0.49, 2.36), (0.44, 2.43), (0.36, 2.43), (0.33, 2.40)]
flask = lathe('flask', glass_prof); flask.parent = rig
flask.modifiers.new('sub', 'SUBSURF').levels = 2
flask.data.materials.append(toon('glass', GLASS, stops=(0.3, 0.7), alpha=0.32, gloss=0.12))

# cutter: a box whose wavy top is the liquid surface
bpy.ops.mesh.primitive_cube_add(size=2)
cut = bpy.context.active_object; cut.name = 'cutter'
bm = bmesh.new(); bm.from_mesh(cut.data)
bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=28, use_grid_fill=True)
bm.to_mesh(cut.data); bm.free()
cut.scale = (1.7, 1.7, 1.0)
wave = cut.modifiers.new('wave', 'WAVE'); wave.use_x = True; wave.use_y = False
wave.height = 0.035; wave.width = 0.55; wave.speed = 0.06; wave.narrowness = 1.2
cut.hide_render = True; cut.display_type = 'WIRE'

def boolean(ob):
    b = ob.modifiers.new('fill', 'BOOLEAN'); b.operation = 'INTERSECT'; b.object = cut
    for sv in ('EXACT', 'MANIFOLD', 'FLOAT', 'FAST'):
        try: b.solver = sv; break
        except Exception: pass

# liquid = inside of the flask, cut by the moving surface
z = 0.06; liq_prof = [(0.001, z)]
while z < 2.30:
    liq_prof.append((radius_at(z) - 0.05, z)); z += 0.05
liq_prof += [(0.23, 2.30), (0.001, 2.30)]
liquid = lathe('liquid', liq_prof); liquid.parent = rig
liquid.data.materials.append(toon('liq', VIOLET))
boolean(liquid)

# the A, revealed by the same surface
cu = bpy.data.curves.new('A', 'FONT'); cu.body = 'A'
try: cu.font = bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf')
except Exception: pass
cu.size = 0.95; cu.align_x = 'CENTER'; cu.extrude = 0.015
ta = link(bpy.data.objects.new('A', cu))
ta.rotation_euler = (math.radians(90 - 31), 0, 0)
ta.location = (0, -(radius_at(0.15) - 0.05) - 0.06, 0.15)
bpy.context.view_layer.objects.active = ta; ta.select_set(True)
bpy.ops.object.convert(target='MESH'); ta = bpy.context.active_object
ta.parent = rig
am = bpy.data.materials.new('Acol'); am.use_nodes = True
n = am.node_tree.nodes; l = am.node_tree.links; n.clear()
out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.58, 0.40, 1.0, 1)
geo = n.new('ShaderNodeNewGeometry'); sep = n.new('ShaderNodeSeparateXYZ'); lv = n.new('ShaderNodeValue'); lv.name = 'LEVEL'
cmp = n.new('ShaderNodeMath'); cmp.operation = 'LESS_THAN'
tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
l.new(geo.outputs['Position'], sep.inputs[0]); l.new(sep.outputs['Z'], cmp.inputs[0]); l.new(lv.outputs[0], cmp.inputs[1])
l.new(cmp.outputs[0], mx.inputs[0]); l.new(tr.outputs[0], mx.inputs[1]); l.new(em.outputs[0], mx.inputs[2]); l.new(mx.outputs[0], out.inputs[0])
try: am.surface_render_method = 'DITHERED'
except Exception: pass
ta.data.materials.append(am)
A_LEVEL = lv

# ---------------- liquid level over time ----------------
FILL_TOP = 0.18 + 0.62 * 1.05
def level(f):
    if f < 10: return -0.2
    if f < 36: return -0.2 + (FILL_TOP + 0.2) * ease((f - 10) / 26)
    return FILL_TOP + 0.025 * math.sin((f - 36) / FPS * math.tau * 0.5)
for f in range(F0, F1 + 1):
    cut.location = (0, 0, level(f) - 1.0); cut.keyframe_insert('location', frame=f)
    A_LEVEL.outputs[0].default_value = level(f) - 0.03; A_LEVEL.outputs[0].keyframe_insert('default_value', frame=f)
    # stronger slosh while filling, calmer afterwards
    wave.height = 0.06 if 12 <= f <= 44 else 0.03; wave.keyframe_insert('height', frame=f)

# ---------------- drop, squash & stretch ----------------
def rk(f, z, sx, sz):
    rig.location = (0, 0, z); rig.scale = (sx, sx, sz)
    rig.keyframe_insert('location', frame=f); rig.keyframe_insert('scale', frame=f)
rk(1, 6.0, 0.94, 1.08)
rk(9, 0.0, 0.94, 1.10)
rk(11, 0.0, 1.16, 0.80)
rk(14, 0.0, 0.95, 1.07)
rk(18, 0.0, 1.03, 0.97)
rk(22, 0.0, 1.0, 1.0)
for f in range(30, F1 + 1, 30):
    rk(f + 15, 0.0, 0.99, 1.015); rk(f + 30, 0.0, 1.0, 1.0)
try:
    for fc in rig.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            if kp.co[0] <= 9: kp.interpolation = 'QUAD'; kp.easing = 'EASE_IN'
except Exception:
    pass

# ---------------- bubbles ----------------
def sphere(name, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=24, ring_count=12)
    o = bpy.context.active_object; o.name = name
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(mat); return o

bub_mat = toon('bub', BUB, stops=(0.3, 0.72), gloss=0.1)
in_mat = toon('inbub', INBUB, stops=(0.3, 0.7))

# escaping bubbles: born at the surface, rise out of the neck, pop
t = 22
i = 0
while t < F1 - 4:
    r = random.uniform(0.05, 0.10)
    b = sphere(f'bub{i}', r, bub_mat)
    x0 = random.uniform(-0.35, 0.35)
    z0 = level(t) + 0.02
    pop = random.uniform(2.6, 3.5) if random.random() < 0.7 else random.uniform(z0 + 0.4, 2.0)
    speed = random.uniform(0.055, 0.08)
    life = int((pop - z0) / speed)
    b.scale = (0, 0, 0); b.location = (x0, -0.1, z0); b.keyframe_insert('scale', frame=t - 1); b.keyframe_insert('location', frame=t)
    b.scale = (1, 1, 1); b.keyframe_insert('scale', frame=t + 3)
    for k in range(1, life + 1, 4):
        zz = z0 + speed * k
        lim = max(0.05, radius_at(zz) - 0.1 - r)
        xx = max(-lim, min(lim, x0 + 0.04 * math.sin(k * 0.35 + i)))
        b.location = (xx, -0.1, zz); b.keyframe_insert('location', frame=t + k)
    b.scale = (1.45, 1.45, 1.45); b.keyframe_insert('scale', frame=t + life + 1)
    b.scale = (0, 0, 0); b.keyframe_insert('scale', frame=t + life + 3)
    t += random.randint(4, 9); i += 1

# subtle bubbles inside the liquid (front face), vanish under the surface
for j in range(16):
    t0 = random.randint(14, F1 - 20)
    r = random.uniform(0.022, 0.045)
    b = sphere(f'in{j}', r, in_mat)
    ang = math.radians(-90 + random.uniform(-50, 50))
    zz0 = random.uniform(0.12, 0.35)
    b.scale = (0, 0, 0); b.keyframe_insert('scale', frame=t0 - 1)
    for k in range(0, 60, 3):
        zz = zz0 + 0.018 * k
        if zz > level(t0 + k) - 0.06:
            b.scale = (0, 0, 0); b.keyframe_insert('scale', frame=t0 + k); break
        rr = radius_at(zz) - 0.05
        b.location = (rr * math.cos(ang), rr * math.sin(ang) - 0.01, zz); b.keyframe_insert('location', frame=t0 + k)
        if k == 0:
            b.scale = (1, 1, 1); b.keyframe_insert('scale', frame=t0 + 2)

# ---------------- wordmark ----------------
def word(txt, size, z, mat, ext):
    c = bpy.data.curves.new(txt, 'FONT'); c.body = txt
    try: c.font = bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf')
    except Exception: pass
    c.size = size; c.align_x = 'CENTER'; c.extrude = ext
    o = link(bpy.data.objects.new(txt, c)); o.rotation_euler = (math.radians(90), 0, 0); o.location = (0, -0.4, z)
    o.data.materials.append(mat); return o

def flat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; n.clear(); out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = col; m.node_tree.links.new(em.outputs[0], out.inputs[0]); return m
aki = word('AKI', 1.0, -1.05, flat('white', (1, 1, 1, 1)), 0.0)
labs = word('L A B S', 0.42, -1.62, flat('labs', LABS[2]), 0.0)
def pop(o, f, base_z):
    o.scale = (0, 0, 0); o.location.z = base_z - 0.3; o.keyframe_insert('scale', frame=f); o.keyframe_insert('location', frame=f)
    o.scale = (1.12, 1.12, 1.12); o.location.z = base_z + 0.05; o.keyframe_insert('scale', frame=f + 6); o.keyframe_insert('location', frame=f + 6)
    o.scale = (0.97, 0.97, 0.97); o.location.z = base_z; o.keyframe_insert('scale', frame=f + 10); o.keyframe_insert('location', frame=f + 10)
    o.scale = (1, 1, 1); o.keyframe_insert('scale', frame=f + 14)
pop(aki, 30, -1.05); pop(labs, 36, -1.62)
LABS_OBJ = labs

# ---------------- background (excluded from ink) ----------------
bgc = bpy.data.collections.new('bg'); scn.collection.children.link(bgc)
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 4, 0.9), rotation=(math.radians(90), 0, 0))
bg = bpy.context.active_object
for c in bg.users_collection: c.objects.unlink(bg)
bgc.objects.link(bg)
for c in LABS_OBJ.users_collection: c.objects.unlink(LABS_OBJ)
bgc.objects.link(LABS_OBJ)
m = bpy.data.materials.new('bg'); m.use_nodes = True
n = m.node_tree.nodes; l = m.node_tree.links; n.clear()
out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission')
tc = n.new('ShaderNodeTexCoord'); gr = n.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.30, 0.30, 0.30)
ramp = n.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.006, 0.002, 0.03, 1)
ramp.color_ramp.elements[1].color = (0.045, 0.010, 0.17, 1)
l.new(tc.outputs['Object'], mp.inputs[0]); l.new(mp.outputs[0], gr.inputs[0]); l.new(gr.outputs[0], ramp.inputs[0])
l.new(ramp.outputs[0], em.inputs['Color']); l.new(em.outputs[0], out.inputs[0])
bg.data.materials.append(m)

# ---------------- camera, lights ----------------
cam = link(bpy.data.objects.new('cam', bpy.data.cameras.new('cam')))
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 6.0
cam.location = (0, -10, 2.15); cam.rotation_euler = (math.radians(83), 0, 0)
scn.camera = cam
for nm, en, rot in (('key', 3.2, (55, -35, -25)), ('rim', 1.4, (70, 60, 30))):
    s = link(bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')))
    s.data.energy = en; s.rotation_euler = tuple(math.radians(v) for v in rot)
world = bpy.data.worlds.new('w'); scn.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[1].default_value = 0.0

# ---------------- Freestyle ink ----------------
scn.render.use_freestyle = True
scn.render.line_thickness_mode = 'ABSOLUTE'
fs = scn.view_layers[0].freestyle_settings
ls = fs.linesets[0] if fs.linesets else fs.linesets.new('ink')
ls.select_by_visibility = True; ls.select_silhouette = True; ls.select_border = True
ls.select_crease = False; ls.select_contour = True
ls.select_by_collection = True; ls.collection = bgc; ls.collection_negation = 'EXCLUSIVE'
lst = ls.linestyle or bpy.data.linestyles.new('ink'); ls.linestyle = lst
lst.color = INK[:3]; lst.thickness = 7.0; lst.caps = 'ROUND'
cal = lst.thickness_modifiers.new('cal', 'CALLIGRAPHY')
cal.orientation = 35; cal.thickness_min = 3.5; cal.thickness_max = 10.5

scn.render.filepath = OUTDIR.rstrip('/') + '/f_'
bpy.ops.render.render(animation=True)
print('DONE', F0, F1)
