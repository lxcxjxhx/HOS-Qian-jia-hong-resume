# build: optimize APK size + upgrade build toolchain

**PR 链接**: [lxcxjxhx/HOS-ARES#2](https://github.com/lxcxjxhx/HOS-ARES/pull/2)
**状态**: Merged
**合并时间**: 2026-08-17T05:49:03Z
**创建时间**: 2026-08-17T01:56:19Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 28
- **删除行数**: 9
- **变更文件数**: 4
- **提交数**: 1

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `app/app/build.gradle` | MOD | +14 | -3 |
| `app/ares-rootfs/requirements/reasonix.txt` | MOD | +12 | -4 |
| `app/build.gradle` | MOD | +1 | -1 |
| `app/gradle/wrapper/gradle-wrapper.properties` | MOD | +1 | -1 |

## PR 描述

## Summary

Optimize APK size by ~15MB and upgrade build toolchain.

## Changes

- **AGP upgrade**: 8.5.2 → 8.7.3
- **Gradle upgrade**: 8.7 → 8.14.4
- **ProGuard enabled**: Code shrinking and dead code removal
- **Packaging options**: Exclude unused native libs and empty directories
- **Reasonix dependencies**: Updated for parallel scheduling support

## Impact

- Reduces APK download size
- Faster installation
- Better runtime performance through code shrinking

## 相关链接

- **源仓库**: [lxcxjxhx/HOS-ARES](https://github.com/lxcxjxhx/HOS-ARES)
- **PR 链接**: https://github.com/lxcxjxhx/HOS-ARES/pull/2
- **Diff**: https://github.com/lxcxjxhx/HOS-ARES/pull/2.diff

---
*Auto-generated at 2026-09-10 02:57:23 UTC*
