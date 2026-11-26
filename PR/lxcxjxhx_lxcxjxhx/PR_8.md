# fix(workflow): hand the stats across the step boundary again

**PR 链接**: [lxcxjxhx/lxcxjxhx#8](https://github.com/lxcxjxhx/lxcxjxhx/pull/8)
**状态**: Merged
**合并时间**: 2026-11-24T13:29:35Z
**创建时间**: 2026-11-24T13:29:09Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 17
- **删除行数**: 3
- **变更文件数**: 1
- **提交数**: 1

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `.github/workflows/update-stats.yml` | MOD | +17 | -3 |

## PR 描述

#7 merged, and the workflow failed on its first manual run ([run 45403111427](https://github.com/lxcxjxhx/lxcxjxhx/actions/runs/45403111427)):

```
stat-prs was not injected
Process completed with exit code 1
```

## Cause

#7 removed the five `echo "PRS=$PRS" >> $GITHUB_ENV` lines, calling them redundant because `$GITHUB_ENV` "had already exported" the values. It is the other way round: those writes are what put the values into `$GITHUB_ENV`. The SVG step then ran `perl` against empty variables, blanked all five `<text id="stat-*">` values, and the check caught it 鈥?which is the one part of #7 that behaved as intended.

## Fix

- the handover is back, as a single `{ ... } >> "$GITHUB_ENV"` block, so it is hard to mistake for boilerplate again
- the SVG step now opens with `set -euo pipefail` and `: "${PRS:?...}"` for all five variables, so a missing handover fails on the first line instead of after five silent substitutions
- `FOLLOWERS=$FOLL` in the log line was a stale name; it now prints the variable it actually reads

## How it was checked

Two structural checks ran locally before opening this:

- a YAML-level check that every `${VAR}` read in the SVG step is assigned in the fetch step and handed over through `$GITHUB_ENV`. Removing the handover block makes it fail, which is exactly this regression.
- a dry run of the five injection regexes and the new `grep` check against the shipped `profile-anim.svg`: all five ids take a value, and a blanked value is rejected.

Real acceptance is the run on `main`: [run 45404051921](https://github.com/lxcxjxhx/lxcxjxhx/actions/runs/45404051921) 鈥?all five steps green, `stats/prs.json` 504 鈫?506 and the card redrawn in the same commit.


## 相关链接

- **源仓库**: [lxcxjxhx/lxcxjxhx](https://github.com/lxcxjxhx/lxcxjxhx)
- **PR 链接**: https://github.com/lxcxjxhx/lxcxjxhx/pull/8
- **Diff**: https://github.com/lxcxjxhx/lxcxjxhx/pull/8.diff

---
*Auto-generated at 2026-11-26 06:43:15 UTC*
