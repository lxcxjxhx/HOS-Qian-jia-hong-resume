# feat: ProotRuntime pre-installed mode + incremental update + error humanization

**PR 链接**: [lxcxjxhx/HOS-ARES#7](https://github.com/lxcxjxhx/HOS-ARES/pull/7)
**状态**: Merged
**合并时间**: 2026-08-17T05:49:47Z
**创建时间**: 2026-08-17T02:00:02Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 166
- **删除行数**: 9354
- **变更文件数**: 30
- **提交数**: 6

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `app/app/build.gradle` | MOD | +14 | -3 |
| `app/app/src/main/java/com/hos/ares/ProotRuntime.kt` | MOD | +152 | -37 |
| `app/ares-rootfs/agents/deepaudit/run.sh` | DEL | +0 | -46 |
| `app/ares-rootfs/agents/pentestgpt/run.sh` | DEL | +0 | -33 |
| `app/ares-rootfs/agents/securityresearch/run.sh` | DEL | +0 | -39 |
| `app/ares-rootfs/opt/agents/deepaudit/app/__init__.py` | DEL | +0 | -0 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/__init__.py` | DEL | +0 | -0 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/deps.py` | DEL | +0 | -50 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/__init__.py` | DEL | +0 | -0 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/api.py` | DEL | +0 | -17 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/__init__.py` | DEL | +0 | -0 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/agent_tasks.py` | DEL | +0 | -3566 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/auth.py` | DEL | +0 | -84 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/config.py` | DEL | +0 | -560 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/database.py` | DEL | +0 | -694 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/embedding_config.py` | DEL | +0 | -435 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/members.py` | DEL | +0 | -215 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/projects.py` | DEL | +0 | -784 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/prompts.py` | DEL | +0 | -378 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/rules.py` | DEL | +0 | -732 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/scan.py` | DEL | +0 | -598 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/ssh_keys.py` | DEL | +0 | -261 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/tasks.py` | DEL | +0 | -309 |
| `app/ares-rootfs/opt/agents/deepaudit/app/api/v1/endpoints/users.py` | DEL | +0 | -230 |
| `app/ares-rootfs/opt/agents/deepaudit/app/core/__init__.py` | DEL | +0 | -0 |
| `app/ares-rootfs/opt/agents/deepaudit/app/core/config.py` | DEL | +0 | -131 |
| `app/ares-rootfs/opt/agents/deepaudit/app/core/encryption.py` | DEL | +0 | -101 |
| `app/ares-rootfs/opt/agents/deepaudit/app/core/security.py` | DEL | +0 | -34 |
| `app/ares-rootfs/opt/agents/deepaudit/app/db/__init__.py` | DEL | +0 | -0 |
| `app/ares-rootfs/opt/agents/deepaudit/app/db/base.py` | DEL | +0 | -17 |

## PR 描述

## Summary

ProotRuntime core optimizations for zero-network Android security app.

## Changes (+131/-54)

**Pre-installed mode (zero network on first launch):**
- Add \isPreinstalled()\ check for \/opt/HOSARES_PREINSTALLED\ marker
- Skip online bootstrap when pre-installed rootfs detected
- Jump directly to environment verification

**Incremental rootfs update:**
- Extract only changed agent directories from APK assets
- Skip full rootfs extraction when version unchanged
- Use per-agent version stamp files for selective updates

**Error humanization:**
- Add \humanizeError()\ mapping for common failure modes:
  - Network timeout → actionable recovery suggestion
  - Rootfs corruption → clear data + retry guidance
  - LLM API error → service unavailable notice
  - Agent execution → detailed log reference

**Performance:**
- Prioritize rootfs.tar.gz over rootfs.tar
- Add extraction progress reporting via StateFlow

## Impact

- **Zero first-launch network requirement** when pre-installed rootfs is used
- Faster agent updates (incremental, not full)
- Better user experience with actionable error messages

## 相关链接

- **源仓库**: [lxcxjxhx/HOS-ARES](https://github.com/lxcxjxhx/HOS-ARES)
- **PR 链接**: https://github.com/lxcxjxhx/HOS-ARES/pull/7
- **Diff**: https://github.com/lxcxjxhx/HOS-ARES/pull/7.diff

---
*Auto-generated at 2026-09-11 02:51:30 UTC*
