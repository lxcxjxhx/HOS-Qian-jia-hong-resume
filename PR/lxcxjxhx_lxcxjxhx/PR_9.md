# docs: reference the counts instead of restating them

**PR 链接**: [lxcxjxhx/lxcxjxhx#9](https://github.com/lxcxjxhx/lxcxjxhx/pull/9)
**状态**: Merged
**合并时间**: 2026-11-24T13:33:09Z
**创建时间**: 2026-11-24T13:32:47Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 5
- **删除行数**: 4
- **变更文件数**: 1
- **提交数**: 1

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `README.md` | MOD | +5 | -4 |

## PR 描述

Follow-up to #7, found by running it.

#7 replaced the stale numbers with numbers re-read from the API on 2026-11-24: 504 on the account, 87 upstream. Then the workflow ran, `stats/prs.json` moved to 506, and the card rendered 506 above prose that still said 504 — the same contradiction #7 was opened to fix.

## Change

The two figures that move daily are no longer restated:

- the **Evidence** row points at the first badge instead of quoting `87 merges across 41 repositories`
- the **Counts** block names the two bases and says why they differ, without quoting either value

Literal numbers stay only where they cannot drift: 136 findings / 2 real / 134 changed the checker, 62 closed PRs, `doc-drift` v0.1.0's 14 checkers, 185 scripts, and the PR numbers.

Rule this settles: a figure that the workflow rewrites belongs in `stats/` or in the card, and the prose refers to it.


## 相关链接

- **源仓库**: [lxcxjxhx/lxcxjxhx](https://github.com/lxcxjxhx/lxcxjxhx)
- **PR 链接**: https://github.com/lxcxjxhx/lxcxjxhx/pull/9
- **Diff**: https://github.com/lxcxjxhx/lxcxjxhx/pull/9.diff

---
*Auto-generated at 2026-11-25 06:51:51 UTC*
