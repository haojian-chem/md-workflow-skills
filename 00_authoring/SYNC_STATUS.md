# Authoring 文件同步状态

更新日期：2026-08-11

# 当前架构基线

```text
Default runtime: Lightweight Runtime v2
Manager core: refactored
Repository root runtime entry: aligned to Lightweight Runtime v2
Skill authoring guide: Lightweight guide, layer boundaries, main templates and deterministic Tool protocol aligned; static revalidation pending
Dedicated Task Execution Agent Skill: not required; root AGENTS.md defines execution behavior
Structure preparation Workflow: lightweight refactor complete
Directory policy: stable Step base directories + task-scoped execution subdirectories
1.1 source recognition: lightweight step interface refactored; revalidation pending
1.2 component/residue classification: lightweight step interface refactored; scientific revalidation pending
1.3 chain/component selection: redesign draft recorded; formal redesign/merge owned by its authoring window
Legacy Workstream / route / event / runtime projection: frozen, not default runtime
```

Lightweight Runtime v2 权威规格：

`00_authoring/lightweight_runtime_v2_spec.md`

Skill 撰写指南当前权威位置：

```text
00_authoring/md-workflow-skill-authoring/SKILL.md
00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md
00_authoring/md-workflow-skill-authoring/references/content_ownership_and_deduplication.md
00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md
00_authoring/md-workflow-skill-authoring/assets/manager_skill.template.md
00_authoring/md-workflow-skill-authoring/assets/workflow_skill.template.md
00_authoring/md-workflow-skill-authoring/assets/operation_skill.template.md
00_authoring/md-workflow-skill-authoring/assets/validator_skill.template.md
```

1.3 当前重设计草案：

`00_authoring/1_3_chain_and_component_selection_redesign_draft.md`

该草案只记录设计输入，不是运行时 Skill。草案与另一个窗口即将同步的新正式设计之间的对照、合并和最终 1.3 冻结由 1.3 authoring 窗口负责；本窗口不继续修改正式 1.3 Operation / Validator，避免并发写入冲突。

# Skill Authoring Lightweight 对齐

当前指南已经完成以下默认规则对齐：

- `md-workflow-skill-authoring/SKILL.md` 从 Workstream / route / subagent task-result 模型切换到 Lightweight Runtime v2；
- 默认 authoring 启动不再要求读取 `03_contracts/**`、route planning protocol、runtime subagent protocol 或 runtime record commit protocol；
- 四层逻辑职责为：Manager 任务管理、Workflow 阶段科学关系、Operation 业务操作、Validator 科学/技术验证；
- Task Execution Agent 是长期运行角色，不是新的 Skill layer，也不需要额外通用 Skill；
- Step-facing Skill 或配套 Operation + Validator 合计必须定义：
  - `purpose`
  - `object requirements`
  - `reuse conditions`
  - `execution rules`
  - `validation requirements`
  - `official results`
- Operation + dedicated Validator 通过 content map 分配唯一 owner，避免重复规则；
- Step 工作目录使用 `<base_work_directory>/<task_id>/`；
- Manager 只记录任务目录路径，不创建任务专属执行目录；
- Task Execution Agent 先检查 reuse，确需执行时才创建当前 `<task_id>/`；直接复用不创建空目录；
- 普通科学歧义由当前 Task Execution Agent 在执行对话中直接向用户确认；
- Manager / Workflow / Operation / Validator 四套主模板已同步；
- `content_ownership_and_deduplication.md` 已同步到 Step interface / official-results 模型；
- `deterministic_tool_protocol.md` 已改为显式业务输入的 Lightweight Tool 规则，不再要求 FAST/FULL runtime state 闭环；
- 历史 Tool 若仍依赖 Legacy `task.yaml` / route / event / transaction，只能标记为 Legacy-interface，不能为了调用它重建旧 Runtime；
- `runtime_subagent_protocol.md` 和 `runtime_record_commit_protocol.md` 已增加明确 `LEGACY / FROZEN` 标识，保留历史内容但禁止作为普通 authoring 输入。

# 当前仍需的 Authoring 工作

当前 Skill 撰写指南内容本身已完成 Lightweight 对齐，剩余主要是**验证和 Tool Authoring 子系统**，而不是继续重写业务 Skill 指南：

- 重新验证 `md-workflow-skill-authoring/scripts/` 中静态检查，确认不存在把 Workstream / route / subagent contract 当成成功条件的旧检查；
- 对已有 authoring fixtures / validation evidence 做 Lightweight 重新验收；
- `md-workflow-tool-authoring` 自身仍需 Lightweight 对齐；
- Legacy subagent / record protocols 保持冻结，不继续扩展。

# 当前目录策略

项目初始化只建立稳定基础目录到 Workflow / Step 层。

不同任务的实际执行目录固定为：

```text
<base_work_directory>/<task_id>/
```

职责边界：

```text
项目初始化 / Manager
→ 可以建立或确认稳定 Step 基础目录
→ 在 Task Sheet 中记录预计 `<base>/<task_id>/` 路径
→ 不创建任务专属目录

Task Execution Agent
→ 子环节开始先检查复用
→ 只有确实需要本地执行时才创建当前任务 `<task_id>/`
→ 如果直接复用已有正式结果，不创建空目录
```

# 当前科学 Skill 基线

```text
1.1 source recognition:
  Lightweight interface complete
  task-scoped outputs
  runtime revalidation pending

1.2 component/residue classification:
  Lightweight interface complete
  task-scoped outputs
  scientific state remains present_unvalidated pending revalidation

1.3 chain/component selection:
  2026-07-31 PASS 仅为旧实现历史结果
  本次重设计由独立 1.3 authoring 窗口继续完成
  本窗口只提供 authoring guide，不执行 draft ↔ 正式设计合并

runtime_schema_validator:
  ACTIVE_LEGACY

source_recognition_deterministic v0.1.0:
  ACTIVE_LEGACY_INTERFACE
  Lightweight 显式路径接口待适配

runtime_dependency_preflight:
  ACTIVE_LEGACY_INTERFACE
  Lightweight 1.2 不再依赖 Manager pre-Agent closure 路径
```

# 后续顺序

当前约定：

```text
1. 由 1.3 authoring 窗口完成 1.3 草案 ↔ 新正式设计合并与最终同步
2. 1.3 同步完成后，确定 Workflow 2 与 Workflow 3 的子环节、小节编号和职责分配
3. 再按当前 Lightweight Skill authoring guide 逐项编写 / 重构对应 Skills
```

同时独立推进 Authoring 基础设施验证：

- authoring 静态检查重验；
- `md-workflow-tool-authoring` Lightweight 对齐；
- Lightweight Runtime 真实任务验收。

本文件只记录当前同步状态和权威位置，不复制具体科学规则。
