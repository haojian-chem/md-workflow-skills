# MD Workflow Authoring Rules

Status: CURRENT

本文件保存 Skill / Tool 设计、冻结、审查和多窗口协作规则，属于 **AUTHORING_ONLY** 材料。真实科研项目运行时不得默认读取本文件。

当前默认 runtime architecture：

`00_authoring/lightweight_runtime_v2_spec.md`

## 1. Authority and version resolution

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
> matching WORKFLOW*_ARCHITECTURE_FREEZE*.md
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

## 2. Default runtime model

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

## 3. Scientific responsibility layers

逻辑职责：

```text
Manager
Workflow
Operation
Validator
```

Tool 是确定性程序，不是第五个科学判断层。

物理目录通常为：

```text
01_workflows/
02_operations/
02_validators/
05_tools/
```

但已冻结 Stage 可以使用明确的 integrated layout，例如：

```text
04_md_simulation/
```

物理布局可以特殊，逻辑职责边界仍必须清楚。

## 4. Manager boundary

Manager 只负责：

- 定位已有任务；
- 创建新任务；
- 初始规划；
- 用户明确要求时重新规划；
- 项目级任务导航/整理。

Manager 普通初始规划只读：

`00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

planning index 只保存规划需要的轻量信息，例如 Workflow/Step ID、名称、顺序、基础工作目录和已冻结的 stage-specific planning mode。

planning index **不保存**：

- `conditional` / applicability；
- 科学判断规则；
- reuse conditions；
- input/output schema；
- validation；
- commands/software dependencies；
- failure recovery；
- artifact lineage；
- subagent prompts。

Manager 不预读具体 Step Skills，也不提前做科学 applicability/reuse 判断。

## 5. Task Sheet and execution ownership

Task Sheet 是默认运行时计划和最小恢复上下文。

普通 sub-stage 至少记录：

```text
状态
对象
工作目录
主要结果（完成后）
执行记录（仅必要时）
```

任务级状态：

```text
未完成 | 已完成 | 已终止
```

普通子环节状态：

```text
待执行 | 未完成 | 已完成
```

Stage-specific 内部对象可以有自己已经冻结的局部状态规则；例如 Stage 4 run units 和 Stage 5 5.1 plan items 使用 `未完成 / 已完成 / 已终止`，但这不改变普通 Task Sheet sub-stage 状态体系。

Task Execution Agent 长期持有一个 Task Sheet，可以依据执行证据：

- 连续推进多个子环节；
- 更新当前状态和结果；
- 增加、删除或重排尚未执行的未来普通 sub-stage；
- 维护已冻结 stage-specific plan structures；
- 用户明确改变任务范围时直接修改 Task Sheet。

已经执行并形成有意义历史的内容不得为了“整理”而静默删除。Stage 5 的 numbered plan items 一旦加入原则上不删除、不重编号，而使用 `已终止` 保留稳定历史。

## 6. Step-facing Skill interface

普通 Step-facing Skill 或一组配套 Operation + Validator 合计应明确：

```text
purpose
object requirements
reuse conditions
execution rules
validation requirements
official results
```

Stage-specific architecture 可以在 freeze 文件中明确不同的内部组织方式，但同样必须让 Task Execution Agent 知道：

- 当前处理什么；
- 如何判断能否复用；
- 如何执行；
- 谁负责 validation；
- 哪些结果需要正式登记。

Workflow 只保存阶段边界、sub-stage/child Skill 映射和真正必要的阶段级科学关系，不复制具体 Step 的算法和详细参数。

## 7. Reuse

普通 Step 的 reuse 在该 Step 真正开始时检查，而不是 Manager 创建任务时检查。

统一逻辑：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足 → 当前 Task Execution Agent 询问用户
用户明确要求重做/对照 → 跳过自动复用
```

Stage-specific freeze 可以改变 reuse 查询的组织时机。例如 Stage 5 已冻结为：5.1 在整体 plan 生成时集中完成 Stage 5 的 reuse 查询/核验，并同时考虑当前计划内后续将生成的 prepared inputs。

复用另一任务的正式结果时直接引用，不为了“本任务完整”复制副本。

## 8. Directories and result indexes

普通 Step 工作目录采用：

```text
<base_work_directory>/<task_id>/
```

项目初始化可以建立稳定 Step 基础目录，但 Manager 不提前创建 task-specific 执行目录。Task Execution Agent 先检查 reuse，只有需要本地执行时才创建目录。

`project_result_index.md` 是跨任务/跨对话正式结果检索入口，不是 summary、artifact registry 或运行状态文件。

只登记当前 Skill 明确定义的正式结果/结果事项；不登记 debug、scratch、cache、普通中间文件。

Stage-specific result registration 以对应 freeze/Skill 为准。例如：

- Stage 4 登记 project-level `run_unit.yaml`；
- Stage 5 登记“对哪些对象做了哪些分析 + 详细 Task Sheet/plan-item 入口”，而不是逐个工具输出文件。

## 9. Tool boundary

共享 Tool 位于：

`05_tools/`

Tool 生命周期 authority：

```text
00_authoring/md-workflow-tool-authoring/SKILL.md
05_tools/tool_registry.yaml
```

Tool 适合承担确定性 parsing / hashing / transformation / file generation / deterministic validation，不承担：

- 用户意图解释；
- 开放式科学方法选择；
- 任务范围；
- runtime orchestration state machine。

未完成可执行 tests/benchmark 的 Tool 不得作为 ACTIVE 默认生产路径。

## 10. Content ownership

一条当前规则只保留一个权威 owner。

- current Skill 主线 → 当前 `SKILL.md`；
- 长 scientific/registry material → 当前 `references/`；
- 当前 Skill 独有结构化约束 → `schemas/`；
- Skill-local deterministic program → `scripts/`；
- 跨 Skill 共享确定性程序 → `05_tools/`；
- stage architecture freeze → matching `WORKFLOW*_ARCHITECTURE_FREEZE*.md`；
- Manager initial planning catalog → `workflow_plan_index.yaml`；
- Legacy contracts/runtime → 只作为历史/迁移材料。

Content map 只记录当前内容唯一归属和必要外部只读引用；不得继续把 Legacy subagent/route contracts 作为 Lightweight Skill 的当前 dependency。

## 11. Multi-window authoring

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

同一 Skill/Tool 目录同一时间只分配给一个编写窗口。写路径重叠时不得并行。

每个窗口开始前必须重新读取 current `SYNC_STATUS.md`、`skill_inventory.yaml`、`file_ownership.yaml` 和目标 content map；不得依赖旧窗口记忆来判断当前版本。

## 12. Validation / review

可继续使用不依赖 Legacy Runtime 的静态检查，例如 Markdown、content-map 和重复内容检查。

任何仍以 Workstream/route/subagent contract 为成功条件的旧检查，只能标记为 Legacy validation，不能反过来否定当前 Lightweight guides。

Representative validation 应覆盖当前 Skill 实际需要的：

- 正向执行；
- 输入缺失；
- reuse 成功/失败/无法判断；
- 用户明确重做；
- 跨对话恢复；
- dynamic plan update；
- official result registration；
- Tool 不可用或输出 invalid 时的合理处理；
- 不写 Legacy runtime records。

## 13. Safety

- 不修改 `01_sources/` 原始来源文件，除非有明确授权；
- 未经授权不删除/覆盖/batch move 科研结果；
- 不自动通过单位计费的期刊数据库下载文献；
- Tool 写路径必须受明确授权边界限制；
- 破坏性或不可逆动作必须取得用户确认；
- Tool 不直接向用户提问，必要确认由当前用户可见对话处理。
