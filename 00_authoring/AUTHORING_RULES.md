# MD Workflow Authoring Rules

本文件保存 Skill / Tool 设计、实现、审查和多窗口协作规则，属于 **AUTHORING_ONLY** 材料。

真实 MD 项目运行时不得默认读取本文件。

当前默认目标架构为 **Lightweight Runtime v2**，权威规格：

`00_authoring/lightweight_runtime_v2_spec.md`

旧的 Workstream / route / event / runtime projection / transaction 架构已冻结为 Legacy，不再作为新 Skill 重构的默认目标。

## 1. 开发与运行分离

### Skill 开发

- 用户可以在网页端打开多个独立窗口；
- 每个窗口只编写被分配的 Skill 或互斥文件范围；
- 网页编写窗口不是运行时 Agent；
- 修改前必须先确认当前文件所有权和同步状态。

### Tool 开发

- 共享 Tool 统一位于 `05_tools/`；
- Tool 生成、修改、测试、注册、升级和废弃由 `00_authoring/md-workflow-tool-authoring/SKILL.md` 管理；
- 业务 Skill 可以提出 `tool_request`，但不得在真实业务 task 中临时修改共享 Tool；
- 未测试 Tool 不得标记为 `ACTIVE` 或作为默认生产路径；
- Tool 只承担确定性动作，不承担科学选择、用户意图解析或开放式判断。

### Runtime 开发

Lightweight Runtime v2 的默认记录层只有：

```text
00_project_records/task_index.md
00_project_records/project_result_index.md
00_project_records/tasks/Txxxx.md
```

不得为普通任务重新引入第二套等价的 route、event、artifact state、Workstream state 或 transaction state。

`runtime/**` 及围绕其建立的 projection compiler / runtime contracts 属于 Legacy。除旧项目迁移、Legacy 调试或明确清理工作外，不继续为 Lightweight Runtime 新增依赖。

## 2. 当前权威文件

运行时架构原则：

`00_authoring/lightweight_runtime_v2_spec.md`

Manager 任务管理与初始规划：

```text
00_manager/md_workflow_manager/SKILL.md
00_manager/md_workflow_manager/references/workflow_plan_index.yaml
```

具体科研职责的常规目录为：

```text
01_workflows/
02_operations/
02_validators/
```

这些目录表达常规物理组织方式，不是强制的逻辑层绑定。若某个 Workflow/Stage 已通过 freeze 文件明确采用 stage-integrated layout，则可将父级 Workflow 职责和子级 Operation/validation 职责放在同一 Stage 目录树中；逻辑职责边界仍须由 Skill/content map 明确。

当前已冻结的例外：

```text
04_md_simulation/
├── SKILL.md
├── 4.1_energy_minimization/
├── 4.2_equilibration/
└── 4.3_production_simulation/
```

Tool 注册状态、版本和入口：

`05_tools/tool_registry.yaml`

Legacy contracts：

`03_contracts/`

Legacy runtime projection：

`runtime/`

Legacy 文件可以保留作为历史和迁移依据，但不得因为其仍存在就把旧接口继续复制到新 Skill。

## 3. 逻辑层与运行对话边界

科研内容仍按以下逻辑职责组织：

```text
Manager
Workflow
Operation
Validator
```

Tool 是确定性程序，不是第五个科学决策层。

逻辑职责不要求一一对应为独立物理目录，也不要求同等数量的 LLM 调度层。物理目录组织应服从已冻结的 Workflow/Stage 架构与内容唯一归属；不得仅因为存在 Workflow/Operation/Validator 逻辑角色就机械拆目录。

默认真实运行模式是：

```text
Manager 对话
→ 创建 / 定位任务并写初始 Task Sheet
→ 一次性交接
→ Task Execution Agent 对话
→ 按当前子环节加载必要 Skill
→ 必要时调用 Operation / Validator / Tool
```

Manager 与 Task Execution Agent 默认是不同对话；普通任务执行不应在每个子环节之间来回调用 Manager。

Workflow / Operation / Validator 应优先作为科研 SOP、执行规则和验证能力存在，而不是要求运行时模拟 BPM 引擎。

## 4. Manager 与任务规划规则

Manager 只负责：

- 定位已有任务；
- 创建新任务；
- 为新任务生成初始子环节计划；
- 用户明确要求时重新规划或整理任务；
- 项目级任务导航。

初始规划只使用 `workflow_plan_index.yaml` 中的轻量信息：

```text
Workflow 顺序
子环节编号
子环节名称
标准工作目录
是否 conditional
```

规划索引不得包含科学判断、reuse conditions、validator 规则、软件依赖、命令或详细输入输出 schema。

Task Sheet 不维护 start / end / route。任务当前范围就是 `计划与进度` 中实际列出的子环节。

## 5. Task Sheet 与执行期计划

任务单固定保存：

```text
任务标题
任务状态
任务目标

每个子环节：
- 状态
- 对象
- 工作目录
- 主要结果（完成后）
- 执行记录（仅必要时）
```

任务级状态只允许：

```text
未完成 | 已完成 | 已终止
```

子环节状态只允许：

```text
待执行 | 未完成 | 已完成
```

Task Execution Agent 可以：

- 连续推进多个子环节；
- 根据当前科研结果增删或调整后续子环节；
- 根据用户在执行对话中的明确要求扩展或缩小任务计划；
- 任务完成或用户明确终止时同步更新 `task_index.md`。

确认不需要且尚未实际执行的子环节直接从计划删除，不增加 `NOT_APPLICABLE` 类状态。

已经实际执行过并形成任务历史的环节不得为了整理计划而静默删除。

## 6. Result Index 与复用

`project_result_index.md` 是跨任务、跨对话的**结果检索索引**，不是项目 summary、artifact registry 或当前状态文件。

一级按子环节组织：

```text
环节
→ 具体结果描述
→ 正式结果文件完整路径
→ 来源任务
```

不要求稳定对象 ID，也不建立 version registry。

每个子环节 Skill 应明确：

```text
purpose
object requirements
reuse conditions
execution rules
validation requirements
official results
```

其中 `official results` 决定完成后哪些正式文件进入 Task Sheet 和 `project_result_index.md`。

每个子环节真正开始时才检查复用：

```text
无候选结果 → 正常执行
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足无法判断 → 询问用户
用户明确要求重做 → 跳过自动复用
```

复用等价性的科学条件由当前子环节 Skill 定义，不由 Manager 或通用 Runtime state machine 统一猜测。

## 7. 最小读取规则

真实运行必须遵守按需读取。

Manager 默认只读：

```text
task_index.md
目标 Txxxx.md
```

创建或显式重新规划时再读 planning index。

Task Execution Agent 默认按以下顺序读取：

```text
目标 Txxxx.md
→ 当前子环节 Skill
→ project_result_index.md 中与该环节有关的候选结果定位
→ 当前对象
→ 当前 Skill 明确要求的其他输入
```

不得默认：

- 预读未来子环节 Skill；
- 扫描所有任务单；
- 扫描整个项目目录；
- 重读上游全部 Skill 和执行全过程；
- 加载 Legacy state / route / event / runtime records；
- 因为“可能有用”而扩大上下文。

任何额外读取必须由当前动作的明确需求触发。

## 8. 执行记录原则

Task Sheet 中的 `执行记录` 只保存对恢复和后续判断有意义的关键事件，例如：

- 用户关键决定；
- 复用来源；
- 异常及其处理结果；
- 当前未完成原因；
- 后续计划为什么调整；
- 结果为什么重新生成或替换。

不记录逐命令流水账、普通 `ls/cat/grep`、Skill 加载过程或临时文件操作。

需要复现的复杂科研操作优先保存实际脚本、配置文件和软件输入文件。

## 9. Legacy Runtime 冻结规则

以下内容默认视为 `Legacy / frozen`：

```text
project_state
workstream_state
route / route revision
runtime task / result
project_events
artifact state machine
runtime projection
transaction closure
围绕上述对象建立的默认 runtime schema / evaluator / committer / initializer
```

规则：

- 不立即删除；
- 不继续为 Lightweight Runtime 新增兼容层；
- 新项目不默认生成 Legacy records；
- 旧项目首次接管时只提取继续工作真正需要的信息，不做一比一历史迁移；
- Lightweight Runtime 建立后不再双写旧 records；
- Scientific Skills 和真正有用的 deterministic tools 不因 Runtime 冻结而废弃。

## 10. 修改前回顾

提出或实施新方案前，先明确：

```text
已做过
已否定
仍未验证
```

若新方案与已失败或已否定方案本质等价，且没有新证据改变前提，不得再次执行。

## 11. 内容唯一归属

一条规则只保留一个权威位置：

- 项目模式路由与最小通用运行原则：根 `AGENTS.md`；
- Lightweight Runtime 架构：`00_authoring/lightweight_runtime_v2_spec.md`；
- authoring / development 规则：本文件；
- Manager 运行职责：`00_manager/md_workflow_manager/SKILL.md`；
- Manager 初始规划目录：`workflow_plan_index.yaml`；
- 当前 Workflow 科研阶段语义：对应 Workflow `SKILL.md`；
- 当前 Operation / Validator 执行或验证逻辑：当前 `SKILL.md`；
- 当前 Tool 的输入输出、权限和实现：当前 `tool.yaml` 与实现文件；
- 当前 Skill 独有领域数据：当前 `references/`；
- 当前 Skill 独有输出结构：当前 `schemas/`；
- 示例与评测：`04_evals/<skill-or-tool-name>/`；
- Legacy 跨 Skill contracts：`03_contracts/`；
- Legacy runtime projection：`runtime/**`。

不得把 Legacy route / state / transaction 语义重新复制到 Lightweight Skill 中。

## 12. 多窗口文件所有权

新窗口开始前按任务需要读取：

```text
00_authoring/SYNC_STATUS.md
00_authoring/skill_inventory.yaml
00_authoring/file_ownership.yaml
目标 content map
目标 Skill / Tool 权威 references
```

规则：

- 同一文件同一时间只有一个编写窗口；
- 一个 Skill 或 Tool 目录默认只有一个编写窗口；
- `AGENTS.md`、authoring shared references、Manager references、content maps、inventory、ownership 表、Legacy contracts、Legacy runtime manifest 和 tool registry 只由主窗口修改；
- 写入路径重叠时不得同时编写；
- 共享接口变更由主窗口统一裁决。

只有明确维护 Legacy Runtime 时才要求读取旧 route protocol、runtime projection 或相关 contract；普通 Lightweight 重构不为“保险”加载它们。

## 13. 权限与安全

- 不修改 `01_sources/` 中的来源文件；
- source recognition 默认复制源结构并校验来源；只有明确用户授权和 source write permission 同时存在时才允许移动；
- 不自动通过单位计费的期刊数据库下载文献；
- 未经授权，不删除、覆盖或批量移动项目文件；
- 破坏性或不可逆动作必须在执行前取得用户确认；
- Tool 不直接向用户提问；需要确认时由当前用户可见的 Manager 或 Task Execution Agent 对话处理；
- 默认 Tool 不访问网络，也不得嵌入 LLM 调用；
- 写入型 Tool 必须限制在明确授权路径，并避免静默覆盖有效科研结果。

## 14. Lightweight 重构完成定义

一个 Skill 完成 Lightweight Runtime 迁移至少应满足：

- 不依赖普通 route / event / Workstream / transaction closure；
- 当前科研职责边界明确；
- 当前子环节对象要求明确；
- reuse conditions 明确；
- official results 明确；
- 必要 Operation / Validator / Tool 的调用边界明确；
- Task Execution Agent 可以只加载当前环节所需内容完成工作；
- 结果可写回 Task Sheet 并登记到 `project_result_index.md`；
- 正向、负向、复用、用户确认和失败/继续场景有相应验证；
- 不重新引入多层 LLM orchestration 或 minute-scale 管理开销。