// 逐块位置探针：输出每个区块相对纸张顶部的 mm 位置，检查底部对齐
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
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 900, height: 1200 } });
await page.goto(pathToFileURL(path.join(root, 'index.html')).href, { waitUntil: 'load' });
await page.emulateMedia({ media: 'print' });

const r = await page.evaluate(() => {
  const mm = (px) => Math.round((px / 96) * 25.4 * 100) / 100;
  const sheet = document.querySelector('.page');
  const s = sheet.getBoundingClientRect();
  const blocks = [];
  document.querySelectorAll('.masthead, .section, .footer').forEach((n) => {
    const b = n.getBoundingClientRect();
    const h2 = n.querySelector('h2');
    blocks.push({
      block: (h2 ? h2.textContent.trim().slice(0, 10) : n.className),
      topMm: mm(b.top - s.top),
      bottomMm: mm(b.bottom - s.top),
      heightMm: mm(b.height),
    });
  });
  const foot = document.querySelector('.footer').getBoundingClientRect();
  return {
    sheetHeightMm: mm(s.height),
    footerBottomMm: mm(foot.bottom - s.top),
    tailGapMm: mm(s.height - (foot.bottom - s.top)),
    blocks,
  };
});

console.log(JSON.stringify(r, null, 2));
await browser.close();
