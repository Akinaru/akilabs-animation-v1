# Aki Labs: studio logo animation (v1)

Animated studio intro for Aki Labs slot games: a cartoon Erlenmeyer flask drops, fills with sloshing violet liquid, bubbles rise out of the neck and pop, and the "AKI LABS" wordmark slides out from behind the flask.

## Contents
- `blender/anim4.py`: current version (Blender 5.x, EEVEE + Freestyle). Text slides out from behind the flask; typeface Titan One.
  - Render: `Blender -b -P blender/anim4.py -- <frames_dir> 1 150` then encode with ffmpeg.
  - Options: `AKI_LAYOUT=stack|line|stack-wide|labs-top`, `AKI_FONT=<path to .ttf>`.
- `blender/anim2.py`, `anim3.py`, `anim.py`, `flask.py`: earlier iterations (kept for reference).
- `blender/aki-v4-stack.mp4`, `blender/aki-v4-line.mp4`: latest previews. `blender/v4.html` compares layouts.
- `blender/typos.html`: typeface comparison. `blender/layouts/`: final-frame stills per layout.
- `fonts/`: open-licensed display fonts (SIL OFL / Apache, from Google Fonts).
- `logo-pistes.html`, `logo-v2/`: first vector/CSS explorations (rejected, kept for history).

## Dynamic loader (PixiJS v8)
- `blender/layers.py` renders the separate layers (`loader/assets/bg.png`, `liquid.png`, `glass.png`, `text.png`) and `geometry.json` (flask silhouette, liquid interior, levels, text box in pixels, 1920×1080 design space).
- `loader/aki-intro.js`: `AkiIntro.create(app)`, `setProgress(0..1)`, `await finish()` (outro 'settle' by default, or 'wipe' / 'zoom'); 100 % fills the flask to the top of the neck, `destroy()`. The liquid level follows the real loading progress, the liquid sloshes, bubbles rise out of the neck and pop, the wordmark slides out from behind the flask. The intro always plays fully before the outro.
- `loader/index.html`: demo with fake fast / medium / slow / manual loads. Serve the folder over HTTP (`python3 -m http.server`) and open it.

## Next steps
1. Polish the outro handover to each game.
2. Integrate the loader into the slot template.
3. Export layers (glass back, liquid, wave loop, glass front, wordmark) for a dynamic loader in PixiJS or Spine, with the liquid level driven by real loading progress and bubbles generated in code.

## In-game UI standard
`ui/`: the studio UI material (tokens) and standard components, starting with the bonus-buy menu (`ui/buy-menu/`).

Competitor research captures are kept locally and are not part of this repository.

## Loader proposals (2026-11-09)
Owner: the flask intro looks cheap; wants a premium loading screen like the best Stake Engine games (dimmed blurred
game scene, light cone, floating game items, big game logo, crafted gauge with milestones, "touch to play", studio
signature). `loader/proposals.html`, served from the Slots folder
(`python3 -m http.server 3661 --bind 127.0.0.1` in `Slots/`, then
`http://127.0.0.1:3661/aki-labs-brand/loader/proposals.html`): A = studio glass-tube gauge (Aki violet liquid,
bubbles, crystal milestones), B = the game's mine rail with the gold cart, C = premium studio ident (flask fills in
the dark, glow, wordmark reveal, light sweep, violet wave) then A. Uses the game's own art in place (no copies).
- Owner correction (same day): the loading belongs to the STUDIO ident, one for every slot, not to a game screen.
  Reference = the Bow21 Studios ident (letters roll in like slot reels and lock left to right, accent drops with a
  flash and a ring, subtitle and tagline type in, ~4.7 s). `loader/ident-proposals.html` (same server): 1 Rouleaux
  (AKI / LABS roll like reels with motion blur, flask drops as the accent, ring + flash, "SLOT STUDIO" types in, the
  flask fills with the loading, letters roll out), 2 Néon (letters light up as flickering violet neons, neon flask
  fills, thin gauge; everything cuts off), 3 Flacon (flask in a light cone fills with the loading; when loaded a big
  bubble pops and the letters jump into place; violet liquid wipe into the game). Each holds while loading, plays
  its outro only once loaded and its intro has played. Letters rendered from Titan One (fonts/).

## Neon studio ident (3D, 2026-11-09)
Owner picked the neon idea, rendered in 3D in Blender, very clean, adapted to mobile and desktop.
- `blender/neon.py` (Blender 5.1, EEVEE): real glass tubes along the Titan One letters AKI / LABS and the flask
  silhouette (studio profile), a dark brick wall, a dim key light, and per part a coloured spill light. Renders
  `off.png` and one `lit-<part>.png` per part (aki-0..2, labs-0..3, flask, liquid) at 2048 x 2048 (about 1 min):
  `Blender -b -P blender/neon.py -- blender/neon-raw 2048 all`.
- `blender/neon_post.py`: `loader/neon/wall.webp` + `light-<part>.webp` = what each lit part adds (tube, light on
  the wall, bloom), linear-light maths, ~350 KB in all: `python3 blender/neon_post.py blender/neon-raw loader/neon`.
- `loader/ident-neon.html`: the layers ADDED with their own neon catch (flask, A, K, I, then L A B S), live hum and
  a stutter now and then; the flask liquid rises with the real loading progress (masked inside the flask, its light
  on the wall grows with the level, bubbles and a bright surface line); slow push-in; outro = surge then power cut,
  then the game. Framing: one square frame, cover on desktop, fitted on the sign on a phone (wall fades to black).
  Previews: full screen / desktop 16:9 / mobile 9:16 buttons.
- No green screen: the neon glow is semi-transparent and keys badly; additive light layers over the rendered wall
  give the exact 3D render on any format.
