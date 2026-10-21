#!/usr/bin/env python3
"""Convert resume.html to PDF using weasyprint with Chinese font support.

Runs on GitHub Actions (Ubuntu) where fonts-noto-cjk / fonts-wqy-zenhei
are pre-installed via apt.  Weasyprint uses fontconfig to resolve fonts,
so we only need to make sure the CSS font-family matches an installed font.

字体策略（按来源分级替换，不再全局重写）：
  * "Microsoft YaHei" / "PingFang SC" / "Hiragino Sans GB" / "SimHei"
      —— 这些是 Windows/macOS 专有字体，Linux 上不存在，替换成 fontconfig 里的 CJK 字体。
  * 其余族名（Cascadia Mono / Consolas / monospace 等）原样保留，
    weasyprint + fontconfig 会自行兜底，避免把等宽代码字体也刷成宋黑。

单页适配（fit-to-one-page）：
  WeasyPrint 的排版引擎与 Chrome 不同，同一份 HTML 在 Chrome 下是 1 页，
  在 WeasyPrint 下可能溢出到 2 页 —— 英文译文比中文长 40% 以上时尤其明显。
  旧版直接写 PDF 就提交，结果英文简历悄悄变成 2 页。
  现在渲染后检查页数，超过 1 页就按比例收缩正文字号重排，最多尝试 N 轮，
  全部失败则非 0 退出（宁可不产出，也不提交 2 页的简历）。
"""

import re
import subprocess
import sys

import weasyprint

# 只在「字体族列表」里替换这些专有族名，不触碰其他声明
PROPRIETARY_CJK = re.compile(
    r'"?\b(Microsoft\s*YaHei|微软雅黑|PingFang\s*SC|Hiragino\s+Sans\s+GB|SimHei|黑体)\b"?',
    re.I,
)

# font-family 声明整体匹配：font-family: <list>;  —— 逐条处理其中的族名
FONT_FAMILY_DECL = re.compile(r'(font-family\s*:\s*)([^;}]+)([;}])', re.I)

# body 的字号声明，用于单页适配时整体缩放
BODY_FONT_SIZE = re.compile(r'(body\s*\{[^}]*?font-size\s*:\s*)([\d.]+)(pt)', re.I | re.S)

# 收缩步进：每次乘以该系数，最多尝试这么多轮
SHRINK_STEP = 0.97
MAX_FIT_ROUNDS = 12
# 字号下限（9.5pt * 0.97^12 ≈ 6.6pt），再小就不可读了
MIN_FONT_PT = 6.5
# 行高收缩：lh_factor 是乘到现有 line-height 上的系数（必须 <= 1 才是压缩）。
# 行高先让出一部分空间，字号就能保住更大 —— 可读性优先。
# scale=0.88 时 lh_factor≈0.926，即 1.40 -> 1.30，仍然舒展。
LH_CURVE = 0.6
LH_FLOOR = 0.85  # 绝对下限：1.40 * 0.85 = 1.19，再低行间会粘连


def get_cjk_fonts():
    """Return a prioritised list of installed CJK font family names."""
    try:
        result = subprocess.run(
            ["fc-list", ":lang=zh", "family"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        print("ERROR: fc-list not found – install fontconfig", file=sys.stderr)
        return None

    raw = sorted(set(
        line.strip()
        for line in (result.stdout or "").strip().split("\n")
        if line and line.strip()
    ))
    if not raw:
        return None

    # Priority: Noto Sans CJK SC > WenQuanYi Micro Hei > WenQuanYi Zen Hei > others
    priority, others = [], []
    for f in raw:
        if "Noto Sans CJK SC" in f:
            priority.insert(0, f)
        elif "WenQuanYi Micro Hei" in f:
            priority.append(f)
        elif "WenQuanYi Zen Hei" in f:
            priority.append(f)
        else:
            others.append(f)
    return priority + others


def rewrite_font_family(css_list, cjk_chain):
    """Replace proprietary CJK family names inside one font-family value.

    Keeps every other family (monospace, Consolas, …) in its original order,
    then appends the CJK chain before the trailing generic family.
    """
    parts = [p.strip() for p in css_list.split(",") if p.strip()]
    had_proprietary = False
    kept = []
    for p in parts:
        if PROPRIETARY_CJK.search(p):
            had_proprietary = True
            continue
        kept.append(p)
    if not had_proprietary:
        return css_list  # 与 CJK 无关的声明原样返回

    # 把 CJK 链插到 generic family（sans-serif/serif/monospace）之前
    generic = {"sans-serif", "serif", "monospace", "-apple-system"}
    head = [p for p in kept if p.strip('"').lower() not in generic]
    tail = [p for p in kept if p.strip('"').lower() in generic]
    merged = head + [f'"{f}"' for f in cjk_chain] + tail
    # 去重但保序
    seen, out = set(), []
    for m in merged:
        if m.lower() not in seen:
            seen.add(m.lower())
            out.append(m)
    return ", ".join(out)


def get_body_font_pt(html, default=9.5):
    """从 CSS 里读出 body 的基准字号，避免硬编码。"""
    m = BODY_FONT_SIZE.search(html)
    return float(m.group(2)) if m else default


def scale_css_sizes(html, factor, lh_factor=None):
    """把 <style> 里的 pt 字号（以及可选的行高）按系数缩放。

    字号与行高一起收，比只收字号更划算：正文行高 1.40 收到 1.30 相当于
    又压掉 7% 高度，却不必把字号继续往下砍，可读性明显更好。
    间距（mm/px 的 margin、padding）不动 —— 它们是章节层级的载体。
    """
    if lh_factor is None:
        lh_factor = factor

    style_re = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.S | re.I)

    def repl(m):
        css = m.group(2)
        css = re.sub(
            r'(font-size\s*:\s*)([\d.]+)(pt)',
            lambda x: f'{x.group(1)}{float(x.group(2)) * factor:.3f}pt',
            css,
        )
        # 只收无单位行高（1.38 这类），带单位的行高另有含义，不动
        css = re.sub(
            r'(line-height\s*:\s*)([\d.]+)(\s*[;}])',
            lambda x: f'{x.group(1)}{float(x.group(2)) * lh_factor:.3f}{x.group(3)}',
            css,
        )
        return m.group(1) + css + m.group(3)

    return style_re.sub(repl, html)


def render_pages(html, base_url):
    """渲染并返回页数（不写盘）。"""
    doc = weasyprint.HTML(string=html, base_url=base_url).render()
    return len(doc.pages), doc


def fit_scale(html, base_url, base_pt):
    """逐级收缩，返回能压进单页的最小收缩系数（1.0 表示原样即可）。

    字号与行高走两条不同曲线：行高是字号的倍数，同倍收缩等于双重压缩，
    所以行高用更温和的指数（factor ** LH_CURVE）先让出空间，
    字号就能保住更大 —— 可读性优先。
    """
    pages, _ = render_pages(html, base_url)
    print(f"pages at scale 1.000: {pages}")
    if pages == 1:
        return 1.0

    scale = 1.0
    for _ in range(MAX_FIT_ROUNDS):
        nxt = scale * SHRINK_STEP
        if base_pt * nxt < MIN_FONT_PT:
            print(
                f"ERROR: 需缩到 {base_pt * nxt:.2f}pt（低于下限 {MIN_FONT_PT}pt）"
                f"才能进单页，正文确实过长，请精简内容",
                file=sys.stderr,
            )
            sys.exit(1)
        scale = nxt
        lh = max(LH_FLOOR, scale ** LH_CURVE)
        pages, _ = render_pages(scale_css_sizes(html, scale, lh), base_url)
        print(
            f"pages at scale {scale:.3f} "
            f"(body ~{base_pt * scale:.2f}pt, line-height x{lh:.3f}): {pages}"
        )
        if pages == 1:
            return scale

    print(
        f"ERROR: 尝试 {MAX_FIT_ROUNDS} 轮后仍有 {pages} 页，拒绝产出非单页简历",
        file=sys.stderr,
    )
    sys.exit(1)


def main():
    # Usage: python convert_to_pdf.py [input.html] [output.pdf]
    input_file = sys.argv[1] if len(sys.argv) > 1 else "resume.html"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "简历 钱佳宏.pdf"
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")

    fonts = get_cjk_fonts()
    if not fonts:
        print("ERROR: No CJK font found!", file=sys.stderr)
        sys.exit(1)

    print(f"Primary CJK font: {fonts[0]}")
    print(f"CJK chain: {', '.join(fonts[:3])}")

    with open(input_file, "r", encoding="utf-8") as f:
        html = f.read()

    # ── Step 1: 只替换专有 CJK 族名，保留等宽等其他字体 ──
    html, n = FONT_FAMILY_DECL.subn(
        lambda m: m.group(1) + rewrite_font_family(m.group(2), fonts[:3]) + m.group(3),
        html,
    )
    print(f"font-family declarations inspected: {n}")

    # ── Step 2: 单页适配 ──
    base_pt_orig = get_body_font_pt(html)
    print(f"base body font-size: {base_pt_orig}pt")
    scale = fit_scale(html, input_file, base_pt_orig)

    if scale < 1.0:
        lh = max(LH_FLOOR, scale ** LH_CURVE)
        print(
            f"[INFO] 已收缩到 {scale:.3f} 倍"
            f"（正文 {base_pt_orig * scale:.2f}pt，行高 x{lh:.3f}）以适配单页"
        )
    else:
        print("[INFO] 原始排版即为单页，无需缩放")

    # ── Step 3: 落盘 ──
    final_html = html if scale >= 1.0 else scale_css_sizes(html, scale, max(LH_FLOOR, scale ** LH_CURVE))
    temp_html = input_file.rsplit(".", 1)[0] + ".weasyprint.tmp.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Converting {temp_html} → PDF …")
    try:
        weasyprint.HTML(filename=temp_html, base_url=input_file).write_pdf(output_file)
    finally:
        import os
        try:
            os.remove(temp_html)
        except OSError:
            pass
    print("PDF generated successfully.")


if __name__ == "__main__":
    main()
