# Aki Labs neon studio ident (owner 2026-11-09): a real 3D neon sign (glass tubes following the Titan One letters
# AKI / LABS and the flask silhouette) on a dark brick wall, rendered with EEVEE as separate layers so the game can
# light each part on its own (flicker, loading) on any screen format:
#   off.png             the wall and the sign, all tubes off (dim key light only)
#   lit-<part>.png      the same frame with ONE part lit (tube emission + its light spilling on the wall)
# neon_post.py turns them into wall + additive light layers with bloom.
#   Blender -b -P neon.py -- <out_dir> [size=1536] [parts=all|off,A,...]
import bpy, math, sys, os

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/neon'
SIZE = int(argv[1]) if len(argv) > 1 else 1536
ONLY = argv[2].split(',') if len(argv) > 2 and argv[2] != 'all' else None
os.makedirs(OUT, exist_ok=True)
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'TitanOne-Regular.ttf')

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = scn.render.resolution_y = SIZE
scn.render.film_transparent = False
scn.view_settings.view_transform = 'Standard'
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGB'
try:
    scn.eevee.taa_render_samples = 96
except Exception:
    pass
world = bpy.data.worlds.new('w'); scn.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.002, 0.001, 0.004, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.0

def link(ob):
    scn.collection.objects.link(ob); return ob

# ---------- wall: dark brick, a little violet, with relief ----------
wall_m = bpy.data.materials.new('wall'); wall_m.use_nodes = True
n = wall_m.node_tree.nodes; l = wall_m.node_tree.links
bsdf = n['Principled BSDF']
tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.6, 1.6, 1.6)
brick = n.new('ShaderNodeTexBrick')
brick.inputs['Color1'].default_value = (0.055, 0.045, 0.06, 1)
brick.inputs['Color2'].default_value = (0.035, 0.028, 0.042, 1)
brick.inputs['Mortar'].default_value = (0.012, 0.010, 0.014, 1)
brick.inputs['Scale'].default_value = 3.0
brick.inputs['Mortar Size'].default_value = 0.018
brick.inputs['Brick Width'].default_value = 0.5
brick.inputs['Row Height'].default_value = 0.22
noise = n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 40.0
mix = n.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 0.35
bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.6
l.new(tc.outputs['Object'], mp.inputs['Vector']); l.new(mp.outputs['Vector'], brick.inputs['Vector']); l.new(mp.outputs['Vector'], noise.inputs['Vector'])
l.new(brick.outputs['Color'], mix.inputs['A']); l.new(noise.outputs['Color'], mix.inputs['B'])
l.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
l.new(brick.outputs['Fac'], bump.inputs['Height']); l.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
bsdf.inputs['Roughness'].default_value = 0.85
bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, -0.12))
wall = bpy.context.active_object; wall.data.materials.append(wall_m)

# ---------- neon tube materials (one per part, emission switched per render) ----------
COLORS = {'aki': (0.62, 0.24, 1.0), 'labs': (1.0, 0.22, 0.78), 'flask': (0.25, 0.48, 1.0), 'liquid': (0.42, 0.08, 1.0)}
mats = {}
def tube_mat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.06, 0.05, 0.07, 1)   # unlit: dark glass with a phosphor tint
    b.inputs['Roughness'].default_value = 0.18
    b.inputs['Coat Weight'].default_value = 1.0
    b.inputs['Coat Roughness'].default_value = 0.05
    b.inputs['Emission Color'].default_value = (*col, 1)
    b.inputs['Emission Strength'].default_value = 0.0
    mats[name] = m; return m

def tube_from_text(txt, size, x, y, mat, r):
    bpy.ops.object.text_add(location=(x, y, 0))
    ob = bpy.context.active_object
    ob.data.body = txt; ob.data.font = bpy.data.fonts.load(FONT); ob.data.size = size
    ob.data.align_x = 'CENTER'; ob.data.align_y = 'CENTER'
    bpy.ops.object.convert(target='CURVE')
    ob = bpy.context.active_object
    ob.data.dimensions = '3D'  # a 3D curve is never face-filled: only the tube along the outline remains
    ob.data.bevel_depth = r; ob.data.bevel_resolution = 6
    ob.data.materials.clear(); ob.data.materials.append(mat)
    return ob

def tube_from_points(name, pts, mat, r, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for p, (px, py) in zip(sp.bezier_points, pts):
        p.co = (px, py, 0); p.handle_left_type = p.handle_right_type = 'AUTO'
    sp.use_cyclic_u = closed
    cu.bevel_depth = r; cu.bevel_resolution = 6; cu.use_fill_caps = True
    ob = link(bpy.data.objects.new(name, cu)); cu.materials.append(mat)
    return ob

# layout (Blender units, sign centred, it must fit the central 56 % of the square frame)
R = 0.026
parts = {}
x0 = 0.62
CENTRES = {}
def word(txt, size, y, key, col, r, gap):
    obs = [tube_from_text(ch, size, 0, y, tube_mat('m-%s-%d' % (key, i), col), r) for i, ch in enumerate(txt)]
    bpy.context.view_layer.update()
    ws = [o.dimensions.x for o in obs]
    total = sum(ws) + gap * (len(obs) - 1)
    x = x0 - total / 2
    for i, (o, w) in enumerate(zip(obs, ws)):
        # centre each letter on its own box (text objects are centred on their advance, not their outline)
        bb = [o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box]
        cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
        o.location.x += x + w / 2 - cx
        CENTRES['%s-%d' % (key, i)] = (x + w / 2, y)
        parts['%s-%d' % (key, i)] = [o]
        x += w + gap
word('AKI', 1.05, 0.42, 'aki', COLORS['aki'], R, 0.1)
word('LABS', 0.56, -0.45, 'labs', COLORS['labs'], R * 0.85, 0.12)

# flask silhouette from the studio flask profile (r, z), scaled, open at the neck
PROF = [(0.86, 0.0), (1.07, 0.04), (1.17, 0.15), (1.15, 0.31), (0.44, 1.45), (0.35, 1.63), (0.34, 2.15), (0.40, 2.26), (0.48, 2.30)]
S = 0.62; FX, FY = -1.25, -0.78
right = [(FX + r * S, FY + z * S) for r, z in PROF]
left = [(FX - r * S, FY + z * S) for r, z in reversed(PROF)]
parts['flask'] = [tube_from_points('flask', left + right, tube_mat('m-flask', COLORS['flask']), R)]
# glowing liquid inside (full level; the game masks it to the loading progress)
liq_m = bpy.data.materials.new('m-liquid'); liq_m.use_nodes = True
lb = liq_m.node_tree.nodes['Principled BSDF']
lb.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1); lb.inputs['Roughness'].default_value = 1.0
lb.inputs['Specular IOR Level'].default_value = 0.0
lb.inputs['Emission Color'].default_value = (*COLORS['liquid'], 1); lb.inputs['Emission Strength'].default_value = 0.0
mats['m-liquid'] = liq_m
inner = [(r * 0.86, z) for r, z in PROF[:5]] + [(0.30, 1.55)]
poly = [(FX - r * S, FY + 0.05 + z * S) for r, z in reversed(inner)] + [(FX + r * S, FY + 0.05 + z * S) for r, z in inner]
me = bpy.data.meshes.new('liquid'); me.from_pydata([(x, y, -0.03) for x, y in poly], [], [list(range(len(poly)))]); me.update()
liq = link(bpy.data.objects.new('liquid', me)); liq.data.materials.append(liq_m)
parts['liquid'] = [liq]

# ---------- lights: a dim cool key (always), and per part a spill light switched with it ----------
key = bpy.data.lights.new('key', 'AREA'); key.energy = 110; key.size = 6; key.color = (0.75, 0.75, 1.0)
k = link(bpy.data.objects.new('key', key)); k.location = (1.5, 3.5, 4.0); k.rotation_euler = (math.radians(-38), math.radians(12), 0)
spills = {}
def spill(name, x, y, col, power):
    L = bpy.data.lights.new('s-' + name, 'POINT'); L.energy = 0; L.color = col; L.shadow_soft_size = 0.25
    o = link(bpy.data.objects.new('s-' + name, L)); o.location = (x, y, 0.22)
    spills.setdefault(name, []).append((L, power))
for k, (cx, cy) in CENTRES.items(): spill(k, cx, cy, COLORS['aki' if k.startswith('aki') else 'labs'], 9 if k.startswith('aki') else 4)
spill('flask', FX, FY + 1.2 * S, COLORS['flask'], 10); spill('flask', FX, FY + 0.3 * S, COLORS['flask'], 8)
spill('liquid', FX, FY + 0.35 * S, COLORS['liquid'], 14)

# ---------- camera: orthographic, slightly tilted so the tubes show their depth and shadows ----------
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = 6.0
c = link(bpy.data.objects.new('cam', cam)); scn.camera = c
c.location = (0.35, -1.2, 8.0); c.rotation_euler = (math.radians(8.5), math.radians(2.5), 0)

def set_lit(name):
    for pname, obs in parts.items():
        on = pname == name
        for ob in obs:
            for m in ob.data.materials:
                b = m.node_tree.nodes['Principled BSDF']
                b.inputs['Emission Strength'].default_value = (1.35 if pname != 'liquid' else 0.85) if on else 0.0
            if pname == 'liquid':
                ob.hide_render = not on  # the liquid only exists in its own layer (no dark shape when off)
        for L, p in spills.get(pname, []):
            L.energy = p if on else 0

renders = ['off'] + list(parts.keys())
for name in renders:
    if ONLY and name not in ONLY:
        continue
    set_lit(None if name == 'off' else name)
    scn.render.filepath = os.path.join(OUT, ('off' if name == 'off' else 'lit-' + name) + '.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
