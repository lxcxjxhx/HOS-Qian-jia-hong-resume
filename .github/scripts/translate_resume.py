#!/usr/bin/env python3
"""
Translate resume.html (Chinese) into resume.en.html (English) — 免费后端版。

结构保持翻译：HTML 树、全部标签、样式、base64 照片、除 `lang`/`alt` 外的所有
属性逐字节保留；只有人类可读文本节点（及 img alt）被翻译。

── 后端策略：只用免费端点，不依赖任何 API Key ──
  1. Google gtx 公开端点（translate.googleapis.com，client=gtx）——主链路
  2. MyMemory 公开 API —— 主链路失败或返回空时的兜底
不存在付费/需鉴权的后端分支，未配置任何 secret 也能完整跑通。

── v4：翻译缓存与 429 熔断 ──
  问题：改 workflow、改转换脚本都会触发构建，而 resume.html 一个字符没变，
  75 段正文仍被全量重译一遍。免费端点对这类重复请求只会回 429，于是
  「不完整不产出」的闸门把整条 CI 判红 —— 明明简历内容毫无改动。
  v4 在 resume.en.html 里写入源文件 sha256 标记：
    * 指纹一致   -> 直接复用，零请求，秒级通过
    * 指纹不一致 -> 正常翻译，完成后刷新标记
    * 需强制重译 -> FORCE_RETRANSLATE=1（workflow_dispatch 提供开关）
  gtx 连续 429 时熔断 60s 并轮换主机，本轮剩余段落直接走 MyMemory，
  而不是对着同一堵墙把 35 段各撞 6 遍。
  另修一处静默污染：MyMemory 额度耗尽时会把 "MYMEMORY WARNING: ..." 塞进
  translatedText，该串含拉丁字母且不等于原文，能同时骗过两道校验，
  最终会作为正文写进英文简历。现在显式拦截。

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
  FORCE_RETRANSLATE=1 可忽略缓存强制重译。
"""

import hashlib
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup, Comment, NavigableString

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "resume.html"
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else "resume.en.html"

CJK_RE = re.compile(r'[\u4e00-\u9fff]')
LATIN_RE = re.compile(r'[A-Za-z]')
DATA_URI_RE = re.compile(r'^\s*data:[\w/+.-]+;base64,', re.I)

# ── 翻译缓存 ──
# 只在 resume.html 内容真正变化时才重新翻译。改 workflow、改转换脚本都会
# 触发构建，但正文没变却要全量重译 75 段 —— 既慢又必然撞上 429。
CACHE_MARKER_RE = re.compile(r'<!--\s*translation-cache:\s*([0-9a-f]{64})\s*-->')
FORCE_RETRANSLATE = os.environ.get('FORCE_RETRANSLATE', '').strip().lower() in ('1', 'true', 'yes')

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
    # 整段自我介绍直连替换：机翻会产出 "It is a habit to locate the root cause"
    # "delivered things" "soft copy review"（软著译错）等不通顺表达。
    # 这段是简历最后一节的收尾语，必须地道，不让机翻经手。
    '在 AI 应用与系统安全之间做工程落地：习惯先定位根因再动手，交付的东西要能跑、能被验证。'
    '向上游项目提交的修复已合并、自研工具通过软著审查，是这套标准的结果——'
    '而这种组合在 AI 产品真正落地时，往往缺一不可。':
        'Engineering where AI applications meet system security: I find the root cause '
        'before writing code, and what I ship has to run and be verifiable. Fixes merged '
        'upstream and self-built tools that cleared software copyright review are the '
        'product of that standard - a combination that is usually indispensable when AI '
        'products actually go live.',
}

TERM_FIXES = [
    (re.compile(r'\bsafety hyacinth\b', re.I), 'Security Hyacinth'),
    (re.compile(r'\bsecurity hyacinth\b', re.I), 'Security Hyacinth'),
    (re.compile(r'\bsafety engineer\b', re.I), 'Security Engineer'),
    # 全链路：机器翻译会直译成 "entire link"，英文里不成立，统一为 pipeline
    (re.compile(r'\bthe entire link of\b', re.I), 'the full pipeline of'),
    (re.compile(r'\bthe entire link\b', re.I), 'the full pipeline'),
    (re.compile(r'\bentire link\b', re.I), 'full pipeline'),
    (re.compile(r'\bfull link\b', re.I), 'full pipeline'),
    # 中文无主语句式会被直译成 "It can independently complete ..."
    (re.compile(r'\bIt can independently complete\b', re.I), 'Independently delivers'),
    (re.compile(r'\bcan also locate and repair\b', re.I), 'also locates and repairs'),
    # 博客粉丝数：机器翻译给 "fans"，英文简历惯例用 "followers"
    (re.compile(r'\b(\d[\d,]*\+?)\s*fans\b', re.I), r'\1 followers'),
    # 软著状态：机翻把"受理中"译成 "is being accepted"，语义错（应为审核中）
    (re.compile(r'\bHOSxAI Command line\b'), 'HOSxAI command-line'),
    (re.compile(r'\bhas been registered\b', re.I), 'registered'),
    (re.compile(r'\bAccepting\b'), 'under examination'),
    (re.compile(r'\baccepting\b'), 'under examination'),
    # 机翻把"既能…也能…"译成 "It can not only handle..."，主语冗余
    (re.compile(r'\bIt can not only handle\b', re.I), 'Handles both'),
    (re.compile(r'\bbut also locate and repair\b', re.I), 'and locates and repairs'),
]

# 翻译规则版本：normalize()/TERM_FIXES 逻辑变更时递增，
# 参与缓存指纹计算 —— 否则改了规则，缓存仍判定"源文件未变"而跳过，
# 新规则永远不生效。
RULES_VERSION = 'v4.3'

FULLWIDTH = str.maketrans({
    '：': ':', '，': ',', '。': '.', '；': ';',
    '（': '(', '）': ')', '、': ',', '！': '!', '？': '?',
    '“': '"', '”': '"', '‘': "'", '’': "'",
})

# ── gtx 限流应对 ──
# 429 时轮换主机，并连续两次失败后熔断一段时间，期间不再尝试 gtx。
GTX_HOSTS = ('translate.googleapis.com', 'translate.google.com')
GTX_UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
GTX_BLOCK_SECONDS = float(os.environ.get('TRANSLATE_GTX_BLOCK', '60'))
_GTX = {'host_idx': 0, 'fails': 0, 'blocked_until': 0.0}

# MyMemory 匿名额度按 IP 每日计算；缓存生效后极少用到，留足一次全量兜底的余量
MYMEMORY_PER_RUN = int(os.environ.get('TRANSLATE_MYMEMORY_BUDGET', '100'))
# 额度耗尽时 MyMemory 会把警告塞进 translatedText，必须拦下，
# 否则英文简历正文里会出现 "MYMEMORY WARNING: YOU USED ALL AVAILABLE ..."
MYMEMORY_BAD_MARKERS = ('MYMEMORY WARNING', 'QUOTA', 'INVALID', 'PLEASE SELECT TWO DISTINCT')


class RateLimited(Exception):
    """gtx 返回 429。"""


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

def gtx_available():
    return time.time() >= _GTX['blocked_until']


def _gtx_mark_ok():
    _GTX['fails'] = 0


def _gtx_mark_429():
    """连续 429 就熔断：与其把每段都撞一遍，不如整轮直接交给 MyMemory。"""
    _GTX['host_idx'] += 1
    _GTX['fails'] += 1
    if _GTX['fails'] >= 2 and gtx_available():
        _GTX['blocked_until'] = time.time() + GTX_BLOCK_SECONDS
        print(f'  [WARN] gtx 连续 429，熔断 {GTX_BLOCK_SECONDS:.0f}s，'
              f'本轮剩余段落直接走 MyMemory')


def _gtx_request(segment):
    """一次 gtx 请求翻一整段；返回译文字符串。"""
    host = GTX_HOSTS[_GTX['host_idx'] % len(GTX_HOSTS)]
    params = [('client', 'gtx'), ('sl', 'zh-CN'), ('tl', 'en'), ('dt', 't'), ('q', segment)]
    r = requests.get(
        f'https://{host}/translate_a/single',
        params=params, timeout=40, headers={'User-Agent': GTX_UA},
    )
    if r.status_code == 429:
        raise RateLimited(host)
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
        if not gtx_available():
            out.append('')
            continue
        parts = []
        for chunk in _soft_split(seg):
            try:
                parts.append(_gtx_request(chunk))
                _gtx_mark_ok()
            except RateLimited as e:  # noqa: BLE001 - 交给 MyMemory 兜底
                print(f'  [WARN] gtx 429 on {e}')
                _gtx_mark_429()
                parts.append('')
                if not gtx_available():
                    break
            except Exception as e:  # noqa: BLE001 - 该段留给 MyMemory / 原文兜底
                print(f'  [WARN] gtx failed: {e}')
                parts.append('')
            time.sleep(0.15)
        out.append(' '.join(p for p in parts if p).strip())
    return out


def _mymemory_ok(text):
    up = (text or '').upper()
    return bool(up.strip()) and not any(b in up for b in MYMEMORY_BAD_MARKERS)


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
                    timeout=40, headers={'User-Agent': GTX_UA},
                )
                r.raise_for_status()
                data = r.json()
                text = data.get('responseData', {}).get('translatedText') or ''
                if not _mymemory_ok(text):
                    # 额度耗尽/非法输入时它会回一段英文警告，绝不能当译文用
                    print(f'  [WARN] mymemory 返回警告而非译文，丢弃: {text[:60]}')
                    text = ''
                out.append(text)
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


def fix_latin_spacing(soup):
    """修补行内标签拼接处的缺失空格。

    翻译按文本节点进行，`基于 <b>Qwen-14B</b> 指令微调` 会被拆成多个节点
    分别翻译；中文靠字形分隔不需要空格，英文拼起来就成了
    "based onQwen-14BCommand fine-tuning"。这里在相邻节点之间、
    两侧都是拉丁字母/数字处补一个空格。
    """
    # 左节点以标点收尾（"attack:"、"Stars"）时同样需要空格；
    # 右节点以 "#" 开头（PR 号）也要隔开，否则拼成 "Stars#10626"。
    LATIN_END = re.compile(r'[A-Za-z0-9:;.,!?)\]]$')
    LATIN_START = re.compile(r'^[A-Za-z0-9#(\[]')
    fixed = 0

    def visible(node):
        return node.get_text() if hasattr(node, 'get_text') else str(node)

    for el in soup.find_all(True):
        kids = [k for k in el.children if str(k).strip()]
        for a, b in zip(kids, kids[1:]):
            if not LATIN_END.search(visible(a).rstrip()):
                continue
            if not LATIN_START.match(visible(b).lstrip()):
                continue
            # 已经隔着空白就不动
            if str(a)[-1:].isspace() or str(b)[:1].isspace():
                continue
            a.insert_after(NavigableString(' '))
            fixed += 1

    if fixed:
        print(f'  [INFO] 修补了 {fixed} 处行内标签拼接缺失的空格')
    return fixed


# 翻译接口偶尔返回零宽字符，在英文排版里会变成看不见的空隙
ZERO_WIDTH_RE = re.compile('[\u200b\u200c\u200d\u2060\ufeff]')


def strip_zero_width(soup):
    """清理零宽字符与不换行空格，避免英文里出现异常空隙。"""
    cleaned = 0
    for s in soup.find_all(string=True):
        if isinstance(s, Comment):
            continue
        t = str(s)
        t2 = ZERO_WIDTH_RE.sub('', t).replace('\u00a0', ' ')
        if t2 != t:
            s.replace_with(NavigableString(t2))
            cleaned += 1
    if cleaned:
        print(f'  [INFO] 清理了 {cleaned} 处零宽字符/不换行空格')
    return cleaned


def fix_punct_spacing(soup):
    """修补标点后缺失的空格。

    中文里"：基于"不需要空格，英文"attack:based"必须写成"attack: based"。
    逐节点翻译后冒号常常紧跟下一个词，这里补上。
    跳过链接/邮箱等含 `//` 或 `@` 的文本，避免把 https:// 拆坏。
    """
    PUNCT_GLUE = re.compile(r'([:;,])(?=[A-Za-z])')
    fixed = 0
    for s in soup.find_all(string=True):
        if isinstance(s, Comment):
            continue
        t = str(s)
        if '//' in t or '@' in t:
            continue
        t2 = PUNCT_GLUE.sub(r'\1 ', t)
        if t2 != t:
            s.replace_with(NavigableString(t2))
            fixed += 1
    if fixed:
        print(f'  [INFO] 修补了 {fixed} 处标点后缺失的空格')
    return fixed


def capitalize_block_starts(soup):
    """把技能/介绍等块级行的首字母改为大写。

    逐节点翻译时 `<b>知识产权：</b>` 被当成独立片段，接口返回
    "intellectual property:"，整行就成了小写开头。这里对每个块级容器
    的第一个文本节点做首字母大写。
    """
    BLOCK_CLASSES = ('skill', 'intro', 'entry-role', 'entry-text')
    fixed = 0
    for el in soup.find_all(True):
        cls = el.get('class') or []
        if not any(c in BLOCK_CLASSES for c in cls):
            continue
        for s in el.find_all(string=True):
            if isinstance(s, Comment):
                continue
            t = str(s)
            stripped = t.lstrip()
            if not stripped:
                continue
            head = stripped[0]
            if head.isalpha() and head.islower():
                s.replace_with(NavigableString(t.replace(head, head.upper(), 1)))
                fixed += 1
            break  # 只处理该容器第一个非空文本节点

    # 上面只看首个节点，但 `<b>标签：</b>5 software copyrights (<span>HOSxAI</span>
    # Command line agent...` 这种结构里，nowrap 之后的文本节点会被误判为
    # 块首而错误大写，收尾纠正回来。
    for pat, repl in (
        (re.compile(r'\bCommand line agent software\b'), 'command-line agent software'),
        (re.compile(r'\bAccepting\b'), 'under examination'),
    ):
        for s in soup.find_all(string=True):
            if pat.search(str(s)):
                s.replace_with(NavigableString(pat.sub(repl, str(s))))
    if fixed:
        print(f'  [INFO] 修正了 {fixed} 处块级行首小写')
    return fixed


def prose_cjk_count(html):
    """只统计真正需要翻译的正文中文，排除 style/script 里的注释。

    resume.html 的 CSS 注释是中文的，它们本来就不翻译；若拿整份 HTML 的
    中文字数当分母，这些注释会被算成"未翻译残留"，把比例虚高到超阈值，
    导致明明译完了却判定失败、拒绝产出。
    """
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all(list(SKIP_TAGS)):
        tag.decompose()
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    return len(CJK_RE.findall(soup.get_text()))


def source_fingerprint(html):
    """缓存指纹 = 源文件内容 + 翻译规则。

    只哈希源文件是不够的：改了 TERM_FIXES / GLOSSARY 后，源文件没变，
    缓存会判定"未变更"直接复用旧产物，新规则永远不生效。把规则一起
    纳入指纹，规则一改就自动失效重译。
    """
    rules = '\x00'.join([
        RULES_VERSION,
        repr(sorted(GLOSSARY.items())),
        repr([(p.pattern, r) for p, r in TERM_FIXES]),
        repr(sorted(FULLWIDTH.items())),
    ])
    h = hashlib.sha256()
    h.update(html.encode('utf-8'))
    h.update(b'\x00')
    h.update(rules.encode('utf-8'))
    return h.hexdigest()


def reuse_cached_output(html, fingerprint):
    """若 resume.en.html 已由同一份源文件产出，直接复用，不再请求翻译接口。

    这是对付免费端点 429 的根本办法：只改 workflow / 转换脚本时，
    正文一个字符都没变，却要把全部段落重译一遍 —— 既慢又必然触发限流。
    """
    if FORCE_RETRANSLATE:
        print('[INFO] FORCE_RETRANSLATE 已置位，忽略缓存强制重译')
        return False
    if not os.path.exists(OUTPUT_FILE):
        return False
    try:
        with open(OUTPUT_FILE, encoding='utf-8') as f:
            prev = f.read()
    except OSError:
        return False

    m = CACHE_MARKER_RE.search(prev)
    if not m:
        print(f'[INFO] {OUTPUT_FILE} 无缓存标记，需完整翻译一次以建立标记')
        return False
    if m.group(1) != fingerprint:
        print(f'[INFO] 源文件已变更 ({m.group(1)[:12]}… -> {fingerprint[:12]}…)，重新翻译')
        return False

    # 指纹一致仍要校验产物本身没坏
    if len(prev) < 1000:
        print('[INFO] 缓存产物过小，重新翻译')
        return False
    if base64_payloads(prev) != base64_payloads(html):
        print('[INFO] 缓存产物 base64 资源与源文件不一致，重新翻译')
        return False
    total = prose_cjk_count(html) or 1
    residual = prose_cjk_count(prev)
    if residual / total > MAX_RESIDUAL:
        print(f'[INFO] 缓存产物中文残留 {residual / total:.0%} 超阈值，重新翻译')
        return False

    print(f'[SKIP] 源文件未变更 (sha256 {fingerprint[:12]}…)，复用现有 {OUTPUT_FILE}')
    return True


def main():
    with open(INPUT_FILE, encoding='utf-8') as f:
        html = f.read()

    fingerprint = source_fingerprint(html)
    if reuse_cached_output(html, fingerprint):
        print('[OK] 无需重新翻译，英文版保持原样，本次不发起任何翻译请求')
        print(f'[INFO] finished at {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} UTC')
        return

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

    total_cjk = prose_cjk_count(html) or 1
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

    # ---- 清理零宽字符 + 修补行内标签拼接处的缺失空格 ----
    # 两者都直接作用于 soup，避免二次序列化带来的格式漂移。
    # 逐节点翻译时中文靠字形分隔不需要空格，英文拼起来会粘成一串，
    # 例如 "based onQwen-14BCommand fine-tuning"、"Stars#10626"。
    strip_zero_width(soup)
    fix_latin_spacing(soup)
    fix_punct_spacing(soup)
    capitalize_block_starts(soup)

    out = str(soup)
    if out.startswith('\n'):
        out = out[1:]

    # ---- 写入缓存标记：下次同源文件可直接复用 ----
    marker = f'<!-- translation-cache: {fingerprint} -->'
    if CACHE_MARKER_RE.search(out):
        out = CACHE_MARKER_RE.sub(marker, out, count=1)
    elif '</head>' in out:
        out = out.replace('</head>', marker + '\n</head>', 1)
    else:
        out = marker + '\n' + out

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
    remaining = prose_cjk_count(out)
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
