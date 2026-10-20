// 截图预览：屏幕版整页 + 打印版整页，用于视觉验收
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(resolvePlaywright());

function resolvePlaywright() {
  const candidates = [
    process.env.PW,
    'playwright',
    'playwright-core',
    process.env.APPDATA && path.join(process.env.APPDATA, 'npm/node_modules/playwright-core'),
  ].filter(Boolean);
  for (const c of candidates) {
    try { return require.resolve(c); } catch { /* try next */ }
  }
  throw new Error('未找到 playwright，设置 PW 环境变量指向其 index.js');
}

const root = path.resolve(process.argv[2] ?? '.');
const url = pathToFileURL(path.join(root, 'index.html')).href;

const browser = await chromium.launch();

// 屏幕预览
const p1 = await browser.newPage({ viewport: { width: 1000, height: 1300 }, deviceScaleFactor: 2 });
await p1.goto(url, { waitUntil: 'load' });
await p1.locator('.page').screenshot({ path: path.join(root, 'out/screen.png') });

// 打印预览（模拟真实打印媒体）
const p2 = await browser.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
await p2.goto(url, { waitUntil: 'load' });
await p2.emulateMedia({ media: 'print' });
await p2.locator('.page').screenshot({ path: path.join(root, 'out/print.png') });

await browser.close();
console.log('shots written');
