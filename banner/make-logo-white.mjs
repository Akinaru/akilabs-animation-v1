// White Aki Labs logo on a transparent 500x500: the mark alone, and the mark with AKI LABS under it.
// Usage: node make-logo-white.mjs (from aki-labs-brand/banner). Silent headless browser, closed in finally.
import {readFileSync, writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {homedir} from 'node:os';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.resolve(here, '../../AdrenaForge/noop.js'));
const {chromium} = require('playwright-core');
const mark = readFileSync(path.resolve(here, '../logo-mark/final/aki-mark.svg'), 'utf8').replace(/<!--[\s\S]*?-->/g, '');
const font = pathToFileURL(path.resolve(here, '../fonts/ArchivoBlack-Regular.ttf')).href;
const S = 500;

const page = (withWord) => `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'Aki Archivo Black';src:url('${font}')}
html,body{margin:0;width:${S}px;height:${S}px;overflow:hidden;background:transparent}
body{display:grid;place-items:center;font-family:'Aki Archivo Black',sans-serif;color:#fff}
.ident{display:flex;flex-direction:column;align-items:center}
.mark{height:${withWord ? 300 : 420}px;width:${(withWord ? 300 : 420) * 0.8344}px}
.mark svg{width:100%;height:100%;fill:#fff;display:block}
.word{margin-top:34px;font-size:78px;line-height:.9;letter-spacing:.01em;white-space:nowrap}
</style></head><body><div class="ident"><div class="mark">${mark}</div>${withWord ? '<div class="word">AKI LABS</div>' : ''}</div></body></html>`;

const browser = await chromium.launch({
  executablePath: `${homedir()}/Library/Caches/ms-playwright/chromium_headless_shell-1255/chrome-headless-shell-mac-arm64/chrome-headless-shell`,
  args: ['--mute-audio', '--allow-file-access-from-files'],
});
try {
  for (const [name, withWord] of [['aki-labs-logo-white-500', false], ['aki-labs-logo-white-wordmark-500', true]]) {
    const html = path.join(here, `.tmp-${name}.html`);
    writeFileSync(html, page(withWord));
    const p = await browser.newPage({viewport: {width: S, height: S}});
    await p.goto(pathToFileURL(html).href);
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({path: path.join(here, `${name}.png`), omitBackground: true});
    await p.close();
  }
} finally {
  await browser.close();
}
