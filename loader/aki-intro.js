// Aki Labs studio intro for PixiJS v8 (global PIXI). Layers are rendered by blender/layers.py.
//
//   const intro = await AkiIntro.create(app, { base: './assets/' });
//   loader.onProgress = (p) => intro.setProgress(p);   // 0..1, real loading progress
//   await intro.finish();                               // plays the outro, resolves when done
//   intro.destroy();
//
// The liquid level follows the loading progress, the liquid sloshes, bubbles rise out of the
// neck and pop. The intro (drop + fill + wordmark) always plays fully before the outro.

const INK = 0x12061f;
const BUB_FILL = 0xa67cff;
const BUB_HI = 0xffffff;
const SURFACE = 0xb894ff;
const INNER = 0x9a5cff;

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const easeInQuad = (t) => t * t;
const easeInOut = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const backOut = (t, s = 1.9) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2);
const rand = (a, b) => a + Math.random() * (b - a);

// x range of the liquid interior at screen height y (from the geometry rows)
function interiorAt(geo, y) {
  const L = geo.liquidLeft, R = geo.liquidRight; // ordered bottom → top (y decreasing)
  for (let i = 0; i < L.length - 1; i++) {
    const y0 = L[i][1], y1 = L[i + 1][1];
    if (y <= y0 && y >= y1) {
      const t = (y0 - y) / (y0 - y1 || 1);
      return [lerp(L[i][0], L[i + 1][0], t), lerp(R[i][0], R[i + 1][0], t)];
    }
  }
  const last = L.length - 1;
  return y > L[0][1] ? [L[0][0], R[0][0]] : [L[last][0], R[last][0]];
}

export class AkiIntro {
  static async create(app, { base = './assets/' } = {}) {
    const geo = await (await fetch(base + 'geometry.json')).json();
    const tex = await PIXI.Assets.load(['bg', 'liquid', 'glass', 'text'].map((k) => ({ alias: 'aki-' + k, src: base + k + '.png' })));
    for (const k of ['bg', 'liquid', 'glass', 'text']) tex[k] = tex['aki-' + k];
    return new AkiIntro(app, geo, tex);
  }

  constructor(app, geo, tex) {
    this.app = app; this.geo = geo;
    const [W, H] = geo.size; this.W = W; this.H = H;
    this.progress = 0; this.shown = 0; this.t = 0;
    this.finishing = false; this.done = false;
    this.tilt = 0; this.tiltV = 0; this.energy = 0;
    this.bubbles = []; this.inner = []; this.drops = [];
    this.spawnIn = 0.6; this.innerIn = 0.3;
    this.cx = geo.pivot[0];

    const root = this.root = new PIXI.Container();
    app.stage.addChild(root);
    root.addChild(new PIXI.Sprite(tex.bg));

    // flask rig: pivot at the base of the flask, for the drop and squash
    const rig = this.rig = new PIXI.Container();
    rig.pivot.set(geo.pivot[0], geo.pivot[1]); rig.position.set(geo.pivot[0], geo.pivot[1]);
    root.addChild(rig);

    const liquidGroup = new PIXI.Container();
    this.waveMask = new PIXI.Graphics();
    liquidGroup.addChild(new PIXI.Sprite(tex.liquid));
    // subtle bubbles inside the liquid, clipped to the liquid shape
    this.innerLayer = new PIXI.Container();
    const innerClip = new PIXI.Sprite(tex.liquid);
    this.innerLayer.mask = innerClip;
    liquidGroup.addChild(this.innerLayer, innerClip);
    // lighter surface band following the waves, clipped to the liquid shape
    this.surface = new PIXI.Graphics();
    const surfClip = new PIXI.Sprite(tex.liquid);
    this.surface.mask = surfClip;
    liquidGroup.addChild(this.surface, surfClip);
    liquidGroup.mask = this.waveMask;
    rig.addChild(liquidGroup, this.waveMask);
    rig.addChild(new PIXI.Sprite(tex.glass));

    // bubbles that leave the flask live in root space
    this.bubbleLayer = new PIXI.Container();
    root.addChild(this.bubbleLayer);

    // wordmark: AKI and LABS slide out from behind the flask (masked by its silhouette)
    const tb = geo.textBox, split = Math.round(lerp(tb[1], tb[3], 0.62));
    const mk = (y0, y1) => {
      const s = new PIXI.Sprite(new PIXI.Texture({ source: tex.text.source, frame: new PIXI.Rectangle(0, y0, W, y1 - y0) }));
      s.y = y0; return s;
    };
    this.aki = mk(0, split); this.labs = mk(split, H);
    const textLayer = new PIXI.Container();
    textLayer.addChild(this.aki, this.labs);
    const tm = new PIXI.Graphics();
    const edge = [...geo.glassRight].sort((a, b) => a[1] - b[1]).map(([x, y]) => [x + 6, y]);
    const pts = [W, 0, edge[0][0], 0];
    edge.forEach(([x, y]) => pts.push(x, y));
    pts.push(edge[edge.length - 1][0], H, W, H);
    tm.poly(pts).fill(0xffffff);
    textLayer.mask = tm;
    root.addChild(textLayer, tm);
    this.hideOffset = this.cx - tb[2] - 10;          // text right edge behind the flask centre
    this.aki.x = this.labs.x = this.hideOffset;

    this.resize = () => {
      const s = Math.min(app.screen.width / W, app.screen.height / H);
      root.scale.set(s);
      root.position.set((app.screen.width - W * s) / 2, (app.screen.height - H * s) / 2);
    };
    this.resize();
    window.addEventListener('resize', this.resize);

    this.tick = (ticker) => this.update(Math.min(ticker.deltaMS / 1000, 0.05));
    app.ticker.add(this.tick);
    this.introDone = new Promise((r) => (this._introResolve = r));
  }

  setProgress(p) { this.progress = clamp(p, 0, 1); }

  /** Plays the outro once the intro has finished; resolves when the screen is clear. */
  async finish() {
    await this.introDone;
    this.finishing = true; this.finishT = 0;
    this.progress = 1;
    return new Promise((r) => (this._finishResolve = r));
  }

  destroy() {
    this.app.ticker.remove(this.tick);
    window.removeEventListener('resize', this.resize);
    this.root.destroy({ children: true });
  }

  levelY(v) { // v: 0 empty .. 1 idle max .. >1 up to the shoulders
    const g = this.geo;
    return v <= 1 ? lerp(g.levelBottom, g.levelIdleMax, v) : lerp(g.levelIdleMax, g.levelTop, v - 1);
  }

  update(dt) {
    const g = this.geo; this.t += dt; const t = this.t;

    // ---- intro: drop, squash & stretch ----
    const DROP = 0.32, LAND = DROP;
    if (t < DROP) {
      this.rig.y = g.pivot[1] - lerp(900, 0, easeInQuad(t / DROP));
      this.rig.scale.set(0.95, 1.08);
    } else {
      this.rig.y = g.pivot[1];
      const k = t - LAND;
      const sq = Math.exp(-k * 7) * Math.cos(k * 26);  // damped oscillation
      const breathe = this.introOver ? 0.008 * Math.sin(t * 2.2) : 0;
      this.rig.scale.set(1 + 0.16 * sq - breathe * 0.5, 1 - 0.2 * sq + breathe);
      if (!this.landed) { this.landed = true; this.tiltV += 0.9; this.energy = 1; }
    }

    // ---- liquid level: fill during the intro, then follow the real progress ----
    let target;
    if (this.finishing) {
      this.finishT += dt;
      target = 1.45;
    } else if (t < LAND + 0.1) target = -0.08;
    else if (t < LAND + 1.0) target = Math.max(this.progress, 0.22) * easeInOut((t - LAND - 0.1) / 0.9);
    else target = Math.max(this.progress, 0.22);
    const rate = this.finishing ? 4 : t < LAND + 1.0 ? 30 : 2.5;
    const prev = this.shown;
    this.shown += (target - this.shown) * (1 - Math.exp(-rate * dt));
    this.tiltV += (this.shown - prev) * 1.5;     // rising liquid feeds the slosh

    // slosh: damped spring on the tilt + wave energy that settles to a lively idle
    this.tiltV += (-this.tilt * 38) * dt; this.tiltV *= Math.exp(-2.2 * dt); this.tilt += this.tiltV * dt;
    this.energy = Math.max(0.35, this.energy - dt * 0.35);

    const y0 = this.levelY(this.shown);
    const xa = 300, xb = 870, cx = this.cx, e = this.energy;
    const wave = (x) => y0 + this.tilt * 0.22 * (x - cx)
      + e * (7 * Math.sin(x * 0.021 + t * 3.1) + 4.5 * Math.sin(x * 0.047 - t * 4.3) + 2.5 * Math.sin(x * 0.09 + t * 6.7));
    const top = []; for (let x = xa; x <= xb; x += 6) top.push(x, wave(x));
    this.waveMask.clear().poly([...top, xb, 900, xa, 900]).fill(0xffffff);
    this.surface.clear().moveTo(top[0], top[1]);
    for (let i = 2; i < top.length; i += 2) this.surface.lineTo(top[i], top[i + 1] + 3);
    this.surface.stroke({ width: 9, color: SURFACE, alpha: 0.9 });
    this.surfaceAt = wave;

    // ---- bubbles ----
    const live = t > LAND + 0.5 && this.shown > 0.05;
    if (live) {
      this.spawnIn -= dt * (this.finishing ? 6 : 1);
      if (this.spawnIn <= 0) { this.spawnBubble(); this.spawnIn = this.finishing ? rand(0.02, 0.06) : rand(0.22, 0.55); }
      this.innerIn -= dt;
      if (this.innerIn <= 0) { this.spawnInner(); this.innerIn = rand(0.12, 0.3); }
    }
    this.updateBubbles(dt);

    // ---- wordmark slides out from behind the flask ----
    const slide = (spr, start) => {
      const k = clamp((t - start) / 0.55, 0, 1);
      spr.x = k <= 0 ? this.hideOffset : lerp(this.hideOffset, 0, backOut(k));
    };
    slide(this.aki, 1.0); slide(this.labs, 1.12);
    if (!this.introOver && t > 1.75) { this.introOver = true; this._introResolve(); }

    // ---- outro: fills up, bubble burst, then fade ----
    if (this.finishing) {
      const k = this.finishT;
      if (k > 0.75) {
        const f = clamp((k - 0.75) / 0.35, 0, 1);
        this.root.alpha = 1 - f;
        const s = this.root.scale.x;
        if (!this.baseScale) this.baseScale = s;
        if (f >= 1 && !this.done) { this.done = true; this._finishResolve?.(); }
      }
    }
  }

  spawnBubble() {
    const y = this.surfaceAt(this.cx) - 4;
    const [l, r] = interiorAt(this.geo, y);
    const half = Math.min(70, (r - l) / 2 - 20);
    const g = new PIXI.Graphics();
    const rad = rand(6, 13);
    g.circle(0, 0, rad).fill(BUB_FILL).stroke({ width: 3, color: INK });
    g.circle(-rad * 0.35, -rad * 0.35, rad * 0.3).fill(BUB_HI);
    g.position.set(this.cx + rand(-half, half), y);
    g.scale.set(0.2);
    this.bubbleLayer.addChild(g);
    const popY = Math.random() < 0.75 ? rand(this.geo.neckTop - 280, this.geo.neckTop - 60) : rand(this.geo.neckTop + 60, this.geo.neckZ);
    this.bubbles.push({ g, rad, vy: rand(150, 210) * (this.finishing ? 1.5 : 1), ph: rand(0, 6), age: 0, popY, drift: rand(-25, 25) });
  }

  spawnInner() {
    const yb = this.geo.levelBottom - rand(5, 25);
    const [l, r] = interiorAt(this.geo, yb);
    const g = new PIXI.Graphics();
    g.circle(0, 0, rand(2.5, 6)).fill({ color: INNER, alpha: 0.55 });
    g.position.set(rand(l + 25, r - 25), yb);
    this.innerLayer.addChild(g);
    this.inner.push({ g, vy: rand(35, 70), ph: rand(0, 6) });
  }

  updateBubbles(dt) {
    const g = this.geo;
    for (let i = this.bubbles.length - 1; i >= 0; i--) {
      const b = this.bubbles[i]; b.age += dt;
      const s = b.g;
      s.scale.set(Math.min(1, s.scale.x + dt * 6));
      s.y -= b.vy * dt;
      s.x += Math.sin(b.age * 7 + b.ph) * 18 * dt;
      if (s.y > g.neckTop) {               // still inside the flask: keep within the glass
        const [l, r] = s.y > g.neckZ ? interiorAt(g, s.y) : g.neckInner;
        s.x = clamp(s.x, l + b.rad + 4, r - b.rad - 4);
      } else {                              // out of the neck: drift and slow slightly
        s.x += b.drift * dt; b.vy *= Math.exp(-0.25 * dt);
      }
      if (s.y < b.popY) { this.pop(s.x, s.y, b.rad); s.destroy(); this.bubbles.splice(i, 1); }
    }
    for (let i = this.inner.length - 1; i >= 0; i--) {
      const b = this.inner[i]; const s = b.g;
      s.y -= b.vy * dt; s.x += Math.sin(this.t * 5 + b.ph) * 8 * dt;
      if (s.y < this.surfaceAt(s.x) + 8) { s.destroy(); this.inner.splice(i, 1); }
    }
    for (let i = this.drops.length - 1; i >= 0; i--) {
      const d = this.drops[i]; d.life -= dt;
      d.g.x += d.vx * dt; d.g.y += d.vy * dt; d.vy += 300 * dt;
      d.g.alpha = clamp(d.life / 0.25, 0, 1); d.g.scale.set(0.5 + d.life * 2);
      if (d.life <= 0) { d.g.destroy(); this.drops.splice(i, 1); }
    }
  }

  pop(x, y, rad) {
    const ring = new PIXI.Graphics();
    ring.circle(0, 0, rad * 1.3).stroke({ width: 3, color: BUB_FILL });
    ring.position.set(x, y);
    this.bubbleLayer.addChild(ring);
    this.drops.push({ g: ring, vx: 0, vy: 0, life: 0.12 });
    for (let k = 0; k < 5; k++) {
      const a = (k / 5) * Math.PI * 2 + rand(-0.3, 0.3), sp = rand(120, 190);
      const d = new PIXI.Graphics();
      d.circle(0, 0, rand(2, 3.5)).fill(BUB_FILL);
      d.position.set(x, y);
      this.bubbleLayer.addChild(d);
      this.drops.push({ g: d, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 0.28 });
    }
  }
}
