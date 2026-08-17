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
> archived / historical / Legacy files
```

**文件存在不等于当前有效。** archive、Legacy 和 Git history 只用于历史追溯，不得用于重建当前接口。

## Root layout

`00_authoring/` 根目录只保留少量 current authoring 入口文件；阶段冻结记录和过期历史材料分别集中到专用目录：

```text
00_authoring/
├── README.md
├── AUTHORING_RULES.md
├── MD_WORKFLOW_MASTER_PLAN.md
├── SYNC_STATUS.md
├── lightweight_runtime_v2_spec.md
├── skill_inventory.yaml
├── file_ownership.yaml
├── architecture_freezes/
├── archive/
├── content_maps/
├── md-workflow-skill-authoring/
├── md-workflow-tool-authoring/
└── window_work_orders/
```

不要把新的 Stage freeze、临时 redesign、validation report 或 superseded Markdown 再散放回 `00_authoring/` 根目录。

## Current Skill model

新科研 Skill 默认采用：

```text
main Skill
├── references/        # 仅放仍属于当前 Skill 的长/条件性细节
├── schemas/           # only when truly useful
├── scripts/           # Skill-local deterministic helper
└── supporting Skill   # only for complex, clear boundaries
```

只有 main `SKILL.md` 是默认必需文件。不要先生成一套目录或角色分类，再把科研职责塞进去。

生成、重构或冻结 Skill 时必须按需读取：

`md-workflow-skill-authoring/references/skill_generation_rules.md`

其中固定：

```text
一个职责 → 一个 main Skill
长而同属当前职责 → reference
复杂且独立 → supporting Skill
确定性机械能力 → script / Tool
已有 owner 的规则 → 引用，不复制
已被取代的 Markdown → archive，不留在 active path
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
- 在当前 Skill 中替其他 Skill 定义内部流程、默认参数、validation 或 official results；
- 复制/改写其他 owner 已有规则形成 shadow specification。

发现跨 Skill 问题时提交 finding / handoff 给对应 owner 或 main window。

## Architecture freeze records

当前 Stage architecture-freeze 统一放在：

`00_authoring/architecture_freezes/`

当前记录：

```text
architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md
architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md
architecture_freezes/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md
architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
```

以后新增 Stage freeze 也进入该目录，不再直接放到 `00_authoring/` 根目录。

## Markdown archive

过期 Markdown 的 current 归档目录：

`00_authoring/archive/`

规则：

- authority 已明确被取代的 `.md` 从 active path 移出；
- current 引用必须先迁移到新 owner；
- active path 不同时保留 `SUPERSEDED` / `LEGACY` tombstone 和 archive 副本；
- archive 不进入普通 startup/read list；
- Git history 保存完整版本历史；
- 不能因为文件“较旧”就归档仍然有效的 current guide / reference / architecture-freeze。

Archive 边界见：

`00_authoring/archive/README.md`

## Authoring support

- `architecture_freezes/`：各 Stage 当前 architecture-freeze 集中目录；
- `archive/`：非 current 的历史 authoring Markdown；
- `md-workflow-skill-authoring/`：Skill 编写指导；
- `md-workflow-tool-authoring/`：Tool 生命周期指导；
- `content_maps/`：内容唯一归属；
- `content_map.schema.yaml`：content map 结构；
- `skill_inventory.yaml`：Skill discovery/status metadata；
- `file_ownership.yaml`：多窗口写入所有权；
- `SYNC_STATUS.md`：当前同步状态。

当前普通科研 Skill 模板：

`md-workflow-skill-authoring/assets/skill.template.md`

旧 workflow/operation/validator 专用模板已经移入 archive，不再留在 active assets。

## Legacy / superseded material

旧 Workstream / route / event / runtime projection / transaction 架构已经冻结为 Legacy。

需要保留的历史 authoring Markdown 应移入 `00_authoring/archive/`；普通 current authoring 不读取这些内容作为默认设计依据。Legacy contracts/runtime 等非 Markdown 历史材料仍按其当前专门边界管理。
