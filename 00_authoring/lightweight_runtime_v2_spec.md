# Lightweight Runtime v2 Specification

Status: CURRENT DEFAULT RUNTIME ARCHITECTURE

## 1. Goal

Lightweight Runtime v2 让 MD Workflow 的默认运行方式接近“长期持有 Task Sheet 的科研执行 Agent + 按需加载当前 Skill”，而不是事务型 Workflow engine。

保留：

- Workflow / Operation / Validator 的科研职责；
- Step-specific scientific SOP；
- reuse、validation、provenance、用户确认和 recovery 中真正必要的信息；
- 确定性 Tools。

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

## 2. Project records

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

登记粒度由当前 Skill/Stage 明确的 official-result boundary 决定。

## 3. Manager

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

- 预读所有 Step Skills；
- 扫描 project_result_index 做每一步 reuse；
- 判断具体 Step 科学 applicability；
- 建 route / Workstream / event；
- 创建 task-specific 科研执行目录。

## 4. Initial planning

Manager planning index 只提供：

- Workflow/Step ID；
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

普通 Workflow 使用 sub-stage Task Sheet 计划。

### Stage 4 exception

Stage 4 不把 Task Sheet 表示成固定 `4.1 → 4.2 → 4.3`，而是 planned run route。4.1/4.2/4.3 是 execution layers，formal run units 是 `em.N / nvt.N / npt.N / md.N` execution objects。

Manager 不在 planning 时分配 formal run-unit IDs。

### Stage 5

Stage 5 仍是普通 sub-stage planning：Manager 只创建 `5.1 Analysis planning and orchestration` 并记录用户明确的分析目标/对象/约束。具体 analysis plan 由 5.1 执行期展开。

## 5. Directory model

普通 Step：

```text
<base_work_directory>/
└── <task_id>/
```

项目初始化可以创建稳定 Step base directories，例如：

```text
01_structure_preparation/
├── 01_source_recognition/
├── 02_component_and_residue_classification/
├── 03_chain_and_residue_selection/
├── 04_altloc_occupancy_resolution/
├── 05_completeness_check/
├── 06_missing_region_completion/
├── 07_protein_protonation_assignment/
├── 08_reorder_and_mapping/
└── 09_validation/
```

Manager 只把未来 `<base>/<task_id>/` 路径写入 Task Sheet，不创建该目录。

Task Execution Agent：

```text
进入当前 Step
→ 先做该 Step 要求的 reuse 检查
→ 可直接复用：不创建空 task directory
→ 需要本地执行：创建当前 task directory
```

Stage-specific directory/index rules以相应 freeze/Skill 为准。

## 6. Task Execution Agent

Task Execution Agent 长期持有一个 Task Sheet，并连续推进多个 Step。

普通执行顺序：

```text
read target Task Sheet
→ determine current Step/object
→ read current Step Skill
→ query project_result_index for current-Step candidates
→ apply current Skill reuse rules
→ execute if required
→ validate according to current Skill
→ update Task Sheet
→ register official results
→ adjust future plan if current evidence requires
→ continue
```

普通子环节之间不回 Manager 调度。

用户在执行对话中明确改变任务范围时，可以直接修改 Task Sheet。

## 7. Step-facing Skill contract

普通 Step-facing Skill 或 Operation + Validator 组合应明确：

```text
purpose
object requirements
reuse conditions
execution rules
validation requirements
official results
```

Workflow 只保存阶段边界、Step mapping 和真正必要的阶段级科学关系，不复制具体 Step 算法。

Stage-specific architecture 可以定义不同内部对象/计划结构，但必须明确其 execution ownership、reuse、validation 和 result registration。

## 8. Reuse

普通 Step 在真正开始时检查 reuse：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足 → 当前用户可见 Task Execution Agent 询问用户
用户明确要求重做/对照 → 跳过自动复用
```

不要仅因为目录/文件存在、文件名相同或任务名称相似就复用。

复用其他任务正式结果时直接引用，不复制一份“本任务副本”。

Stage 5 是已冻结的组织例外：5.1 在整体 analysis plan 生成时集中查询和核验 Stage 5 reuse，并同时考虑当前 plan 中前置 producer 将生成、供后续 item 使用的文件；正常后续执行不逐项重做全局查询。

## 9. Validation ownership

Validation ownership 由当前 Stage/Skill 明确：

- 普通 Operation 可以调用专属 Validator；
- Validator-only Step 可以自己拥有完整 Step validation；
- Stage 4 run-specific validation 直接属于 4.1/4.2/4.3 Skills；
- Stage 5 不设统一 Validator layer，各 Tool/analysis Skill 对自己产生的数据负责 validation，5.1 只负责 plan/orchestration consistency。

## 10. Result registration

只登记当前 Skill/Stage 定义的 official results。

不登记：

- debug/scratch/cache；
- 普通过程文件；
- 为了“完整”而复制的重复文件索引。

Stage-specific examples：

- Stage 4：登记 project-level `04_md_simulation/run_unit.yaml`；
- Stage 5：登记“对哪些对象做了哪些分析 + 详细 Task Sheet/5.1 plan-item 入口”，不逐个登记所有分析输出文件。

## 11. Stage 4 project-level run units

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

## 12. Stage 5 planning/index model

Stage 5 catalog：

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

维护责任和 reuse 规则以：

```text
01_workflows/analysis_workflow/SKILL.md
02_operations/analysis_planning_and_orchestration/SKILL.md
```

为准。

## 13. Minimal reads

按需读取，不以“全面了解”为理由扩大上下文。

Manager 不默认读 project result、其他 Task Sheets、全部 Skills、Legacy runtime records。

Task Execution Agent 不默认：

- 预读未来 Steps；
- 扫描所有任务；
- 重读上游全过程；
- 加载 Legacy route/state/event/runtime records。

## 14. Legacy rule

Legacy Runtime 可以保留用于 Git history、旧项目迁移或明确调试，但：

- 新项目不默认生成 Legacy records；
- Lightweight Runtime 不双写旧 records；
- 新 Skills 不增加 Legacy compatibility layer；
- historical files 标为 `LEGACY` / `SUPERSEDED` 时不得用来推翻 current Skills/freeze records。

当前 authoring/version authority 规则见：

`00_authoring/README.md`
