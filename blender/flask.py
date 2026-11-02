# Aki Labs flask: stylised toon render (Blender 5.x, EEVEE). Run:
#   Blender -b -P flask.py -- <out.png> <style: toon|sketch> [fill 0..1]
import bpy, bmesh, math, sys, random
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/flask.png'
STYLE = argv[1] if len(argv) > 1 else 'toon'
FILL = float(argv[2]) if len(argv) > 2 else 0.62
random.seed(7)

INK = (0.006, 0.002, 0.018, 1)
VIOLET = [(0.060, 0.005, 0.42, 1), (0.170, 0.022, 0.88, 1), (0.36, 0.15, 1.0, 1)]   # shadow, mid, light
A_COL = [(0.12, 0.02, 0.62, 1), (0.27, 0.07, 1.0, 1), (0.45, 0.24, 1.0, 1)]
GLASS = [(0.36, 0.30, 0.70, 1), (0.66, 0.60, 0.92, 1), (0.95, 0.92, 1.0, 1)]

# ---------- reset scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x, scn.render.resolution_y = 1200, 1500
scn.render.film_transparent = True
scn.view_settings.view_transform = 'Standard'
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'
try:
    scn.eevee.taa_render_samples = 64
except Exception:
    pass

# ---------- materials ----------
def toon(name, cols, stops=(0.28, 0.62), alpha=1.0, gloss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; l = nt.links
    n.clear()
    out = n.new('ShaderNodeOutputMaterial')
    dif = n.new('ShaderNodeBsdfDiffuse')
    s2r = n.new('ShaderNodeShaderToRGB')
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, cols[0]
    e[1].position, e[1].color = stops[0], cols[1]
    e3 = e.new(stops[1]); e3.color = cols[2]
    l.new(dif.outputs[0], s2r.inputs[0]); l.new(s2r.outputs[0], ramp.inputs[0])
    col = ramp.outputs[0]
    if gloss:
        g = n.new('ShaderNodeBsdfGlossy'); g.inputs['Roughness'].default_value = gloss
        g2 = n.new('ShaderNodeShaderToRGB'); r2 = n.new('ShaderNodeValToRGB')
        r2.color_ramp.interpolation = 'CONSTANT'
        r2.color_ramp.elements[0].color = (0, 0, 0, 1)
        r2.color_ramp.elements[1].position = 0.55; r2.color_ramp.elements[1].color = (1, 1, 1, 1)
        l.new(g.outputs[0], g2.inputs[0]); l.new(g2.outputs[0], r2.inputs[0])
        mix = n.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MIX'
        l.new(r2.outputs[0], mix.inputs['Factor']); l.new(col, mix.inputs['A'])
        mix.inputs['B'].default_value = (1, 1, 1, 1)
        col = mix.outputs['Result']
        hl = r2.outputs[0]
    em = n.new('ShaderNodeEmission'); l.new(col, em.inputs['Color'])
    if alpha < 1.0:
        tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
        a = n.new('ShaderNodeMath'); a.operation = 'MAXIMUM'
        lw = n.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.35
        fr = n.new('ShaderNodeValToRGB'); fr.color_ramp.interpolation = 'CONSTANT'
        fr.color_ramp.elements[0].color = (alpha * 0.25,) * 3 + (1,)
        fr.color_ramp.elements[1].position = 0.55; fr.color_ramp.elements[1].color = (alpha,) * 3 + (1,)
        l.new(lw.outputs['Facing'], fr.inputs[0]); l.new(fr.outputs[0], a.inputs[0])
        if gloss:
            l.new(hl, a.inputs[1])
        else:
            a.inputs[1].default_value = alpha
        l.new(a.outputs[0], mx.inputs[0]); l.new(tr.outputs[0], mx.inputs[1]); l.new(em.outputs[0], mx.inputs[2])
        l.new(mx.outputs[0], out.inputs[0])
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    else:
        l.new(em.outputs[0], out.inputs[0])
    return m

def ink(name='ink'):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; n.clear()
    out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = INK
    m.node_tree.links.new(em.outputs[0], out.inputs[0])
    m.use_backface_culling = True
    return m

INKM = ink()

def outline(obj, thick, wobble=0.0):
    return
    obj.data.materials.append(INKM)
    so = obj.modifiers.new('outline', 'SOLIDIFY')
    so.thickness = thick; so.offset = 1.0; so.use_flip_normals = True
    so.material_offset = len(obj.data.materials) - 1
    so.use_rim = False
    if wobble:
        # hand-drawn feel: irregular ink width (vertex-group-free noise on the hull)
        tex = bpy.data.textures.new('wob', 'CLOUDS'); tex.noise_scale = 0.18
        d = obj.modifiers.new('wobble', 'DISPLACE'); d.texture = tex; d.strength = wobble; d.mid_level = 0.5

# ---------- geometry helpers ----------
def lathe(name, prof, steps=96):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    verts = [bm.verts.new((r, 0, z)) for r, z in prof]
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=steps, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scn.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth = True
    return ob

def radius_at(z):
    # inner radius of the body cone (glass inside)
    pts = [(0.00, 1.02), (0.12, 1.08), (0.28, 1.05), (1.42, 0.36), (1.60, 0.28)]
    for (z0, r0), (z1, r1) in zip(pts, pts[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0); return r0 + (r1 - r0) * t
    return 0.28

# flask glass (outer profile, chunky cartoon proportions)
glass_prof = [(0.001, 0.0), (0.86, 0.0), (1.07, 0.04), (1.17, 0.15), (1.15, 0.31),
              (0.44, 1.45), (0.35, 1.63), (0.34, 2.20), (0.37, 2.24), (0.47, 2.27),
              (0.49, 2.36), (0.44, 2.43), (0.36, 2.43), (0.33, 2.40)]
flask = lathe('flask', glass_prof)
sub = flask.modifiers.new('sub', 'SUBSURF'); sub.levels = sub.render_levels = 2
flask.data.materials.append(toon('glass', GLASS, stops=(0.3, 0.7), alpha=0.32, gloss=0.12))
outline(flask, 0.055, wobble=0.035 if STYLE == 'sketch' else 0.0)

# liquid
h = 0.18 + FILL * 1.05
liq_prof = [(0.001, 0.06)]
z = 0.06
while z < h:
    liq_prof.append((radius_at(z) - 0.05, z)); z += 0.06
liq_prof += [(radius_at(h) - 0.05, h), (0.001, h)]
liquid = lathe('liquid', liq_prof)
# wavy surface
for v in liquid.data.vertices:
    if abs(v.co.z - h) < 1e-4:
        a = math.atan2(v.co.y, v.co.x)
        v.co.z += 0.035 * math.sin(3 * a) + 0.02 * math.sin(5 * a + 1)
liquid.modifiers.new('sub', 'SUBSURF').levels = 2
liquid.data.materials.append(toon('liq', VIOLET, stops=(0.30, 0.66)))
outline(liquid, 0.02)

# the A, lighter, sitting on the front of the liquid
font_path = '/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf'
cu = bpy.data.curves.new('A', 'FONT'); cu.body = 'A'
try:
    cu.font = bpy.data.fonts.load(font_path)
except Exception:
    pass
cu.size = 0.78; cu.align_x = 'CENTER'; cu.extrude = 0.01
ta = bpy.data.objects.new('A', cu); scn.collection.objects.link(ta)
ta.rotation_euler = (math.radians(90 - 31), 0, 0)
ta.location = (0, -(radius_at(0.42) - 0.05) - 0.03, 0.17)
ta.data.materials.append(toon('Acol', A_COL, stops=(0.30, 0.66)))

# bubbles: escaping from the surface (big, outlined) + subtle ones inside the liquid
def sphere(name, loc, r, mat, line):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=12)
    o = bpy.context.active_object; o.name = name
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(mat)
    if line: outline(o, line)
    return o

bub_mat = toon('bub', [(0.20, 0.06, 0.90, 1), (0.42, 0.22, 1.0, 1), (0.85, 0.78, 1.0, 1)], stops=(0.3, 0.72), gloss=0.1)
out_bubbles = [(0.10, 0.05, h + 0.16, 0.085), (-0.18, 0.0, h + 0.38, 0.065), (0.05, 0.0, h + 0.66, 0.075),
               (-0.04, 0.0, 1.90, 0.06), (0.10, 0.0, 2.62, 0.09), (-0.12, 0.0, 2.95, 0.065), (0.06, 0.0, 3.25, 0.05)]
for i, (x, y, zz, r) in enumerate(out_bubbles):
    sphere(f'bub{i}', (x, y, zz), r, bub_mat, 0.016)
in_mat = toon('inbub', [(0.10, 0.012, 0.55, 1), (0.22, 0.04, 0.95, 1), (0.30, 0.08, 1.0, 1)], stops=(0.3, 0.7))
for i in range(9):
    zz = 0.15 + random.random() * (h - 0.25)
    ang = math.radians(-90 + random.uniform(-55, 55))
    rr = radius_at(zz) - 0.05
    sphere(f'in{i}', (rr * math.cos(ang), rr * math.sin(ang), zz), random.uniform(0.025, 0.05), in_mat, 0)

# ---------- camera & light (shader-to-RGB needs real lights) ----------
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scn.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 4.3
cam.location = (0, -10, 3.3); cam.rotation_euler = (math.radians(81), 0, 0)
scn.camera = cam
sun = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN')); scn.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(55), math.radians(-35), math.radians(-25))
rim = bpy.data.objects.new('rim', bpy.data.lights.new('rim', 'SUN')); scn.collection.objects.link(rim)
rim.data.energy = 1.4; rim.rotation_euler = (math.radians(70), math.radians(60), math.radians(30))
world = bpy.data.worlds.new('w'); scn.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[1].default_value = 0.15

# ---------- Freestyle ink ----------
scn.render.use_freestyle = True
scn.render.line_thickness_mode = 'ABSOLUTE'
vl = scn.view_layers[0]; fs = vl.freestyle_settings
fs.crease_angle = math.radians(120)
ls = fs.linesets[0] if fs.linesets else fs.linesets.new('ink')
ls.select_by_visibility = True; ls.visibility = 'VISIBLE'
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = False; ls.select_contour = True
lst = ls.linestyle or bpy.data.linestyles.new('ink'); ls.linestyle = lst
lst.color = INK[:3]; lst.thickness = 10.0
lst.caps = 'ROUND'
cal = lst.thickness_modifiers.new('cal', 'CALLIGRAPHY')
cal.orientation = 35; cal.thickness_min = 5.0; cal.thickness_max = 15.0
if STYLE == 'sketch':
    lst.geometry_modifiers.new('n1', 'PERLIN_NOISE_1D').amplitude = 2.5
    g2 = lst.geometry_modifiers.new('n2', 'SPATIAL_NOISE'); g2.amplitude = 1.5; g2.scale = 14
    lst.geometry_modifiers.new('bb', 'BACKBONE_STRETCHER').backbone_length = 6
    t2 = lst.thickness_modifiers.new('nz', 'NOISE'); t2.amplitude = 3; t2.period = 18

scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('WROTE', OUT); print('ADIM', ta.dimensions[:], ta.location[:], [m.name for m in ta.data.materials])
