# Lightweight Runtime v2 Specification

Status: CURRENT DEFAULT RUNTIME ARCHITECTURE

## 1. Goal

Lightweight Runtime v2 让 MD Workflow 的默认运行方式接近：

```text
长期持有 Task Sheet 的科研执行 Agent
+ 按需加载当前 main Skill
+ 只有需要时再读取 reference / supporting Skill / Tool guide
```

而不是事务型 Workflow engine。

保留：

- 科研 Skill 中真正需要的科学/执行 guidance；
- reuse、validation、provenance、用户确认和 recovery 中真正必要的信息；
- 确定性 Tools；
- Stage-specific execution objects，例如 Stage 4 run units、Stage 5 plan items。

默认不再依赖：

```text
Workstream
route / route revision
runtime task/result
project event
artifact state machine
transaction closure
runtime projection state
```

## 2. Current Skill model

科研 Skill 当前不强制分类为 Workflow / Operation / Validator。

默认：

```text
main Skill
├── references/
├── schemas/           # only when genuinely useful
├── scripts/
└── supporting Skill   # only for complex, clear boundaries
```

现存 `01_workflows/`、`02_operations/`、`02_validators/` 是历史布局/迁移中的路径，不是 Runtime 或 authoring 必须遵循的分类。

Task Execution Agent 按当前任务加载**当前 main Skill**，而不是机械经过 Workflow → Operation → Validator 调度链。

## 3. Skill is guidance, not a parser gate

Skill 的作用是指导 Agent 如何处理任务。

默认：

- Agent 可以直接读取实际科研文件并理解当前对象；
- parser / Tool 用于真正需要精确、稳定、批量、可测试的确定性动作；
- 推荐 Tool 不自动等于唯一允许实现；
- 只有科学方法或明确技术接口真正要求时，才规定不可替代的软件/算法/格式路径；
- 不为简单判断增加无必要 parser/schema/dispatcher 状态链。

## 4. Project records

默认项目记录：

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    ├── T001.md
    └── ...
```

### `task_index.md`

只用于任务导航：

```text
Task ID
Task name
Task status
Task Sheet full path
```

任务状态：

```text
未完成
已完成
已终止
```

### Task Sheet

Task Sheet 是任务计划、进度和最小恢复上下文。

普通 sub-stage 至少记录：

```text
状态
对象
工作目录
主要结果（完成后）
执行记录（仅必要时）
```

普通 sub-stage 状态：

```text
待执行
未完成
已完成
```

Stage-specific 内部对象可以使用其 freeze 文件明确的局部状态模型，例如：

- Stage 4 run units：`未完成 / 已完成 / 已终止`；
- Stage 5 5.1 plan items：`未完成 / 已完成 / 已终止`。

### `project_result_index.md`

用于跨任务/跨对话检索正式结果，不保存当前任务状态，也不是 artifact registry 或 summary。

登记粒度由当前 Skill/Stage 明确的 result boundary 决定。

## 5. Manager

Manager 与 Task Execution Agent 默认是不同对话。

Manager 只负责：

1. 任务定位；
2. 新任务创建；
3. 初始规划；
4. 用户明确要求时重新规划；
5. 项目级任务导航/整理。

Manager 正常只读：

```text
00_project_records/task_index.md
目标 tasks/Txxxx.md
```

创建新任务或显式重新规划时再读：

`00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

Manager 不：

- 预读所有科研 Skills；
- 扫描 project_result_index 做每一步 reuse；
- 判断具体科研步骤 applicability；
- 建 route / Workstream / event；
- 创建 task-specific 科研执行目录。

## 6. Initial planning

Manager planning index 只提供：

- Stage/Step ID；
- name；
- order；
- project/base work directory；
- 明确冻结的 stage-specific planning mode。

不含：

```text
conditional / applicability
scientific decision rules
reuse conditions
input/output schemas
validation
commands
dependencies
failure recovery
artifact lineage
```

### Stage 4 exception

Stage 4 不把 Task Sheet 表示成固定 `4.1 → 4.2 → 4.3`，而是 planned run route。4.1/4.2/4.3 是 execution layers，formal run units 是 `em.N / nvt.N / npt.N / md.N` execution objects。

Manager 不在 planning 时分配 formal run-unit IDs。

### Stage 5

Stage 5 仍是普通 sub-stage planning：Manager 只创建 `5.1 Analysis planning and orchestration` 并记录用户明确的分析目标/对象/约束。具体 analysis plan 由 Stage 5 main Skill 在执行期展开。

## 7. Directory model

普通 Step：

```text
<base_work_directory>/
└── <task_id>/
```

项目初始化可以创建稳定 Step base directories。

Manager 只把未来 `<base>/<task_id>/` 路径写入 Task Sheet，不创建该目录。

Task Execution Agent：

```text
进入当前工作
→ 按当前 Skill/Stage 规则检查 reuse
→ 可直接复用：不创建空 task directory
→ 需要本地执行：创建当前 task directory
```

Stage-specific directory/index rules 以相应 freeze/main Skill 为准。

## 8. Task Execution Agent

Task Execution Agent 长期持有一个 Task Sheet，并连续推进多个 Step。

普通执行顺序：

```text
read target Task Sheet
→ determine current task item/object
→ read current main Skill
→ query relevant historical results when required
→ apply current Skill/Stage reuse rules
→ read only needed references/supporting Skills/Tool guides
→ execute if required
→ validate according to current owner
→ update Task Sheet
→ register formal results
→ adjust future plan if current evidence requires
→ continue
```

普通子环节之间不回 Manager 调度。

用户在执行对话中明确改变任务范围时，可以直接修改 Task Sheet。

## 9. Task-facing Skill information requirements

当前 main Skill 不需要使用固定 section schema，但必须让 Agent 能回答：

```text
当前目的是什么？
实际处理对象/输入是什么？
已有结果什么情况下可复用？
执行必须遵守哪些规则？
结果如何 validation？
哪些结果/记录需要 handoff？
```

常用表达可以是：

```text
purpose
object/input requirements
reuse conditions
execution guidance
validation requirements
results / handoff
```

这些是信息要求，不代表需要拆成多个 Skill。

## 10. External Skill boundary

Task Execution Agent 可以按当前任务需要读取其他 Skill 来理解接口。

一个 main Skill 可以声明：

```text
消费外部哪个正式结果
调用外部什么能力
依赖外部哪个已冻结判据
```

但不复制其他 Skill 的内部流程、默认参数、validation、official results 或文件生命周期。

## 11. Reuse

普通工作通常在真正开始时检查 reuse：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足 → 当前用户可见 Task Execution Agent 询问用户
用户明确要求重做/对照 → 跳过自动复用
```

不要仅因为目录/文件存在、文件名相同或任务名称相似就复用。

复用其他任务正式结果时直接引用，不复制“本任务副本”。

Stage 5 是已冻结组织例外：5.1 在整体 analysis plan 生成时集中查询和核验 Stage 5 reuse，并同时考虑当前 plan 中前置 producer 将生成、供后续 item 使用的文件；正常后续执行不逐项重做全局查询。

## 12. Validation ownership

Validation 默认跟随当前结果 owner。

```text
main Skill 产生/判断结果
→ main Skill 定义 validation
```

只有 validation 本身复杂、可复用、边界清晰时才拆 supporting Skill。

Tool 对自己生成的确定性输出负责机械/格式有效性；main Skill 对这些输出是否满足当前科研目标负责。

Stage 4：4.1/4.2/4.3 supporting Skills 各自负责对应 run validation。

Stage 5：每个 concrete analysis Skill/Tool 对自己的输出负责 validation；5.1 只负责 plan/orchestration consistency。

## 13. Result registration

只登记当前 Skill/Stage 定义的正式结果/结果事项。

不登记：

- debug/scratch/cache；
- 普通过程文件；
- 为了“完整”而复制的重复文件索引。

Stage-specific examples：

- Stage 4：登记 project-level `04_md_simulation/run_unit.yaml`；
- Stage 5：登记“对哪些对象做了哪些分析 + 详细 Task Sheet/5.1 plan-item 入口”。

## 14. Stage 4 project-level run units

Stage 4 项目级文件：

`<project_root>/04_md_simulation/run_unit.yaml`

当前最小 record：

```yaml
- run_unit_id:
  start_from_run_unit_id:
  status:
  path:
  top:
```

`path` 是完整存放目录，用于查询，不规定 working directory。

`top` 是该 run unit 实际用于 `grompp` 的主 `.top` 完整路径。

详细规则以：

`04_md_simulation/SKILL.md`

为准。

## 15. Stage 5 planning/index model

Stage 5 main Skill：

```text
05_analysis/SKILL.md
```

Catalog：

```text
5.1 Analysis planning and orchestration
```

5.1 plan items 使用局部固定整数编号，最小字段：

```text
编号
tool
inputs
settings
status
path
```

Project-level prepared-input indexes：

```text
<project_root>/05_analysis/indexes/
├── trajectory_index.yaml
└── ndx_index.yaml
```

Capability inventory：

`05_analysis/references/analysis_tool_inventory.yaml`

维护责任和 reuse 规则以 `05_analysis/SKILL.md` 和具体 capability owner 为准。

## 16. Minimal reads

真实科研 runtime 按需读取，不以“全面了解”为理由扩大上下文。

Manager 不默认读 project result、其他 Task Sheets、全部 Skills、Legacy runtime records。

Task Execution Agent 不默认：

- 预读未来 Steps；
- 扫描所有任务；
- 重读上游全过程；
- 加载 Legacy route/state/event/runtime records。

注意：这条 runtime 最小读取规则不等同于 authoring 窗口禁止阅读其他 Skill。Authoring 为了理解边界可以按需读取相关外部 Skill，但写入所有权仍严格受限。

## 17. Legacy rule

Legacy Runtime 可以保留用于 Git history、旧项目迁移或明确调试，但：

- 新项目不默认生成 Legacy records；
- Lightweight Runtime 不双写旧 records；
- 新 Skills 不增加 Legacy compatibility layer；
- historical files 标为 `LEGACY` / `SUPERSEDED` 时不得用来推翻 current Skills/freeze records。

当前 authoring/version authority 见：

`00_authoring/README.md`
