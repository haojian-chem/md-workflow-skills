---
name: md-workflow-skill-authoring
description: 设计、拆分、编写或重构本项目的 MD Manager、Workflow、Operation、Validator Skill 时使用。默认面向 Lightweight Runtime v2；保留科研职责分层、内容唯一归属、按需读取、确定性 Tool 边界和多窗口文件所有权，不再把 Legacy Workstream/route/task-result/event 运行时接口写入新 Skill。
---

# 目标

将 MD 工作流需求转化为职责清晰、内容不重复、可直接被 Task Execution Agent 使用的科研 Skills。

当前默认架构为：

```text
Manager 对话
→ Task Sheet
→ Task Execution Agent 对话
→ 当前 Step 所需 Skill
   ├─ Operation
   ├─ Validator
   └─ 必要的 deterministic Tool
```

逻辑上的 Manager / Workflow / Operation / Validator 职责继续保留，但不要求对应为多层 LLM 调度链。

本 Authoring Skill 的目标是保证：

- Manager 只承担任务定位、创建、初始规划和项目级管理；
- Workflow 保存阶段科学边界、子环节关系和 Step→Skill 映射，而不是 route/decision dispatcher；
- Operation 执行明确业务操作；
- Validator 执行检查、分类或独立质量判定；
- Task Execution Agent 可以在一个长期执行对话中连续推进多个子环节；
- 每个当前 Step 只加载真正需要的 Skill、reference 和文件；
- Step 的复用和正式结果定义明确；
- 不重新引入 Workstream、route、event、runtime task/result、artifact state machine 或 transaction closure 作为普通任务依赖；
- 确定性 Tool 只承担确定性动作，不成为第五个科学决策层；
- 网页端多个编写窗口与真实运行对话完全分离。

# 启动前检查

Authoring / maintenance 开始时读取：

1. 项目根 `AGENTS.md`；
2. `00_authoring/AUTHORING_RULES.md`；
3. `00_authoring/lightweight_runtime_v2_spec.md`；
4. `00_authoring/SYNC_STATUS.md`；
5. `00_authoring/skill_inventory.yaml`；
6. `00_authoring/file_ownership.yaml`；
7. 目标 Skill 的 content map；
8. 与当前改动直接相关的上下游 Skill / draft / validation evidence。

仅在确实涉及相应内容时再读取：

- `references/layer_boundaries.md`：需要确认职责边界；
- `references/content_ownership_and_deduplication.md`：需要拆分或去重；
- `references/progressive_disclosure.md`：主 Skill 内容过长；
- `references/multi_window_authoring_protocol.md`：多窗口并行编写；
- `references/deterministic_tool_protocol.md` 与 `05_tools/tool_registry.yaml`：确实涉及共享 Tool；
- `03_contracts/**`、`runtime/**`、`runtime_subagent_protocol.md`、`runtime_record_commit_protocol.md`：只有 Legacy 维护、旧项目迁移或明确历史兼容审计时读取。

普通 Lightweight Skill 撰写不得把 Legacy contracts 作为默认启动依赖。

提出或实施修改前先列出：

```text
已做过
已否定
仍未验证
```

若新方案与已失败/已否定方案本质等价，且没有新证据改变前提，不重复实施。

# 步骤 1：确定职责层级

需要区分层级时读取：

`references/layer_boundaries.md`

至少明确：

```yaml
skill_name:
skill_layer: manager | workflow | operation | validator
primary_job:
nearest_neighbor_skills: []
responsibility_conflicts: []
deterministic_tool_candidates: []
```

一个 Skill 同时拥有多个层级的主职责时，应先拆分；但“逻辑职责拆分”不等于必须建立额外 Agent 对话。

Tool 不是 Skill 层级。Tool 只执行确定性程序，不能承担研究对象选择、科学判断、任务范围或用户意图解释。

# 步骤 2：确认 Lightweight Runtime 关系

默认真实运行关系：

```text
Manager
→ 写入 / 定位 Txxxx.md
→ 一次性交接给 Task Execution Agent
→ Task Execution Agent 从任务单确定当前 Step
→ 加载当前 Step 所需 Skill
→ 执行 / 验证 / 复用
→ 更新 Txxxx.md 与 project_result_index.md
→ 继续下一 Step
```

必须满足：

- Manager 与 Task Execution Agent 默认是不同对话；
- 普通子环节之间不回 Manager 调度；
- 不为 Task Execution Agent 单独再增加一层通用编排 Skill；
- Workflow 不返回 `workflow_route_fragment` 或 `workflow_decision`；
- Workflow 不维护 Workstream、active route、artifact state 或 event；
- 当前 Step 的用户确认由当前 Task Execution Agent 在执行对话中直接提出；
- Operation / Validator / Tool 本身不建立新的 Agent 层；
- 用户在执行对话中明确调整任务范围时，可直接修改 Task Sheet；
- 任务完成或用户明确终止时，Task Execution Agent 可同步更新 `task_index.md`。

# 步骤 3：冻结当前 Skill 的局部接口

在正文前先明确当前 Skill 真正拥有的内容。

## Manager

至少冻结：

```yaml
purpose:
task_location_rules:
new_task_boundary:
initial_planning_inputs:
task_sheet_write_rules:
project_level_management_rules:
minimal_reads: []
forbidden_default_reads: []
```

Manager 不拥有具体 Step 的科学输入、reuse conditions、validation requirements、official results 或适用性判断。

Manager planning index 只保存生成初始 Task Sheet 所需的 Workflow/Step 目录与顺序信息，不使用 `conditional` 或其他科学适用性标记。

## Workflow

至少冻结：

```yaml
purpose:
stage_goal:
ordered_substeps: []
step_to_skill_mapping: []
stage_scientific_relations: []
stage_completion_condition:
```

Workflow 可以描述阶段内科学依赖，以及“某个正式结果可能使后续 Step 被增加、删除、替换或重排”的关系；具体适用性判定仍归当前 Step Skill 与 Task Execution Agent。

Workflow 不建立 planning fragment、execution decision、route revision、Workstream state、runtime task unit，也不为 Manager 维护 `conditional step` 元数据。

## Step-facing Operation / Validator

任何直接承担某个 Workflow 子环节执行的 Skill，或一组配套 Operation + Validator，必须**合计**明确以下统一接口：

```text
1. purpose
2. object requirements
3. reuse conditions
4. execution rules
5. validation requirements
6. official results
```

单一 Skill 独立完成 Step 时，由该 Skill 全部定义。

Operation + 专属 Validator 配套时，必须在 content map 中明确唯一 owner，避免两份文件重复：

- Operation 通常拥有 `purpose / object requirements / reuse conditions / execution rules / official results`；
- Validator 通常拥有独立 `validation requirements` 和验证报告；
- 如实际职责不同，可调整 owner，但同一规则只能有一个权威位置。

Validator-only Step 则由 Validator 直接拥有完整 Step 接口。

# 步骤 4：设计复用规则

Reuse 发生在**子环节真正开始时**，不是任务创建时。

Step Skill 只定义真正决定本 Step 输出是否仍有效的少数条件，例如：

- 输入结构 SHA；
- selected model；
- retain selection；
- pH / protonation method；
- force field；
- residue definition / parameter source；
- 影响结果的人工科学决定。

统一判定：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足无法判断 → 当前 Task Execution Agent 询问用户
用户明确要求重做 / 对照 → 跳过自动复用
```

不得只因文件名相同、目录已有文件或任务名称相似就复用。

复用另一任务的结果时直接引用其正式结果，不为了“本任务完整”复制一份新的副本。

# 步骤 5：设计目录与 official results

每个 Step 使用两级目录：

```text
<base_work_directory>/
└── <task_id>/
```

例如：

```text
01_structure_preparation/02_component_and_residue_classification/
└── T001/
```

规则：

- `workflow_plan_index.yaml` 和 Workflow 只保存/描述 Step 基础目录；
- 项目初始化可以建立稳定 Step 基础目录；
- Manager 在 Task Sheet 中记录 `<base_work_directory>/<task_id>/` 预留路径；
- Manager 不创建 `Txxxx/` 任务执行目录；
- Task Execution Agent 进入当前 Step 后先做 reuse 检查；
- 只有确实需要本地执行时才创建当前任务目录；
- 直接复用已有结果时不创建空目录；
- 不同任务固定文件名输出必须隔离在各自 `<task_id>/` 下。

每个 Step Skill 必须区分：

```text
official results
vs
internal/intermediate/debug/recovery files
```

只有 `official results` 登记到 `project_result_index.md`。

正式结果描述必须足以让下游 Skill 直接定位和消费，而不需要重新读取上游全过程。

# 步骤 6：设计用户确认与未完成状态

普通科学歧义由当前 Task Execution Agent 在当前执行对话中确认，不返回 Manager 走 decision record。

Skill 应明确：

- 哪些情况可以自动判断；
- 哪些情况必须让用户选择；
- 确认前哪些写入禁止发生；
- 确认结果如何进入当前 Step 的正式/恢复材料。

Task Sheet 子环节状态只使用：

```text
待执行
未完成
已完成
```

依赖缺失、等待用户决定、可重试失败等都保持 `未完成`，必要原因写入简短执行记录；不要重新引入 BLOCKED / WAITING / FAILED 状态机作为 Task Sheet 状态。

# 步骤 7：识别 Tool 候选

满足以下任一条件时考虑共享 Tool：

- 同一确定性逻辑跨 Skill 重复；
- 脚本明显比 LLM 更快、更稳定；
- 需要可靠 parsing / hashing / transformation；
- 需要稳定原子写入或结构化校验；
- 需要可重复测试与 benchmark。

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

交由：

`00_authoring/md-workflow-tool-authoring/SKILL.md`

新 Tool 默认应接受明确业务输入和路径，不为了兼容旧 Runtime 强制要求 `task.yaml`、route、event、runtime receipt 或 transaction closure。

不要因为“可以写 Tool”就把简单的一次性管理动作工具化。此前已经验证：旧 Runtime 的主要延迟来自多层 LLM 编排，不来自几百毫秒级确定性脚本。

# 步骤 8：建立内容唯一归属

使用：

`assets/content_map.template.yaml`

详细规则：

`references/content_ownership_and_deduplication.md`

核心要求：

- 当前 `SKILL.md` 保存当前职责的执行/判定主线；
- 长科学规则和 registry 放 `references/`；
- 当前 Skill 独有的结构化文件约束放 `schemas/`；
- 当前 Skill 独有且不值得共享的程序放 `scripts/`；
- 跨 Skill 可复用程序放 `05_tools/`；
- Workflow 不复制 Step 科学细节；
- Step 不复制上游 Skill 的算法，只消费正式结果；
- Lightweight Runtime 规则引用 `00_authoring/lightweight_runtime_v2_spec.md`，不在各 Skill 重写整套运行时设计。

# 步骤 9：设计文件结构

按需创建：

```text
<skill-name>/
├── SKILL.md
├── references/
├── schemas/
├── scripts/
└── assets/
```

只创建实际需要的目录。

不因为旧架构历史自动创建：

```text
agents/
runtime projection
local copies of shared task/result schemas
```

如果某 Skill 需要专用辅助 Agent 元数据，必须有当前明确需求；不得把网页编写窗口或 Task Execution Agent 写成 Skill 内嵌子 Agent。

渐进披露规则见 `references/progressive_disclosure.md`。

# 步骤 10：编写

选择当前 Lightweight 模板：

- `assets/manager_skill.template.md`
- `assets/workflow_skill.template.md`
- `assets/operation_skill.template.md`
- `assets/validator_skill.template.md`

编写要求：

- 先写职责边界，再写流程；
- Step-facing Skill 明确六项统一接口；
- 明确任务专属工作目录语义；
- 明确 reuse 在本 Step 开始时检查；
- 明确 official results；
- 明确用户确认条件；
- 明确 Preflight，但不要把 Preflight 扩展成通用 runtime engine；
- 只在实际需要时读取 reference / schema；
- 复杂可复现操作保存真实脚本/config，而不是全局命令流水日志；
- 不复制共享运行架构；
- 不生成 route、Workstream、event、runtime task/result 或 transaction closure 的新依赖；
- 不预读未来 Step；
- 不以“全面了解”为理由扫描整个项目。

# 步骤 11：多窗口编写

仅在确实采用多个网页窗口并行 authoring 时读取：

`references/multi_window_authoring_protocol.md`

每个窗口必须有互斥 `write_paths`。

共享文件，例如：

```text
AGENTS.md
00_authoring/AUTHORING_RULES.md
00_authoring/lightweight_runtime_v2_spec.md
skill_inventory.yaml
file_ownership.yaml
共享 content maps
05_tools/tool_registry.yaml
```

仍由主窗口统一修改。

网页窗口不是运行时 Agent。

# 步骤 12：检查与评测

现有静态脚本可以继续用于 Markdown、重复内容、content map 等不依赖 Legacy Runtime 的检查，例如：

```bash
python 00_authoring/md-workflow-skill-authoring/scripts/validate_md_skill.py \
  <project-root> <skill-directory>

python 00_authoring/md-workflow-skill-authoring/scripts/detect_cross_file_duplication.py \
  <skill-directory>

python 00_authoring/md-workflow-skill-authoring/scripts/validate_content_maps.py \
  <project-root>
```

任何仍以 Workstream/route/subagent contract 为成功条件的旧检查，在迁移前只能作为 Legacy 检查，不能反过来否定已经冻结的 Lightweight 规则。

行为评测至少覆盖当前 Skill 实际适用的：

- 正向执行；
- 最近邻边界；
- 输入缺失；
- 用户确认；
- 复用成功；
- 明确不可复用；
- 无法判断复用等价性；
- 用户显式重做；
- task-scoped 工作目录隔离；
- 直接复用时不创建空任务目录；
- official results 登记；
- 跨对话恢复；
- 当前结果导致后续 Step 增删、替换或重排；
- Tool 不可用时的合理回退；
- 不写 Legacy runtime records。

Workflow 评测应重点检查阶段映射和科学关系，不再要求 route fragment / workflow decision fixtures，也不要求 conditional-step metadata。

# 交付

Authoring 对话返回：

```yaml
status: DRAFTED | REVIEW_REQUIRED | BLOCKED
skill_name:
owned_paths: []
created_files: []
modified_files: []
validation:
  errors: []
  warnings: []
duplication_findings: []
tool_requests: []
open_questions: []
next_action:
```

# 完成条件

- 层级和单一职责已确认；
- 当前 Skill 与 Lightweight Runtime v2 一致；
- Step-facing 接口六项内容完整且 owner 唯一；
- task-scoped 目录与 reuse-before-create 规则正确；
- official results 明确；
- 用户确认边界明确；
- 文件所有权无冲突；
- 主文件、reference、schema、scripts 无高风险重复；
- Tool 候选没有重新承担科学决策或 Runtime orchestration；
- 未重新引入普通 Workstream / route / event / runtime task-result / transaction 依赖；
- 静态检查和适用行为评测完成；
- 未把网页编写窗口、Workflow 或 Task Execution Agent误写成新的嵌套 Agent 层。
