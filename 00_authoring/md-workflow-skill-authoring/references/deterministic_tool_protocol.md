# MD Workflow 确定性 Tool 协议

## 1. 定位

Tool 是可重复执行的确定性程序，不是新的科学决策层，也不是新的 Agent 层。

Lightweight Runtime v2 下的基本关系为：

```text
Task Execution Agent
→ 当前 Step Skill
→ 必要时调用 deterministic Tool
→ Tool 返回确定性结果
→ 当前 Step 继续执行或验证
```

Tool 的价值是把已经能够明确程序化的动作做得更快、更稳定、更可测试，而不是替代 Task Execution Agent 理解用户意图、作开放式科学判断或维护一套 Runtime 编排系统。

Tool 不得：

- 解释或扩大用户研究目标；
- 选择当前 Task 或 Task 范围；
- 决定 Workflow 下一 Step；
- 作开放式科学判断；
- 向用户提问；
- 自行创建或调用 Agent；
- 为普通 Lightweight 执行强制构造 Workstream、route、event、runtime task/result、artifact state 或 transaction closure；
- 修改超出自身明确授权范围的文件。

## 2. 工具归属

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

业务 Skill 可以声明现有 Tool 依赖或提出 `tool_request`，但不得在真实运行中的业务 Task 内临时修改共享 Tool。

Skill 独有、不会跨 Skill 复用的小脚本可以保留在当前 Skill 的 `scripts/`；跨 Skill 重复使用、需要独立生命周期管理的程序才进入 `05_tools/`。

## 3. 两个根目录

任何 Tool 调用都必须区分：

```text
Skill architecture root
MD project root
```

- Tool 实现、Tool registry、Skill 自身 reference/schema 位于 Skill architecture root；
- Task Sheet、result index 和真实科研业务文件位于 MD project root；
- Tool 不得默认两个 root 相同；
- Tool 不得默认真实项目根目录存在 `03_contracts/`；
- Lightweight Tool 应优先接受明确文件路径、目录路径和业务参数，而不是隐式扫描项目寻找输入。

## 4. Tool 开发触发条件

满足以下任一条件时可以考虑共享 Tool：

- 同一确定性逻辑在多个 Skill 中重复；
- 程序执行明显比 LLM 更快、更稳定；
- parsing / hashing / mapping / deterministic transform 容易被自然语言执行造成不一致；
- 需要可靠格式校验；
- 需要批量或缓存；
- 需要安全的原子文件写入；
- 需要稳定、可重复的测试和 benchmark。

以下情况本身不足以开发新 Tool：

- 只是为了把一次简单文件操作包装起来；
- 只是为了减少几行 Skill 说明；
- 只是为了恢复旧 Runtime 的 task/result/event/route 闭环；
- 只是因为“程序化看起来更正式”。

此前 Runtime 性能测试已经表明，分钟级开销主要来自多层 LLM 编排，而不是几百毫秒级确定性程序，因此不得通过继续堆叠 orchestration Tool 解决同类问题。

## 5. Tool request

需要新共享 Tool 时，业务 Skill 至少提出：

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
```

还应说明：

- 哪部分规则已经冻结为确定性逻辑；
- 哪部分仍属于 Task Execution Agent / Operation / Validator 的科学判断；
- 是否存在现有 Tool 可以复用或适配；
- Tool 不可用时是否存在合理的内建确定性备用路径。

## 6. 生命周期

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

只有 `ACTIVE` 且当前接口适配 Lightweight Runtime 的 Tool 才能作为默认运行路径。

历史 Tool 即使科学动作仍然有效，只要当前接口要求 Legacy `task.yaml`、subagent result、route/event/transaction closure，就只能标记为 Legacy-interface，不能为了调用它重新构造旧 Runtime 对象。

## 7. Lightweight Tool 接口原则

新 Tool 默认优先采用显式业务接口，例如：

```text
输入文件路径
+ 输出目录/文件路径
+ 必要业务参数
→ deterministic execution
→ 明确结果 / report
```

避免：

```text
runtime task object
→ Tool 解包项目状态
→ Tool 决定下一阶段
→ Tool 构造 route/event/state closure
```

Tool 输出应尽量直接被当前 Operation / Validator 消费。

如果输出属于 Step 的正式结果，是否登记为 `official result` 由 Step Skill 决定，不由 Tool 自行登记 `project_result_index.md`。

## 8. Hard gate 与能力检查

任何 Step 把某项确定性能力设为不可跳过的 hard gate 前，必须至少存在一种可运行实现：

```text
ACTIVE 且接口适配的 Tool
或
当前 Skill 明确定义的内建确定性路径
```

规则：

- `DESIGNED / IMPLEMENTED / TESTED` 但未 ACTIVE 的共享 Tool 不是默认生产实现；
- Tool 仍是 Legacy-interface 时，不得算作 Lightweight 默认能力闭合；
- 缺少所需能力时，当前 Step 保持 `未完成`，向用户说明当前技术问题；
- 不得通过降低科学 gate 或伪造 Tool 结果继续；
- 不得为了满足 hard gate 临时重新引入旧 Runtime orchestration。

简单软件依赖检查可以由当前 Task Execution Agent 在 Step 开始时最小化执行；不要求所有依赖检查都先开发一个独立 Tool。

## 9. 失败与回退

Tool 执行失败时：

- 不得由 LLM 把失败结果解释成成功；
- 当前 Step 根据实际影响保持 `未完成` 或使用已批准的备用路径；
- 有明确、安全、等价的内建确定性路径时可以回退；
- 没有等价备用路径时停止当前动作并说明 blocker；
- 不自动修改 schema、降低 gate 或忽略校验错误；
- 不因为 Tool 失败扩大扫描整个项目。

如果 Tool 产生部分文件，应由 Tool contract 或调用 Skill 明确 cleanup / recovery 行为，避免残留文件被误认为正式结果。

## 10. 写入型 Tool

只读 Tool 不修改项目文件。

写入型 Tool 必须明确：

- 输入路径；
- 输出路径；
- 是否允许覆盖；
- 冲突行为；
- 部分失败 cleanup；
- 原子写入要求（若需要）；
- 执行前后需要核验的 hash / count / schema / format 条件。

科研业务文件的写入必须由当前 Step 的 Operation / Validator 语义授权。

Tool 不直接维护：

```text
00_project_records/task_index.md
00_project_records/tasks/Txxxx.md
00_project_records/project_result_index.md
```

这些 Lightweight records 由 Manager / Task Execution Agent 按当前职责维护。

## 11. Schema 与格式校验

Skill 自身拥有的 schema 可以直接由其脚本或合适的 Tool 校验。

不再要求普通 Lightweight Task 统一通过 Legacy `runtime_schema_validator FAST/FULL` 对 project state、route、event、artifact 等事务对象闭环。

历史 `runtime_schema_validator`、runtime record committer、route fast-path evaluator 等可以继续保留用于：

- Legacy 项目维护；
- 历史审计；
- 明确的 Legacy migration；

但不属于新 Skill 的默认 Tool 依赖。

如果未来需要针对 Lightweight records 建立专门的静态/格式检查，应根据实际问题单独设计，不直接复用旧 Runtime transaction 模型。

## 12. Cache 与中间数据

Tool 的 cache / temporary data 必须：

- 可删除、可重建；
- 不作为 Task 当前状态的唯一来源；
- 不替代 official results；
- 不污染 Skill architecture root 的权威 source；
- 明确属于哪个 project / task / step，避免跨任务误用。

如果 cache 参与结果等价性判断，决定其有效性的条件必须由对应 Step Skill 的 reuse rules 明确，而不是由 Tool 私自扩大复用范围。

## 13. Authoring 自检

为业务 Skill 引入 Tool 前确认：

- [ ] 该逻辑确实是确定性的；
- [ ] Tool 不解释用户意图或作开放式科学判断；
- [ ] Tool 不决定下一 Step；
- [ ] Tool 接受明确业务输入而不是依赖 Legacy task/route/event；
- [ ] Tool 输出可直接映射到当前 Operation / Validator 的需要；
- [ ] Tool 不直接登记 Task Sheet / result index；
- [ ] Tool 不可用时的行为已明确；
- [ ] 没有为了简单动作或旧 Runtime 兼容而无必要新增 Tool；
- [ ] 如果是历史 Tool，已经核验其接口是否真正 Lightweight-compatible。
