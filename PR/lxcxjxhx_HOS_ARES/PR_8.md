# feat: bootstrap.sh pre-installed validation + entry.sh tool shims

**PR 链接**: [lxcxjxhx/HOS-ARES#8](https://github.com/lxcxjxhx/HOS-ARES/pull/8)
**状态**: Merged
**合并时间**: 2026-08-17T05:49:57Z
**创建时间**: 2026-08-17T02:00:56Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 297
- **删除行数**: 293
- **变更文件数**: 2
- **提交数**: 1

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `app/app/src/main/assets/root/entry.sh` | MOD | +149 | -245 |
| `app/ares-rootfs/bootstrap.sh` | MOD | +148 | -48 |

## PR 描述

## Summary

Bootstrap and entry point optimizations for pre-installed rootfs mode.

## Changes

**bootstrap.sh (+196/-97):**
- Add pre-installed mode detection via \/opt/HOSARES_PREINSTALLED\
- Skip pip install in pre-installed mode, verify env instead
- Add wheel-based fallback recovery for missing dependencies
- Add dry-run pre-check to validate rootfs integrity
- Add per-module pass/fail verification reporting

**entry.sh (+198/-196):**
- Add tool shim layer with fallback resolution
- Add PATH resolution for agent tools
- Add agent runtime environment setup
- Support both pre-installed and online bootstrap paths

## 相关链接

- **源仓库**: [lxcxjxhx/HOS-ARES](https://github.com/lxcxjxhx/HOS-ARES)
- **PR 链接**: https://github.com/lxcxjxhx/HOS-ARES/pull/8
- **Diff**: https://github.com/lxcxjxhx/HOS-ARES/pull/8.diff

---
*Auto-generated at 2026-09-10 02:57:23 UTC*
