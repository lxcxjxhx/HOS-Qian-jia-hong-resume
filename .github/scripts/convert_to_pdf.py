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

    # ── Step 2: 写临时文件并转换（同目录，保证相片等相对路径可解析）──
    temp_html = input_file.rsplit(".", 1)[0] + ".weasyprint.tmp.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html)

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
