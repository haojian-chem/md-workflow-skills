# MD Workflow 四层职责边界

本文件是四层职责的唯一权威定义。

## Manager

唯一主工作：维护全局项目状态、用户交互和临时子 Agent 生命周期。

负责：

- 确认 Skill 架构根目录和真实 MD 项目根目录；
- 读取项目状态并选择当前 Workflow；
- 请求 Workflow 返回当前下一步决定；
- 根据 Workflow 决定构建 `subagent_task`；
- 任意时刻只创建一个临时子 Agent；
- 接收 `subagent_result`；
- 汇总用户确认事项；
- 更新项目状态；
- 决定暂停、重试或再次请求 Workflow 判断。

不得：

- 脱离 Workflow 决策自行选择局部 Operation/Validator；
- 在主上下文执行大量局部文件解析或日志分析；
- 复制 Operation/Validator 的业务规则；
- 同时运行多个 MD 临时子 Agent。

## Workflow

唯一主工作：根据阶段状态返回当前阶段的下一任务决定。

负责：

- 定义阶段内有序 substep；
- 判断当前 substep；
- 判断执行、跳过、暂停、阻塞或阶段完成；
- 指定下一 Operation/Validator Skill；
- 声明输入来源、预期输出和 gate；
- 规定阶段完成条件。

不得：

- 执行 Operation 或 Validator；
- 创建、管理或模拟子 Agent；
- 直接向用户提问；
- 修改业务文件；
- 复制子 Skill 的命令、算法、字段或详细判定标准；
- 决定进入下一全局阶段。

Workflow 是 Skill，不是 Agent。

## Operation

唯一主工作：执行一个明确、可验证的文件或命令操作。

负责：

- 执行自身 preflight；
- 在授权路径内创建、移动、修改或生成文件；
- 运行规定命令；
- 验证操作实际完成；
- 将详细过程落盘；
- 按 `subagent_result` 返回精简摘要。

不得：

- 决定全局或阶段路线；
- 创建其他子 Agent；
- 直接向用户请求确认；
- 修改未授权路径；
- 代替 Validator 给出独立质量判决。

## Validator

唯一主工作：读取并检查目标对象，输出结构化判定。

负责：

- 读取目标文件和项目记录；
- 执行确定的检查、识别或分类；
- 区分“Validator 是否成功执行”与“被检查对象是否通过”；
- 输出 findings、gate 建议与确认事项；
- 将详细结果落盘；
- 按 `subagent_result` 返回精简摘要。

不得：

- 修改被验证的目标结构或拓扑；
- 修复发现的问题；
- 创建其他子 Agent；
- 直接向用户提问；
- 将不确定自动等同为执行失败。

## 运行关系

```text
主智能体
├── Manager Skill
├── Workflow Skill
└── 临时子 Agent
    └── 一个 Operation 或 Validator Skill
```

Workflow 不作为运行时执行主体；Operation/Validator 不进行嵌套委派。
