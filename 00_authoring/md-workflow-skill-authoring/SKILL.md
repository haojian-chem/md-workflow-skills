---
name: md-workflow-skill-authoring
description: 设计、编写、拆分或重构本项目科研 Skill 时使用。当前模式以“主 Skill 指导 Agent 如何完成任务”为核心；不强制 Workflow/Operation/Validator 分类，不把 Agent 锁进固定 parser 或编排链，并严格区分多窗口的读取范围与写入所有权。
---

# 目标

把科研工作要求转化为**Agent 可直接使用的任务处理指南**。

当前设计原则：

```text
Manager
→ Task Sheet
→ Task Execution Agent
→ 当前任务所需 main Skill
   ├─ 按需读取 references
   ├─ 按需调用 supporting Skill
   └─ 按需调用 deterministic Tool
```

科研 Skill 的首要职责是告诉 Agent：

- 当前任务要解决什么；
- 要理解哪些对象和证据；
- 必须做哪些判断；
- 哪些科学/技术边界不能越过；
- 哪些方法/工具适合使用；
- 怎样判断结果有效；
- 如何记录和交接结果。

Skill 不是为了把 Agent 包装成一个固定 parser/workflow runner。

# 启动前

开始 authoring / maintenance 时读取：

1. `AGENTS.md`；
2. `00_authoring/README.md`；
3. `00_authoring/AUTHORING_RULES.md`；
4. `00_authoring/lightweight_runtime_v2_spec.md`；
5. `00_authoring/SYNC_STATUS.md`；
6. `00_authoring/skill_inventory.yaml`；
7. `00_authoring/file_ownership.yaml`；
8. 目标 Skill 的 content map；
9. 目标当前 Skill；
10. 与当前输入/输出/边界直接相关的其他 Skill、Tool guide 和 architecture-freeze record。

这里第 10 项很重要：**业务窗口可以并且应该读取不属于自己写入范围的相关 Skill。** 读取用于理解边界和 handoff，不意味着获得写入权或定义权。

提出修改前先列出：

```text
已做过
已否定
仍未验证
```

# 1. 先确认当前 Skill 真正拥有的任务

不要先问“这是 Workflow、Operation 还是 Validator”。

先回答：

```text
这个 Skill 指导 Agent 完成什么任务？
这个任务的输入/证据是什么？
这个 Skill 的科学判断边界在哪里？
它消费哪些外部结果？
它产生什么可继续使用的结果？
哪些内容属于别的 Skill？
```

详细边界参考：

`references/skill_boundaries.md`

Manager 是项目级管理 Skill，保留特殊职责；普通科研 Skill 不再强制分类为 Workflow / Operation / Validator。

# 2. 设计 main Skill，而不是先拆层

默认先写一个 main `SKILL.md`，确保 Agent 可以据此完成当前职责。

主文件通常需要覆盖：

```text
purpose / goal
scope and boundaries
inputs / evidence
reuse logic
execution guidance
validation
results / handoff
```

这些是需要表达的信息，不是强制 section schema。

只有以下情况才拆 supporting Skill：

- 一块内容复杂且有清楚独立边界；
- 可以独立按需加载；
- 多个 main Skill 会复用它；
- 需要独立测试或 validation 生命周期；
- 拆出后能显著减少主 Skill 上下文，而不会制造额外编排层。

如果只是内容较长但仍属于当前 Skill 的规则，优先放 `references/`，不要为了“层级完整”增加新 Skill。

# 3. Skill 是指南，不是 parser gate

编写每条执行规则时检查：

> 这是当前科学/技术任务真正要求，还是只是为了让 Agent 必须经过某个 parser / wrapper / workflow？

默认不要规定：

```text
必须 parser A → schema B → dispatcher C → 才能理解输入
```

如果 Agent 可以直接可靠读取当前文件并完成判断，就允许直接读取。

应优先使用 Tool 的场景包括：

- 精确 parsing；
- 批量结构化提取；
- hash / mapping；
- 稳定文件变换；
- 明确格式校验；
- 高重复度、可测试的确定性计算。

Tool 是能力组件。除非方法本身明确要求，Skill 不应仅因为某 Tool 已存在就把它写成唯一许可路径。

若特定软件/算法是科学方法的一部分，可以明确要求，并说明它承担的实际方法职责。

# 4. 外部 Skill：可以读，不可以代写

Authoring 窗口应按需了解上下游和相邻 Skill。

在当前 Skill 中，外部 Skill 只记录接口级关系：

```text
需要读取它的哪个正式结果
需要调用它的什么能力
当前 Skill 依赖它已冻结的哪个判据
当前输出将被哪个下游能力消费
```

禁止在当前 Skill 内重新定义外部 Skill 的：

- 内部步骤；
- 默认参数；
- 选择逻辑；
- validation；
- official results；
- 文件保存规则；
- 任务计划规则。

发现外部规则有问题时：

```text
记录 finding / handoff
→ 指明 owner Skill
→ 交给 owner window / main window
```

不要把修正偷偷写进当前 Skill 作为“兼容规则”。

详细协议：

`references/multi_window_authoring_protocol.md`

# 5. 读取范围与写入所有权分离

多窗口时：

```text
read_paths 可以很宽
write_paths 必须很窄
```

读取其他 Skill 不需要拥有它。

写入必须满足：

- 当前路径位于本窗口分配的 `write_paths`；
- 没有与其他窗口重叠；
- 共享 authoring/index/architecture 文件只由 main window 修改；
- 若用户明确扩大本窗口职责，再重新分配 write ownership。

不要把 `read_paths` 写成“只能读取这些路径”的白名单。它只是启动上下文建议；需要理解接口时应继续按需读取相关外部 Skill。

# 6. Reuse

Skill 应定义真正影响当前结果是否仍可用的条件，而不是根据文件名或目录存在猜 reuse。

通常：

```text
明确等价 → 自动复用
明确不等价 → 重新执行
信息不足 → 当前 Task Execution Agent 向用户确认
用户明确要求重做/对照 → 不自动复用
```

如果某 Stage 已冻结不同的 reuse 组织时机，例如 Stage 5 在 5.1 planning 时集中核验，则遵循该 Stage guide，不为了模板统一改回逐项模式。

# 7. Execution guidance

执行规则应区分：

```text
必须遵守的科学/技术约束
推荐路径 / tendency
可替代实现
明确禁止的做法
```

不要把“推荐”写成“唯一合法实现”。

如果多个工具都能完成同一动作，Skill 可以给选择原则；Agent 根据当前对象、环境、用户要求和可用能力选择。

如果有真正不可替代的顺序或软件要求，要明确原因。

# 8. Validation

Validation 默认由拥有当前动作/结果的 main Skill 或 Tool 定义。

只有当 validation：

- 本身复杂；
- 有独立清楚边界；
- 需要复用；
- 需要独立测试/维护；

才拆出 supporting validation Skill。

不要为了形成 `Operation + Validator` 对而人工拆分。

Validation 必须说明“什么证据意味着当前结果有效”，而不是只检查某个 parser/report 文件是否存在。

# 9. Results and handoff

Skill 必须让后续 Agent 能定位并理解真正需要的结果。

应区分：

```text
正式结果 / handoff
中间文件
临时/debug/cache
```

`project_result_index.md` 的登记粒度由当前 Stage/Skill 决定，不强制所有 Skill 都逐文件登记。

跨 Skill handoff 优先通过正式结果和清楚接口完成，不要求下游重新读取上游全过程。

# 10. 文件组织

默认按科学职责组织，不按旧角色分类组织。

典型：

```text
<skill-directory>/
├── SKILL.md
├── references/
├── schemas/
├── scripts/
└── <supporting-skill>/SKILL.md   # only when justified
```

只创建实际需要的目录。

仓库中现有：

```text
01_workflows/
02_operations/
02_validators/
```

是历史布局/迁移中的现存路径，不是新 Skill 的强制模板。新 Skill 不得仅为了落入其中某类而拆分职责。

渐进披露：

`references/progressive_disclosure.md`

# 11. Content ownership

使用 content map 记录：

- 当前 main Skill 拥有哪些规则；
- supporting Skill / reference 各自拥有哪些明确内容；
- 当前 Skill 只读哪些外部 authority。

新 content map 不再使用 `workflow / operation / validator` 强制类型字段。

详细规则：

`references/content_ownership_and_deduplication.md`

# 12. Tool candidates

只有确定性、重复、稳定、可测试的动作才优先工具化。

Tool request 至少说明：

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

同时说明：

- Agent 仍需做哪些科学判断；
- Tool 是否只是 optional helper；
- Tool 不可用时是否有合理替代；
- 为什么它不是不必要的 parser gate。

Tool authoring：

`00_authoring/md-workflow-tool-authoring/SKILL.md`

# 13. 多窗口交付检查

提交前检查：

- [ ] 已按需读取直接相关的上下游/相邻 Skill；
- [ ] 未修改未分配的 write path；
- [ ] 当前 Skill 未重新定义外部 Skill 内部规则；
- [ ] 没有因为旧目录而强制 Workflow/Operation/Validator 分类；
- [ ] 没有为了形式化新增无价值 supporting Skill；
- [ ] 没有把 Agent 锁死到不必要 parser/wrapper/dispatcher；
- [ ] 推荐工具和强制方法要求区分清楚；
- [ ] reuse、validation、handoff 足以支持跨对话继续；
- [ ] 没有恢复 Legacy Workstream/route/event/transaction 依赖。

# 14. 模板

普通科研 Skill 使用：

`assets/skill.template.md`

Manager 可使用：

`assets/manager_skill.template.md`

旧 `workflow_skill.template.md`、`operation_skill.template.md`、`validator_skill.template.md` 仅保留为 `SUPERSEDED` 指向，不再作为当前模板。

# 交付

Authoring 对话返回精简摘要：

```yaml
status: DRAFTED | REVIEW_REQUIRED | BLOCKED
skill_name:
read_context: []
owned_write_paths: []
created_files: []
modified_files: []
validation:
  errors: []
  warnings: []
cross_skill_findings: []
tool_requests: []
open_questions: []
next_action:
```
