# MD Workflow Authoring Rules

Status: CURRENT

本文件保存 Skill / Tool 设计、冻结、审查和多窗口协作规则，属于 **AUTHORING_ONLY** 材料。真实科研项目运行时不得默认读取本文件。

当前默认 runtime architecture：

`00_authoring/lightweight_runtime_v2_spec.md`

## 1. Current authority

Authoring 开始时按需读取：

```text
AGENTS.md
00_authoring/README.md
00_authoring/AUTHORING_RULES.md
00_authoring/lightweight_runtime_v2_spec.md
00_authoring/SYNC_STATUS.md
00_authoring/skill_inventory.yaml
00_authoring/file_ownership.yaml
目标 content map
目标当前 Skill / Tool guide
与当前修改直接相关的 architecture-freeze / 上下游 guide
```

发生冲突时：

```text
current Skill / Tool guide
> matching architecture-freeze record
> MD_WORKFLOW_MASTER_PLAN.md / SYNC_STATUS.md
> explicitly SUPERSEDED / LEGACY / historical files
```

**文件存在不代表当前有效。** `SUPERSEDED` / `LEGACY` 文件只用于历史追溯或明确迁移维护，不得用于恢复当前接口。

提出或实施修改前先明确：

```text
已做过
已否定
仍未验证
```

没有新证据改变前提时，不重复已经失败或明确否定的方案。

## 2. Core design principle: Skill guides the Agent

新的科研 Skill 首先是**指导 Agent 如何处理任务的科研/执行指南**，不是把 Agent 锁进一个固定 parser、固定程序链或人为工作流引擎。

Skill 应明确：

- 当前任务要达到什么科学/技术目标；
- 需要理解哪些输入和证据；
- 哪些判断必须做、哪些边界不能越过；
- 哪些步骤存在真正的科学先后关系；
- 可使用哪些 Tool / software / supporting Skill；
- 如何判断结果有效；
- 哪些信息需要记录和交接。

Skill **不应仅为了形式化**而要求：

- 先经过某个 parser 才允许理解一个 Agent 本来可以直接读取的文件；
- 把所有任务转成固定 schema 后才能继续；
- 通过额外 Workflow/dispatcher 层才能调用实际能力；
- 把一种推荐工具写成唯一允许实现，除非该实现本身是已经冻结的科学/技术要求；
- 为简单判断建立不必要的中间状态机。

Parser / deterministic Tool 的定位是：在 parsing、批量处理、精确变换、稳定写入、可重复计算或机械校验上提供可靠能力。它们是**能力组件**，不是 Agent 理解任务的前置许可层。

如果某一步确实必须使用特定软件/算法/文件格式，Skill 可以明确要求；但必须来自科学方法、可重复性或实际接口需求，而不是因为 authoring 模板习惯如此。

## 3. Skill organization: main Skill first

当前设计**不再强制把科研 Skill 分类成 Workflow / Operation / Validator，也不要求分别放入 `01_workflows/`、`02_operations/`、`02_validators/`。**

默认组织方式是：

```text
main Skill
├── references/        # 长规则、表、registry、按需说明
├── schemas/           # 只有确有稳定结构化约束时才建立
├── scripts/           # Skill-local deterministic helpers
└── supporting Skill   # 仅在复杂且边界清晰时拆出
```

主 Skill 应足够让 Agent 完成当前职责。只有满足以下条件之一时才考虑拆 supporting Skill：

- 内容复杂，放在主 Skill 会明显淹没主线；
- 边界稳定且可独立加载；
- 多处复用同一套完整判断/执行逻辑；
- 需要独立 validation / testing 生命周期；
- 独立维护能明显减少上下文而不制造额外编排层。

Validation 默认跟随拥有该动作/结果的 Skill 或 Tool；只有 validation 本身复杂、可复用、边界清晰时才拆成独立 supporting Skill。

Manager 是项目级管理 Skill，保留自己的特殊职责。Tool 是确定性能力组件，不属于科研 Skill 分类层。

仓库中现存的 `01_workflows/`、`02_operations/`、`02_validators/` 是历史布局和逐步迁移中的现有路径，**不得被新窗口当成新 Skill 必须遵循的目录模板**。不要仅为了匹配旧目录分类而新建或拆分 Skill。

详细边界：

`00_authoring/md-workflow-skill-authoring/references/skill_boundaries.md`

## 4. Read broadly, write narrowly

多窗口 authoring 中必须区分：

```text
read scope  ≠  write ownership
```

每个窗口**可以并且应该**按当前任务需要读取其不负责写入的 Skill，尤其是：

- 直接上游 Skill；
- 直接下游 Skill；
- 当前输入/输出所依赖的 supporting Skill / Tool guide；
- 具有相邻科学边界的 Skill；
- 当前 Skill 明确引用的外部规则。

读取这些内容的目的，是理解接口、避免重复定义、确认边界和保证 handoff 正确。

但除非用户或 main authoring window 明确重新分配职责，业务窗口只允许修改自己的 `write_paths`。

在自己负责的 Skill 内，对其他 Skill 只允许记录**接口级关系**，例如：

```text
消费上游哪个正式结果
需要下游提供哪类能力
调用哪个 supporting Skill / Tool
依赖哪个已经冻结的外部判据
```

不得在自己的 Skill 中重新定义其他 Skill 的：

- 内部执行流程；
- 默认参数；
- 科学判断逻辑；
- validation 细节；
- official results；
- 文件生命周期；
- 任务计划规则。

如果发现其他 Skill 缺失规则、存在冲突或需要修改：

```text
发现问题
→ 在当前窗口记录 cross-skill finding / handoff
→ 交给拥有该 Skill 的窗口或 main window
→ 不把临时修正规则塞进自己负责的 Skill
```

## 5. Multi-window ownership

共享文件由 main authoring window 修改：

```text
AGENTS.md
00_authoring/README.md
00_authoring/AUTHORING_RULES.md
00_authoring/MD_WORKFLOW_MASTER_PLAN.md
00_authoring/SYNC_STATUS.md
architecture-freeze records
skill_inventory.yaml
file_ownership.yaml
content_maps/
Manager shared references
05_tools/tool_registry.yaml
```

同一 Skill/Tool 目录同一时间只分配给一个编写窗口；写路径重叠时不得并行。

每个窗口开始前必须重新读取 current `SYNC_STATUS.md`、`skill_inventory.yaml`、`file_ownership.yaml`、目标 content map 和当前目标 Skill。与当前接口有关的其他 Skill 可以按需读取，不受 write ownership 限制。

业务窗口不得因为读取了外部 Skill，就擅自修改该 Skill 或在自己的文件中替它定义规则。

## 6. Lightweight runtime boundary

Lightweight Runtime v2 默认记录层：

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/Txxxx.md
```

普通任务不得重新引入第二套等价的：

```text
Workstream
route / route revision
runtime task/result
project event
artifact state machine
transaction closure
runtime projection state
```

这些属于 Legacy history，不是新 Skill 的兼容目标。

Manager 只负责：任务定位、创建、初始规划、用户明确要求时的重新规划，以及项目级导航/整理。普通科研执行由长期持有 Task Sheet 的 Task Execution Agent 完成。

## 7. Task-facing Skill interface

一个主 Skill 不需要为了匹配模板而固定使用某组 section 名，但必须让 Agent 能回答：

```text
当前目的是什么？
实际处理对象/输入是什么？
什么情况下已有结果可以复用？
执行时有哪些必须遵守的科学/技术规则？
如何验证当前结果？
哪些结果/记录需要保留并供后续使用？
```

常用表达仍可采用：

```text
purpose
object/input requirements
reuse conditions
execution guidance
validation requirements
official results / handoff
```

但这些是**信息要求**，不是固定 parser schema，也不要求拆成多个 Skill。

Stage-specific architecture 可以定义自己的计划对象，例如 Stage 4 run unit、Stage 5 plan item；不得为了统一模板强行改写这些已经冻结的局部模型。

## 8. Reuse and results

普通任务的 reuse 通常在实际开始该项工作时检查；如果某 Stage 已冻结其他组织方式，以对应 Stage guide 为准。

统一判断原则：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足 → 当前 Task Execution Agent 向用户确认
用户明确要求重做/对照 → 跳过自动复用
```

复用另一任务的正式结果时直接引用，不为了“本任务完整”复制副本。

`project_result_index.md` 是跨任务/跨对话正式结果检索入口，不是 summary、artifact registry 或运行状态文件。登记粒度由当前 Skill/Stage 决定。

## 9. Tool boundary

共享 Tool 位于：

`05_tools/`

Tool 生命周期 authority：

```text
00_authoring/md-workflow-tool-authoring/SKILL.md
05_tools/tool_registry.yaml
```

Tool 适合承担确定性 parsing / hashing / transformation / file generation / deterministic validation。

引入 Tool 时必须问：

> 这个 Tool 是为了可靠完成一个确定性动作，还是仅仅为了让 Agent 必须经过一个额外接口？

如果属于后者，不应引入。

Tool 不承担：用户意图解释、开放式科学方法选择、任务范围、通用 runtime orchestration state machine。

## 10. Content ownership

一条当前规则只保留一个权威 owner。

- 当前 main Skill 主线 → 当前 `SKILL.md`；
- 长 scientific/registry material → 当前 `references/`；
- 当前 Skill 独有且确有价值的结构化约束 → `schemas/`；
- Skill-local deterministic helper → `scripts/`；
- 跨 Skill 共享确定性程序 → `05_tools/`；
- stage architecture freeze → matching architecture-freeze record；
- Manager initial planning catalog → `workflow_plan_index.yaml`；
- Legacy contracts/runtime → 只作为历史/迁移材料。

Content map 记录当前内容归属和外部只读引用，不再要求 `workflow / operation / validator` 类型字段。

## 11. Validation / review

Representative review 除科学正确性外，必须检查以下 authoring 失败模式：

- Skill 是否把 Agent 锁死到不必要的 parser / wrapper / dispatcher；
- 是否把推荐工具误写成唯一允许实现；
- 是否为了形式化复制大量 schema/状态；
- 是否在当前 Skill 中重新定义其他 Skill 的内容；
- 是否把外部 Skill 的接口描述扩展成其内部算法；
- 是否因为旧 `01_workflows/02_operations/02_validators` 路径而强行分类新 Skill；
- 是否拆出没有独立复杂度或边界价值的 supporting Skill；
- 多窗口是否越过 `write_paths`。

静态检查只能检查结构问题，不能反过来强迫当前 Skill 采用已经废弃的分类或 Legacy Runtime 接口。

## 12. Safety

- 不修改 `01_sources/` 原始来源文件，除非有明确授权；
- 未经授权不删除/覆盖/batch move 科研结果；
- 不自动通过单位计费的期刊数据库下载文献；
- Tool 写路径必须受明确授权边界限制；
- 破坏性或不可逆动作必须取得用户确认；
- Tool 不直接向用户提问，必要确认由当前用户可见对话处理。
