# 打印 / 导出说明

## 结论先说

`index.html` 和 `out/resume-a4.pdf` 是**同一套排版**，实测两边纸张都是 210×297mm、姓名字号都是 17.5pt。

看起来"两回事情"，只有一个原因：**打开方式不同**。

## 两种打开方式的差异

| 方式 | 背景 | 结果 |
|---|---|---|
| 双击 `index.html` | 深灰 `rgb(111,122,134)` | 屏幕媒体渲染，灰底衬托白纸，仅供预览 |
| `print.ps1` 导出 | 纯白 | 强制 A4、无页眉页脚、缩放 100%，**这是准的** |

## 手动 Ctrl+P 的四个坑（会导致和屏幕不一致）

1. **纸张**：默认可能是 Letter，必须在"更多设置 → 纸张尺寸"选 **A4**
2. **缩放**：默认可能不是 100%，会导致内容缩水或溢出，必须设 **默认 / 100%**
3. **边距**：必须选 **无**（留白已由 CSS 的 padding 控制，选"默认"会二次加边距）
4. **页眉和页脚**：必须**取消勾选**，否则会多出网址、日期、页码

## 推荐做法

不要用 Ctrl+P，直接跑：

```powershell
.\print.ps1                 # -> out\resume-a4.pdf
.\print.ps1 -Out "out\钱佳宏 个人简历.pdf"   # 投递用的正式文件名
```

它用无头 Chrome，绕开以上全部四坑。

**编辑器保存陷阱**：`print.ps1` 含中文抛错文案，必须以 **UTF-8 with BOM** 保存。无 BOM 时 Windows PowerShell 5.1 按 GBK 解析，会直接 `Unexpected token` 报错。

## 版面自检

三个脚本都会自动在 `PW` → 本地 `playwright` → `playwright-core` → 全局 npm 目录里找浏览器驱动，**无需先设 `$env:PW`**；找不到时才报错提示。

```powershell
node out\verify.mjs .      # 填充率、是否裁切（sheetClipped / overflowPx / fillPct）
node out\probe.mjs .       # 逐块 mm 定位，看页脚是否贴底（tailGapMm）
node out\check-rows.mjs .  # 开源列表是否折行/截断
```

判定口径：`sheetClipped=false`、`tailGapMm ≈ 0`、rows 全绿 = 版面合格。

## 当前版面基线（实测）

- 纸张：210mm × 297mm，填充率 **99.7%**
- 页脚距纸底：**0.94mm**
- 页数：1 页，无裁切（`overflowPx = -4`，还有 4px 余量）
- 开源贡献 7 行全部单行、无省略号截断
- 姓名字号 17.5pt，章节标题 10.2pt，正文 9.05pt，行距 1.58
