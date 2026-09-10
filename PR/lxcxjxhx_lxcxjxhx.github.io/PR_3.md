# feat: 首页观测台重构 + 数据中枢多域 SQLite 文件管理

**PR 链接**: [lxcxjxhx/lxcxjxhx.github.io#3](https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/3)
**状态**: Merged
**合并时间**: 2026-08-20T23:16:51Z
**创建时间**: 2026-08-20T23:16:44Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 492
- **删除行数**: 80
- **变更文件数**: 7
- **提交数**: 1

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `README.md` | MOD | +1 | -1 |
| `scripts/collect-external.mjs` | MOD | +85 | -34 |
| `src/App.tsx` | MOD | +100 | -27 |
| `src/components/FlowerCanvas.tsx` | MOD | +77 | -14 |
| `src/data/pr_readme.ts` | MOD | +2 | -2 |
| `src/data/readme.ts` | MOD | +2 | -2 |
| `src/styles.css` | MOD | +225 | -0 |

## PR 描述

## 变更内容

### 首页重构为「安全风信子观测台」（告别模板化居中 Hero）
- **非对称布局**：左侧品牌区（大字渐变标题 + 数字滚动统计），右侧旋转光环装饰 + 交互提示
- **终端开机日志**：boot sequence 逐行淡入，数据驱动实时状态（seed_db 直连 / sources live 数 / 数据日期）
- **数据跑马灯**：最新博文 + 统计数字无缝滚动（数据来自 external.json），hover 暂停，点击直达原文
- **可交互花丛**：光标移动花茎随之倾斜，点击激起花粉迸射（Canvas）
- **氛围层**：点阵网格 + 扫描线 + 光晕叠层；章节头部加 \\$ ls garden/<id>\ 终端风标签

### 数据中枢文件管理规范化（HOS-BLOG-DATA）
- 采集器 \HOS_DB\ → \HOS_DB_DIR\：每个数据域一个 SQLite 库文件（SOURCE_DB 映射自动建库）
- data 子分支目录约定：\db/<数据域>.db\ + \export/\ + \rchive/\ + \manifest.json\（数据库台账：库名/文件/来源/schema 版本/更新时间）
- 库内统一表结构：meta + latest + history（数据湖），schema 版本化管理

## 验证
- npm run build 通过（tsc + vite）
- 无头浏览器 DOM 验证：光环/终端日志/跑马灯/交互提示/\$ ls 标签全部渲染
- 数据中枢：data 分支 db/external.db（meta+latest+history）+ manifest.json 台账验证通过

## 相关链接

- **源仓库**: [lxcxjxhx/lxcxjxhx.github.io](https://github.com/lxcxjxhx/lxcxjxhx.github.io)
- **PR 链接**: https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/3
- **Diff**: https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/3.diff

---
*Auto-generated at 2026-09-10 02:57:23 UTC*
