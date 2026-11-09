"""Neon ident layers from the neon.py renders: wall.webp (all off) + light-<part>.webp (what lighting one part adds:
tube glow, its light on the wall, and a soft bloom), meant to be ADDED over the wall by the game, each with its own
flicker / level. Linear-light maths, written in sRGB. python3 neon_post.py <raw_dir> <out_dir>"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

RAW, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
to_lin = lambda a: np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
to_srgb = lambda a: np.where(a <= 0.0031308, a * 12.92, 1.055 * np.clip(a, 0, None) ** (1 / 2.4) - 0.055)
load = lambda p: to_lin(np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255)
off = load(os.path.join(RAW, 'off.png'))
H = off.shape[0]
Image.open(os.path.join(RAW, 'off.png')).convert('RGB').save(os.path.join(OUT, 'wall.webp'), quality=92)
off_s = to_srgb(off)
for f in sorted(os.listdir(RAW)):
    if not f.startswith('lit-'):
        continue
    lit = load(os.path.join(RAW, f))
    d = np.clip(lit - off, 0, None)
    # bloom: only the bright core spreads (tubes / liquid), at three radii
    core = np.clip(d - 0.08, 0, None)
    bloom = sum(w * nd.gaussian_filter(core, sigma=(s * H / 2048, s * H / 2048, 0)) for s, w in ((5, 0.55), (16, 0.45), (48, 0.35)))
    out = np.clip(to_srgb(np.clip(off + d + bloom, 0, 1)) - off_s, 0, 1)
    name = f[4:-4]
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f'light-{name}.webp'), quality=92)
    print(name, 'max', round(float(out.max()), 3))
