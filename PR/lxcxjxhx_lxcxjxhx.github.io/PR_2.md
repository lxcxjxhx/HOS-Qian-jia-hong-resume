# feat: 外部数据管线 + 导航常规化（数据及时同步）

**PR 链接**: [lxcxjxhx/lxcxjxhx.github.io#2](https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/2)
**状态**: Merged
**合并时间**: 2026-08-20T22:53:50Z
**创建时间**: 2026-08-20T22:53:43Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 1304
- **删除行数**: 3013
- **变更文件数**: 30
- **提交数**: 2

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `.github/workflows/deploy.yml` | MOD | +17 | -6 |
| `README.md` | MOD | +45 | -8 |
| `index.html` | MOD | +10 | -3 |
| `package-lock.json` | MOD | +208 | -1633 |
| `package.json` | MOD | +4 | -14 |
| `public/data/external.json` | NEW | +56 | -0 |
| `public/illustrations/blog-header.jpg` | DEL | +0 | -0 |
| `public/illustrations/hero-decoration.jpg` | DEL | +0 | -0 |
| `public/illustrations/projects-header.jpg` | DEL | +0 | -0 |
| `public/illustrations/research-header.jpg` | DEL | +0 | -0 |
| `scripts/collect-external.mjs` | NEW | +104 | -0 |
| `scripts/fetch-csdn-data.mjs` | DEL | +0 | -183 |
| `scripts/fetch-github-data.mjs` | DEL | +0 | -167 |
| `scripts/fetch-resume-data.mjs` | NEW | +56 | -0 |
| `src/App.tsx` | MOD | +439 | -52 |
| `src/components/FlowerCanvas.tsx` | NEW | +125 | -0 |
| `src/components/Markdown.tsx` | NEW | +240 | -0 |
| `src/components/effects/CanvasBackground.tsx` | DEL | +0 | -233 |
| `src/components/layout/Container.tsx` | DEL | +0 | -25 |
| `src/components/layout/Footer.tsx` | DEL | +0 | -52 |
| `src/components/layout/Header.tsx` | DEL | +0 | -91 |
| `src/components/sections/AboutSection.tsx` | DEL | +0 | -98 |
| `src/components/sections/BlogSection.tsx` | DEL | +0 | -53 |
| `src/components/sections/HeroSection.tsx` | DEL | +0 | -53 |
| `src/components/sections/ProjectsSection.tsx` | DEL | +0 | -60 |
| `src/components/sections/ResearchSection.tsx` | DEL | +0 | -55 |
| `src/components/ui/AnimatedNumber.tsx` | DEL | +0 | -57 |
| `src/components/ui/Badge.tsx` | DEL | +0 | -70 |
| `src/components/ui/Card.tsx` | DEL | +0 | -82 |
| `src/components/ui/FloatingWidget.tsx` | DEL | +0 | -18 |

## PR 描述

## 变更内容

1. **导航常规化**：右上角改为 关于 / 项目 / 专栏 / 开源 / 领域 / 成就 / 数据源，便于浏览与翻找
2. **外部数据管线**：新增 scripts/collect-external.mjs，逐源采集 GitHub / HuggingFace / PyPI / CSDN RSS，单源容错（失败保留旧值）
3. **自动同步**：deploy.yml 升级为 Build, Sync Data & Deploy —— cron 每 6 小时 + 推送自动 采集 → 刷新 resume 内嵌 → 构建 → 发布
4. **站点展示**：运行时读取 ./data/external.json（同源防缓存），「数据源」章节新增外部数据 live 卡片，「温室」章节新增最新博文 RSS 同步条
5. **私有数据中枢**：新建私有仓库 HOS-BLOG-DATA 作为外部数据采集与存储中心（cron 快照存储、保留历史），后续更多数据搜集需求统一在此管理

## 验证

- npm run build 通过（tsc + vite）
- 无头浏览器 DOM 验证：导航标签、最新博文（真实 RSS 数据）、外部数据 live 卡片、termbar 数据状态均正常渲染
- 站点「数据源」章节实时直连 HOS-Qian-jia-hong-resume 仓库校验通过

## 相关链接

- **源仓库**: [lxcxjxhx/lxcxjxhx.github.io](https://github.com/lxcxjxhx/lxcxjxhx.github.io)
- **PR 链接**: https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/2
- **Diff**: https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/2.diff

---
*Auto-generated at 2026-09-10 02:57:23 UTC*
