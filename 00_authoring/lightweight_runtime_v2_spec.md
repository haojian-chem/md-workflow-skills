# Lightweight Runtime v2 Specification

## 1. 目标与设计原则

Lightweight Runtime v2 的目标，是让 MD Workflow Skills 的默认运行方式接近“具备可靠科研 SOP 的直接 Agent 工作模式”，而不是让 LLM 维护一套事务型工作流引擎。

### 1.1 科研 Skill 与运行时管理分离

保留 Workflow、Step/Operation、Validator、reference/SOP、实际执行脚本和确定性工具中真正用于科研判断、执行和验证的内容。

默认运行时不再依赖 route、transaction、event、artifact state machine、workstream state machine 等管理对象。

### 1.2 Task Sheet 是默认运行时核心状态载体

默认运行时只通过：

- `00_project_records/task_index.md`
- `00_project_records/project_result_index.md`
- `00_project_records/tasks/Txxxx.md`

维持跨对话任务状态、计划和结果定位。

不再为普通任务同步维护另一套等价 runtime state。

### 1.3 只读取当前动作真正需要的信息

Manager 只负责任务管理和初始规划。

Task Execution Agent 按当前子环节加载对应 Skill，并只读取当前动作明确需要的输入、结果和辅助资料。

不得为了“全面了解项目”默认扫描整个项目、全部历史记录、其他任务单或无关 Skill。

### 1.4 计划是动态工作计划，不是固定 route

任务计划直接保存在 Task Sheet 中。

Manager 创建初始计划；Task Execution Agent 根据科研结果或用户明确指令直接调整后续子环节。

不再维护独立 route object、route revision 或 route transaction。

---

## 2. 项目记录与目录体系

### 2.1 项目记录目录

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    ├── T001.md
    ├── T002.md
    └── ...
```

### 2.2 `task_index.md`

只承担任务导航。

每个任务只记录：

- Task ID；
- Task name；
- Task status；
- Task Sheet 完整路径。

任务级状态只允许：

```text
未完成
已完成
已终止
```

规则：

- 新任务创建时为 `未完成`；
- 当前计划全部完成后为 `已完成`；
- 仅当用户明确放弃任务时为 `已终止`；
- 排错、失败、等待、阻塞不增加新的任务级状态。

Manager 负责创建和定位任务；Task Execution Agent 在任务完成或用户明确终止时可以同步更新该索引。

### 2.3 Task Sheet：`tasks/Txxxx.md`

Task Sheet 是可动态维护的多环节工作计划与最小恢复上下文。

任务级固定内容：

- Task ID / title；
- Task status；
- Task goal；
- Plan and progress。

不单独维护：

- task-level input；
- start step；
- end step；
- task scope field；
- route；
- current node；
- current stage。

任务当前范围完全由 `计划与进度` 中实际列出的子环节定义。

每个子环节记录：

- `状态`；
- `对象`；
- `工作目录`；
- `主要结果`（完成后）；
- `执行记录`（仅必要时）。

`对象` 表示该子环节实际处理的具体对象，可以是一个结构文件、一个上游正式结果文件、一组明确文件或必要时一个目录；不要求项目级稳定 object ID。

子环节状态只允许：

```text
待执行
未完成
已完成
```

确认不需要执行且尚未实际执行的子环节，直接从任务单删除，不保留 `不适用` 状态。

已经实际执行过的子环节不得为了整理计划而静默删除；如结果被替换，保留必要执行记录。

### 2.4 工作目录两级模型

科研工作目录分为：

```text
Step 基础目录
→ 当前任务执行目录
```

例如 1.2：

```text
01_structure_preparation/02_component_and_residue_classification/
└── T001/
```

#### Step 基础目录

稳定基础目录可以在项目初始化时创建到这一层，例如：

```text
01_structure_preparation/
├── 01_source_recognition/
├── 02_component_and_residue_classification/
├── 03_chain_and_component_selection/
└── ...
```

项目初始化到 Step 基础目录即停止。

#### Task 执行目录

不同任务的实际执行目录固定为：

```text
<base_work_directory>/<task_id>/
```

例如：

```text
01_structure_preparation/02_component_and_residue_classification/T001/
01_structure_preparation/02_component_and_residue_classification/T005/
```

Manager 在 Task Sheet 中记录该预留路径，但**不创建 `Txxxx/` 任务执行目录**。

Task Execution Agent 在真正进入该子环节时：

1. 先做 reuse 检查；
2. 若可以直接复用已有正式结果，不创建当前任务空目录；
3. 若确实需要本地执行，才创建当前 `<base_work_directory>/<task_id>/`；
4. 当前执行不得顺带创建其他任务或未来子环节的 task 目录。

该规则用于：

- 隔离不同任务的固定文件名输出；
- 防止 T005 覆盖 T001 的正式结果；
- 避免 Manager 为尚未执行或最终被复用的步骤提前创建大量空目录。

### 2.5 Task Sheet 的动态维护

Manager 创建初始子环节计划。

Task Execution Agent 可以根据当前结果：

- 更新当前子环节状态；
- 更新对象、工作目录和主要结果；
- 增加完成当前任务所必需的后续子环节；
- 删除确认不需要的尚未执行后续子环节；
- 调整后续子环节顺序；
- 写入必要执行记录。

用户在 Task Execution Agent 对话中明确改变任务计划时，可以直接修改 Task Sheet，不需要返回 Manager。

### 2.6 `project_result_index.md`

`project_result_index.md` 是跨任务、跨对话的正式结果检索索引。

它不是项目 summary、artifact registry、运行日志，也不保存当前任务或当前环节状态。

一级按 Workflow 子环节组织：

```text
环节
  → 具体结果描述
      → 完整结果文件路径
      → 来源任务
```

结果描述用于区分不同输入、选择或处理条件，不要求稳定对象层或 version registry。

如果两个结果在影响该环节输出的条件上完全等价，正常情况下应在执行前触发复用；真正产生多个结果时，通过实际差异描述区分，而不是人为增加版本号。

### 2.7 什么进入结果索引

一个子环节完成后，只登记当前 Step Skill 明确定义的 `official results`。

不登记：

- 临时文件；
- debug 输出；
- scratch；
- cache；
- 普通中间文件；
- 与正式交付无关的过程文件。

### 2.8 执行记录不是流水日志

Task Sheet 的 `执行记录` 只保存对恢复、判断和继续执行有意义的关键事件，例如：

- 用户关键决定；
- 关键科学或技术判断；
- 异常及处理结果；
- 当前未完成原因；
- 复用来源；
- 为什么增加、删除或调整后续子环节；
- 为什么结果被重新生成或替换。

不记录普通文件读取、Skill 加载、`ls/cat/grep`、临时文件操作等流水信息。

默认不建立独立 `workflow_log.md` 或 `commands.log`。

需要复现的复杂命令优先保存为实际脚本、配置或软件输入文件。

---

## 3. Manager 职责

Manager 与 Task Execution Agent 默认处于不同对话，应尽量减少二者往返。

Manager 的核心职责只保留：

1. 任务定位；
2. 新任务创建；
3. 初始规划；
4. 项目级任务管理；
5. 必要时显式重新规划。

### 3.1 任务定位

Manager 默认先读：

`00_project_records/task_index.md`

定位规则：

- 用户指定 Task ID：直接定位；
- 用户指定可唯一匹配的任务名称：从索引定位；
- 当前 Manager 对话已明确任务：继续该任务；
- 无法唯一确定：询问用户；
- 不为了猜测当前任务遍历所有 Task Sheet。

确定任务后才读取对应 `Txxxx.md`。

### 3.2 新任务创建边界

检查、解释、排错、重新查看结果、继续已有环节等默认属于已有任务，不创建新任务。

只有：

- 用户提出新的独立工作目标；
- 用户显式要求另建任务；

才创建新 Task Sheet。

### 3.3 初始规划

Manager 根据用户目标和 `workflow_plan_index.yaml` 直接生成 Task Sheet 中需要列出的子环节。

Manager 不需要：

- 建立 start/end runtime object；
- 生成独立 route；
- 预先查询全部复用结果；
- 读取所有子环节 Skill；
- 提前运行科学检查。

Manager 为每个子环节记录：

```text
<project_root>/<base_work_directory>/<task_id>/
```

作为未来执行目录，但不创建该目录。

### 3.4 Manager 与 Task Execution Agent 的交接

```text
Manager 对话
→ 创建 / 定位任务
→ 初始规划
→ 写好 Txxxx.md
→ 一次性交接

Task Execution Agent 对话
→ 连续执行多个子环节
→ 持续维护 Txxxx.md
→ 持续维护 project_result_index.md
```

普通子环节之间不回 Manager 调度。

### 3.5 后续计划变化

用户在 Task Execution Agent 对话中明确改变任务计划时，Task Execution Agent 可以直接修改 Task Sheet，并在需要时读取 planning index 补充对应子环节。

Task Execution Agent 也可以依据科研结果对后续计划做必要局部增删和排序调整。

---

## 4. Manager Planning Index

规划索引位于：

`00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

它只用于轻量初始规划，不是 Workflow Skill 摘要，也不是 route 配置。

### 4.1 允许保存的信息

每个 Workflow / Step 只保存规划需要的信息：

- Workflow ID / name；
- Workflow directory；
- Step ID；
- Step name；
- `base_work_directory`；
- Step order；
- 是否 conditional；
- 必要时的轻量 planning alias。

统一目录规则：

```text
base_work_directory + task_id
→ Task Sheet 预留工作目录
```

planning index 可以声明目录创建责任，但不创建任务专属科研目录。

### 4.2 禁止进入 planning index 的内容

不得写入：

- 科学判断规则；
- 输入要求；
- 输出 schema；
- reuse conditions；
- preflight；
- validator 规则；
- 软件依赖；
- 执行命令；
- 错误恢复；
- 用户确认条件；
- artifact lineage；
- subagent prompt；
- 完整 Workflow / Operation 内容。

---

## 5. Task Execution Agent 与 Step Skill 统一接口

Task Execution Agent 是长期持有并推进一个 Task Sheet 的执行对话，不要求每个 1.x/2.x 子环节启动新的独立 Agent。

### 5.1 每个 Step Skill 必须明确

1. `purpose`
2. `object requirements`
3. `reuse conditions`
4. `execution rules`
5. `validation requirements`
6. `official results`

这些内容只描述当前科研子环节，不包含 transaction、route、event、artifact state 等管理逻辑。

### 5.2 子环节统一执行顺序

```text
读取当前 Txxxx.md
  ↓
确定当前子环节及对象
  ↓
读取当前 Step Skill
  ↓
在 project_result_index.md 中检索该 Step 历史正式结果
  ↓
按 reuse conditions 判断
  ├─ 明确等价：自动复用
  ├─ 明确不等价：正常执行
  └─ 无法判断：询问用户
  ↓
若需要本地执行：创建当前任务专属工作目录
  ↓
执行当前子环节
  ↓
按当前 Skill 要求验证
  ↓
更新 Txxxx.md
  ↓
登记 official results
  ↓
根据结果调整后续子环节
```

`project_result_index.md` 本身没有“当前环节”字段；当前执行到哪里只由 Task Sheet 决定。

### 5.3 用户显式要求重做

如果用户明确要求重新分析、重新检查、重跑或生成新的对照结果，则跳过自动复用。

### 5.4 Operation / Validator

Operation 和 Validator 继续作为科研能力模块保留，但不再是 Runtime 强制穿过的固定层级。

Step Skill 可以直接指导执行，或按需要调用 Operation / Validator。

### 5.5 最低回写要求

Task Execution Agent 只需要：

1. 更新当前 Task Sheet；
2. 如产生正式结果，更新 `project_result_index.md`；
3. 如当前结果影响计划，直接修改后续子环节。

不再生成普通 runtime task/result/event/artifact/route closure 对象。

---

## 6. 结果登记与复用

### 6.1 复用发生在子环节开始时

不在 Task Sheet 创建时冻结复用判断。

因为创建任务时不存在的结果，推进到该环节时可能已经由其他任务完成；上游结果也可能改变后续步骤的必要性。

### 6.2 Reuse conditions 由当前 Step Skill 定义

每个 Step Skill 只声明真正决定其输出是否仍有效的条件，例如：

- 相同输入结构；
- 相同 retain selection；
- 相同 pH；
- 相同 protonation method；
- 相同 force field；
- 相同 residue definition / parameter source。

不同 Step 的 reuse conditions 不由 Manager 统一推断。

### 6.3 复用判定

- 明确等价：自动复用；
- 明确不等价：正常执行；
- 信息不足：询问用户；
- 用户明确要求重做：不复用。

复用后在当前 Task Sheet 中记录来源结果路径和必要 provenance。

直接复用时，不复制结果到当前任务目录，也不创建无意义空目录。

---

## 7. 最小读取与运行规则

### 7.1 Manager

Manager 默认只读：

```text
task_index.md
目标 Txxxx.md
```

只有创建或显式重新规划时再读 planning index。

默认不得为了解项目情况读取：

- `project_result_index.md`；
- 其他 Task Sheet；
- 具体 Step Skill；
- Operation / Validator；
- Legacy runtime records；
- 整个项目目录。

### 7.2 Task Execution Agent

正常读取路径：

```text
Txxxx.md
→ current Step Skill
→ project_result_index.md 中该 Step 的历史结果条目
→ 必要的候选正式结果
→ 当前对象
→ 当前 Step 明确需要的其他输入
```

### 7.3 禁止预读未来 Step

真正准备进入某个子环节时才读取其 Skill。

### 7.4 禁止默认扫描整个项目

对象优先来自 Task Sheet；进一步输入来自当前 Step Skill 和正式结果索引。

只有信息确实不足时，才进行有明确目标的局部查找。

### 7.5 Operation / Validator / Reference 按需加载

```text
Task Sheet
→ Step Skill
    → 真正需要时再读 Operation
    → 真正需要时再读 Validator
    → 真正需要时再读 Reference
```

### 7.6 跨环节通过正式结果传递

当前 Step 需要上游内容时，优先读取上游正式结果文件，而不是重新加载上游 Skill 或扫描上游全过程。

### 7.7 额外读取必须有明确原因

允许原因包括：

- 当前 Step Skill 明确要求；
- reuse conditions 需要核验；
- 当前对象引用；
- Validator 需要；
- 用户明确要求；
- 当前错误排查需要。

不得仅以“可能有用”“为了保险”“先全面了解”为理由扩大读取。

---

## 8. Legacy Runtime

### 8.1 冻结范围

以下机制不再作为默认运行时继续扩展：

- `project_state`；
- `workstream_state`；
- route / route revision；
- runtime task / result；
- project events；
- artifact state；
- runtime projection；
- runtime task builder；
- runtime record committer；
- route fast-path evaluator；
- runtime project initializer；
- 围绕上述对象建立的 transaction closure、schema 和 runtime eval。

### 8.2 Lightweight Runtime 禁止依赖 Legacy Runtime

新的 Manager、Task Execution Agent 和 Step Skill 不得要求普通任务先构造或维护 Legacy runtime objects。

默认执行链只依赖：

- `task_index.md`；
- 当前 `Txxxx.md`；
- `project_result_index.md`；
- 当前 Step Skill；
- 实际科研输入/输出；
- 当前 Step 真正需要的 Operation / Validator / Tool。

不得建立 Lightweight records 到 Legacy runtime 的兼容包装层。

### 8.3 新项目

新项目建立 Lightweight records，并可创建已定义的稳定 Workflow / Step 基础目录。

不生成 Legacy project state、Workstream、route、event、runtime task/result，也不预创建任何 `<base_work_directory>/<task_id>/` 科研目录。

### 8.4 旧项目接管

已有旧项目不做一比一自动迁移。

只恢复当前继续工作真正需要的信息，例如：

- 已有任务目标；
- 已完成主要子环节；
- 当前仍需处理的子环节；
- 已有正式结果路径；
- 必要关键用户决定。

随后建立 Lightweight records 并继续维护。

### 8.5 Legacy records 读取边界

仅在旧项目首次接管、当前记录缺失关键历史、用户明确要求、恢复或排错确有需要时按需读取。

即使如此，也不扫描整套 Legacy records。

### 8.6 第一阶段不删除 Legacy 工具

至少验证以下场景后再决定删除还是归档：

- 新项目初始化；
- 新任务创建；
- 多子环节连续执行；
- 结果复用；
- 中途增删计划；
- 跨对话恢复；
- 跨 Workflow 任务；
- 旧项目接管。

### 8.7 Scientific Skills 不属于 Legacy

继续保留并重构：

- Workflow scientific rules；
- Step / Operation Skill；
- Validator；
- reference / SOP；
- 实际有用的 deterministic tools；
- 软件调用脚本；
- 输入输出规范；
- reuse conditions。

工具应回归“完成科学动作并返回结果”的角色，而不是为 runtime receipt、event commit、route evaluation 等管理闭环服务。

---

## 9. 重构验收原则

Lightweight Runtime v2 的目标不是降低科研严谨性，而是减少 LLM 在管理层的重复读取、状态维护和多轮调度。

默认普通任务应满足：

- 一个 Manager 对话完成任务定位 / 创建和初始规划；
- 一个 Task Execution Agent 对话可以连续推进多个子环节；
- 当前子环节只加载当前真正需要的 Skill 和文件；
- 复用检查发生在子环节开始时；
- 不为普通科研动作维护事务型 runtime closure；
- 简单判断和简单工具调用不产生分钟级管理开销；
- 不同任务的固定文件名结果通过 `<base_work_directory>/<task_id>/` 隔离；
- 可复用结果直接引用来源任务，不生成副本或空目录。

后续 Manager、Workflow、Step/Operation、Validator 和 1.1/1.2/1.3 的重构均以本文件为运行时架构依据。
