// 检查开源列表每行是否单行渲染（无折行）、各列是否在同一基线
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
const page = await browser.newPage({ viewport: { width: 794, height: 1123 } });
await page.goto(pathToFileURL(path.join(root, 'index.html')).href, { waitUntil: 'load' });
await page.emulateMedia({ media: 'print' });

const rows = await page.evaluate(() => {
  const mm = (px) => Math.round((px / 96) * 25.4 * 100) / 100;
  return [...document.querySelectorAll('.prs li')].map((li) => {
    const cells = ['repo', 'star', 'pr', 'desc'].map((c) => {
      const el = li.querySelector('.' + c);
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const lh = parseFloat(cs.lineHeight);
      return {
        cell: c,
        text: el.textContent.trim().slice(0, 28),
        lines: Math.round(r.height / lh),
        widthMm: mm(r.width),
        scrollW: el.scrollWidth,
        clientW: el.clientWidth,
        clipped: el.scrollWidth > el.clientWidth + 1,
      };
    });
    return { itemH: mm(li.getBoundingClientRect().height), cells };
  });
});

const bad = [];
rows.forEach((r, i) => {
  r.cells.forEach((c) => {
    if (c.lines > 1) bad.push(`行${i + 1} ${c.cell} 折行 ${c.lines} 行: ${c.text}`);
    if (c.clipped) bad.push(`行${i + 1} ${c.cell} 被截断 (ellipsis): ${c.text}`);
  });
});

console.log('每行高度(mm):', rows.map((r) => r.itemH).join(', '));
console.log(bad.length ? '问题:\n' + bad.join('\n') : '全部单行且无截断 ✔');
await browser.close();
