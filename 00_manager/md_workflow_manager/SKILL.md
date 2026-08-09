---
name: md_workflow_manager
description: 管理真实 MD 项目的入口、Workstream、路线、执行后端、状态记录、用户决定和恢复；运行时优先消费 runtime 紧凑投影，不执行结构、拓扑、模拟或分析业务操作。
---

# 目标

Manager 负责真实 MD 项目的语义管理边界：项目入口、Focus、Workstream、跨 Workflow 路线、执行后端选择、用户决定、恢复和管理记录提交。

Manager 不承担 Operation/Validator 的业务工作，也不应通过反复读取静态设计文档来模拟确定性 schema、引用、序列化或事务。

# Runtime 启动

真实 MD 项目运行时默认只读取：

1. 根 `AGENTS.md`；
2. `runtime/runtime_manifest.yaml`；
3. `runtime/manager_runtime_spec.yaml`；
4. 已存在时的 `00_project_state/project_state.yaml`；
5. 当前 Focus Workstream state；
6. 本轮直接需要的 active route / decision / submission / artifact 摘要。

正常 runtime **不得默认读取**：

- `00_authoring/**`；
- `design_records/**`；
- 完整 Manager references；
- `03_contracts/*.schema.yaml` 正文；
- 无关 Workflow 或业务 Skill；
- 全项目历史和科学日志。

以下情况才允许按 runtime manifest 回退读取权威 source：

- runtime projection 缺失、版本不兼容或 provenance 失效；
- 项目进入 `NEEDS_RECOVERY`；
- runtime spec 与实际状态/contract 冲突；
- route 需要语义重规划且 compact spec 信息不足；
- Tool/contract 调试；
- 用户明确要求完整架构审计。

schema 由确定性 Tool 消费；Manager LLM 不为“保险”逐字段重读 schema。

# 使用边界

用于：

- `INSPECT | PLAN | EXECUTE`；
- `NEW | RESUMABLE | NEEDS_RECOVERY` 入口管理；
- Focus 与 Workstream 生命周期；
- route scope、跨 Workflow route 和 revision；
- 执行后端选择；
- 用户决定与异常处理；
- 外部 submission 状态；
- `00_project_state/**` 与 `00_project_records/**` 的提交授权。

不用作：

- 一般 MD 问答；
- 结构/拓扑/MDP/轨迹业务修改；
- 科学质量判定；
- Skill/Tool 编写。

# 核心 barrier

```text
ENTRY_INTERPRETABLE
→ PROJECT_INITIALIZED / RESUMABLE
→ ROUTE_SCOPE_RESOLVED
→ ACTIVE_ROUTE_AVAILABLE
→ BUSINESS_EXECUTION
```

硬规则：

- NEW 初始化完成前不进入 Workflow 业务执行；
- route scope 未明确时不创建业务 route；
- active route 不存在或不适用时不创建业务执行单元；
- 不根据阶段名编造 Workflow 内部步骤；
- 不自动重试失败、降低 gate 或跳过 Validator；
- 同时最多一个前台 MD Agent context；
- 后台 tmux/调度任务不自动改变 Focus。

# 项目目录与权限

```text
<project_root>/
├── 00_project_state/
├── 00_project_records/
├── 01_structure_preparation/
├── 02_topology_preparation/
├── 03_md_preparation/
├── 04_md_simulation/
└── 05_analysis/
```

Manager 控制以下目录的提交边界：

```text
00_project_state/**
00_project_records/**
```

Operation/Validator 只能写 task 授权业务路径。

“Manager controls commit”不等于“Manager LLM 手工生成全部 YAML”。已批准 deterministic builder/recorder 可在 Manager 授权下构造和提交机械记录。

# 项目入口

## 最小入口检查

只使用文件/目录元数据和最小状态对象判断：

```text
NEW | RESUMABLE | NEEDS_RECOVERY
```

入口检查不解析 PDB/mmCIF 内容，不扫描全部 route/artifact/event 历史，也不执行科学检查。

### NEW

仅适用于：没有可信状态，项目为空或只有初始输入，且没有明显旧业务产物。

初始化只建立管理目录、初始 project state、首个 Workstream 和必要事件。业务输入内容由后续对应 Operation/Validator 检查。

初始化细节优先由 `runtime/manager_runtime_spec.yaml` 表达；只有初始化异常/调试时才读取 `references/project_initialization_protocol.md`。

### RESUMABLE

项目状态可解释，当前目标可以安全继续。

### NEEDS_RECOVERY

状态、根目录、索引、artifact lineage、目录所有权或外部任务事实无法安全解释时使用。恢复完成前不创建新的写入型业务执行。

# 请求与路线范围

请求动作可以组合：

```text
INSPECT
PLAN
EXECUTE
```

纯 INSPECT 不要求 route scope。

PLAN/EXECUTE 的终点必须来自：

- 用户明确指定；
- resolved decision；
- 用户明确继续一个仍适用的 active route；
- 用户明确按已记录 Workstream 目标继续。

没有这些证据时，不默认补成“下一步”“当前 Workflow 结束”或“项目终点”，而是形成 blocking decision。

正常 scope 解析使用 `runtime/manager_runtime_spec.yaml`；复杂歧义、跨 Workflow 冲突或 revision 调试时才读取完整 route planning protocol。

# Focus 与 Workstream

一个 Manager 运行周期只有一个主要 Focus：

```text
PROJECT | WORKSTREAM
```

Focus 优先级：用户指定 → 指定对象所属 Workstream → 本轮写入/执行目标 → 未闭环前台任务 → 最近 Focus → 仍不唯一则确认。

已有有效下游产物、模拟已开始、需要保留旧版本/比较方案，或上游修改会使旧结果失效时创建新 Workstream；否则可在尚未闭环且无下游依赖的原 Workstream 内修正。

# Workflow runtime

## PLAN

优先读取：

- `runtime/runtime_manifest.yaml` 中的 stage registry projection；
- 本轮涉及的 `runtime/workflows/<workflow>.runtime.yaml`。

compact runtime spec 信息足够时，不读取完整 Workflow `SKILL.md`。

只有以下情况进入完整 Workflow 语义规划：

- runtime spec 标记 `semantic_planning_required`；
- 条件/接口无法由 compact spec 表达；
- runtime projection 缺失或 provenance 失效；
- route revision 需要新的科学/语义判断。

Manager 仍负责跨 Workflow fragment/节点接口一致性与完整 route 的提交。

## EXECUTE

推进前确认：

- active route 存在且适用；
- 当前 route node 可定位；
- 当前 Workstream 不处于 blocking recovery/decision；
- node 所需输入可定位。

普通执行优先读取当前 `*.runtime.yaml` 中该 node 的紧凑信息，而不是完整 Workflow。

R5 fast-path 尚未正式激活前，route node 推进仍按当前 contract 生成/核验 execution decision；R5 激活后可在严格条件下跳过重复 Workflow LLM 重判。

# 执行后端

逻辑 Operation/Validator 职责与执行后端分离。

候选后端：

```text
DETERMINISTIC
AGENT_TASK
AGENT_SEQUENCE
```

Manager 按 runtime spec 和 active Tool capability 解析后端：

### DETERMINISTIC

仅当：

- node 明确标记可确定性执行；
- 所需 capability 有 `ACTIVE` Tool；
- 不需要科学判断、用户决定或开放式解释。

此模式不创建业务子 Agent。

### AGENT_TASK

当前默认语义后端。一个前台 Agent context 执行一个明确 Operation、Validator 或共享即时上下文的 Operation+Validator 单元。

### AGENT_SEQUENCE

架构已允许，但在 sequence contract / eligibility validation 未实现前保持 `DISABLED_BY_DEFAULT`。不得仅为省时间私自串联多个 node。

具体边界见 runtime manifest 和 `runtime_subagent_protocol.md`；正常 runtime 不需要每次全文读取该协议。

# Task 与记录闭环

业务执行完成后必须保留：

- 可定位的 task identity；
- Operation/Validator 各自结果；
- 必要 artifact/decision/submission；
- 一个终态 event；
- 必要 Workstream state 更新；
- 用户可见 closure。

机械记录构造优先交给 deterministic builder/recorder。Manager LLM 只提供语义变化，不重复转写工具已经能够确定的字段。

在 R4 recorder 尚未 ACTIVE 前继续使用现有最小闭环，但不得额外生成无变化 project state、snapshot、route revision、逐 task session 增量或重复审计。

# 校验

- 普通 changed runtime instances：一次 FAST；
- FULL 只用于 runtime spec/权威协议明确列出的关键节点；
- schema/meta-validation 由 Tool 执行；
- 已有有效 validation result 且 candidate 未变化时不重复；
- Tool FAIL/ERROR 时不得宣称通过或降低 gate。

NEW 初始化的最终 candidate validation 模式由 R6 单独收敛；当前实现保持与现有初始化协议兼容，直到 R6 migration 完成。

# 用户决定与异常

以下情况必须退出普通快速路径并进入 Manager/Workflow 语义判断：

- blocking decision；
- route-affecting evidence；
- failure；
- artifact-interface conflict；
- unexpected output；
- active route 与实际状态不一致；
- recovery；
- 高风险或不可逆动作。

子 Agent/Tool 不直接向用户提问，由 Manager 统一展示并持久化 decision。

# 外部任务

外部 submission 状态：

```text
PREPARED → SUBMITTED → RUNNING → FINISHED_UNVERIFIED
                                      ↓
                              COMPLETED | FAILED
```

另有 `CANCELLED | UNKNOWN`。tmux/job 消失不能直接判定成功。

# 结束

本轮结束前确保：

- 无活动前台 Agent context；
- 必要状态/记录已提交；
- blocking decision 已展示；
- 已完成 task 有精简 closure；
- 未因“保险”重新读取无关 authoring corpus 或执行重复全量审计。
