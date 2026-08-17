# Authoring directory guide

本目录服务于 MD Workflow Skill / Tool 的设计、冻结、同步和多窗口 authoring。它不是科研项目运行目录。

## Current-authority rule

开始 authoring 时优先使用：

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

发生设计冲突时：

```text
current Skill / Tool guide
> matching architecture-freeze record
> MD_WORKFLOW_MASTER_PLAN.md / SYNC_STATUS.md
> historical redesign / validation / benchmark / Legacy Runtime files
```

**文件存在不等于当前有效。** `SUPERSEDED` / `LEGACY` 文件只作为 Git 历史入口，不得用于重建当前接口。

## Current Skill model

新科研 Skill 默认采用：

```text
main Skill
├── references/
├── schemas/           # only when truly useful
├── scripts/
└── supporting Skill   # only for complex, clear boundaries
```

不再强制 Workflow / Operation / Validator 分类，也不要求新 Skill 落入：

```text
01_workflows/
02_operations/
02_validators/
```

这些目录仍包含历史时期创建、目前可能仍有效的 Skill，但只是现存物理路径，不是新 authoring 模板。

当前 Stage 4 / Stage 5 已采用 stage-centric integrated main Skill：

```text
04_md_simulation/
05_analysis/
```

## Agent-guidance principle

Skill 的目的，是指导 Agent 如何处理科研任务，而不是把 Agent 锁进固定 parser / wrapper / dispatcher。

Parser / Tool 用于真正需要确定性 parsing、变换、计算或校验的动作；除非科学/技术方法本身要求，不把某个 Tool 写成 Agent 理解输入的唯一入口。

## Multi-window rule

```text
read scope can be broad
write ownership must be narrow
```

每个窗口可以并且应该按需读取不归自己写入的上下游/相邻 Skill，以理解接口和避免重复。

未经明确重新分配，不得：

- 修改其他 Skill；
- 在当前 Skill 中替其他 Skill 定义内部流程、默认参数、validation 或 official results。

发现跨 Skill 问题时提交 finding / handoff 给对应 owner 或 main window。

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
- `skill_inventory.yaml`：Skill discovery/status metadata；
- `file_ownership.yaml`：多窗口写入所有权；
- `SYNC_STATUS.md`：当前同步状态。

当前普通科研 Skill 模板：

`md-workflow-skill-authoring/assets/skill.template.md`

旧 `workflow_skill.template.md` / `operation_skill.template.md` / `validator_skill.template.md` 已 `SUPERSEDED`。

## Legacy / superseded material

旧 Workstream / route / event / runtime projection / transaction 架构已经冻结为 Legacy。

Legacy contracts、runtime projection 和历史 authoring validation 可以保留用于历史追溯或明确迁移维护，但普通 current authoring 不读取这些内容作为默认设计依据。
