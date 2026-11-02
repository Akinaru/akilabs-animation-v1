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

## Next steps
1. Pick the layout.
2. Seamless idle loop + outro (handover to the game).
3. Export layers (glass back, liquid, wave loop, glass front, wordmark) for a dynamic loader in PixiJS or Spine, with the liquid level driven by real loading progress and bubbles generated in code.

Competitor research captures are kept locally and are not part of this repository.
