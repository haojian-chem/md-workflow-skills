# MD simulation 讨论决策记录

```yaml
status: DISCUSSION_BASELINE
branch: draft/md-simulation-skills
scope: 04_md_simulation
recorded_at: 2026-08-06
implementation_authorized: false
workflow_review_required: true
```

本文只保存当前已经明确的讨论结论，作为后续检查和重构 `md_simulation_workflow` 的基准。未明确事项不得由实现自行补全。

后续提出的完整工作流程均为讨论草案，只有在用户逐项确认后，才可以补入本文件。

## 1. 阶段职责

`04_md_simulation` 只负责当前 Workstream 中的 MD 模拟准备、执行和结果检查。

- 输入为当前 Workstream 已准备完成的 MD 体系文件。
- SYSTEM 在本阶段只读，不允许修改结构、拓扑、盒子、溶剂或离子。
- 若输入准备或检查发现 SYSTEM 存在问题，停止当前 Workflow，并向用户反馈。
- 用户要求改变体系时，属于另一条 Workstream，不是当前 `04_md_simulation` 的分支或回退路径。
- 不使用“返回 `md_preparation_workflow`”或类似反向跳转表述。

## 2. 阶段目录

实际项目目录固定为：

```text
04_md_simulation/
```

不为方案文件额外建立 `00_plan/` 等子目录。

## 3. run unit 类型

当前仅设置四类 run unit：

```text
EM
NVT
NPT
MD
```

实例通过编号区分，例如：

```text
em.1
nvt.1
npt.1
md.1
md.2
```

暂不设置 `EQUILIBRATION`、`PRODUCTION`、`CUSTOM` 或 `CONTINUATION` 类型。

## 4. run unit 边界

- 一个 run unit 拥有一个确定的 TPR。
- 新生成 TPR 时建立新的 run unit。
- 在原输出文件上 append 续跑，不建立新的 run unit。
- 使用 noappend 生成独立输出段时，建立新的 run unit。
- 失败后是否建立新 run unit，取决于是否保留失败任务：
  - 保留失败任务：建立新的 run unit；
  - 不保留失败任务：在原 run unit 中重新运行。

## 5. run unit 起点

不设置 `NEXT`、`CONTINUE_FROM`、`RETRY_OF`、`BRANCH_FROM` 等关系枚举。

每个 run unit 只记录：

```text
run_unit_id
run_unit_type
start_from_run_unit_id
```

- `start_from_run_unit_id` 可为空。
- 如存在前置 run unit，只记录其 ID。
- 具体使用前置 run unit 的 `.gro`、`.cpt` 或两者，由输入准备过程确定。

## 6. 新 run unit 的连续运行

从前一个 run unit 建立新 run unit 时，通常使用前一步的：

```text
.gro
.cpt
```

并使用当前 run unit 的 MDP 生成新的 TPR。

若动力学连续阶段需要 checkpoint，但前一步 `.cpt` 缺失，不得无依据地重新生成速度，应停止并反馈。

## 7. append 与原地重跑

以下情况仍属于原 run unit：

- 使用同一 TPR 和原输出前缀进行 append 续跑；
- 不保留失败任务时，在原 run unit 中重新执行。

执行命令、时间、tmux、失败原因、append 和重跑过程统一进入项目既有日志体系，不建立 `execution_records/`。

## 8. run unit 业务目录

各 run unit 目录只保存实际模拟文件，例如：

```text
04_md_simulation/md.1/
├── md.1.mdp
├── md.1.tpr
├── md.1.log
├── md.1.edr
├── md.1.xtc
├── md.1.gro
└── md.1.cpt
```

- 主要文件使用 run unit ID 作为前缀。
- 各 run unit 目录中不重复放置单独的 `run_unit.yaml`。
- 不建立 `execution_records/`。

## 9. 集中式 run unit 索引

集中式索引文件位于：

```text
04_md_simulation/run_unit.yaml
```

用于记录全部 run units 的：

```text
run_unit_id
run_unit_type
start_from_run_unit_id
```

示例：

```yaml
schema_version: 1
run_units:
  - run_unit_id: em.1
    run_unit_type: EM
    start_from_run_unit_id: null
  - run_unit_id: nvt.1
    run_unit_type: NVT
    start_from_run_unit_id: em.1
  - run_unit_id: npt.1
    run_unit_type: NPT
    start_from_run_unit_id: nvt.1
  - run_unit_id: md.1
    run_unit_type: MD
    start_from_run_unit_id: npt.1
```

## 10. 预计路线

预计路线单独记录在：

```text
04_md_simulation/expected_route.yaml
```

该文件只记录预计路线，不重复保存 run unit 的类型、起点、MDP 参数或状态。

示例：

```yaml
schema_version: 1
expected_route:
  - em.1
  - nvt.1
  - npt.1
  - md.1
```

预计路线不硬性锁定，可根据执行结果动态更新；调整原因进入项目日志。

## 11. MDP 生成

04 根据以下信息生成 MDP：

- 用户对模拟目的和参数的描述；
- 当前体系情况；
- 可用模板；
- 已有项目设置和明确上下文。

流程为：

```text
用户描述 + 体系情况 + 模板
→ 生成 MDP 草案
→ 汇总无法可靠确定的内容
→ 一次性向用户确认
→ 生成最终 MDP
```

- 不要求用户逐项提供所有参数。
- 可根据可靠依据确定的参数直接生成。
- 具有歧义或显著科学影响的内容集中确认。
- 最终实际参数以 `<run_unit_id>.mdp` 为准。
- 不在模拟方案或 run unit 索引中重复保存 MDP 参数、模板来源或确认内容。
- MDP 的生成、修改和用户确认过程进入项目日志。

## 12. 本地与外部执行

智能体只代为执行本地任务：

- 短任务可前台同步运行；
- 长任务必须建立 tmux 后运行。

对于外部计算环境：

- 04 只准备 MDP、TPR、必要输入和运行命令；
- 同步出去后由使用者自行提交；
- 不在 v1 中实现 LSF、SLURM、PBS 或远程 scheduler 提交和状态查询模型。

## 13. 输出与分析边界

- 当前未确认需要 `simulation_output_index`、stage-level MD_OUTPUT collection 或面向分析的输出索引。
- `04_md_simulation` 不负责选择分析对象，也不决定哪些 run units 用于具体分析。
- 是否需要阶段级输出汇总对象，必须在完整工作流程检查后重新判断，不能以“方便分析”为理由预设。

## 14. 暂缓决策

以下事项暂不确定，必须在工作流程复核后再讨论：

1. 是否同时保留 simulation protocol 和 simulation plan；
2. 状态体系及不同层级状态的定义；
3. EM、NVT、NPT、MD 各阶段的完成与验证标准；
4. 是否需要阶段级输出汇总对象；
5. Operation 与 Validator 的最终拆分；
6. 具体 Skill 数量和调用顺序。

## 15. 当前复核要求

在继续讨论其余细节前，必须先检查现有 `md_simulation_workflow`：

- 是否把当前阶段之外的职责写入 Workflow；
- 是否存在重复记录或重复对象；
- 是否过度拆分 Operation/Validator；
- 是否错误引入外部 scheduler、submission、attempt 或分析选择；
- 是否与本文件已经确认的目录、run unit、MDP 和执行规则冲突；
- 是否能形成一条简洁、可实际执行的主流程。

## 16. 暂时通过：本轮请求、预计路线与当前 run unit

本节只表示当前讨论暂时通过，仍属于完整 Workflow 草案的一部分；后续若与其他环节产生实质冲突，可以继续修订。

### 16.1 建立当前模拟上下文

根据本轮用户请求，按相关性读取：

- 当前 Workstream 信息；
- `04_md_simulation/run_unit.yaml`；
- 相关 run unit 目录中的实际文件；
- 必要的项目日志；
- 如有需要，将上一轮 `expected_route.yaml` 作为历史参考。

前两个 YAML 不能单独用于解释用户请求；必须结合实际文件、日志和 Workstream 上下文。

### 16.2 解释本轮请求

结合当前模拟上下文，确定本轮用户希望处理的范围。

用户描述不要求直接包含具体 `run_unit_id`。

- 能唯一解释时直接继续；
- 存在多个合理解释时，汇总候选解释后向用户确认；
- 记录、实际文件或日志之间存在冲突时，停止并报告，不自行猜测。

### 16.3 基于本轮请求生成预计路线

`04_md_simulation/expected_route.yaml` 基于本轮请求生成，只记录本轮当前预计涉及的 run units 及顺序。

它不是当前 Workstream 的长期总路线，也不需要包含此前完成但与本轮请求无关的 run units。

新一轮请求到来后，根据新请求重新生成或替换；本轮执行过程中允许根据实际结果动态调整、扩展或缩短。

### 16.4 根据当前预计路线确定当前需要处理的节点

先结合本轮请求、当前进展和 `expected_route.yaml`，确定当前首先需要处理的路线节点。

不在本轮开始时一次性锁定全部所需 run units。预计路线推进或发生调整后，需要重新判断当前节点及后续所需 run units。

### 16.5 按当前可确定范围引用或创建 run unit

针对当前节点以及当前已经能够明确定义的路线部分：

- 已存在且符合当前需求的 run unit：直接引用，不复制、不修改、不自动重新执行；
- 当前需要但尚不存在的 run unit：创建并加入 `run_unit.yaml`；
- 尚不能明确定义的后续 run unit：暂不创建；
- 需要不同类型、不同起点或新 TPR 时：创建新的 run unit，不修改已有确定 run unit。

`run_unit.yaml` 累积保存当前 Workstream 已定义的全部 run units。每次路线推进或调整时，可以继续追加新创建的 run units。

### 16.6 检查当前已落实范围的一致性

在当前已经落实为 run units 的路线范围内检查：

- `expected_route.yaml` 中当前已落实的 ID 存在于 `run_unit.yaml`；
- `run_unit_type` 只能为 `EM/NVT/NPT/MD`；
- 非空 `start_from_run_unit_id` 指向已存在的 run unit。

尚未能够明确定义的后续路线部分不应为了通过一致性检查而被强制提前创建为 run unit。

### 16.7 随路线推进循环更新

当前 run unit 完成检查后，重新评估本轮请求和预计路线：

```text
当前 run unit 处理结果
→ 判断 expected_route.yaml 是否仍适用
→ 必要时调整预计路线
→ 确定新的当前节点
→ 引用或创建该节点所需 run unit
→ 再次检查当前已落实范围的一致性
```

因此，run unit 的确定和创建是随路线推进反复执行的过程，不是本轮请求开始时的一次性步骤。

后续的 MDP 要求整理、用户确认、MDP/TPR 生成及执行流程尚未确认，不属于本节暂时通过的范围。
