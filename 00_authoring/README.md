# Authoring directory guide

本目录服务于 MD Workflow Skill / Tool 的设计、冻结、同步和多窗口 authoring。它不是科研项目运行目录。

## Current-authority rule

开始 authoring 时，优先使用：

```text
00_authoring/AUTHORING_RULES.md
00_authoring/lightweight_runtime_v2_spec.md
00_authoring/SYNC_STATUS.md
00_authoring/MD_WORKFLOW_MASTER_PLAN.md
00_authoring/skill_inventory.yaml
00_authoring/file_ownership.yaml
目标 content map
目标当前 Skill / Tool guide
```

发生设计冲突时按以下顺序判断：

```text
current Skill / Tool guide
> matching WORKFLOW*_ARCHITECTURE_FREEZE*.md
> MD_WORKFLOW_MASTER_PLAN.md / SYNC_STATUS.md
> historical redesign / validation / benchmark / Legacy Runtime files
```

**文件存在不等于当前有效。** 明确标记 `SUPERSEDED` 或 `LEGACY` 的文件只作为 Git 历史入口，不得用于重建当前接口。

## Current stage freeze records

```text
WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md
WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md
WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md
WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
```

## Authoring support

- `md-workflow-skill-authoring/`：Skill 编写指导；
- `md-workflow-tool-authoring/`：Tool 生命周期指导；
- `content_maps/`：内容唯一归属；
- `content_map.schema.yaml`：content map 结构；
- `skill_inventory.yaml`：当前 Skill discovery/status metadata；
- `file_ownership.yaml`：多窗口互斥写入范围；
- `SYNC_STATUS.md`：当前同步状态。

`skill_inventory.yaml` 和 `SYNC_STATUS.md` 是导航/状态信息，不应复制具体 Skill 的科学规则。

## Legacy / superseded material

旧 Workstream / route / event / runtime projection / transaction 架构已经冻结为 Legacy。

Legacy contracts、runtime projection 和历史 authoring 验证可以保留用于历史追溯或明确迁移维护，但普通 Lightweight Skill authoring 不读取这些内容作为当前默认设计依据。

为减少版本混乱，已过期的 root-level redesign/validation/benchmark 文件应改为简短 `SUPERSEDED` / `LEGACY` tombstone；原内容保留在 Git history 中。
