// 校验 A4 版式：真实 DOM 高度 vs 210mm x 297mm 纸张高度
// 用法: PW=/path/to/playwright node out/verify.mjs [项目根]
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
    // 全局 npm 安装（本机现状：playwright-core 为全局包）
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
const page = await browser.newPage({ viewport: { width: 900, height: 1200 } });
await page.goto(url, { waitUntil: 'load' });
await page.emulateMedia({ media: 'print' });

const r = await page.evaluate(() => {
  const sheet = document.querySelector('.page');
  const cs = getComputedStyle(sheet);
  const px2mm = (px) => Math.round((px / 96) * 25.4 * 100) / 100;
  const inner = sheet.clientHeight;                 // 含 padding
  const contentBottom = () => {
    const nodes = [...sheet.querySelectorAll('.section, .footer, .masthead')];
    return Math.max(...nodes.map((n) => n.getBoundingClientRect().bottom));
  };
  const sheetRect = sheet.getBoundingClientRect();
  const used = contentBottom() - sheetRect.top;
  return {
    sheetPx: { w: sheet.getBoundingClientRect().width, h: sheetRect.height },
    sheetBox: {
      wmm: px2mm(sheet.getBoundingClientRect().width),
      hmm: px2mm(sheetRect.height),
    },
    padTop: cs.paddingTop,
    padBottom: cs.paddingBottom,
    contentUsedMm: px2mm(used),
    contentUsedPx: Math.round(used),
    sheetClipped: used > inner + 0.5,
    overflowPx: Math.round(used - inner),
    fillPct: Math.round((used / sheetRect.height) * 1000) / 10,
    scrollOverflow: sheet.scrollHeight - sheet.clientHeight,
  };
});

console.log(JSON.stringify(r, null, 2));
await browser.close();
