# refactor: remove deepaudit agent (~40K lines)

**PR 链接**: [lxcxjxhx/HOS-ARES#3](https://github.com/lxcxjxhx/HOS-ARES/pull/3)
**状态**: Merged
**合并时间**: 2026-08-17T05:49:11Z
**创建时间**: 2026-08-17T01:56:50Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 14
- **删除行数**: 9693
- **变更文件数**: 30
- **提交数**: 2

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `app/app/build.gradle` | MOD | +14 | -3 |
| `app/ares-rootfs/agents/deepaudit/run.sh` | DEL | +0 | -46 |
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
| `app/ares-rootfs/opt/agents/deepaudit/app/db/init_db.py` | DEL | +0 | -284 |
| `app/ares-rootfs/opt/agents/deepaudit/app/db/session.py` | DEL | +0 | -33 |
| `app/ares-rootfs/opt/agents/deepaudit/app/main.py` | DEL | +0 | -131 |

## PR 描述

## Summary

Remove the DeepAudit agent, reducing APK size by ~40MB.

## Changes

- Remove 127 files (39,614 lines) of DeepAudit code
- Remove heavyweight RAG/knowledge-base pipeline
- Remove complex LLM adapter layer (Baidu, Doubao, MiniMax, LiteLLM)
- Remove 30+ vulnerability knowledge modules
- Remove pgvector + SQLite RAG dependencies

## Rationale

DeepAudit was a monolithic security audit platform that duplicated
functionality already provided by Argus, Strix, and RepoAudit.
Its RAG pipeline added significant complexity without proportional value.

The functionality will be re-implemented as lightweight skills
within the Strix agent framework.

## Impact

- APK size reduction: ~40MB
- Build time improvement (fewer dependencies)
- Reduced maintenance surface

## 相关链接

- **源仓库**: [lxcxjxhx/HOS-ARES](https://github.com/lxcxjxhx/HOS-ARES)
- **PR 链接**: https://github.com/lxcxjxhx/HOS-ARES/pull/3
- **Diff**: https://github.com/lxcxjxhx/HOS-ARES/pull/3.diff

---
*Auto-generated at 2026-09-10 02:57:23 UTC*
