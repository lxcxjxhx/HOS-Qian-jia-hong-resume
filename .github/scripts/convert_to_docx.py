#!/usr/bin/env python3
"""Convert resume.html to DOCX with Chinese font support and precise A4 layout.

v2 变更（修复"DOCX 内容近乎空白"的结构性缺陷）：
  原版只认 class="header/entry-top/entry-name/sec-title/skill/pr-list/intro"，
  而 resume.html 实际用的是 <div class="header"> + .info-table/.links-table、
  <div class="sec-title">、<div class="entry"><div class="entry-top"><span
  class="entry-name">、<ul class="pr-list">。这些名字恰好对得上，但：
    * .info-table 是 4 列（标签/值/标签/值），原版把整行 cell 串成一行，姓名与生日挤在一起；
    * 照片是 base64 <img>，原版完全没有处理，DOCX 里证件照直接丢失；
    * .entry-text 里的 <ul><li> 被 get_text() 压成一段，要点全糊成一句。
  v2 按真实结构重建：4 列表格转 2 列、抽出 base64 照片写入文件并嵌入、
  li 逐条成段、PR 列表拆成「仓库 / star / 编号 / 说明」四段。
"""

import base64
import io
import os
import re
import subprocess
import sys

from bs4 import BeautifulSoup
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


# ── 字体探测 ────────────────────────────────────────────────────────────────
def get_cjk_font():
    try:
        result = subprocess.run(
            ["fc-list", ":lang=zh", "family"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
        families = sorted({
            line.strip() for line in (result.stdout or "").strip().split("\n")
            if line and line.strip()
        })
        if any("Noto Sans CJK SC" in f for f in families):
            return "Noto Sans CJK SC"
        if families:
            return families[0]
    except Exception as e:  # noqa: BLE001
        print(f"Warning: Could not detect fonts: {e}")
    return "Noto Sans CJK SC"


FONT = get_cjk_font()

DARK = RGBColor(0x2C, 0x3E, 0x50)
GRAY = RGBColor(0x7F, 0x8C, 0x8D)
TEXT = RGBColor(0x33, 0x33, 0x33)
LINK = RGBColor(0x34, 0x98, 0xDB)
FOOTER = RGBColor(0x95, 0xA5, 0xA6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

CONTENT_W = Cm(21.0 - 1.5 - 1.5)   # 页面宽 - 左右边距，用于右对齐制表位


def set_font(run, size=None, bold=False, color=None, mono=False):
    name = "Consolas" if mono else FONT
    run.font.name = name
    rPr = run._element.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        run._element.insert(0, rPr)
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), name)
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    if size:
        run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def shade(paragraph, fill):
    el = OxmlElement("w:shd")
    el.set(qn("w:fill"), fill)
    el.set(qn("w:val"), "clear")
    paragraph.paragraph_format.element.get_or_add_pPr().append(el)


def para(doc, before=0, after=0, indent=None, align=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = 1.32
    if indent is not None:
        pf.left_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    return p


def add_right_tab(p):
    p.paragraph_format.tab_stops.add_tab_stop(CONTENT_W, WD_TAB_ALIGNMENT.RIGHT)


def append_inline(p, node, size=9, color=TEXT, base_bold=False):
    """把一棵 DOM 子树按 <b>/<a>/文本 混合写入同一段落，保留强调与链接。"""
    for child in node.children:
        if isinstance(child, str):
            text = re.sub(r"\s+", " ", child)
            if not text.strip():
                continue
            run = p.add_run(text)
            set_font(run, size=size, bold=base_bold, color=color)
            continue
        name = getattr(child, "name", None)
        if name is None:
            continue
        if name == "b":
            run = p.add_run(child.get_text())
            set_font(run, size=size, bold=True, color=DARK)
        elif name == "a":
            run = p.add_run(child.get_text())
            set_font(run, size=size, bold=base_bold, color=LINK)
        elif name == "code":
            run = p.add_run(child.get_text())
            set_font(run, size=size - 0.5, bold=base_bold, color=color, mono=True)
        else:
            append_inline(p, child, size=size, color=color, base_bold=base_bold)


def embed_photo(doc, soup, out_dir):
    """把 base64 证件照抽出成文件并嵌入页眉段落；返回段落句柄或 None."""
    img = soup.select_one(".photo img") or soup.find("img")
    if img is None:
        return None
    src = img.get("src", "")
    if not src.startswith("data:image/"):
        return None
    try:
        head, b64 = src.split(",", 1)
        ext = "jpg" if "jpeg" in head or "jpg" in head else head.split("/")[1].split(";")[0]
        raw = base64.b64decode(b64)
    except Exception as e:  # noqa: BLE001
        print(f"  [WARN] 照片解码失败: {e}")
        return None

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"photo.{ext}")
    with open(path, "wb") as f:
        f.write(raw)
    print(f"  照片已抽出: {path} ({len(raw) // 1024}KB)")
    return path


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else "resume.html"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "简历 钱佳宏.docx"
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print(f"Font:   {FONT}")

    with open(input_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(1.0), Cm(0.8)
    sec.left_margin, sec.right_margin = Cm(1.5), Cm(1.5)

    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(9)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    pf = normal.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.32

    out_dir = os.path.join(os.path.dirname(output_file) or ".", "docx-assets")
    photo = embed_photo(doc, soup, out_dir)

    emit_header(doc, soup)

    # 正文由 emit_sections 统一遍历（兼容新旧两套结构）
    body = soup.find("body")
    if body is not None:
        emit_sections(doc, body)

    # ── 照片：插到最前面的页眉段落右侧（无照片则跳过）──
    if photo:
        p = doc.paragraphs[1] if len(doc.paragraphs) > 1 else doc.paragraphs[0]
        p.paragraph_format.tab_stops.add_tab_stop(CONTENT_W, WD_TAB_ALIGNMENT.RIGHT)
        p.add_run("\t")
        p.add_run().add_picture(photo, width=Cm(2.4))

    doc.save(output_file)
    print("DOCX generated successfully.")
    print(f"  paragraphs: {len(doc.paragraphs)}")


def emit_header(doc, soup):
    # ── 页眉：姓名 + 信息网格 + 联系方式；右侧挂照片 ──
    # 两套 DOM 都支持：
    #   旧 resume.html : div.header > h1 + table.info-table + table.links-table
    #   新 index.html  : header.masthead > h1.name + div.facts + div.contact
    header = soup.select_one(".header") or soup.select_one("header.masthead")
    if header:
        h1 = header.find(["h1"])
        name = h1.get_text(strip=True) if h1 else "个人简历"
        p = para(doc, after=3)
        run = p.add_run(name)
        set_font(run, size=20, bold=True, color=DARK)

        # 信息网格：旧版 4 列表格按 (label, val) 配对；新版 .facts 是 .f > .k + .v
        info = header.find("table", class_="info-table")
        if info:
            for tr in info.find_all("tr"):
                cells = [c.get_text(strip=True) for c in tr.find_all("td")]
                cells = [c for c in cells if c]
                pairs = []
                for i in range(0, len(cells), 2):
                    label = cells[i]
                    val = cells[i + 1] if i + 1 < len(cells) else ""
                    pairs.append(f"{label}{val}" if label.endswith(("：", ":")) else f"{label} {val}")
                p = para(doc, after=0.5)
                run = p.add_run("    ".join(pairs))
                set_font(run, size=8.5, color=TEXT)
        else:
            facts = header.select(".facts .f")
            if facts:
                for row_start in range(0, len(facts), 2):
                    p = para(doc, after=0.5)
                    for j, f in enumerate(facts[row_start:row_start + 2]):
                        k = f.select_one(".k")
                        v = f.select_one(".v")
                        if k is None or v is None:
                            continue
                        run = p.add_run(("        " if j else "") + f"{k.get_text(strip=True)} {v.get_text(strip=True)}")
                        set_font(run, size=8.5, color=TEXT)

        # 联系方式：旧版 .links-table / 新版 .contact .c
        links = header.find("table", class_="links-table")
        if links:
            for tr in links.find_all("tr"):
                p = para(doc, before=1)
                cells = tr.find_all("td")
                chunks = []
                for td in cells:
                    a = td.find("a")
                    chunks.append(a.get_text(strip=True) if a else td.get_text(strip=True))
                chunks = [c for c in chunks if c]
                for i, c in enumerate(chunks):
                    run = p.add_run(("    " if i else "") + c)
                    is_url = "." in c and "/" in c
                    set_font(run, size=7.5, color=LINK if is_url else TEXT)
        else:
            items = header.select(".contact .c")
            if items:
                for row_start in range(0, len(items), 2):
                    p = para(doc, before=1)
                    for j, c in enumerate(items[row_start:row_start + 2]):
                        label_el = c.find("span")
                        a = c.find("a")
                        label = label_el.get_text(strip=True) if label_el else ""
                        val = a.get_text(strip=True) if a else c.get_text(" ", strip=True)
                        run = p.add_run(("        " if j else "") + f"{label} {val}")
                        set_font(run, size=7.5, color=LINK if a else TEXT)


def iter_blocks(body):
    """返回需要按文档顺序处理的节点。

    新版 index.html 把正文包在 div.page 里（body > div.page > section…），
    只看 body 的直接子节点会漏掉整份正文，所以这里展开一层 .page / .container 包装。
    """
    nodes = []
    for node in body.find_all(recursive=False):
        if not getattr(node, "name", None):
            continue
        classes = node.get("class") or []
        if ("page" in classes or "container" in classes) and node.find("section", class_="section"):
            nodes.extend(node.find_all(recursive=False))
        else:
            nodes.append(node)
    return nodes


def emit_sections(doc, body):
    """顺序遍历正文，兼容旧版扁平结构（直接子 div）与新版 section 包裹结构。"""
    for node in iter_blocks(body):
        if not getattr(node, "name", None):
            continue
        classes = node.get("class") or []

        # 章节标题：旧版 .sec-title / 新版 .section > h2
        if "sec-title" in classes:
            emit_section_title(doc, node.get_text(strip=True))
            continue

        if "section" in classes:
            h2 = node.find("h2")
            if h2:
                emit_section_title(doc, h2.get_text(strip=True))
            # 用 descendants 而非 children：article.entry / .skills .row / .prs li 都要收
            for entry in node.find_all("article", class_="entry"):
                emit_entry(doc, entry)
            for row in node.select(".skills .row"):
                emit_skill(doc, row)
            for pr in node.select(".prs li"):
                emit_pr(doc, pr)
            for intro in node.select(".intro"):
                p = para(doc, before=2, after=2)
                append_inline(p, intro, size=9)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            continue

        if "entry" in classes:
            emit_entry(doc, node)
        elif "skill" in classes:
            emit_skill(doc, node)
        elif "pr-list" in classes:
            for li in node.find_all("li"):
                emit_pr(doc, li)
        elif "intro" in classes:
            p = para(doc, before=2, after=2)
            append_inline(p, node, size=9)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif "footer" in classes:
            p = para(doc, before=6, align=WD_ALIGN_PARAGRAPH.CENTER)
            run = p.add_run(node.get_text(strip=True))
            set_font(run, size=7.5, color=FOOTER)


def emit_section_title(doc, text):
    p = para(doc, before=7, after=3)
    shade(p, "2C3E50")
    run = p.add_run("  " + text)
    set_font(run, size=10.5, bold=True, color=WHITE)


def emit_entry(doc, node):
    """一条经历：标题行（左名右时间）+ 角色行 + 要点逐条。"""
    top = node.select_one(".entry-top") or node.select_one(".entry-head")
    p = para(doc, before=3, after=1)
    add_right_tab(p)
    if top:
        name = top.select_one(".entry-name") or top.select_one(".org")
        date = top.select_one(".entry-date") or top.select_one(".when")
        if name:
            run = p.add_run(name.get_text(strip=True))
            set_font(run, size=9.5, bold=True, color=DARK)
        if date:
            run = p.add_run("\t" + date.get_text(strip=True))
            set_font(run, size=8, color=GRAY)
    else:
        run = p.add_run(node.get_text(strip=True)[:60])
        set_font(run, size=9.5, bold=True, color=DARK)

    role = node.select_one(".entry-role") or node.select_one(".entry-sub")
    if role:
        p = para(doc, after=1)
        run = p.add_run(role.get_text(" ", strip=True))
        set_font(run, size=8.5, bold=True, color=DARK)

    # 要点：resume.html 是 <ul><li>，新版是 ul.bullets > li —— 逐条成段
    lis = node.select("ul li")
    if lis:
        for li in lis:
            p = para(doc, indent=0.45)
            run = p.add_run("• ")
            set_font(run, size=9, bold=True, color=LINK)
            append_inline(p, li, size=9)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    else:
        text_div = node.select_one(".entry-text")
        if text_div:
            p = para(doc, indent=0.45)
            append_inline(p, text_div, size=9)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def emit_skill(doc, node):
    p = para(doc, after=1)
    # 新版结构：.row > span.k（"AI 工程"） + span.v（值），k 是独立标签需补分隔
    label = node.select_one(".k")
    value = node.select_one(".v")
    if label is not None and value is not None:
        run = p.add_run(label.get_text(strip=True) + "：")
        set_font(run, size=9, bold=True, color=DARK)
        append_inline(p, value, size=9)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        return

    b = node.find("b")
    if b:
        run = p.add_run(b.get_text(strip=True))
        set_font(run, size=9, bold=True, color=DARK)
        rest = node.get_text()
        rest = rest.replace(b.get_text(), "", 1)
        run = p.add_run(rest)
        set_font(run, size=9)
    else:
        append_inline(p, node, size=9)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def emit_pr(doc, li):
    """PR 行：仓库（链接）+ star + 编号 + 说明，四段。

    resume.html 里仓库名以 <a> 出现，且说明文本中还会再包含一次仓库名与 star，
    所以不能简单地"删掉 a 再取文本"，否则重复。改为：先扣掉 tag/a/star 节点与
    仓库名、star 字面量，剩下的才是真正的说明。
    """
    p = para(doc, indent=0.4)
    p.paragraph_format.line_spacing = 1.25
    run = p.add_run("▸ ")
    set_font(run, size=8, bold=True, color=LINK)

    repo_link = None
    for a in li.find_all("a"):
        href = a.get("href") or ""
        if "github.com" in href and "/pull/" not in href:
            repo_link = a
            break
    repo_name = repo_link.get_text(strip=True) if repo_link else ""
    # 新版 resume 把仓库名写在 .repo 里（非链接），两套结构都要认
    if not repo_name:
        repo_el = li.select_one(".repo")
        if repo_el is not None:
            repo_name = repo_el.get_text(strip=True)

    star = li.select_one(".star") or next(
        (s for s in li.find_all("span") if "星" in s.get_text()), None
    )
    star_text = star.get_text(strip=True) if star else ""

    if repo_name:
        run = p.add_run(repo_name)
        set_font(run, size=8.5, bold=True, color=LINK)
    if star_text:
        run = p.add_run("  " + star_text)
        set_font(run, size=7.5, color=GRAY)

    # 构造说明文本：删 tag / star / 仓库链接，再扣掉重复出现的仓库名与 star 字面量
    clone = BeautifulSoup(str(li), "html.parser").find("li")
    for sel in (".pr-tag", ".star"):
        for x in clone.select(sel):
            x.decompose()
    if repo_name:
        for a in clone.find_all("a"):
            if a.get_text(strip=True) == repo_name:
                a.decompose()

    desc = clone.get_text(" ", strip=True)
    # 新版结构里仓库名被拆成 "org/" + "repo" 两段输出，会留下 "hiyouga/ LlamaFactory"，
    # 于是整体替换失败。先把空白压掉再按单字/单词逐个剔除重复片段。
    desc = re.sub(r"[ \t]*/[ \t]*", "/", desc)
    for noise in (repo_name, star_text):
        if noise:
            desc = desc.replace(noise, " ")
    if repo_name:
        for frag in {repo_name} | set(repo_name.split("/")):
            if frag:
                desc = desc.replace(frag, " ")
    desc = re.sub(r"\s+", " ", desc).strip(" -—|·")

    if desc:
        run = p.add_run("  " + desc)
        set_font(run, size=8.5, color=TEXT)


if __name__ == "__main__":
    main()
