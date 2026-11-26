# docs: rewrite the front page against links that resolve

**PR 链接**: [lxcxjxhx/lxcxjxhx#7](https://github.com/lxcxjxhx/lxcxjxhx/pull/7)
**状态**: Merged
**合并时间**: 2026-11-24T13:23:50Z
**创建时间**: 2026-11-24T12:55:31Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 85
- **删除行数**: 101
- **变更文件数**: 4
- **提交数**: 2

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `.github/workflows/update-stats.yml` | MOD | +44 | -61 |
| `README.md` | MOD | +39 | -39 |
| `stats/repos.json` | MOD | +1 | -1 |
| `stats/upstream.json` | NEW | +1 | -0 |

## PR 描述

Three of the six PR references on the front page did not resolve, and the two count bases contradicted each other in the same scroll.

## What the page claimed vs. what the API returns

| claim on the page | checked 2026-11-24 |
|---|---|
| `microsoft/agent-framework` (8 merges) | repository does not resolve; author has **zero** merged PRs in that org |
| `agent-framework#10400` | 404 |
| `microsoft/agent-framework#10236` | 404 |
| 86 merges across 39 repositories | **87** across **41** |
| 56 merges in November | **57** |
| `llm-compressor` (4) | **5** |
| `stats/*.json` | five shields endpoints, never rendered by any page |
| pipecat (14), thc-hydra (6), FastGPT (6), peft (3), torchtitan (3) | all correct |

The 1–2 unit drift between the README and the API is normal staleness; hard-coded counts in prose will always drift, so the numbers now live in `stats/` and the page dates them.

## Changes

**`README.md`** — rebuilt around references that resolve:

- `pipecat-ai/pipecat#6690` (merged), `harbor-framework/harbor#4213` and `#4214` (open), `vllm-project/llm-compressor#3526` (open, described as *filed*, not merged)
- a **Counts** block that states both bases instead of letting the card's 504 and the prose's 87 contradict each other: whole account vs. repositories I do not own
- the empty-header table (`| | |`) and the four same-sized `####` headings are gone; the page follows the card's own three-band rhythm (board → flagship → highlights), which is why it read as a poster glued to a Word document before
- table cells hold one claim plus one thing you can run (`selftest ok ran=14`), not a paragraph plus a full shell command
- the four shields endpoints that already existed in `stats/` are now actually rendered

**`.github/workflows/update-stats.yml`** —

- new `stats/upstream.json`: `is:merged -user:lxcxjxhx`, the basis the README quotes. `prs.json` stays as the whole-account figure
- the step fails when any of the six values is not a number; it used to check one of them (`stat-prs`) and commit the rest even when empty
- `users/:user/repos` pages through with `gh api --paginate` instead of three hard-coded pages
- the retry after a rejected push uses `--force-with-lease` too; the second push was unguarded
- dropped the five `VAR="${{ env.VAR }}"` reassignments that re-read what `$GITHUB_ENV` had already exported

**`stats/repos.json`** — `a9b665` → `D8C4E4`, the purple the card uses for that column.

## Verify

```bash
gh api "search/issues?q=author:lxcxjxhx+type:pr+is:merged+-user:lxcxjxhx&per_page=1" --jq .total_count   # 87
gh api repos/microsoft/agent-framework            # 404
gh api repos/pipecat-ai/pipecat/pulls/6690 --jq .merged                                  # true
gh api repos/harbor-framework/harbor/pulls/4213 --jq .state                              # open
gh api repos/vllm-project/llm-compressor/pulls/3526 --jq .state                          # open
```

The injection step's regexes and the new five-way check were dry-run against the shipped `profile-anim.svg`: all five ids take a value, and a blanked value is rejected.

## Not in this PR

- `dist/hos-card.html` and `docs/index.html` are the same 2.17 MB blob (identical sha). Pages builds from `main:/docs`, so `dist/` is dead weight — and neither file has a build source in the repo, so it can only be hand-edited. Worth a separate PR.
- `CONTRIBUTING.md` declares AGPLv3, SaaS disclosure and commercial licensing, but the repository has no `LICENSE` file and no source to license. Either add the licence or cut the file to three lines.
- repository topics are empty and the description is still `Profile README` — the only searchable text on the repo.


## 相关链接

- **源仓库**: [lxcxjxhx/lxcxjxhx](https://github.com/lxcxjxhx/lxcxjxhx)
- **PR 链接**: https://github.com/lxcxjxhx/lxcxjxhx/pull/7
- **Diff**: https://github.com/lxcxjxhx/lxcxjxhx/pull/7.diff

---
*Auto-generated at 2026-11-26 06:43:15 UTC*
