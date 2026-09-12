# feat: 首页重构为海报式 SOC 信号分析台（去模板化）

**PR 链接**: [lxcxjxhx/lxcxjxhx.github.io#4](https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/4)
**状态**: Merged
**合并时间**: 2026-08-20T23:30:43Z
**创建时间**: 2026-08-20T23:30:35Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 289
- **删除行数**: 28
- **变更文件数**: 6
- **提交数**: 3

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `src/App.tsx` | MOD | +38 | -17 |
| `src/components/FlowerCanvas.tsx` | MOD | +1 | -1 |
| `src/data/pr_readme.ts` | MOD | +2 | -2 |
| `src/data/readme.ts` | MOD | +2 | -2 |
| `src/data/static.ts` | MOD | +6 | -6 |
| `src/styles.css` | MOD | +240 | -0 |

## PR 描述

## 首页去模板化 —— 海报式 SOC 信号分析台

彻底放弃「居中标题 + 按钮 + 统计卡片」的常规落地页套路，改为编辑海报 × 安全运营中心（SOC）仪表盘：

- **海报式排版**：旋转 -2° 的流光渐变大字标题 + 巨大的描边水印「风信子」叠在字后
- **声呐雷达**：右上实时扫描（conic-gradient 旋转），中心显示实时数据源数
- **竖向信号仪表**：六项统计改为竖向信号柱（EQ 风格），数字滚动 + 量程比例填充
- **机密章戳**：TOP SECRET // 观测站 01、HYACINTH.SIG · v2.0 旋转贴角
- **扫描线**：一条亮线自上而下循环滑过，SOC 屏幕质感
- 花茎移到中部「信号源」位置，标题与仪表之间的负空间露出交互花丛（光标倾斜/点击花粉）

## 验证
- npm run build 通过（tsc + vite）
- 无头浏览器 DOM 验证：水印/雷达/仪表/章戳/扫描线全部渲染

## 相关链接

- **源仓库**: [lxcxjxhx/lxcxjxhx.github.io](https://github.com/lxcxjxhx/lxcxjxhx.github.io)
- **PR 链接**: https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/4
- **Diff**: https://github.com/lxcxjxhx/lxcxjxhx.github.io/pull/4.diff

---
*Auto-generated at 2026-09-12 02:59:49 UTC*
