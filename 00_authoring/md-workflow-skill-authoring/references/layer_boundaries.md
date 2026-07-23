# MD Workflow 四层职责边界

本文件是 Manager、Workflow、Operation 和 Validator 职责边界的唯一权威定义。

## Manager

唯一主工作：维护项目入口与初始化、项目索引、Workstream 状态、用户交互、路线、历史记录和临时子 Agent 生命周期。

负责：

- 确认 Skill 架构根目录和真实 MD 项目根目录；
- 判断项目入口状态 `NEW | RESUMABLE | NEEDS_RECOVERY`；
- 对 NEW 项目自动完成项目初始化；
- 在初始化完成后独立解析请求动作和路线范围；
- 路线终点模糊时创建用户 decision，不自行选择默认终点；
- 解析可组合的 `INSPECT | PLAN | EXECUTE` 请求；
- 选择项目级或 Workstream 级 Focus；
- 创建、切换和恢复 Workstream；
- 在范围明确后确定路线起点、终点和涉及的 Workflow；
- 请求各 Workflow 返回本阶段 route fragment；
- 核验相邻 fragment 的 artifact 接口并拼接 Workstream route；
- 请求当前 Workflow 对 Focus Workstream 返回一个实时 decision；
- 构建单个临时子 Agent 的 task unit；
- 接收 `subagent_result`；
- 汇总并持久化用户决策；
- 记录外部 submission 和 artifact set；
- 唯一提交 `00_project_state/` 与 `00_project_records/`；
- 决定暂停、恢复、重试、重规划或再次请求 Workflow 判断。

Manager 必须保持以下 barrier：

```text
PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLVED
→ ROUTE_CREATED
→ BUSINESS_TASK
```

- `PROJECT_INITIALIZED` 前不得调用 Workflow、创建 route 或业务 task；
- `ROUTE_SCOPE_RESOLVED` 前不得请求 route fragment 或创建 route；
- 有效 active route 不存在时不得创建业务 task。

不得：

- 把 NEW 判定、初始化、范围解析、规划和执行合并成一个隐式动作；
- 在 NEW 初始化时创建首条业务路线；
- 因用户表述模糊而默认选择下一 task、当前 Workflow 结束、Workstream 目标或项目终点；
- 自行编造 Workflow 内部步骤或业务条件；
- 脱离 Workflow decision 自行选择局部 Operation/Validator；
- 在主上下文执行大量局部文件解析、日志分析或科学判定；
- 复制 Operation/Validator 的业务规则；
- 同时运行多个前台 MD 临时子 Agent；
- 因某个后台 MD 正在运行而自动切换 Focus；
- 把项目整体“回退阶段”来覆盖已有下游结果；需要保留旧结果时应创建新 Workstream。

## Workflow

唯一主工作：定义一个阶段的局部流程，并为一个 Workstream 提供规划片段与实时下一步决定。

### 规划接口

负责：

- 定义阶段内有序 substep；
- 基于 Workstream 局部状态和已解析规划范围生成本阶段 route fragment；
- 标记 `REQUIRED | CONDITIONAL` 步骤；
- 声明入口要求、出口 artifact、前置条件、gate、假设和 blocker；
- 返回 `workflow_route_fragment.schema.yaml`。

### 执行接口

负责：

- 读取 Focus Workstream 的当前位置、有效产物和已解决决定；
- 判断执行、跳过、暂停、阻塞或阶段完成；
- 指定一个 Operation、一个 Validator，或一个 Operation 与其专属 Validator 组成的 task unit；
- 声明当前 task 的输入来源、预期输出和 gate；
- 返回 `workflow_decision.schema.yaml`。

Workflow 不得：

- 判断项目入口状态或初始化项目；
- 解析用户的跨 Workflow 路线终点；
- 在路线范围未解析时自行补全范围；
- 拼接其他 Workflow 的 route fragment 或写完整 route record；
- 选择跨 Workflow 起点、终点或整个项目的范围；
- 执行 Operation 或 Validator；
- 创建、管理或模拟子 Agent；
- 直接向用户提问；
- 修改业务文件或管理状态；
- 复制子 Skill 的命令、算法、字段或详细判定标准；
- 选择项目级 Focus；
- 创建 Workstream；
- 决定整个项目只存在一个当前阶段。

Workflow 是可复用 Skill，不是 Agent。一个 Workstream 可以依次经过多个 Workflow。

## Operation

唯一主工作：执行一个明确、可验证的文件或命令操作。

负责：

- 执行自身 preflight；
- 在授权业务路径内创建、移动、修改或生成文件；
- 运行规定命令；
- 验证操作是否实际执行完成；
- 将详细过程写入业务日志；
- 按 `subagent_result` 返回精简 Operation result。

不得：

- 决定项目级或 Workflow 路线；
- 创建其他子 Agent；
- 直接向用户请求确认；
- 修改未授权路径；
- 修改 `00_project_state/` 或 `00_project_records/`；
- 代替 Validator 给出独立质量判决。

## Validator

唯一主工作：读取并检查目标对象，输出结构化判定。

负责：

- 读取目标文件和必要项目记录；
- 执行确定的检查、识别或分类；
- 区分“Validator 是否成功执行”与“被检查对象是否通过”；
- 输出 outcome code、findings、gate 建议和决策请求；
- 将详细结果写入授权的业务报告；
- 按 `subagent_result` 返回精简 Validation result。

不得：

- 修改被验证的目标结构、拓扑或模拟结果；
- 修复发现的问题；
- 创建其他子 Agent；
- 直接向用户提问；
- 修改 `00_project_state/` 或 `00_project_records/`；
- 将不确定自动等同为执行失败。

## 运行关系

```text
项目入口：
主智能体 + Manager
→ entry state
→ NEW 自动初始化（如适用）
→ 独立路线范围解析

路线规划：
主智能体 + Manager
→ 逐个读取涉及的 Workflow
→ workflow route fragments
→ Manager 拼接 Workstream route

实际执行：
主智能体
├── Manager Skill
├── 当前 Workflow Skill
└── 最多一个前台临时子 Agent
    ├── 一个 Operation
    ├── 一个 Validator
    └── 或 Operation → 专属 Validator
```

其他 Workstream 的 tmux 或调度任务可以在后台继续运行。它们不占用前台子 Agent 名额。

Operation/Validator 不进行嵌套委派；Manager 是状态和记录的唯一提交者。
