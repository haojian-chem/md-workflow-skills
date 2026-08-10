# MD Workflow Project Instructions

## 1. 项目范围

本仓库同时用于：

1. 真实 MD 项目的运行与任务管理；
2. MD Workflow Skill / Tool / contract / runtime 架构的设计与维护。

Skill 架构根目录：

`/root/data/5_codex/3_md_workflow`

真实 MD 项目根目录不固定。任何真实项目操作都必须区分 Skill root 与 MD project root。

## 2. 先判断当前模式

### REAL_MD_RUNTIME

真实 MD 项目默认使用 **Lightweight Runtime v2**。

默认项目记录只有：

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    ├── T001.md
    ├── T002.md
    └── ...
```

真实运行分成两个长期对话角色：

```text
Manager 对话
→ 创建 / 定位任务并生成初始计划
→ Txxxx.md
→ Task Execution Agent 对话
→ 连续推进任务中的子环节
```

Manager 与 Task Execution Agent 默认不在每个子环节之间往返。

#### Manager 请求

当用户要求创建、定位、整理或重新规划任务时：

1. 读取 `00_manager/md_workflow_manager/SKILL.md`；
2. 按该 Skill 的最小读取规则使用 `task_index.md` 和目标任务单；
3. 只有创建或明确重新规划任务时才读取 Manager planning index；
4. 不默认读取具体科研 Step Skill、项目结果索引或 Legacy Runtime records。

#### Task execution 请求

当用户要求继续、执行、检查、解释或排错一个已有任务时：

1. 读取目标 `Txxxx.md`；
2. 由任务单确定当前要处理的子环节和对象；
3. 只加载当前子环节需要的 Skill；
4. 在真正开始该子环节时，按环节在 `project_result_index.md` 中检索已有正式结果，并按当前 Skill 的 reuse conditions 判断是否复用；
5. 只读取当前对象、候选复用结果及当前 Skill 明确要求的其他输入；
6. 执行后直接维护任务单、登记正式结果，并根据结果或用户明确要求调整后续子环节。

普通 task execution 不需要为了推进下一子环节返回 Manager。

#### Legacy Runtime

以下体系已冻结，不再是默认真实运行入口：

```text
runtime/**
00_project_state/**
Workstream state
route / route revision
runtime task / result
project event
artifact state machine
transaction closure
```

只有旧项目首次接管、明确历史恢复、Legacy 调试或用户明确要求时才按需读取相关旧记录；不得默认扫描整套 Legacy Runtime。

### AUTHORING_OR_MAINTENANCE

当用户要求编写、修改、审查或规划 Skill、Tool、Manager、Workflow、contract 或 runtime 架构时：

1. 读取 `00_authoring/AUTHORING_RULES.md`；
2. 再读取目标文件对应的 content map、同步状态和适用权威 references；
3. Lightweight Runtime v2 的架构规格位于 `00_authoring/lightweight_runtime_v2_spec.md`；
4. Legacy Runtime 相关文件默认只作为冻结历史材料，不应为了新设计继续扩展。

不要把 authoring 材料自动带入真实 MD runtime。

## 3. Runtime 职责边界

默认运行关系是：

```text
Manager
  ↓ 一次性交接
Task Sheet
  ↓
Task Execution Agent
  ↓ 按当前子环节加载
Step / Operation / Validator Skill
  ↓ 必要时
Deterministic Tool
```

逻辑上的 Workflow、Operation、Validator 科研职责继续保留，但不要求每个子环节通过一套 Manager → Workflow → Operation → Validator → closure 的 LLM 调度链。

Tool 是确定性执行组件，不是科学决策层。

Task Execution Agent 可以在当前用户对话中处理需要的科学判断、确认、复用判定和局部计划调整；Tool 不直接向用户提问。

## 4. Runtime 最小读取原则

- Manager 只读取任务管理与规划真正需要的信息；
- Task Execution Agent 一次只加载当前子环节需要的信息；
- 不预读未来子环节 Skill；
- 不为了“全面了解”默认扫描项目目录、其他任务单或完整历史；
- 跨环节优先消费上游正式结果文件，而不是重新读取上游 Skill 和全过程；
- 每一次额外文件、Skill 或目录读取都必须由当前动作的明确需求触发；
- `project_result_index.md` 只用于结果检索，不保存当前任务或当前环节状态。

## 5. 任务与结果记录原则

`task_index.md`：

- 只记录任务导航；
- 任务级状态仅使用 `未完成 | 已完成 | 已终止`。

`tasks/Txxxx.md`：

- 记录任务目标；
- 记录每个子环节的 `状态 / 对象 / 工作目录 / 主要结果 / 必要执行记录`；
- 子环节状态仅使用 `待执行 | 未完成 | 已完成`；
- 确认不需要的未执行子环节直接从计划删除；
- 任务范围由当前列出的子环节定义，不维护独立 start/end/route。

`project_result_index.md`：

- 一级按子环节组织；
- 登记该环节定义的正式结果文件完整路径与来源任务；
- 不建立稳定对象 registry 或 version registry。

## 6. 通用权限与安全

- 不修改 `01_sources/` 中的来源文件；
- source recognition 默认复制源结构；只有用户明确授权且具备 source write permission 时才允许移动；
- 不自动通过单位计费的期刊数据库下载文献；
- 未经授权，不删除、覆盖或批量移动项目文件；
- 破坏性或不可逆操作必须在执行前取得用户确认；
- 默认 Tool 不访问网络，也不得嵌入 LLM 调用；
- Tool 只能在明确授权的路径与权限边界内写入；
- 需要复现的复杂科研操作优先保存实际脚本、配置或软件输入文件，不维护全局 shell 流水账。

## 7. 架构来源

- Lightweight Runtime v2 规格：`00_authoring/lightweight_runtime_v2_spec.md`
- authoring/maintenance：`00_authoring/AUTHORING_RULES.md`
- Manager：`00_manager/md_workflow_manager/`
- Workflow：`01_workflows/`
- Operation：`02_operations/`
- Validator：`02_validators/`
- Tool：`05_tools/`
- Legacy contracts：`03_contracts/`
- Legacy runtime projection：`runtime/`

`03_contracts/**` 与 `runtime/**` 当前保留用于 Legacy 历史和迁移，不是 Lightweight Runtime v2 普通任务的默认依赖。
