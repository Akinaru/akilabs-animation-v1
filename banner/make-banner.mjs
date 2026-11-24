// Aki Labs provider banner, in the spirit of the studio loading screen ("Tracé"): the white mark, AKI LABS under it,
// the tagline under that, on a gradient. Renders PNGs with headless Chromium (silent, closed in finally).
// Usage: node make-banner.mjs   (from aki-labs-brand/banner) -> aki-labs-banner-<variant>-<w>x<h>.png
import {readFileSync, writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {homedir} from 'node:os';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.resolve(here, '../../AdrenaForge/noop.js'));
const {chromium} = require('playwright-core');

const TAGLINE = 'SLOTS WITH A STORY';
const mark = readFileSync(path.resolve(here, '../logo-mark/final/aki-mark.svg'), 'utf8').replace(/<!--[\s\S]*?-->/g, '');
const font = pathToFileURL(path.resolve(here, '../fonts/ArchivoBlack-Regular.ttf')).href;

// dark = the loading screen's own background; violet / sunset = brand colour versions
const VARIANTS = {
  dark: 'radial-gradient(ellipse 60% 75% at 50% 45%, #1b1b22 0%, #0c0c10 55%, #050506 100%)',
  violet: 'linear-gradient(135deg, #2a0f4d 0%, #5b1f8f 50%, #c2367f 100%)',
  sunset: 'linear-gradient(135deg, #ff7a2f 0%, #f0508f 100%)',
};
const SIZES = [[1920, 1080], [1920, 600], [1500, 500], [1200, 630], [1080, 1080]];

const page = (bg, w, h) => {
  const u = Math.min(h / 600, w / 1000, 1.4); // layout unit: the stack fits the height and keeps side room
  return `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'Aki Archivo Black';src:url('${font}')}
html,body{margin:0;width:${w}px;height:${h}px;overflow:hidden}
body{background:${bg};display:grid;place-items:center;font-family:'Aki Archivo Black',sans-serif;color:#f4f4f6}
.ident{display:flex;flex-direction:column;align-items:center}
.mark{height:${200 * u}px;width:${200 * u * 0.8344}px;display:block}
.mark svg{width:100%;height:100%;fill:#f4f4f6;filter:drop-shadow(0 ${6 * u}px ${18 * u}px rgb(0 0 0 / .35))}
.word{margin-top:${36 * u}px;font-size:${104 * u}px;line-height:.9;letter-spacing:.01em;white-space:nowrap}
.tag{margin-top:${34 * u}px;font-size:${26 * u}px;letter-spacing:.38em;padding-left:.38em;opacity:.78;white-space:nowrap}
</style></head><body><div class="ident"><div class="mark">${mark}</div><div class="word">AKI LABS</div><div class="tag">${TAGLINE}</div></div></body></html>`;
};

const browser = await chromium.launch({
  executablePath: `${homedir()}/Library/Caches/ms-playwright/chromium_headless_shell-1255/chrome-headless-shell-mac-arm64/chrome-headless-shell`,
  args: ['--mute-audio', '--allow-file-access-from-files'],
});
try {
  for (const [name, bg] of Object.entries(VARIANTS)) {
    for (const [w, h] of SIZES) {
      const html = path.join(here, `.tmp-${name}-${w}x${h}.html`);
      writeFileSync(html, page(bg, w, h));
      const p = await browser.newPage({viewport: {width: w, height: h}});
      await p.goto(pathToFileURL(html).href);
      await p.evaluate(() => document.fonts.ready);
      await p.screenshot({path: path.join(here, `aki-labs-banner-${name}-${w}x${h}.png`)});
      await p.close();
    }
  }
} finally {
  await browser.close();
}
