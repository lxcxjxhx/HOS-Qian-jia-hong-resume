#!/usr/bin/env python3
"""
Translate resume.html (Chinese) into resume.en.html (English) — 免费后端版。

结构保持翻译：HTML 树、全部标签、样式、base64 照片、除 `lang`/`alt` 外的所有
属性逐字节保留；只有人类可读文本节点（及 img alt）被翻译。

── 后端策略：只用免费端点，不依赖任何 API Key ──
  1. Google gtx 公开端点（translate.googleapis.com，client=gtx）——主链路
  2. MyMemory 公开 API —— 主链路失败或返回空时的兜底
不存在付费/需鉴权的后端分支，未配置任何 secret 也能完整跑通。

── v3：免费后端的质量与稳定性修复 ──
  旧版按 80 字符切块、每块一次请求，长句被硬切断后逐块翻译再拼接，
  得到的是「句子的碎片译文」，语序断裂且重复关键词。
  v3 改为「整段一次请求」：Google gtx 单请求支持约 5000 字符源文本，
  一份简历的单条要点最长不过 ~120 字，完全可以整段送出去。
  实测：请求数从 ~10×N 降到 N，且译文是完整的句子。

── v2 已修的结构性缺陷（保留）──
  * 旧版把 `soup.find_all(string=True)` 全部塞进 800 字符的桶里，而
    resume.html 的证件照是一段 ~41KB 的 base64 data URI：
      - base64 里没有中文，本不该进翻译队列；
      - 一旦进队，批次会在任意位置切断 base64，后端返回的内容再被
        `replace_with()` 写回，照片直接损坏。
  * v2 在收集阶段排除 `data:` URI 与 script/style/pre/code，并加两道断言：
      - base64 负载必须与原文逐字节相同；
      - 输出体积不得异常膨胀。

Usage:
  python .github/scripts/translate_resume.py [input.html] [output.html]
  Defaults: resume.html -> resume.en.html
"""

import os
import re
import sys
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup, Comment

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "resume.html"
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else "resume.en.html"

CJK_RE = re.compile(r'[\u4e00-\u9fff]')
LATIN_RE = re.compile(r'[A-Za-z]')
DATA_URI_RE = re.compile(r'^\s*data:[\w/+.-]+;base64,', re.I)

# ── 循环补齐策略 ──
# 免费端点会 429 / 断连，单轮失败不该让整份简历带中文发出去。
# 最多重试 MAX_ROUNDS 轮，退避 BACKOFF_BASE * 2^(n-1)，上限 BACKOFF_MAX 秒。
# 最坏总耗时 ≈ 6 轮 × (段数 × 0.15s + 退避)，默认约 8 分钟，在 CI 默认超时内。
MAX_ROUNDS = int(os.environ.get('TRANSLATE_MAX_ROUNDS', '6'))
BACKOFF_BASE = float(os.environ.get('TRANSLATE_BACKOFF_BASE', '8'))
BACKOFF_MAX = float(os.environ.get('TRANSLATE_BACKOFF_MAX', '90'))

# 中文残留超过该比例即视为"未翻译完整"，不落盘、不产出更新
MAX_RESIDUAL = float(os.environ.get('TRANSLATE_MAX_RESIDUAL', '0.10'))

# 不可翻译的容器：其中的文本是代码/样式，绝不能送去翻译
SKIP_TAGS = {'script', 'style', 'pre', 'code'}

# Google 单请求的源文本上限约 5000 字符；留足余量，同时保证不把整条要点切断
SEGMENT_LIMIT = 1800

GLOSSARY = {
    '合并': 'Merged',
    '照片': 'Photo',
}

TERM_FIXES = [
    (re.compile(r'\bsafety hyacinth\b', re.I), 'Security Hyacinth'),
    (re.compile(r'\bsecurity hyacinth\b', re.I), 'Security Hyacinth'),
    (re.compile(r'\bsafety engineer\b', re.I), 'Security Engineer'),
]

FULLWIDTH = str.maketrans({
    '：': ':', '，': ',', '。': '.', '；': ';',
    '（': '(', '）': ')', '、': ',', '！': '!', '？': '?',
    '“': '"', '”': '"', '‘': "'", '’': "'",
})

# MyMemory 匿名额度较低，只在前半段用尽时才全量兜底
MYMEMORY_PER_RUN = 40


def normalize(text):
    """Normalise a translated segment: full-width punct, whitespace, terms."""
    text = text.replace('——', ' - ')
    text = text.translate(FULLWIDTH)
    text = re.sub(r'\s+', ' ', text).strip()
    for pat, repl in TERM_FIXES:
        text = pat.sub(repl, text)
    return text


def is_translatable(node):
    """True only for real prose: skips data URIs, scripts/styles and code blocks."""
    if isinstance(node, Comment):
        return False
    raw = str(node)
    if not raw.strip():
        return False
    if DATA_URI_RE.match(raw):
        return False
    if not CJK_RE.search(raw):
        return False
    for parent in node.parents:
        if getattr(parent, 'name', None) in SKIP_TAGS:
            return False
    return True


# ---- 免费后端 ---------------------------------------------------------------

def _gtx_request(segment):
    """一次 gtx 请求翻一整段；返回译文字符串。"""
    params = [('client', 'gtx'), ('sl', 'zh-CN'), ('tl', 'en'), ('dt', 't'), ('q', segment)]
    r = requests.get(
        'https://translate.googleapis.com/translate_a/single',
        params=params, timeout=40,
    )
    r.raise_for_status()
    data = r.json()
    if not data or not data[0]:
        return ''
    # data[0] 是逐句数组，全量 join —— 多句段落不会被截成第一句
    return ' '.join(seg[0] for seg in data[0] if seg and seg[0]).strip()


SENT_RE = re.compile(r'[^。！？；]+[。！？；]?')


def _soft_split(segment):
    """仅在段落实在过长时才按句子边界切分（绝不切进句子中间）。"""
    if len(segment) <= SEGMENT_LIMIT:
        return [segment]
    out, cur = [], ''
    for piece in SENT_RE.findall(segment):
        if len(cur) + len(piece) <= SEGMENT_LIMIT:
            cur += piece
            continue
        if cur:
            out.append(cur)
        cur = piece
    if cur:
        out.append(cur)
    return out or [segment]


def google_translate(segments):
    """Google gtx 免费端点：整段一次请求，段与段之间轻微限速。"""
    out = []
    for seg in segments:
        parts = []
        for chunk in _soft_split(seg):
            try:
                parts.append(_gtx_request(chunk))
            except Exception as e:  # noqa: BLE001 - 该段留给 MyMemory / 原文兜底
                print(f'  [WARN] gtx failed: {e}')
                parts.append('')
            time.sleep(0.15)
        out.append(' '.join(p for p in parts if p).strip())
    return out


class MyMemory:
    """MyMemory 免费兜底，带本次运行额度计数。"""

    def __init__(self, budget=MYMEMORY_PER_RUN):
        self.budget = budget
        self.used = 0

    def translate(self, segments):
        out = []
        for s in segments:
            if self.used >= self.budget:
                out.append('')
                continue
            try:
                r = requests.get(
                    'https://api.mymemory.translated.net/get',
                    params={'q': s, 'langpair': 'zh-CN|en'},
                    timeout=40,
                )
                r.raise_for_status()
                data = r.json()
                out.append(data.get('responseData', {}).get('translatedText') or '')
            except Exception as e:  # noqa: BLE001
                print(f'  [WARN] mymemory failed: {e}')
                out.append('')
            self.used += 1
            time.sleep(0.25)
        return out


def translate_batch(batch, mop_up):
    """先 Google，再 MyMemory 补齐空位。

    失败段返回空串、不回填原文 —— 回填会让"已翻译计数"虚高，
    掩盖缺口。空串由外层循环重试，最终仍未补齐就不写文件。
    """
    segments = [text for text, _ in batch]
    results = google_translate(segments)

    empty = [i for i, t in enumerate(results) if not t]
    if empty:
        print(f'  [INFO] {len(empty)} 段 gtx 未返回，转 MyMemory 兜底')
        mopped = mop_up.translate([segments[i] for i in empty])
        for i, t in zip(empty, mopped):
            if t:
                results[i] = t

    return results


def base64_payloads(html):
    """原文里所有 base64 负载（去空白），用于逐字节比对。"""
    return [m.group(1) for m in re.finditer(r'data:[\w/+.-]+;base64,([^"\'\s)]+)', html, re.I)]


def main():
    with open(INPUT_FILE, encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # ---- 收集目标：正文文本节点 + img alt ----
    targets = []
    for s in soup.find_all(string=True):
        if is_translatable(s):
            targets.append((s, lambda v, node=s: node.replace_with(v)))
    for img in soup.find_all('img'):
        alt = img.get('alt')
        if alt and CJK_RE.search(alt):
            targets.append((alt, lambda v, node=img: node.__setitem__('alt', v)))

    total_cjk = len(CJK_RE.findall(html))
    print(f'{len(targets)} text/alt target(s) to translate (source CJK chars: {total_cjk})')
    print('backend chain: google-gtx -> mymemory (free only)')

    # ---- 词表命中项无需请求 ----
    api_targets, direct = [], []
    for target in targets:
        (api_targets if target[0] not in GLOSSARY else direct).append(target)
    for text, setter in direct:
        setter(GLOSSARY[text])
    if direct:
        print(f'  {len(direct)} glossary term(s) applied directly')

    # ---- 循环补齐：只有全部段落都译完才允许写文件 ----
    # 免费端点会 429 / 断连，单次失败不该让整份简历带中文发出去。
    # 这里按轮次重试，只重试仍未翻译的段落，退避递增。
    pending = [(t, s) for t, s in api_targets]
    done_count = 0
    mop_up = MyMemory()
    round_no = 0

    def backoff(n):
        return min(BACKOFF_BASE * (2 ** (n - 1)), BACKOFF_MAX)

    while pending and round_no < MAX_ROUNDS:
        round_no += 1
        if round_no > 1:
            wait = backoff(round_no - 1)
            print(f'  [RETRY] 第 {round_no}/{MAX_ROUNDS} 轮，剩余 {len(pending)} 段，等待 {wait}s')
            time.sleep(wait)

        still = []
        for idx, (text, setter) in enumerate(pending, 1):
            got = translate_batch([(text, setter)], mop_up)
            normalized = normalize(got[0]) if got else ''
            # 译文必须存在、且确实含拉丁字母（排除后端把中文原样回显）
            if normalized and LATIN_RE.search(normalized) and normalized != text.strip():
                setter(normalized)
                done_count += 1
            else:
                still.append((text, setter))
            if idx % 10 == 0 or idx == len(pending):
                print(f'    {idx}/{len(pending)} 段处理完 (mymemory used: {mop_up.used})')
        pending = still

    # ---- 完整性闸门：任一段未译完，直接失败且不落盘 ----
    if pending:
        print(f'[ERROR] {len(pending)} 段在 {MAX_ROUNDS} 轮后仍未翻译完成:', file=sys.stderr)
        for text, _ in pending[:10]:
            print(f'  - {text[:80]}', file=sys.stderr)
        if os.path.exists(OUTPUT_FILE):
            print(f'[ERROR] 保留上一版 {OUTPUT_FILE} 不动，本次不产出更新', file=sys.stderr)
        sys.exit(1)

    # ---- lang -> en ----
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang'):
        html_tag['lang'] = 'en'

    # ---- 残留全角标点 ----
    for s in soup.find_all(string=True):
        if isinstance(s, Comment) or not is_translatable(s):
            continue
        t = s.translate(FULLWIDTH)
        if t != s:
            s.replace_with(t)

    out = str(soup)
    if out.startswith('\n'):
        out = out[1:]

    # ---- 断言 1：base64 负载必须逐字节一致 ----
    before_b64 = base64_payloads(html)
    after_b64 = base64_payloads(out)
    if len(before_b64) != len(after_b64):
        print(f'[ERROR] base64 资源数量变了: {len(before_b64)} -> {len(after_b64)}', file=sys.stderr)
        sys.exit(1)
    for a, b in zip(before_b64, after_b64):
        if a != b:
            print('[ERROR] base64 资源内容被改动（照片会损坏）', file=sys.stderr)
            sys.exit(1)

    # ---- 断言 2：输出体积不得异常膨胀 ----
    if len(out) > len(html) * 1.6 + 20000:
        print(f'[ERROR] 输出异常膨胀: {len(html)} -> {len(out)} 字符', file=sys.stderr)
        sys.exit(1)

    # ---- 断言 3：中文残留必须低于阈值，否则同样不落盘 ----
    remaining = len(CJK_RE.findall(out))
    ratio = remaining / total_cjk if total_cjk else 0
    if ratio > MAX_RESIDUAL:
        print(f'[ERROR] 中文残留 {remaining} 字 ({ratio:.0%}) 超过阈值 {MAX_RESIDUAL:.0%}，', file=sys.stderr)
        print('[ERROR] 视为翻译不完整，本次不产出更新', file=sys.stderr)
        sys.exit(1)

    # ---- 先写临时文件再原子替换，避免中途失败留下半成品 ----
    tmp_path = OUTPUT_FILE + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(out)
    os.replace(tmp_path, OUTPUT_FILE)

    print(f'[OK] {OUTPUT_FILE} written ({len(out)} chars, base64 assets intact: {len(after_b64)})')
    print(f'     完整翻译 {done_count}/{len(api_targets)} 段 | 轮次 {round_no} | 中文残留 {remaining} 字 ({ratio:.1%})')
    print(f'[INFO] finished at {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} UTC')


if __name__ == '__main__':
    main()
