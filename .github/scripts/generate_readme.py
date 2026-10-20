#!/usr/bin/env python3
"""
自动生成 README.md 的脚本
从各个数据源获取最新信息并更新 README
"""

import requests
import base64
from datetime import datetime
import os

# 配置
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USERNAME = 'lxcxjxhx'
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}


def get_github_stats():
    """获取 GitHub 统计数据"""
    stats = {
        'total_commits': 0,
        'total_repos': 0,
        'total_prs': 0,
        'total_stars': 0,
        'pinned_repos': []
    }
    
    if not GITHUB_TOKEN:
        return stats
    
    # 获取用户信息
    r = requests.get(f'https://api.github.com/users/{GITHUB_USERNAME}', headers=HEADERS)
    if r.status_code == 200:
        user_data = r.json()
        stats['total_repos'] = user_data.get('public_repos', 0)
    
    # 获取仓库列表
    r = requests.get(f'https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100', headers=HEADERS)
    if r.status_code == 200:
        repos = r.json()
        stats['total_stars'] = sum(repo.get('stargazers_count', 0) for repo in repos)
        
        # 获取置顶仓库（通过 GraphQL API）
        query = """
        query {
            user(login: "lxcxjxhx") {
                pinnedItems(first: 6, types: REPOSITORY) {
                    nodes {
                        ... on Repository {
                            name
                            description
                            url
                            stargazerCount
                            primaryLanguage {
                                name
                                color
                            }
                        }
                    }
                }
            }
        }
        """
        r = requests.post('https://api.github.com/graphql', 
                         json={'query': query}, 
                         headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            pinned = data.get('data', {}).get('user', {}).get('pinnedItems', {}).get('nodes', [])
            stats['pinned_repos'] = pinned
    
    # 获取年度贡献数
    r = requests.get(f'https://github-contributions-api.jogruber.de/v4/{GITHUB_USERNAME}')
    if r.status_code == 200:
        contrib_data = r.json()
        if 'contributions' in contrib_data:
            # 获取最近一年的贡献
            current_year = datetime.now().year
            year_contribs = [c for c in contrib_data['contributions'] 
                           if c.get('date', '').startswith(str(current_year))]
            stats['total_commits'] = sum(c.get('count', 0) for c in year_contribs)
    
    return stats


def get_pypi_stats():
    """获取 PyPI 包统计"""
    stats = {
        'total_packages': 0,
        'packages': []
    }
    
    r = requests.get(f'https://pypi.org/pypi/security_hyacinth/json')
    # 这个 API 不支持用户级别查询，需要通过其他方式
    # 暂时返回占位数据
    stats['total_packages'] = 7  # 根据原 README
    return stats


def get_pr_count():
    """获取已合并 PR 数量。

    search/issues 默认每页 30 条，靠 len(items) 数会严重低估；
    这里直接读返回体里的 total_count —— 与 update_pr_workflow.py 的口径一致。
    """
    if not GITHUB_TOKEN:
        return 0

    r = requests.get(
        f'https://api.github.com/search/issues?q=author:{GITHUB_USERNAME}+is:pr+is:merged&per_page=1',
        headers=HEADERS
    )
    if r.status_code == 200:
        return r.json().get('total_count', 0)
    return 0


def get_contributed_repo_count():
    """已合并 PR 涉及的仓库数。

    原版 README 里写的是 len(pinned_repos)，那是 GitHub 置顶仓库数（上限 6），
    与"涉及项目"毫无关系，会渲染成 "6+" 这种假数字。这里按真实 PR 归属去重统计。
    """
    if not GITHUB_TOKEN:
        return 0

    repos = set()
    page = 1
    while page <= 10:
        r = requests.get(
            f'https://api.github.com/search/issues?q=author:{GITHUB_USERNAME}+is:pr+is:merged'
            f'&per_page=100&page={page}',
            headers=HEADERS
        )
        if r.status_code != 200:
            break
        items = r.json().get('items', [])
        if not items:
            break
        for it in items:
            parts = it.get('repository_url', '').split('/')
            if len(parts) >= 2:
                repos.add(f'{parts[-2]}/{parts[-1]}')
        if len(items) < 100:
            break
        page += 1
    return len(repos)


def generate_readme():
    """生成 README 内容"""
    github_stats = get_github_stats()
    pypi_stats = get_pypi_stats()
    pr_count = get_pr_count()
    repo_count = get_contributed_repo_count()
    
    current_date = datetime.now().strftime('%B %Y')
    
    readme = f"""
<!-- ═══════════════════════════════════════════════════════════════════════════
     安全风信子 | 信息安全×AI 双域实践者 — Personal Achievement Portfolio
     ═══════════════════════════════════════════════════════════════════════════ -->

<div align="center">

🌐 **语言 / Language:** [🇨🇳 中文](README.md) &nbsp;|&nbsp; [🇬🇧 English](README.en.md)

</div>

---

<div align="center">

<!-- Banner -->
<table align="center" width="90%" style="margin: 0 auto; border-collapse: collapse;">
<tr><td align="center" style="background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); padding: 40px 20px; border-radius: 16px;">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&duration=3500&pause=500&color=00D4FF&center=true&vCenter=true&width=700&lines=%F0%9F%9B%A1%EF%B8%8F+%E5%AE%89%E5%85%A8%E9%A3%8E%E4%BF%A1%E5%AD%90+%7C+%E4%BF%A1%E6%81%AF%E5%AE%89%E5%85%A8%C3%97AI+%E5%8F%8C%E5%9F%9F%E5%AE%9E%E8%B7%B5%E8%80%85;%F0%9F%94%A5+%E7%94%A8%E4%BB%A3%E7%A0%81%E9%94%BB%E9%80%A0%E6%99%BA%E8%83%BD%E6%97%B6%E4%BB%A3%E7%9A%84%E5%9D%9A%E7%9B%BE%E4%B8%8E%E5%88%A9%E7%9B%BE" alt="Typing SVG" />

<br/>

<img src="https://img.shields.io/badge/阿里云-专家博主-FF6A00?style=for-the-badge&logo=alibabacloud&logoColor=white" alt="阿里云专家博主" />
<img src="https://img.shields.io/badge/华为云-专家博主-C7000B?style=for-the-badge&logo=huawei&logoColor=white" alt="华为云专家博主" />
<img src="https://img.shields.io/badge/腾讯云-创作之星-0052D9?style=for-the-badge&logo=tencentqq&logoColor=white" alt="腾讯云创作之星" />
<img src="https://img.shields.io/badge/中美创客-特等奖-FFD700?style=for-the-badge&logo=award&logoColor=white" alt="中美创客特等奖" />

<br/><br/>

<img src="https://img.shields.io/badge/{current_date.replace(' ', '_')}-0f0c29?style=flat-square&logo=github&logoColor=white" alt="{current_date}" />

</td></tr>
</table>

<br/>

<!-- ════════ Highlights ════════ -->

## ✨ Highlights

<table align="center" width="90%" style="margin: 0 auto;">
<tr>
<td width="20%" align="center">
<br/><img src="https://img.shields.io/badge/AI_Driven-0A84FF?style=for-the-badge&logo=robot&logoColor=white&labelColor=0A84FF" width="120"/><br/><br/>
<b>HOS-LS</b><br/>
<sub>AI 驱动安全分析<br/>攻击链推理引擎</sub>
</td>
<td width="20%" align="center">
<br/><img src="https://img.shields.io/badge/1,400+-7C3AED?style=for-the-badge&logo=mdbook&logoColor=white&labelColor=7C3AED" width="120"/><br/><br/>
<b>技术博文</b><br/>
<sub>1,467 篇原创<br/>12+ 系统专栏</sub>
</td>
<td width="20%" align="center">
<br/><img src="https://img.shields.io/badge/{pypi_stats['total_packages']}_Pkgs-10B981?style=for-the-badge&logo=pypi&logoColor=white&labelColor=10B981" width="120"/><br/><br/>
<b>PyPI 开源包</b><br/>
<sub>{pypi_stats['total_packages']} 个发布包<br/>安全工具集</sub>
</td>
<td width="20%" align="center">
<br/><img src="https://img.shields.io/badge/Award-FFD700?style=for-the-badge&logo=trophy&logoColor=white&labelColor=FFD700" width="120"/><br/><br/>
<b>中美创客特等奖</b><br/>
<sub>国家级竞赛荣誉<br/>AI×安全创新</sub>
</td>
<td width="20%" align="center">
<br/><img src="https://img.shields.io/badge/{github_stats['total_commits']}-22D3EE?style=for-the-badge&logo=github&logoColor=white&labelColor=22D3EE" width="120"/><br/><br/>
<b>GitHub 贡献</b><br/>
<sub>年度 {github_stats['total_commits']} commits<br/>持续开源</sub>
</td>
</tr>
</table>

</div>

---

<!-- ════════ About Me ════════ -->

<div align="center">

## 👋 About Me

**Qian Jiahong (钱佳宏) · 上海，中国**

信息安全 × AI 双域实践者，以代码为武器深耕大模型攻防与系统安全。
CSDN **1,467** 篇原创文章、**{pr_count}** 个已合并 Pull Request、
**{pypi_stats['total_packages']}** 个 PyPI 开源包、年度 **{github_stats['total_commits']}** 次 GitHub 贡献，
持续用工程实践探索 AI 时代的安全边界。

</div>

---

<!-- ════════ Quick Links ════════ -->

## 🔗 Quick Links

<div align="center">

<a href="https://security-hyacinth.blog.csdn.net/"><img src="https://img.shields.io/badge/CSDN_博客-1,467_篇原创-FC5531?style=for-the-badge&logo=c&logoColor=white" alt="CSDN Blog"/></a>
<a href="https://github.com/{GITHUB_USERNAME}"><img src="https://img.shields.io/badge/GitHub-{GITHUB_USERNAME}-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/></a>
<a href="https://pypi.org/user/security_hyacinth/"><img src="https://img.shields.io/badge/PyPI-{pypi_stats['total_packages']}_Packages-3775A9?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"/></a>
<a href="https://huggingface.co/{GITHUB_USERNAME}"><img src="https://img.shields.io/badge/Hugging_Face-Models-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Hugging Face"/></a>
<a href="mailto:aqfxz_zh@qq.com"><img src="https://img.shields.io/badge/Email-aqfxz_zh@qq.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Email"/></a>

</div>

---

<!-- ════════ Open Source Contributions ════════ -->

<div align="center">

## 🔓 Open Source Contributions

<br/>

<a href="./PR/README.md">
<img src="https://img.shields.io/badge/📊_查看_PR_记录-{pr_count}_merged-10B981?style=for-the-badge&logo=github&logoColor=white" />
</a>

<br/><br/>

<sub>已合并 Pull Request: <b>{pr_count}</b> | 涉及项目: <b>{repo_count}</b></sub>

</div>

---

<!-- ════════ Pinned Repositories ════════ -->

<div align="center">

## 📌 Pinned Repositories

</div>

<!-- ★ Featured: HOS-LS -->
<div align="center">
<table align="center" width="90%" style="margin: 0 auto;">
<tr><td>

### 🛡️ [HOS-LS](https://github.com/{GITHUB_USERNAME}/HOS-LS) — AI 驱动的代码安全分析与攻击链推理系统

> *用 AI 语义理解重新定义代码安全分析*

| 核心能力 | |
|---|---|
| 🧠 AI 语义分析引擎 | 超越正则匹配的深层代码理解 |
| ⛓️ 攻击链分析引擎 | 端到端攻击路径推理与可视化 |
| 🤖 多 Agent 架构 | 多智能体协同分析与决策 |
| 💉 Exploit 生成 | 自动化漏洞利用代码生成 |
| ✅ 自动验证 | 漏洞可利用性自动验证 |

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Multi--Agent_AI-0A84FF?style=flat-square&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/RAG-7C3AED?style=flat-square&logo=langchain&logoColor=white" />
  <img src="https://img.shields.io/badge/⭐_1-F59E0B?style=flat-square&logo=github&logoColor=white" />
</p>

</td></tr>
</table>
</div>

<!-- ★ Featured: HOS_SKILL_WORKFLOW -->
<div align="center">
<table align="center" width="90%" style="margin: 0 auto;">
<tr><td>

### ⚙️ [HOS_SKILL_WORKFLOW](https://github.com/{GITHUB_USERNAME}/HOS_SKILL_WORKFLOW) — HOS 工作流提示词工厂

> *LLM 任务工作流与 Prompt 工程系统 · 🔥 2026.07 活跃 (28 commits)*

<p align="center">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Prompt_Engineering-EC4899?style=flat-square&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/Workflow-10B981?style=flat-square&logo=githubactions&logoColor=white" />
  <img src="https://img.shields.io/badge/⭐_2-F59E0B?style=flat-square&logo=github&logoColor=white" />
</p>

</td></tr>
</table>
</div>

<!-- Other Repos -->
<div align="center">
<table align="center" width="90%" style="margin: 0 auto;">
<tr>
<td width="33%" align="center" valign="top">

**[BOS-FS](https://github.com/{GITHUB_USERNAME}/BOS-FS)**<br/>
<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/⭐_1-F59E0B?style=flat-square" />

</td>
<td width="33%" align="center" valign="top">

**[HOS-MATCH-PROJECT](https://github.com/{GITHUB_USERNAME}/HOS-MATCH-PROJECT)**<br/>
Intel AI 竞赛 · AI+威胁检测<br/>
<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Qwen2.5-6366F1?style=flat-square" />
<img src="https://img.shields.io/badge/React-22D3EE?style=flat-square&logo=react&logoColor=black" />
<img src="https://img.shields.io/badge/KG-10B981?style=flat-square" />
<img src="https://img.shields.io/badge/⭐_2-F59E0B?style=flat-square" />

</td>
<td width="33%" align="center" valign="top">

**[BOS-NI](https://github.com/{GITHUB_USERNAME}/BOS-NI)**<br/>
<img src="https://img.shields.io/badge/—-6B7280?style=flat-square" />

</td>
</tr>
<tr>
<td colspan="3" align="center">

**[HOS-Qian-jia-hong-resume](https://github.com/{GITHUB_USERNAME}/HOS-Qian-jia-hong-resume)** — 当前仓库 · 个人成就作品集<br/>
<img src="https://img.shields.io/badge/Markdown-000000?style=flat-square&logo=markdown&logoColor=white" />
<img src="https://img.shields.io/badge/⭐_1-F59E0B?style=flat-square" />

</td>
</tr>
</table>
</div>

<p align="center">
  <a href="https://github.com/{GITHUB_USERNAME}"><img src="https://img.shields.io/badge/→_查看完整_GitHub_主页-181717?style=for-the-badge&logo=github&logoColor=white" alt="View GitHub"/></a>
</p>

---

<!-- ════════ Tech Stack ════════ -->

<div align="center">

## 🧰 Tech Stack

<br/>

**Languages & Frameworks**

<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" />
<img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
<img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
<img src="https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=node.js&logoColor=white" />

<br/><br/>

**AI / LLM**

<img src="https://img.shields.io/badge/vLLM-生产级推理-6366F1?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-10B981?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/MCP-工程化-EC4899?style=for-the-badge&logo=typescript&logoColor=white" />
<img src="https://img.shields.io/badge/Taro-跨端开发-000000?style=for-the-badge&logo=taro&logoColor=white" />

<br/><br/>

**DevOps & Tools**

<img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
<img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" />
<img src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white" />

</div>

---

<!-- ════════ CSDN Blog Stats ════════ -->

<div align="center">

## 📝 CSDN Blog — Security Hyacinth

<br/>

<a href="https://security-hyacinth.blog.csdn.net/">
<img src="https://img.shields.io/badge/📖_1,467_篇原创-FC5531?style=for-the-badge" />
</a>
<a href="https://security-hyacinth.blog.csdn.net/">
<img src="https://img.shields.io/badge/👁_1.2M_访问-0A84FF?style=for-the-badge" />
</a>
<a href="https://security-hyacinth.blog.csdn.net/">
<img src="https://img.shields.io/badge/👍_20K+_点赞-F59E0B?style=for-the-badge" />
</a>
<a href="https://security-hyacinth.blog.csdn.net/">
<img src="https://img.shields.io/badge/👥_3,312_粉丝-7C3AED?style=for-the-badge" />
</a>
<a href="https://security-hyacinth.blog.csdn.net/">
<img src="https://img.shields.io/badge/💬_347_评论-10B981?style=for-the-badge" />
</a>
<a href="https://security-hyacinth.blog.csdn.net/">
<img src="https://img.shields.io/badge/⭐_19,544_收藏-EC4899?style=for-the-badge" />
</a>
<a href="https://security-hyacinth.blog.csdn.net/">
<img src="https://img.shields.io/badge/💻_977_代码片-6366F1?style=for-the-badge" />
</a>

<br/><br/>

> 🎯 *欢迎来到智能安全前线！这里是 AI 与信息安全交汇之地。以代码为武器，深入大模型攻防实战，破解系统漏洞。追踪 OpenAI、Meta 前沿动态，用红蓝对抗思维，锻造智能时代的坚盾与利矛。*

<br/>

<a href="https://security-hyacinth.blog.csdn.net/"><img src="https://img.shields.io/badge/→_立即访问博客-FC5531?style=for-the-badge&logo=c&logoColor=white" alt="Visit Blog"/></a>

</div>

---

<!-- ════════ Featured Columns ════════ -->

<div align="center">

## 📚 Featured Columns

</div>

<br/>

<table align="center" width="80%" style="margin: 0 auto;">
<thead>
<tr>
<th align="left">专栏</th>
<th align="center">篇数</th>
<th align="left">标签</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left"><strong>HOS-CTF \\| 从入门到国赛的攻防之路 2026</strong></td>
<td align="center">20</td>
<td align="left">🔒 付费专栏</td>
</tr>
<tr>
<td align="left"><strong>vLLM 生产级 LLM 推理引擎实战（2026）</strong></td>
<td align="center">70</td>
<td align="left">🏭 生产级实战</td>
</tr>
<tr>
<td align="left"><strong>MCP 工程实战：构建可控的 AI 工具与 Agent 系统</strong></td>
<td align="center">69</td>
<td align="left">📐 系统化教程</td>
</tr>
<tr>
<td align="left"><strong>HOS-AI \\| 大模型系统工程 × AI变现实战</strong></td>
<td align="center">150</td>
<td align="left">⭐ 核心专栏</td>
</tr>
<tr>
<td align="left"><strong>日学日新 · HF/MS 模型进化录</strong></td>
<td align="center">45</td>
<td align="left">🔄 持续更新</td>
</tr>
<tr>
<td align="left"><strong>如果夜神月学会 AIx信安：77个技术脑洞</strong></td>
<td align="center">76</td>
<td align="left">💡 创意系列</td>
</tr>
<tr>
<td align="left"><strong>L的AIx信安推理：76次防御与溯源基拉</strong></td>
<td align="center">76</td>
<td align="left">💡 创意系列</td>
</tr>
<tr>
<td align="left"><strong>HOS工程急救库 \\| Git·Python·AI环境问题速查</strong></td>
<td align="center">41</td>
<td align="left">🔧 工具速查</td>
</tr>
<tr>
<td align="left"><strong>专业帮助文档特辑：即用模板与专家解决方案</strong></td>
<td align="center">40</td>
<td align="left">📋 实用模板</td>
</tr>
<tr>
<td align="left"><strong>2025 大模型+AIGC</strong></td>
<td align="center">165</td>
<td align="left">📦 归档</td>
</tr>
<tr>
<td align="left"><strong>2025 信息安全CTF全题型&题解</strong></td>
<td align="center">160</td>
<td align="left">📦 归档</td>
</tr>
<tr>
<td align="left"><strong>个人思考分享（安全风信子精选专栏）</strong></td>
<td align="center">13</td>
<td align="left">💎 精选</td>
</tr>
</tbody>
</table>

<br/>

---

<!-- ════════ Achievements ════════ -->

<div align="center">

## 🏆 Achievements & Milestones

</div>

<br/>

<table align="center" width="80%" style="margin: 0 auto;">
<tbody>
<tr>
<td align="left">🥇 <strong>竞赛</strong></td>
<td align="left">中美青年创客大赛<strong>特等奖</strong>、Intel AI 竞赛、多项国家级/省级创新大赛</td>
</tr>
<tr>
<td align="left">📜 <strong>认证</strong></td>
<td align="left">阿里云专家博主、华为云专家博主、腾讯云创作之星、Intel AI 系列、携程技术系列、CET-4 & CET-6、网络安全应急响应（中级）</td>
</tr>
<tr>
<td align="left">✍️ <strong>分享</strong></td>
<td align="left">CSDN 1,467 篇原创文章，12+ 系统化专栏，记录 AI x Security 实战心得</td>
</tr>
<tr>
<td align="left">🔓 <strong>开源</strong></td>
<td align="left">PyPI {pypi_stats['total_packages']} 个开源包、GitHub {github_stats['total_commits']} 年度贡献、Hugging Face 微调模型</td>
</tr>
</tbody>
</table>

<br/>

---

<!-- ════════ Exploration Areas ════════ -->

<div align="center">

## 🔬 Core Exploration Areas

</div>

<br/>

<table align="center" width="80%" style="margin: 0 auto;">
<thead>
<tr>
<th align="left">领域</th>
<th align="left">实践内容</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left">🧠 <strong>LLM Applications</strong></td>
<td align="left">Qwen2.5 / LLaMA 微调与本地部署、Multi-Agent 系统、Prompt Engineering、vLLM 生产级部署、MCP 工程</td>
</tr>
<tr>
<td align="left">🛡️ <strong>Cybersecurity</strong></td>
<td align="left">CTF 实战（国赛级）、红队自动化工具、AI 驱动代码安全分析 (HOS-LS)、攻击链推理</td>
</tr>
<tr>
<td align="left">🌐 <strong>Full-Stack</strong></td>
<td align="left">React + Taro 前端 + FastAPI 后端，中小型 Web 与小程序项目</td>
</tr>
<tr>
<td align="left">🏥 <strong>Healthcare AI</strong></td>
<td align="left">非临床视角下的对话系统与数据可视化探索</td>
</tr>
<tr>
<td align="left">🛠️ <strong>DevOps</strong></td>
<td align="left">本地 AI 环境搭建、CUDA/WSL2 问题排查、uv 包管理</td>
</tr>
</tbody>
</table>

<br/>

---

<!-- ════════ Contact ════════ -->

<div align="center">

## 📬 Contact

<br/>

**Qian Jiahong (钱佳宏)**

📍 上海，中国 &nbsp;|&nbsp; 📱 +86 19921057118 &nbsp;|&nbsp; ✉️ [aqfxz_zh@qq.com](mailto:aqfxz_zh@qq.com)

<br/>

<a href="https://github.com/{GITHUB_USERNAME}"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" /></a>
<a href="https://security-hyacinth.blog.csdn.net/"><img src="https://img.shields.io/badge/CSDN-FC5531?style=for-the-badge&logo=c&logoColor=white" /></a>
<a href="https://pypi.org/user/security_hyacinth/"><img src="https://img.shields.io/badge/PyPI-3775A9?style=for-the-badge&logo=pypi&logoColor=white" /></a>
<a href="https://huggingface.co/{GITHUB_USERNAME}"><img src="https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" /></a>

</div>

---

<div align="center">

<sub>⭐ 感谢所有队友、导师和朋友在学习旅程中给予的指导与支持。正是因为你们，我才能持续前行。</sub>

<br/>

<img src="https://komarev.com/ghpvc/?username={GITHUB_USERNAME}&style=flat-square&color=0A84FF" alt="Profile Views"/>

</div>

---

<div align="center">
<sub>🤖 本 README 通过 GitHub Actions 自动更新，英文版 README.en.md 自动翻译 | 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</sub>
</div>
"""
    
    return readme


if __name__ == '__main__':
    readme_content = generate_readme()
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✅ README.md 已生成")
