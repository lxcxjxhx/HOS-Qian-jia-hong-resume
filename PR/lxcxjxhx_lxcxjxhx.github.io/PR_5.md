# feat: 去竖线导航 + GitHub 多维观测面板 + 页脚重构

**PR 链接**: [lxcxjxhx/lxcxjxhx.github.io#5](https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/5)
**状态**: Merged
**合并时间**: 2026-08-20T23:41:27Z
**创建时间**: 2026-08-20T23:41:19Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 274
- **删除行数**: 62
- **变更文件数**: 6
- **提交数**: 5

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `public/data/external.json` | MOD | +17 | -3 |
| `scripts/collect-external.mjs` | MOD | +31 | -2 |
| `src/App.tsx` | MOD | +77 | -16 |
| `src/data/pr_readme.ts` | MOD | +2 | -2 |
| `src/data/readme.ts` | MOD | +2 | -2 |
| `src/styles.css` | MOD | +145 | -37 |

## PR 描述

## 变更内容

### 1. 移除无用竖线导航
删除左侧「茎脉」竖线 + 圆点导航（.rail），页面更干净。

### 2. 丰富 GitHub 数据采集
采集器新增维度：following / publicGists / 总 Star / 总 Fork / top 语言 / 最高星仓库 / 账号年限。

### 3. GitHub 观测面板
「数据源」章节新增多维面板：7 项数值（Followers/Following/Repos/Gists/总 Star/总 Fork/账号）+ top languages 语言 chip + 最高星仓库直达链接。

### 4. 页脚重构
三栏布局（品牌 / 通道 / 数据快照）+ 底栏 colophon（HYACINTH.SIG · v2.0 / 致谢 / built by GitHub Actions）。

## 验证
- npm run build 通过（tsc + vite）
- 无头浏览器 DOM 验证：观测面板（数值/语言/HOS-Forge 仓库）、新页脚、rail 已移除均确认

## 相关链接

- **源仓库**: [lxcxjxhx/lxcxjxhx.github.io](https://github.com/lxcxjxhx/lxcxjxhx.github.io)
- **PR 链接**: https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/5
- **Diff**: https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/5.diff

---
*Auto-generated at 2026-09-11 02:51:30 UTC*
