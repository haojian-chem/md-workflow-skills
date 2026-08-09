# MD Workflow Runtime Execution Protocol

本协议定义真实 MD runtime 中 Operation/Validator 的执行后端、Agent context 边界和最小任务信息。

逻辑职责由 `layer_boundaries.md` 定义；本文件只定义**如何执行**。

## 1. 总原则

```text
职责边界 ≠ Agent 边界
```

运行时支持：

```text
DETERMINISTIC
AGENT_TASK
AGENT_SEQUENCE
```

任意时刻最多一个前台 MD Agent context。Tool 调用不是 Agent，但不得绕过业务依赖关系。

Operation/Validator 不创建或调用其他 Agent，也不直接向用户提问。

## 2. Backend resolution

Manager 根据当前 route node / compact Workflow runtime spec 解析：

- logical task mode；
- `preferred_backend`；
- `fallback_backend`；
- `required_capability`；
- 当前 Tool registry capability；
- blocking decision / recovery / risk 状态。

Manager 不得为了性能临时发明 backend 或扩大 sequence。

### 2.1 DETERMINISTIC

仅当以下条件全部满足：

- node 明确允许；
- 所需 capability 有 ACTIVE Tool；
- 输入已确定且有界；
- 不要求开放式科学判断；
- 不产生需要 Agent 解释才能判断是否成功的结果；
- Tool 输出可被确定性映射为对应 Operation/Validator result。

执行：

```text
route node
→ Manager authorizes deterministic capability
→ Tool
→ structured Operation/Validator result candidate
→ runtime validation / record commit
```

不创建业务子 Agent。

Tool 缺失时：

- 若 runtime spec 允许 `fallback_backend: AGENT_TASK`，使用 AGENT_TASK；
- 否则返回 capability blocker；
- 不在运行时临时开发 Tool。

## 3. AGENT_TASK

当前兼容默认后端。

一个临时 Agent context 只执行一个明确的 task unit：

```text
OPERATION
VALIDATOR
OPERATION_WITH_VALIDATOR
```

`OPERATION_WITH_VALIDATOR` 仅用于专属 Validator 必须共享前一 Operation 即时上下文的情况。

即使同一 Agent 连续执行 Operation + Validator：

- 两种职责保持分离；
- Validator 不修改被验证对象；
- 两部分 result 分开；
- artifact candidate 与 validation outcome 不合并成模糊“成功”。

### 3.1 Agent 创建前条件

- 项目为可信 `RESUMABLE` 或已初始化；
- Focus Workstream 唯一；
- active route/node 可定位；
- 当前 node 允许 AGENT_TASK；
- 没有活动前台 Agent；
- 输入、工作目录和权限已解析；
- blocking decision 已解决；
- task identity 已分配。

### 3.2 最小 Agent context

只传递当前 task 必需信息：

- task / Workstream / Workflow / route-node identity；
- task mode；
- Operation/Validator Skill path；
- project root 与 work directory；
- allowed read/write 和 forbidden paths；
- 当前有效输入；
- 精简上游摘要；
- resolved decisions；
- 必需输出；
- detail log/report path；
- 返回 contract/version identifier。

不得传入：

- 完整对话；
- 全部项目日志；
- 全部 Workstream 状态；
- authoring corpus；
- 无关 Skill；
- schema 正文，除非该 Agent 的任务就是 schema/contract 调试。

当前 Skill 自身可以读取其运行必需的局部 `references/`、`scripts/README` 或 local schema；不得因为启动 Agent 就读取全局 authoring references。

## 4. AGENT_SEQUENCE

目标：对上下文连续、语义稳定的多个 node 复用一个 Agent context，减少重复启动和静态规则重读。

### 4.1 Eligibility

必须同时满足：

- 同一 Workstream；
- 同一 Workflow；
- sequence 由明确 contract/route projection 列出；
- 所有节点顺序确定；
- 中间没有用户 decision barrier；
- 中间没有 route-changing branch；
- 没有外部 submission；
- 没有高风险/不可逆 checkpoint；
- 不跨目录所有权边界；
- 上游输出直接进入下一节点；
- 每个节点仍能独立产生 task/result/gate evidence；
- 任一节点 BLOCKED/FAILED 时 sequence 立即终止。

### 4.2 当前启用状态

在以下能力实现并验证之前：

```text
AGENT_SEQUENCE = DISABLED_BY_DEFAULT
```

所需前置：

- sequence contract；
- deterministic eligibility validator；
- multi-result record/commit support；
- interruption/recovery fixtures；
- route-node provenance tests。

因此当前 runtime 不得直接把多个普通 task 合并为 sequence。

## 5. 管理目录写权限

业务 Agent 不得直接修改：

```text
00_project_state/**
00_project_records/**
```

Agent 只能写：

- task 授权业务路径；
- 详细业务日志/报告；
- 明确授权的候选输出。

结构化管理记录由 Manager 提交边界处理；R4 完成后优先由 deterministic recorder 构造。

## 6. 返回信息

AGENT_TASK 至少返回：

- identity；
- task mode；
- terminal status；
- 精简执行摘要；
- 分开的 Operation result / Validation result；
- artifact candidates；
- confirmation items；
- warnings/failure；
- detail log/report paths。

详细中间过程落盘，不完整回灌 Manager 上下文。

DETERMINISTIC backend 必须生成等价的结构化 responsibility result，使下游不依赖“结果来自 Agent 还是 Tool”。

## 7. Decision handling

Agent/Tool 不直接问用户。

需要用户决定时：

```text
result confirmation_items
→ Manager
→ decision record
→ user
→ resolved decision
→ route/workflow re-evaluation as needed
```

非空 blocking decision 会终止当前普通推进/sequence。

## 8. 普通 task closure

当前 R4 recorder 未完成前，兼容闭环为：

```text
execute backend
→ structured result candidate
→ one applicable FAST validation
→ commit necessary result/artifact/event/state
→ visible closure
```

不得机械增加：

- TASK_PREPARED/TASK_STARTED（普通短 task）；
- 无变化 project state；
- snapshot；
- 无变化 route revision；
- 逐 task Manager session rewrite；
- 重复 FULL；
- 为解释 Tool 已确定结果而再次全文读取 authoring source。

R4 完成后，机械 result/event/artifact/state 构造交由 deterministic recorder。

## 9. 强化预记录

以下情况仍要求副作用前建立恢复锚点：

- 外部 submission；
- 长耗时 task；
- 高风险或不可逆操作；
- 中断后必须区分未启动/已启动；
- Workflow/Operation 明确要求 checkpoint。

该规则不因执行后端改变。

## 10. 性能约束

Agent context 隔离的目标是减少主上下文污染，不是让每个几秒钟确定性动作都强制产生一次 LLM lifecycle。

运行时应优先：

1. DETERMINISTIC capability；
2. 最小 AGENT_TASK context；
3. 未来经验证的 AGENT_SEQUENCE；

同时保持科学 gate、权限和恢复语义不变。
