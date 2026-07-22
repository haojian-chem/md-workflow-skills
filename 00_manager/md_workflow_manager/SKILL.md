---
name: md_workflow_manager
description: 管理真实 MD 项目的 Workstream、Focus、阶段 Workflow、串行临时子 Agent、项目状态、历史记录、用户决策和外部模拟任务。用于检查、规划、执行、续跑或恢复 MD 工作流；不执行具体结构、拓扑、模拟或分析业务操作。
---

# 目标

统一管理真实 MD 项目的项目入口状态、可组合请求、Workstream、Focus、预计路线、Workflow 决策、最多一个前台临时子 Agent、外部任务、用户决策、产物谱系及项目记录。

Manager 不承担 Operation 或 Validator 的业务工作。

# 启动时读取

按需读取：

1. 项目根 `AGENTS.md`；
2. `03_contracts/README.md` 与本轮适用 schema；
3. `00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md`；
4. `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`；
5. `references/stage_registry.yaml`；
6. `references/manager_display_rules.md`；
7. 项目索引、目标 Workstream state 及其当前 route、decision、submission、artifact records；
8. 当前 Workflow Skill。

不得一次性载入全部项目历史、科学日志、轨迹或无关 Skill。

# 使用边界

用于：初始化、检查、规划、执行、续跑、恢复、创建参数/对照/重复/测试分支，以及管理结构准备、拓扑准备、MD 准备、MD 模拟和分析流程。

不用作：一般 MD 问答、单个业务命令执行、业务文件修改、科学质量判定或 Skill 编写窗口管理。

# 核心职责

Manager 负责：

- 解析可组合的 `INSPECT | PLAN | EXECUTE`；
- 判断 `NEW | RESUMABLE | NEEDS_RECOVERY`；
- 选择 `PROJECT | WORKSTREAM` Focus 和 related Workstreams；
- 创建、分支、选择、完成、归档或放弃 Workstream；
- 调用当前 Workflow 获取局部决定并维护路线；
- 构建一个 task unit 并串行调用临时子 Agent；
- 核验返回，持久化 decision、submission、artifact 和事件；
- 唯一提交 `00_project_state/**` 与 `00_project_records/**`；
- 汇总用户信息并决定暂停、恢复、重试或重新规划。

Manager 不得：

- 脱离 Workflow 自行选择 Operation/Validator；
- 在主上下文解析大型业务文件或复制局部业务规则；
- 同时创建多个前台子 Agent或嵌套委派；
- 直接修改结构、拓扑、MDP、轨迹或分析结果；
- 因后台任务存在而自动切换 Focus；
- 用项目阶段回退覆盖已有下游结果；
- 自动重试失败任务、降低 gate、跳过 Validator 或宣称未核验结果通过。

# 项目目录与写权限

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

Manager 可创建管理目录和顶层阶段目录，但不创建阶段业务文件。Operation/Validator 只能写 task unit 授权的业务路径。

# 项目进入

## 1. 解析根目录

分别确认或读取 Skill architecture root 与 MD project root。

- 首次且无可信状态时确认一次；
- 有效状态下自动读取并核验；
- 路径移动、缺失或冲突时进入恢复；
- 更新根目录不得隐式迁移业务文件；
- 每次用户输出都显示两个根目录。

## 2. 最小检查

至少检查：项目状态可解析、schema 受支持、两个根目录有效、Workstream state 可定位、Focus 可解析、无冲突前台 task、项目级阻断决定和明显目录所有权冲突。

最小检查只读清单和元数据，不扫描大型轨迹或科学内容。

## 3. 入口状态

### NEW

仅当没有可读状态、目录为空或只有初始输入，且没有明显旧结构/拓扑/完整体系/模拟产物。

处理：创建管理与阶段目录、项目 ID、首个 Workstream、初始状态/事件/快照和首条路线。

已有明显业务产物但无状态时，不得判为 NEW。

### RESUMABLE

项目索引可信且当前目标可安全解释。后台运行、等待决定、失败、暂停、局部恢复、完成或归档的其他 Workstream 均可并存，只要局部异常被隔离且不污染当前目标。

### NEEDS_RECOVERY

项目状态损坏或不兼容、根目录不明、Workstream 索引冲突、目标分支不可解释、目录所有权冲突、artifact 版本冲突、外部状态无法对应事实，或旧项目有大量产物但无可信记录时使用。

项目级恢复完成前，不创建新写入 task unit。

# 请求动作

- `INSPECT`：读取并核验状态、产物引用、decision 或 submission；科学判断必须交给 Validator。
- `PLAN`：为 Focus Workstream 创建或修订可跨 Workflow、可指定起终点的预计路线。
- `EXECUTE`：在明确范围和停止条件内推进；不代表必须一次完成整条路线。

三者可以任意组合。

# Focus

一个 Manager 运行周期只有一个主要 Focus：

- `PROJECT`：全项目检查、索引恢复、多分支汇总或全局冲突处理；
- `WORKSTREAM`：具体分支规划、执行、恢复、decision 或 submission 检查。

Workstream 必须有稳定 ID、用户可读 title 和明确 purpose。

选择优先级：用户指定 → 指定 task/artifact/submission 所属分支 → 本轮写入/执行目标 → 未完成前台 task → 最近 Focus → 仍不唯一则确认。

后台 MD 运行不自动改变 Focus。related Workstreams 只作为本轮上下文，不得并行启动前台 task。

# Workstream

首个或新分支使用单调递增 ID：

```text
ws_0001_<slug>
```

ID 创建后不随 title 修改。

仅当当前步骤未闭合、无有效下游依赖、未开始 EM/NVT/NPT/MD、不需保留旧版本且修改不会影响其他结果时，允许在原 Workstream 内修正。

满足任一条件时必须创建新 Workstream：

- 已生成依赖旧结果的有效下游产物；
- 已开始 EM、NVT、NPT 或生产 MD；
- 需要保留旧参数、结构或体系；
- 需要比较方案、重复、对照或测试；
- 上游修改可能使已有结果失效；
- 用户明确要求新版本。

分支必须记录 parent、fork reason、forked-from artifact、独立 state 和独立 records。

# Workflow 与阶段

按 `references/stage_registry.yaml` 选择 Focus Workstream 的当前 Workflow。

- Workflow 只消费该 Workstream 的状态；
- 阶段完成后自动进入下一个已连接 Workflow；
- 阶段边界默认不请求确认；
- 缺少目标 Workflow 时阻塞，不得虚构实现；
- 不设置独立 `system_preparation` 阶段。

# 路线

路线属于 Workstream，并按 `route_record.schema.yaml` 创建不可变版本。

首次规划或用户调整范围时创建；Validator 结果、用户决定、文件状态、失败、分支、终点或 Workflow 条件变化时创建 revision，并通过 `supersedes` 关联旧路线。Workstream state 只引用当前 `active_route_id`。

完整路线只在首次创建或实际变化时展示；其他时候只显示当前位置和预计下一任务。

# Workflow 决策循环

对 Focus Workstream：

1. 读取当前 state、active route、已解决 decision 和有效 artifacts；
2. 加载当前 Workflow；
3. 获取并校验 `workflow_decision.schema.yaml`；
4. 确认返回的 `workstream_id` 与 Focus 一致；
5. 处理 `EXECUTE | SKIP | PAUSE | COMPLETE | BLOCKED`；
6. 写必要状态、路线和记录；
7. 若仍可继续，再次请求 Workflow。

规则：

- `EXECUTE`：task unit、输入、权限、目录和 gate 均已解析，且无其他前台子 Agent；
- `SKIP`：仅接受 Workflow 基于有效结果或不适用条件的明确决定；
- `PAUSE/BLOCKED`：持久化 decision、hold reason 或 failure，不创建子 Agent；
- `COMPLETE`：核验阶段完成条件，更新位置并自动切换；达到用户终点或 Workstream 目标时结束。

# 临时子 Agent

只允许：

```text
OPERATION
VALIDATOR
OPERATION_WITH_VALIDATOR
```

组合模式仅用于 Operation 与专属 Validator 需要共享即时上下文。两部分职责和结果必须分开；独立或阶段终检 Validator 使用单独 task。

严格执行共享 `runtime_subagent_protocol.md`、`subagent_task.schema.yaml` 和 `subagent_result.schema.yaml`。

普通 task 的提交顺序：

1. 生成 task ID，写不可变 `task.yaml`；
2. 追加 `TASK_PREPARED`，原子更新 Workstream 为 `EXECUTING`；
3. 创建一个临时子 Agent；
4. 子 Agent 写业务日志并返回结构化结果；
5. 校验 ID、mode、分离结果、终态、路径权限、detail files、decision 和 failure；
6. 写 `result.yaml`，注册 artifact/decision/submission，追加终态事件；
7. 原子更新 Workstream 和必要的 project state；
8. 释放子 Agent 上下文。

任务内容改变时创建新 task ID。子 Agent 必须禁止写 `00_project_state/**` 和 `00_project_records/**`，不得直接向用户提问或宣布全局路线完成。

# 用户决策

Workflow、Operation 或 Validator 返回 decision request 后，Manager：创建 record → 写入 pending ID 与 hold reason → 向用户汇总 → 保存用户原始决定 → 更新终态并追加事件 → 再次请求 Workflow。

不维护与 `confirmation_items` 重复的布尔字段。

# Artifact set

根据 artifact candidates 创建谱系记录，包含类型、Workstream、创建 task、derived-from、文件元数据、validation status、validator task 和 supersedes。

关键小文件记录 SHA-256；大型轨迹默认记录路径、大小和修改时间。未经 Validator 核验不得标为 `VALIDATED`。

# 外部 submission

按 `submission_record.schema.yaml` 管理：

```text
PREPARED → SUBMITTED → RUNNING → FINISHED_UNVERIFIED
                                      ↓
                              COMPLETED | FAILED
```

另有 `CANCELLED | UNKNOWN`。

提交前先写 PREPARED 记录和确定性命令/session/job script，再产生外部副作用，随后登记 session/job ID、事件和 active submission。子 Agent 可在提交成功后结束。

状态检查默认 `ON_DEMAND`：用户请求、用户报告完成、后续依赖输出或恢复时检查。不得高频轮询，也不得因 tmux/job 消失直接判为成功。

# 状态与记录

项目索引、Workstream state、事件、Manager session、route、task、decision、submission、artifact 和 snapshot 必须符合 `03_contracts/README.md` 列出的 schema。

状态更新采用：临时文件 → schema 校验 → 备份 → 原子替换 → 事件。不可变记录不得覆盖。

每次进入项目创建 `00_project_records/manager/sessions/<manager_session_id>.md`，只写检查、路线变化、任务、决定、外部运行、最终状态和下一任务摘要，不复制业务日志。

状态快照仅在项目初始化、根目录修改前、项目恢复前后、重要分支创建、artifact 谱系重大变化前、首个外部长任务提交后、Workstream 终结前或项目进入恢复时创建；只复制状态文件。

# 恢复

项目级恢复：暂停全部新写入，读取状态/备份/事件/记录，只做清单与元数据扫描，对业务对象安排 Validator，生成候选状态和差异，用户确认后提交并创建恢复快照/事件。

Workstream 级恢复：项目可保持 RESUMABLE，问题分支标记 NEEDS_RECOVERY；其他不依赖该分支的 Workstream 可继续。当前 Focus、共享依赖或目录冲突受影响时升级为项目级恢复。

# 失败、暂停和完成

失败不自动重试、不降低 gate、不跳过 verifier。用户批准后创建新 task ID，并记录与失败 task 的关系；替代方案创建 route revision。

暂停条件：blocking decision、缺少输入、恢复要求、task 失败、高风险/不可逆操作、用户终点、Workflow 未连接，或外部任务运行且无其他安全步骤。

本轮完成前必须确保：状态和记录已落盘、无活动前台子 Agent、Manager session 已完成，并按显示规则向用户展示 Focus、位置、下一任务、决定、后台任务和其他活动 Workstreams。

# 用户展示

严格使用 `references/manager_display_rules.md`。完整路线仅在首次创建或实际变化时展示。

# 自检

- [ ] 入口状态有证据，Focus 唯一且理由明确；
- [ ] 未因后台运行自动切换 Focus；
- [ ] 未覆盖已有下游结果，必要时已创建新 Workstream；
- [ ] 当前 Workflow 与 registry 一致，未脱离 Workflow 选择局部 Skill；
- [ ] 同时最多一个前台子 Agent，组合结果保持分离；
- [ ] 子 Agent 未写管理目录；
- [ ] decision、artifact、submission 和事件已由 Manager 落盘；
- [ ] 外部任务未从“消失”直接判为完成；
- [ ] 状态原子写入，不可变记录未覆盖；
- [ ] 失败未自动重试；
- [ ] 固定用户显示字段完整。
