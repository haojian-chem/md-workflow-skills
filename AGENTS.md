# MD Workflow Project Instructions

## 1. 项目范围

本仓库同时用于：

1. 真实 MD 项目的运行与任务管理；
2. MD Workflow Skill / Tool / runtime 架构的设计与维护。

Skill architecture root 与真实 MD project root 必须区分。真实项目根目录不固定。

## 2. 先判断当前模式

### REAL_MD_RUNTIME

真实 MD 项目默认使用 **Lightweight Runtime v2**。

默认项目记录：

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
2. 按其最小读取规则使用 `task_index.md` 和目标 Task Sheet；
3. 只有创建或明确重新规划任务时才读取 Manager planning index；
4. 不默认读取具体科研 Skill、项目结果索引或 Legacy Runtime records。

#### Task execution 请求

当用户要求继续、执行、检查、解释或排错已有任务时：

1. 读取目标 `Txxxx.md`；
2. 由任务单确定当前要处理的子环节/对象；
3. 加载当前任务所需的 main Skill；
4. 按当前 Skill / Stage 已冻结规则检查 reuse；
5. 只读取当前对象、候选结果和当前工作明确需要的其他资料；
6. 必要时按需读取 supporting Skill / reference / Tool guide；
7. 执行后维护 Task Sheet、登记正式结果，并根据结果或用户明确要求调整后续计划。

普通 task execution 不需要为了推进下一子环节返回 Manager。

### AUTHORING_OR_MAINTENANCE

当用户要求编写、修改、审查或规划 Skill / Tool / Manager / Stage architecture 时，默认启动链只有：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

之后由 `00_authoring/SKILL.md` 和当前任务决定是否按需读取：

- 对应 architecture freeze；
- 与当前输入、输出和边界直接相关的其他 Skill / Tool guide；
- 涉及多窗口写入协调时的 `00_authoring/coordination/file_ownership.yaml` 或 window work order；
- 涉及项目级状态时的 `00_authoring/SYNC_STATUS.md` / `MD_WORKFLOW_MASTER_PLAN.md`；
- 涉及 runtime architecture 时的 `00_authoring/lightweight_runtime_v2_spec.md`。

**不要把整个 `00_authoring/` 作为新 authoring 窗口的固定 preload。**

Authoring 中必须区分：

```text
read scope  ≠  write ownership
```

可以并且应该读取不属于当前写入范围的相关 Skill 来理解接口；未经明确分配，不得修改它们，也不得在当前 Skill 中替它们定义内部规则。

## 3. Current Skill model

当前科研 Skill 设计原则：

```text
main Skill
├── references/        # 长规则/registry/按需细节
├── schemas/           # 只有确有稳定结构化约束时使用
├── scripts/           # Skill-local deterministic helper
└── supporting Skill   # 仅复杂且边界清晰时拆出
```

**不再强制把科研 Skill 分类为 Workflow / Operation / Validator。**

仓库中现存：

```text
01_workflows/
02_operations/
02_validators/
```

是历史布局和迁移中的现有路径，不是新 Skill 的强制目录模板。

Manager 是项目级管理 Skill；Tool 是确定性能力组件。

## 4. Skill 是 Agent guide

Skill 的首要作用是指导 Agent 如何处理科研任务，而不是把 Agent 锁进固定 parser、wrapper 或 dispatcher。

默认原则：

- Agent 可以直接读取并理解实际科研文件；
- parser / Tool 用于需要精确、稳定、批量、可测试的确定性动作；
- 推荐 Tool 不自动等于唯一允许实现；
- 只有科学方法或明确技术接口真正要求时，才规定不可替代的软件/算法/格式路径；
- 不为简单判断增加无必要 schema、状态机或中间 workflow hop。

## 5. 跨 Skill 边界

当前 Skill 可以引用其他 Skill 的：

```text
正式结果
对外能力
已经冻结的判据
handoff interface
```

不得在当前 Skill 中重新定义其他 Skill 的：

```text
内部步骤
默认参数
科学判断逻辑
validation
official results
文件生命周期
计划维护规则
```

发现外部 Skill 缺失/冲突时，交给 owner window / main authoring window 处理。

## 6. Runtime 最小读取原则

- Manager 只读取任务管理与规划真正需要的信息；
- Task Execution Agent 只加载当前动作需要的信息；
- 不为了“全面了解”扫描整个项目；
- 跨环节优先消费上游正式结果，而不是重读上游全过程；
- 但当当前科学判断确实需要理解相邻 Skill 的接口时，可以按需读取；
- `project_result_index.md` 只用于结果检索，不保存当前任务状态。

## 7. 任务与结果记录

`task_index.md`：

- 只记录任务导航；
- 任务级状态：`未完成 | 已完成 | 已终止`。

`tasks/Txxxx.md`：

- 记录任务目标、计划、状态和最小恢复信息；
- 普通子环节状态：`待执行 | 未完成 | 已完成`；
- Stage-specific 内部对象可以使用其已冻结的局部状态规则。

`project_result_index.md`：

- 用于跨任务/跨对话正式结果检索；
- 登记粒度由当前 Stage / Skill 定义；
- 不建立通用 version registry。

## 8. Legacy Runtime

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

只有旧项目恢复、Legacy 调试、历史审计或用户明确要求时才按需读取。

## 9. 通用权限与安全

- 不修改 `01_sources/` 中的来源文件，除非有明确授权；
- 不自动通过单位计费的期刊数据库下载文献；
- 未经授权，不删除、覆盖或批量移动科研文件；
- 破坏性或不可逆操作必须在执行前取得用户确认；
- 默认 Tool 不访问网络，也不得嵌入 LLM 调用；
- Tool 只能在明确授权路径内写入；
- 需要复现的复杂科研操作优先保存实际脚本、配置或软件输入文件。

## 10. 当前 authority

- Runtime：`00_authoring/lightweight_runtime_v2_spec.md`
- Authoring：`00_authoring/SKILL.md`
- Skill boundary：`00_authoring/references/skill_boundaries.md`
- Manager：`00_manager/md_workflow_manager/`
- Current Stage guides：以 `00_authoring/SYNC_STATUS.md` 和对应 `00_authoring/architecture_freezes/` record 为准
- Tool：`05_tools/`
- Legacy contracts：`03_contracts/`
- Legacy runtime projection：`runtime/`
