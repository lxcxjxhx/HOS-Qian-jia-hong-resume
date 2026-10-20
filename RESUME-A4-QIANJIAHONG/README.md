# RESUME-A4-QIANJIAHONG — 钱佳宏单页 A4 简历

独立项目文件夹，基于 [HOS-Qian-jia-hong-resume/resume.html](https://github.com/lxcxjxhx/HOS-Qian-jia-hong-resume/blob/main/resume.html) 重建版式。

## 文件结构

```
RESUME-A4-QIANJIAHONG/
├── index.html         简历正文（内容与原版一致 + 新增学校/专业）
├── src/style.css      版式样式，所有调参集中在顶部 :root
├── assets/photo.jpg   证件照（从原 HTML base64 抽出，285x373）
├── print.ps1          一键导出 out/resume-a4.pdf
├── out/               产物：PDF + 截图 + 校验脚本
├── PRINT.md           打印/导出的坑与自检口径
└── README.md
```

## 与原版的差异

1. **学校 / 专业**：原版只有 `学历：本科在读`，现头部信息表新增 `上海建桥学院`、`计算机科学与技术（计科）· 本科在读 · 2028 届`。
2. **A4 铺满**：`.page` 固定 210mm x 297mm，`overflow:hidden` 强制单页；实测填充率 99.7%，页脚距纸底 0.94mm，无裁切。
3. **版式升级**：去深色标题条改为「左竖线 + 章节标题 + 细延伸线」；信息表改两列网格；开源 PR 列表四段定宽排布省纵向空间；页脚横线钉底。
4. **证件照外置**：不再内嵌 base64，HTML 体积从 ~2MB 降至 ~9.5KB。

## 调参（src/style.css :root）

| 变量 | 作用 | 当前值 |
|---|---|---|
| `--fs-body` | 正文全字号基准 | 9.05pt |
| `--lh-body` | 行距 | 1.58 |
| `--pad-y` / `--pad-x` | 纸张留白 | 10mm / 14mm |

内容再增删时若溢出，先降 `--lh-body` 到 1.45，再降 `--fs-body` 到 8.9pt。

## 使用

```powershell
.\print.ps1            # 导出 out\resume-a4.pdf（-Open 才自动打开）
node out\verify.mjs .  # 校验单页/填充率
node out\check-rows.mjs .
```

校验脚本自动定位 playwright（`PW` 环境变量 → 本地包 → 全局 `playwright-core`），不需要预先配置。详见 [PRINT.md](./PRINT.md)。
