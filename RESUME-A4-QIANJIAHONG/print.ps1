# A4 简历打印脚本：无头 Chrome 导出，强制 A4、无页眉页脚、100% 缩放
#
# 修订要点（对照旧版缺陷）：
#   1. 先删旧 PDF         —— 旧版不删，文件被占用时 Chrome 静默失败，脚本仍报 OK
#   2. 校验写入时间       —— 旧版只看 Test-Path，无法发现"没真正生成"
#   3. 校验产物体积下限   —— 防止写入 0 字节或残缺文件也被判成功
#   4. 默认不自动打开     —— 旧版 Invoke-Item 会用 Edge 占用 PDF，导致下次无法覆盖
#   5. 使用 -LiteralPath  —— 中文路径安全
#   6. 让 Chrome 以独立用户目录运行，避免复用正在运行的实例而静默退出

param(
  [switch]$Open,                     # 需要打开时显式加 -Open
  [string]$OutFile = 'out\resume-a4.pdf'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# ---------- 定位浏览器 ----------
$chrome = @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $chrome) { throw '未找到 Chrome / Edge 可执行文件' }

$src  = Join-Path $root 'index.html'
if (-not (Test-Path -LiteralPath $src)) { throw "源文件不存在: $src" }

$pdf  = Join-Path $root $OutFile
$pdfDir = Split-Path -Parent $pdf
New-Item -ItemType Directory -Force -Path $pdfDir | Out-Null

# ---------- 1. 清理旧产物，并确认真的删掉了 ----------
if (Test-Path -LiteralPath $pdf) {
  try {
    Remove-Item -LiteralPath $pdf -Force
  } catch {
    throw "旧 PDF 被占用，无法覆盖。请关闭正在查看该 PDF 的窗口后重试。`n$($_.Exception.Message)"
  }
  if (Test-Path -LiteralPath $pdf) { throw "旧 PDF 删除失败，仍占位: $pdf" }
}

# ---------- 2. 导出 ----------
$url  = ([uri]$src).AbsoluteUri
$profileDir = Join-Path $env:TEMP ("resume-chrome-" + [guid]::NewGuid().ToString('N').Substring(0,8))

$args = @(
  '--headless=new'
  '--disable-gpu'
  '--no-pdf-header-footer'
  '--no-first-run'
  '--no-default-browser-check'
  "--user-data-dir=$profileDir"
  '--virtual-time-budget=5000'
  "--print-to-pdf=$pdf"
  $url
)

# 走 cmd 包一层：Chrome 会把进度日志写入 stderr，PS 5.1 会误判为 NativeCommandError
$argLine = ($args | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
$cmdLine = '"' + $chrome + '" ' + $argLine + ' 2>nul'
$null = cmd /c $cmdLine

# ---------- 3. 产物校验（旧版缺失的关键环节）----------
if (-not (Test-Path -LiteralPath $pdf)) {
  throw "导出失败：PDF 未生成。Chrome 可能因复用运行中实例而静默退出。"
}

$file = Get-Item -LiteralPath $pdf
if ($file.Length -lt 50KB) {
  throw "导出异常：PDF 仅 $([math]::Round($file.Length/1KB))KB，疑似残缺文件。"
}

# 新生成的文件必然晚于源文件，否则说明写的是旧内容
$srcTime = (Get-Item -LiteralPath $src).LastWriteTime
if ($file.LastWriteTime -lt $srcTime) {
  throw "时间戳异常：PDF($($file.LastWriteTime)) 早于 index.html($srcTime)，说明未重新生成。"
}

# 页数校验：以 /Type /Pages 对象里的 /Count 为准。
# 不用 /Type /Page[^s] 正则计数——它依赖压缩流的可读性，Skia 压缩对象字典时会漏数，
# 曾导致"多页文档被误判为 1 页"的假阴性（已用双页样张实测复现）。
$bytes = [IO.File]::ReadAllBytes($pdf)
$raw   = [Text.Encoding]::GetEncoding(28591).GetString($bytes)
$box   = [regex]::Match($raw, '/MediaBox\s*\[\s*([\d\.\-]+)\s+([\d\.\-]+)\s+([\d\.\-]+)\s+([\d\.\-]+)\s*\]')

# 根节点 Pages 对象：/Type /Pages ... /Count N（树根的 Count = 总页数，与压缩无关）
$pages = 0
[regex]::Matches($raw, '/Type\s*/Pages[\s\S]{0,400}?/Count\s+(\d+)') | ForEach-Object {
  $n = [int]$_.Groups[1].Value
  if ($n -gt $pages) { $pages = $n }   # 取最大值即根节点
}
if ($pages -eq 0) { $pages = ([regex]::Matches($raw, '/Type\s*/Page[^s]')).Count }  # 兜底
if ($pages -ne 1) { throw "页数异常：期望 1 页，实际 $pages 页。内容可能溢出 A4。" }

$sizeNote = 'MediaBox 未解析'
if ($box.Success) {
  $wmm = [math]::Round([double]$box.Groups[3].Value / 72 * 25.4, 2)
  $hmm = [math]::Round([double]$box.Groups[4].Value / 72 * 25.4, 2)
  if ([math]::Abs($wmm - 210) -gt 1 -or [math]::Abs($hmm - 297) -gt 1) {
    throw "纸张异常：${wmm}mm x ${hmm}mm，不是 A4。"
  }
  $sizeNote = "${wmm}mm x ${hmm}mm"
}

Remove-Item -LiteralPath $profileDir -Recurse -Force -ErrorAction SilentlyContinue

$kb = [math]::Round($file.Length / 1KB)
Write-Host "OK  $pdf" -ForegroundColor Green
Write-Host "    大小 ${kb}KB | 页数 $pages | 纸张 $sizeNote | 生成于 $($file.LastWriteTime.ToString('HH:mm:ss'))"

if ($Open) { Invoke-Item -LiteralPath $pdf }
