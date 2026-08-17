# MD Workflow 确定性 Tool 协议

Status: CURRENT

## 1. 定位

Tool 是可重复执行的确定性能力组件，不是新的科学决策层，也不是 Agent 理解任务的前置许可层。

基本关系：

```text
Task Execution Agent
→ 当前 main Skill
→ 必要时调用 deterministic Tool
→ Tool 返回确定性结果
→ Agent 继续当前任务
```

Tool 的价值是把已经能够明确程序化的动作做得更快、更稳定、更可测试，而不是替代 Agent 理解用户意图、阅读科学文件或维护一套 Runtime 编排系统。

## 2. 不把 Tool 变成 parser gate

Skill 引入 Tool 前必须区分：

```text
A. 当前任务真正需要可靠 deterministic capability
B. 只是为了让 Agent 必须经过一个额外 parser / wrapper
```

只有 A 是合理默认理由。

如果 Agent 可以直接可靠读取一个文件并完成开放式科学判断，不应仅因为存在 parser 就规定：

```text
必须 parser → schema → Agent 才允许理解原文件
```

适合 Tool 的典型场景：

- 精确 parsing / structured extraction；
- hash；
- atom/residue mapping；
- 批量处理；
- 稳定文件变换；
- 明确格式校验；
- 可重复数值计算；
- 安全的原子写入；
- 已冻结规则的机械检查。

## 3. Tool 不得承担

Tool 不得：

- 解释或扩大用户研究目标；
- 选择当前 Task 或 Task 范围；
- 决定其他 Skill 应该做什么；
- 作开放式科学判断；
- 向用户提问；
- 自行创建或调用 Agent；
- 为普通 Lightweight 执行强制构造 Workstream、route、event、runtime task/result、artifact state 或 transaction closure；
- 修改超出自身明确授权范围的文件。

## 4. 工具归属

共享 Tool 位于：

```text
05_tools/
```

权威注册表：

```text
05_tools/tool_registry.yaml
```

共享 Tool 的设计、实现、测试、注册、升级、废弃和迁移由：

```text
00_authoring/md-workflow-tool-authoring/SKILL.md
```

负责。

Skill 独有、不会跨 Skill 复用的小 helper 可以保留在当前 Skill 的 `scripts/`；跨 Skill 重复使用、需要独立生命周期管理的程序才进入 `05_tools/`。

## 5. Tool 开发触发条件

满足以下任一条件时可以考虑共享 Tool：

- 同一确定性逻辑跨 Skill 重复；
- 程序执行明显比自然语言操作更稳定；
- parsing / hashing / mapping / deterministic transform 容易产生不一致；
- 需要可靠格式校验；
- 需要批量或缓存；
- 需要安全原子写入；
- 需要稳定、可重复的测试和 benchmark。

以下情况本身不足以开发新 Tool：

- 只是为了包装一次简单文件读取；
- 只是为了减少几行 Skill 说明；
- 只是为了恢复旧 Runtime 的 task/result/event/route 闭环；
- 只是为了让 Agent 必须通过统一 parser；
- 只是因为“程序化看起来更正式”。

## 6. 强制 Tool 与可选 Tool

Skill 引用 Tool 时应说明它属于哪一类：

```text
required capability
preferred implementation
optional helper
```

`required capability` 表示当前任务确实需要该确定性能力，但不必自动等于“只能由某一个 Tool 实现”。

只有以下情况才把某个具体 Tool 写成不可替代：

- 当前科学方法明确规定；
- 当前数据格式/安全约束只有该实现满足；
- 已冻结接口要求必须由它产生完全确定的 handoff；
- 没有等价且已验证的替代实现。

## 7. Tool request

需要新共享 Tool 时，至少说明：

```yaml
tool_request:
  capability:
  reason:
  callers: []
  required_inputs: []
  expected_outputs: []
  read_paths: []
  write_paths: []
  side_effects: []
  role: required_capability | preferred_implementation | optional_helper
```

还应说明：

- 哪部分规则已经冻结为确定性逻辑；
- 哪部分仍属于 Agent 的科学判断；
- 是否存在现有 Tool 可以复用或适配；
- Tool 不可用时是否存在合理的等价路径；
- 为什么它不是不必要的 parser gate。

## 8. 两个根目录

任何 Tool 调用都必须区分：

```text
Skill architecture root
MD project root
```

Tool 实现、registry、Skill reference 位于 Skill architecture root；Task Sheet、result index 和真实科研文件位于 MD project root。

Tool 不得默认两个 root 相同，也不得为了找输入无限扫描项目。

Lightweight Tool 应优先接受明确业务文件/目录和必要参数。

## 9. 生命周期

共享 Tool 生命周期保持：

```text
REQUESTED
→ DESIGNED
→ IMPLEMENTED
→ TESTED
→ ACTIVE
→ DEPRECATED
→ RETIRED
```

只有 `ACTIVE` 且当前接口适配 Lightweight Runtime 的 Tool 才能作为默认 production implementation。

历史 Tool 如果仍依赖 Legacy `task.yaml`、route/event/transaction closure，只能作为 Legacy-interface 工具，不能为了调用它重新构造旧 Runtime。

## 10. Lightweight Tool 接口原则

默认接口：

```text
明确输入文件/目录
+ 必要业务参数
+ 明确输出位置或输出策略
→ deterministic execution
→ 明确结果/report
```

避免：

```text
runtime task object
→ Tool 解包项目状态
→ Tool 决定下一阶段
→ Tool 构造 route/event/state closure
```

Tool 输出是否成为正式科研结果由调用 main Skill 决定；Tool 不自行决定项目级任务状态。

## 11. Hard gate

任何 Skill 把某项确定性能力设为不可跳过的 hard gate 前，必须存在：

```text
一个可运行、已验证的实现
或
一个明确、安全、等价的可执行备用路径
```

缺少能力时保持当前任务未完成并说明问题；不得通过降低科学要求或伪造 Tool 结果继续。

## 12. 失败与回退

Tool 失败时：

- 不把失败解释成成功；
- 有明确等价路径时可以回退；
- 没有等价路径时停止当前动作；
- 不因为 Tool 失败扩大扫描整个项目；
- 不临时修改 schema 或科学 gate 以绕过问题。

如果 Tool 产生部分文件，其 cleanup / recovery 必须由 Tool contract 或调用 Skill 说明。

## 13. 写入型 Tool

写入型 Tool 必须明确：

- 输入路径；
- 输出路径/目录；
- 是否允许覆盖；
- 冲突行为；
- 部分失败 cleanup；
- 必要的执行前后校验。

Tool 不直接维护：

```text
00_project_records/task_index.md
00_project_records/tasks/Txxxx.md
00_project_records/project_result_index.md
```

除非某个当前 Stage architecture 明确把某个项目级索引交给该 Tool 维护，例如 Stage 5 已冻结的 prepared-input indexes；这种例外必须由对应 Stage/main Skill 明确授权，而不是 Tool 自己扩权。

## 14. Authoring 自检

- [ ] 该逻辑确实具有确定性 Tool 价值；
- [ ] Tool 不解释用户意图或作开放式科学判断；
- [ ] Tool 不决定其他 Skill 行为；
- [ ] Tool 不成为无必要 parser gate；
- [ ] required / preferred / optional 的定位清楚；
- [ ] Tool 接受明确业务输入；
- [ ] Tool 不恢复 Legacy orchestration；
- [ ] Tool 不可用时的行为清楚；
- [ ] 没有因为“已有 Tool”就强制 Agent 使用它。
