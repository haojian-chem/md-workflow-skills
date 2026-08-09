# MD Workflow 四层职责与执行后端边界

本文件是 Manager、Workflow、Operation、Validator **逻辑职责边界**的权威定义。

核心原则：

```text
职责边界 ≠ LLM 调用边界 ≠ 进程边界
```

运行时可以通过确定性 Tool 或受控 Agent context 执行某一职责，但不得改变该职责的语义所有权。

## 1. Manager

唯一主工作：管理项目级语义与提交边界。

负责：

- 两个 root 与项目入口状态；
- Focus 和 Workstream；
- route scope、跨 Workflow route 与 revision；
- 用户决定；
- 当前执行后端解析；
- 外部 submission；
- 恢复、暂停、重试、重规划；
- `00_project_state/**` 与 `00_project_records/**` 的提交授权；
- 用户可见状态与 closure。

Manager 不负责：

- 结构/拓扑/模拟/分析业务操作；
- 科学质量判断；
- 根据阶段名编造 Workflow 内部步骤；
- 用 LLM 逐字段模拟 schema/引用/序列化；
- 因记录所有权而手工构造全部机械 YAML。

Manager 的提交边界可以调用已批准 deterministic builder/recorder，但语义决定仍归 Manager。

## 2. Workflow

唯一主工作：拥有一个阶段的局部流程语义。

负责：

- 阶段内有序 node/substep；
- REQUIRED / CONDITIONAL；
- entry/exit artifact requirements；
- planning fragment；
- route-affecting 条件和 blocker；
- 当需要语义重判时给出当前 execution decision；
- 声明 node 的 Operation/Validator 责任与允许的 execution backend preference。

Workflow 不负责：

- 项目入口/初始化；
- 跨 Workflow 起终点；
- Focus/Workstream 创建；
- 直接执行 Operation/Validator；
- 修改业务或管理文件；
- 直接向用户提问。

compact Workflow runtime spec 是本 Workflow 权威定义的派生投影，不是第二套流程定义。

## 3. Operation

唯一主工作：执行一个明确、可验证的业务操作。

负责：

- task-local preflight；
- 授权路径内的文件/命令操作；
- 必要业务日志；
- 操作是否实际完成的确定性/操作性核验；
- Operation result 与 artifact candidates。

Operation 不负责：

- 项目/Workflow 路线；
- 用户确认；
- 管理目录提交；
- 独立科学质量判决；
- 创建嵌套 Agent。

Operation 可以由 `DETERMINISTIC` Tool 或 Agent context 执行，但结果仍必须表示为 Operation responsibility。

## 4. Validator

唯一主工作：读取并检查目标对象，输出结构化判定。

负责：

- 目标和必要上下文读取；
- 科学/技术检查、识别或分类；
- 区分“Validator 是否成功执行”和“目标是否通过”；
- outcome、findings、gate 建议与 decision request；
- Validation result/report。

Validator 不负责：

- 修改被验证对象；
- 自动修复；
- 用户确认；
- 管理目录提交；
- 项目/Workflow 路线；
- 嵌套 Agent。

完全确定性的 Validator 可以由 Tool 后端执行；需要科学判断的 Validator 通常使用 Agent 后端。

## 5. Tool

Tool 是确定性执行组件，不是第五个决策层。

Tool 可以承担：

- parsing / hashing / copy / deterministic transform；
- schema/reference validation；
- deterministic record building；
- controlled state commit；
- 已冻结规则的确定性检查。

Tool 不得：

- 选择 Focus、route scope、route revision；
- 作开放式科学判断；
- 向用户提问；
- 创建 Agent；
- 降低 gate；
- 超出 registry 权限写入。

## 6. 执行后端模型

运行时必须把逻辑 task/node 与执行后端分开表示。

### DETERMINISTIC

适用于同时满足：

- 业务逻辑已冻结为确定性规则；
- 不需要开放式科学判断或用户决定；
- 所需 capability 有 `ACTIVE` Tool；
- Tool 输出可以映射到对应 Operation/Validator result contract。

不创建业务 Agent。

### AGENT_TASK

一个临时前台 Agent context 执行一个上下文有界 task unit：

```text
OPERATION
VALIDATOR
OPERATION_WITH_VALIDATOR
```

这是当前兼容默认后端。

### AGENT_SEQUENCE

一个临时 Agent context 连续执行多个上下文连续 node/task，但每个 Operation/Validator 责任和结果必须保持独立。

只有同时满足以下条件才可启用：

- 同一 Workstream；
- 同一 Workflow；
- sequence contract 明确列出节点；
- 不跨用户 decision barrier；
- 不跨 route-changing branch；
- 不跨外部 submission；
- 不跨高风险/不可逆恢复锚点；
- 不改变目录所有权边界；
- 上一个节点输出直接构成下一个节点输入；
- 中间每个节点仍可单独记录结果和 gate。

在 sequence contract、校验和 fixture 未实现前：

```text
AGENT_SEQUENCE = DISABLED_BY_DEFAULT
```

不得为了省时间临时把多个节点塞进一个 Agent。

## 7. 后端选择规则

Workflow/runtime spec 可以声明：

```text
preferred_backend
fallback_backend
required_capability
```

Manager 只解析 capability 与已冻结 eligibility，不创造新的科学路由。

典型顺序：

```text
preferred DETERMINISTIC
  + ACTIVE capability
  → DETERMINISTIC

preferred DETERMINISTIC
  + capability unavailable
  + fallback AGENT_TASK allowed
  → AGENT_TASK

需要科学判断
  → AGENT_TASK
```

后端变化不改变 Operation/Validator 的责任归属，也不改变 artifact/validation 语义。

## 8. Runtime context 边界

真实 MD runtime 优先读取 `runtime/**` 紧凑投影。

完整 authoring references 只在：

- runtime projection 缺失/失效；
- 恢复；
- contract/协议冲突；
- 开发或审计

时加载。

任何层都不得把“为了遵守规则”解释成每次运行都全文读取全部权威设计文件。

## 9. 管理与业务写权限

Manager 控制：

```text
00_project_state/**
00_project_records/**
```

Operation/Validator/业务 Agent 只写 task 授权业务路径。

确定性 recorder/state Tool 可以在 Manager 明确授权且 registry 权限覆盖时写管理目录；这不改变 Manager 的所有权。

## 10. 并发边界

- 同时最多一个前台 MD Agent context；
- `DETERMINISTIC` Tool 调用不占用业务 Agent 名额，但不得被用于绕过串行业务依赖；
- 多个 tmux/调度系统外部任务可后台并存；
- Operation/Validator/Tool 不创建嵌套 Agent。
