# MD Workflow 四层职责边界

本文件是 Manager、Workflow、Operation 和 Validator 职责边界的唯一权威定义。

## Manager

唯一主工作：维护项目索引、Workstream 状态、用户交互、历史记录和临时子 Agent 生命周期。

负责：

- 确认 Skill 架构根目录和真实 MD 项目根目录；
- 判断项目入口状态 `NEW | RESUMABLE | NEEDS_RECOVERY`；
- 解析可组合的 `INSPECT | PLAN | EXECUTE` 请求；
- 选择项目级或 Workstream 级 Focus；
- 创建、切换和恢复 Workstream；
- 请求当前 Workflow 对 Focus Workstream 返回局部决定；
- 消费 Workflow 决定并维护 Workstream 路线；
- 构建单个临时子 Agent 的 task unit；
- 接收 `subagent_result`；
- 汇总并持久化用户决策；
- 记录外部 submission 和 artifact set；
- 唯一提交 `00_project_state/` 与 `00_project_records/`；
- 决定暂停、恢复、重试或再次请求 Workflow 判断。

不得：

- 脱离 Workflow 决策自行选择局部 Operation/Validator；
- 在主上下文执行大量局部文件解析、日志分析或科学判定；
- 复制 Operation/Validator 的业务规则；
- 同时运行多个前台 MD 临时子 Agent；
- 因某个后台 MD 正在运行而自动切换 Focus；
- 把项目整体“回退阶段”来覆盖已有下游结果；需要保留旧结果时应创建新 Workstream。

## Workflow

唯一主工作：根据一个 Workstream 的局部状态返回当前阶段下一任务决定。

负责：

- 定义阶段内有序 substep；
- 读取 Focus Workstream 的当前位置、有效产物和已解决决定；
- 判断执行、跳过、暂停、阻塞或阶段完成；
- 指定一个 Operation、一个 Validator，或一个 Operation 与其专属 Validator 组成的 task unit；
- 声明输入来源、预期输出和 gate；
- 规定阶段完成条件。

不得：

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
