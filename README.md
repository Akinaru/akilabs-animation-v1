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

Competitor research captures are kept locally and are not part of this repository.
