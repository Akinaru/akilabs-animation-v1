# Aki Labs intro v2: horizontal lock-up, sloshing liquid, bubbles that keep rising and pop.
#   Blender -b -P anim2.py -- <frames_dir> [first] [last]
import bpy, bmesh, math, sys, random

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUTDIR = argv[0] if argv else '/tmp/aki2'
F0 = int(argv[1]) if len(argv) > 1 else 1
F1 = int(argv[2]) if len(argv) > 2 else 150
random.seed(5)
FPS = 30
TOTAL = 150
FONT = '/Users/maximegallotta/Documents/Developpement/Slots/aki-labs-brand/fonts/LilitaOne-Regular.ttf'
OX = -1.75                                  # flask x (text sits on the right)

INK = (0.006, 0.002, 0.018, 1)
VIOLET = [(0.060, 0.005, 0.42, 1), (0.170, 0.022, 0.88, 1), (0.36, 0.15, 1.0, 1)]
GLASS = [(0.36, 0.30, 0.70, 1), (0.66, 0.60, 0.92, 1), (0.95, 0.92, 1.0, 1)]
BUB = [(0.20, 0.06, 0.90, 1), (0.42, 0.22, 1.0, 1), (0.85, 0.78, 1.0, 1)]
INBUB = [(0.10, 0.012, 0.55, 1), (0.24, 0.05, 0.98, 1), (0.32, 0.10, 1.0, 1)]
A_RGB = (0.58, 0.40, 1.0, 1)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.fps = FPS
scn.frame_start, scn.frame_end = F0, F1
scn.view_settings.view_transform = 'Standard'
scn.render.image_settings.file_format = 'PNG'
try: scn.eevee.taa_render_samples = 32
except Exception: pass
prefs = bpy.context.preferences.edit

# ---------------- materials ----------------
def toon(name, cols, stops=(0.30, 0.66), alpha=1.0, gloss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links; n.clear()
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

def flat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; n.clear(); out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = col; m.node_tree.links.new(em.outputs[0], out.inputs[0]); return m

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
    pts = [(0.00, 1.02), (0.12, 1.08), (0.28, 1.05), (1.42, 0.36), (1.60, 0.28), (4.0, 0.28)]
    for (z0, r0), (z1, r1) in zip(pts, pts[1:]):
        if z0 <= z <= z1: return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 0.28

def ease(t): return t * t * (3 - 2 * t)

def sphere(name, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=24, ring_count=12)
    o = bpy.context.active_object; o.name = name
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(mat); return o

def K(o, f, loc=None, sc=None):
    if loc is not None: o.location = loc; o.keyframe_insert('location', frame=f)
    if sc is not None: o.scale = (sc, sc, sc) if isinstance(sc, (int, float)) else sc; o.keyframe_insert('scale', frame=f)

# ---------------- flask ----------------
rig = link(bpy.data.objects.new('rig', None)); rig.location.x = OX
glass_prof = [(0.001, 0.0), (0.86, 0.0), (1.07, 0.04), (1.17, 0.15), (1.15, 0.31),
              (0.44, 1.45), (0.35, 1.63), (0.34, 2.20), (0.37, 2.24), (0.47, 2.27),
              (0.49, 2.36), (0.44, 2.43), (0.36, 2.43), (0.33, 2.40)]
flask = lathe('flask', glass_prof); flask.parent = rig
flask.modifiers.new('sub', 'SUBSURF').levels = 2
flask.data.materials.append(toon('glass', GLASS, stops=(0.3, 0.7), alpha=0.32, gloss=0.12))

# liquid surface = top of a cutter box (two crossing wave fields + slosh tilt)
bpy.ops.mesh.primitive_cube_add(size=2)
cut = bpy.context.active_object; cut.name = 'cutter'
bm = bmesh.new(); bm.from_mesh(cut.data)
bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=40, use_grid_fill=True)
bm.to_mesh(cut.data); bm.free()
cut.scale = (1.6, 1.6, 1.0)
w1 = cut.modifiers.new('w1', 'WAVE'); w1.use_x = True; w1.use_y = False; w1.width = 0.75; w1.speed = 0.035; w1.narrowness = 1.0
w2 = cut.modifiers.new('w2', 'WAVE'); w2.use_x = False; w2.use_y = True; w2.width = 0.5; w2.speed = -0.05; w2.narrowness = 1.2
w3 = cut.modifiers.new('w3', 'WAVE'); w3.use_x = True; w3.use_y = True; w3.width = 0.42; w3.speed = 0.06; w3.narrowness = 1.6
w3.start_position_x = 0.3; w3.start_position_y = -0.4
cut.hide_render = True; cut.display_type = 'WIRE'

z = 0.06; prof = [(0.001, z)]
while z < 2.30: prof.append((radius_at(z) - 0.05, z)); z += 0.05
prof += [(0.23, 2.30), (0.001, 2.30)]
liquid = lathe('liquid', prof); liquid.parent = rig
liquid.data.materials.append(toon('liq', VIOLET))
b = liquid.modifiers.new('fill', 'BOOLEAN'); b.operation = 'INTERSECT'; b.object = cut
for sv in ('EXACT', 'MANIFOLD', 'FLOAT'):
    try: b.solver = sv; break
    except Exception: pass

# the A (higher in the liquid), revealed by the level through its shader
cu = bpy.data.curves.new('A', 'FONT'); cu.body = 'A'
try: cu.font = bpy.data.fonts.load(FONT)
except Exception: pass
cu.size = 0.74; cu.align_x = "CENTER"; cu.extrude = 0.015
ta = link(bpy.data.objects.new('A', cu))
AZ = 0.44
ta.rotation_euler = (math.radians(90 - 31), 0, 0)
ta.location = (0, -(radius_at(AZ) - 0.05) - 0.06, AZ)
bpy.context.view_layer.objects.active = ta; ta.select_set(True)
bpy.ops.object.convert(target='MESH'); ta = bpy.context.active_object; ta.parent = rig
am = bpy.data.materials.new('Acol'); am.use_nodes = True
n = am.node_tree.nodes; l = am.node_tree.links; n.clear()
out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = A_RGB
geo = n.new('ShaderNodeNewGeometry'); sep = n.new('ShaderNodeSeparateXYZ'); lv = n.new('ShaderNodeValue')
cmp = n.new('ShaderNodeMath'); cmp.operation = 'LESS_THAN'
tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
l.new(geo.outputs['Position'], sep.inputs[0]); l.new(sep.outputs['Z'], cmp.inputs[0]); l.new(lv.outputs[0], cmp.inputs[1])
l.new(cmp.outputs[0], mx.inputs[0]); l.new(tr.outputs[0], mx.inputs[1]); l.new(em.outputs[0], mx.inputs[2]); l.new(mx.outputs[0], out.inputs[0])
try: am.surface_render_method = 'DITHERED'
except Exception: pass
ta.data.materials.append(am)

# ---------------- level, waves, slosh ----------------
TOP = 0.18 + 0.72 * 1.05
LAND = 10
def level(f):
    if f < LAND: return -0.3
    if f < 40: return -0.3 + (TOP + 0.3) * ease((f - LAND) / 30)
    return TOP + 0.03 * math.sin((f - 40) / FPS * math.tau * 0.5)
def amp(f):            # wave energy: big while filling, settles to a lively idle
    if f < LAND: return 0.0
    if f < 50: return 0.11
    return 0.05 + 0.06 * math.exp(-(f - 50) / 25)
def tilt(f):           # slosh after the landing, then a gentle sway
    if f < LAND: return 0.0
    t = (f - LAND) / FPS
    return math.radians(9) * math.exp(-t * 1.6) * math.sin(t * math.tau * 1.3) + math.radians(2.2) * math.sin(t * math.tau * 0.45)
for f in range(1, TOTAL + 1):
    cut.location = (OX, 0, level(f) - 1.0); cut.rotation_euler = (0, tilt(f), 0)
    cut.keyframe_insert('location', frame=f); cut.keyframe_insert('rotation_euler', frame=f)
    a = amp(f)
    w1.height = a; w2.height = a * 0.6; w3.height = a * 0.5
    for w in (w1, w2, w3): w.keyframe_insert('height', frame=f)
    lv.outputs[0].default_value = level(f) - 0.06; lv.outputs[0].keyframe_insert('default_value', frame=f)

# ---------------- drop, squash & stretch ----------------
def rk(f, zz, sx, sz):
    rig.location = (OX, 0, zz); rig.scale = (sx, sx, sz)
    rig.keyframe_insert('location', frame=f); rig.keyframe_insert('scale', frame=f)
rk(1, 6.0, 0.94, 1.08); rk(LAND - 1, 0.0, 0.94, 1.10); rk(LAND + 1, 0.0, 1.16, 0.80)
rk(LAND + 4, 0.0, 0.95, 1.07); rk(LAND + 8, 0.0, 1.03, 0.97); rk(LAND + 12, 0.0, 1.0, 1.0)
for f in range(40, TOTAL + 1, 40):
    rk(f + 20, 0.0, 0.99, 1.015); rk(f + 40, 0.0, 1.0, 1.0)

# ---------------- bubbles: continuous rise, real pop ----------------
NOINK = bpy.data.collections.new('noink'); scn.collection.children.link(NOINK)
bub_mat = toon('bub', BUB, stops=(0.3, 0.72), gloss=0.1)
drop_mat = toon('drop', BUB, stops=(0.3, 0.72))
in_mat = toon('inbub', INBUB, stops=(0.3, 0.7))
prefs.keyframe_new_interpolation_type = 'LINEAR'
t = 24; i = 0
while t < TOTAL - 6:
    r = random.uniform(0.05, 0.10)
    bo = sphere(f'bub{i}', r, bub_mat)
    x0 = random.uniform(-0.3, 0.3); z0 = level(t) + 0.03
    top = random.uniform(3.0, 4.0) if random.random() < 0.75 else random.uniform(2.6, 3.0)
    speed = random.uniform(0.06, 0.085)
    life = int((top - z0) / speed)
    K(bo, t - 1, sc=0); K(bo, t, loc=(OX + x0, -0.1, z0)); K(bo, t + 3, sc=1)
    for k in range(0, life + 1, 2):
        zz = z0 + speed * k
        lim = max(0.03, radius_at(zz) - 0.08 - r) if zz < 2.45 else 0.6
        xx = max(-lim, min(lim, x0 + 0.05 * math.sin(k * 0.3 + i) + (0.012 * (k - (2.45 - z0) / speed) if zz > 2.45 else 0)))
        K(bo, t + k, loc=(OX + xx, -0.1, zz))
    P = t + life
    K(bo, P, sc=1); K(bo, P + 2, sc=1.6); K(bo, P + 3, sc=0)
    px, pz = OX + xx, zz
    for d in range(5):                   # pop droplets
        ang = d / 5 * math.tau + random.uniform(-0.3, 0.3)
        dr = sphere(f'drop{i}_{d}', r * 0.28, drop_mat)
        for c in dr.users_collection: c.objects.unlink(dr)
        NOINK.objects.link(dr)
        K(dr, P + 1, sc=0, loc=(px, -0.12, pz)); K(dr, P + 2, sc=1)
        K(dr, P + 7, loc=(px + math.cos(ang) * 0.32, -0.12, pz + math.sin(ang) * 0.32)); K(dr, P + 8, sc=0)
    t += random.randint(5, 10); i += 1
# subtle bubbles inside the liquid
for j in range(18):
    t0 = random.randint(16, TOTAL - 20); r = random.uniform(0.022, 0.045)
    bo = sphere(f'in{j}', r, in_mat)
    ang = math.radians(-90 + random.uniform(-50, 50)); zz0 = random.uniform(0.12, 0.35)
    K(bo, t0 - 1, sc=0)
    for k in range(0, 80, 3):
        zz = zz0 + 0.016 * k
        if zz > level(t0 + k) - 0.12: K(bo, t0 + k, sc=0); break
        rr = radius_at(zz) - 0.05
        K(bo, t0 + k, loc=(OX + rr * math.cos(ang), rr * math.sin(ang) - 0.01, zz))
        if k == 0: K(bo, t0 + 2, sc=1)
prefs.keyframe_new_interpolation_type = 'BEZIER'

# ---------------- wordmark on the right, letter by letter ----------------
shadow_coll = NOINK
white = flat('white', (1, 1, 1, 1)); lilac = flat('lilac', (0.62, 0.45, 1.0, 1)); deep = flat('deep', (0.09, 0.015, 0.40, 1))
def letters(txt, size, x0, z0, mat, track, f0, step):
    x = x0; objs = []
    for ch in txt:
        c = bpy.data.curves.new(ch, 'FONT'); c.body = ch
        try: c.font = bpy.data.fonts.load(FONT)
        except Exception: pass
        c.size = size
        o = link(bpy.data.objects.new('L_' + ch, c)); o.rotation_euler = (math.radians(90), 0, 0); o.location = (x, -0.5, z0)
        o.data.materials.append(mat)
        sh = link(bpy.data.objects.new('S_' + ch, c.copy()), shadow_coll)       # chunky drop shadow
        sh.rotation_euler = o.rotation_euler; sh.location = (x + 0.05, -0.45, z0 - 0.09); sh.data.materials.clear(); sh.data.materials.append(deep)
        bpy.context.view_layer.update()
        wdt = o.dimensions.x
        objs.append((o, sh, x, wdt)); x += wdt + track
    for k, (o, sh, xx, wdt) in enumerate(objs):
        f = f0 + k * step
        for ob in (o, sh):
            ob.hide_render = True; ob.keyframe_insert('hide_render', frame=1)
            ob.hide_render = False; ob.keyframe_insert('hide_render', frame=f + 3)
        for ob, dx, dz in ((o, 0, 0), (sh, 0.05, -0.09)):
            ob.location = (xx + dx, ob.location.y, z0 + dz - 0.5); ob.scale = (0, 0, 0)
            ob.keyframe_insert('location', frame=f); ob.keyframe_insert('scale', frame=f)
            ob.location = (xx + dx, ob.location.y, z0 + dz + 0.08); ob.scale = (1.0, 1.0, 1.22)
            ob.keyframe_insert('location', frame=f + 5); ob.keyframe_insert('scale', frame=f + 5)
            ob.location = (xx + dx, ob.location.y, z0 + dz); ob.scale = (1.12, 1.12, 0.86)
            ob.keyframe_insert('location', frame=f + 8); ob.keyframe_insert('scale', frame=f + 8)
            ob.scale = (1, 1, 1); ob.keyframe_insert('scale', frame=f + 13)
    return objs
letters('AKI', 1.75, -0.35, 1.05, white, 0.06, 32, 3)
letters('LABS', 0.82, -0.30, 0.15, lilac, 0.16, 42, 2)

# ---------------- background (no ink) ----------------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 4, 1.4), rotation=(math.radians(90), 0, 0))
bg = bpy.context.active_object
for c in bg.users_collection: c.objects.unlink(bg)
shadow_coll.objects.link(bg)
m = bpy.data.materials.new('bg'); m.use_nodes = True
n = m.node_tree.nodes; l = m.node_tree.links; n.clear()
out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission')
tc = n.new('ShaderNodeTexCoord'); gr = n.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.2, 0.2, 0.2)
ramp = n.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.006, 0.002, 0.03, 1)
ramp.color_ramp.elements[1].color = (0.05, 0.011, 0.18, 1)
l.new(tc.outputs['Object'], mp.inputs[0]); l.new(mp.outputs[0], gr.inputs[0]); l.new(gr.outputs[0], ramp.inputs[0])
l.new(ramp.outputs[0], em.inputs['Color']); l.new(em.outputs[0], out.inputs[0])
bg.data.materials.append(m)

# ---------------- camera, lights ----------------
cam = link(bpy.data.objects.new('cam', bpy.data.cameras.new('cam')))
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 8.6
cam.location = (0.15, -10, 2.3); cam.rotation_euler = (math.radians(84), 0, 0)
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
ls.select_by_collection = True; ls.collection = shadow_coll; ls.collection_negation = 'EXCLUSIVE'
lst = ls.linestyle or bpy.data.linestyles.new('ink'); ls.linestyle = lst
lst.color = INK[:3]; lst.thickness = 6.0; lst.caps = 'ROUND'
cal = lst.thickness_modifiers.new('cal', 'CALLIGRAPHY')
cal.orientation = 35; cal.thickness_min = 3.0; cal.thickness_max = 9.0

scn.render.filepath = OUTDIR.rstrip('/') + '/f_'
bpy.ops.render.render(animation=True)
print('DONE', F0, F1)
