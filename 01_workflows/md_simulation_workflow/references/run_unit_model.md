# MD Simulation Run Unit Model

## 1. 定义

`run unit` 是 `md_simulation_workflow` 中一个稳定的**科学模拟片段**。它描述该片段要模拟什么、从哪里开始、使用什么 MDP 方案、依赖哪些上游结果，以及需要达到什么技术完成条件。

一个 run unit 可以表示：

- 一次 energy minimization；
- 一个 NVT、NPT 或其他 equilibration segment；
- 一个 production segment；
- 用户明确设计的其他 GROMACS 模拟片段。

run unit 不是 Workstream，也不是一次具体提交。一个 Workstream 可以包含多个 run units；一个 run unit 可以有多个 execution attempts。

## 2. 三层对象

```text
protocol run unit
→ scientific segment identity

execution attempt
→ one concrete execution/submission of that run unit

run-level MD_OUTPUT
→ validated collection of all accepted attempts for that run unit
```

阶段出口再将多个 required run-level outputs 组装为唯一 stage-level MD_OUTPUT collection。

不得把这四类对象合并：

- run unit；
- execution attempt；
- run-level output；
- stage-level output。

## 3. Plan、route 与 run unit

```text
validated simulation protocol
→ immutable md_simulation_plan
→ Manager projects current Workstream route
→ run-unit and attempt task lifecycle
```

- protocol 是科学字段唯一 owner；
- plan 保存 protocol identity、run-unit task projection、依赖 gate、路径和修订谱系；
- route 由 Manager 持久化，描述本轮 task unit 路线；
- run unit 是 protocol 中的科学片段身份；
- execution attempt 是运行时对象；
- plan 和 route 均不直接授权 backend side effect。

## 4. 稳定身份

每个 run unit 必须有稳定且在当前 Workstream 中唯一的 `run_unit_id`。

推荐命名：

```text
em.1
eq.1
npt.1
md.1
md.2
```

命名只用于身份和目录定位，不推导 ensemble、参数、时长、backend、continuation 或完成阈值。

科学设置发生变化并需要新 `.tpr` 时，必须产生新的或明确 superseding 的 run unit identity；不得静默复用旧 run unit ID 覆盖旧输入和输出。

## 5. 科学角色

run unit role 只描述科学片段：

```text
ENERGY_MINIMIZATION
EQUILIBRATION
PRODUCTION
CUSTOM
```

`CONTINUATION` 不是科学 role。continuation 是 execution attempt 的 restart mode：

- production continuation 的 run unit role 仍是 `PRODUCTION`；
- equilibration continuation 的 role 仍是 `EQUILIBRATION`；
- energy-minimization retry 的 role 仍是 `ENERGY_MINIMIZATION`。

## 6. Run unit 最小语义

```yaml
run_unit_id:
role: ENERGY_MINIMIZATION | EQUILIBRATION | PRODUCTION | CUSTOM
depends_on: []
mdp_spec:
start_state:
completion_criteria:
expected_output_roles: []
```

run unit 不拥有：

- GROMACS executable 路径；
- host、tmux session 或 scheduler；
- MPI/OMP/GPU/内存/walltime；
- attempt ID；
- append/noappend；
- submission ID。

这些属于 execution attempt。

## 7. 起始状态

### 7.1 SYSTEM

第一个或独立 run unit 可以从 VALIDATED SYSTEM 开始。SYSTEM 来自 `md_preparation_workflow`，提供完整体系的结构、拓扑、盒子、溶剂和离子等内容。

`source_type: SYSTEM` 时不得同时声明 continuation checkpoint。

### 7.2 PRIOR_RUN_OUTPUT

下游 run unit 可以从明确上游 VALIDATED MD_OUTPUT 开始。必须：

- source run unit 存在；
- source run unit 位于依赖闭包；
- 坐标/结构来源唯一；
- 若新 `.tpr` 的预处理需要 checkpoint，则 checkpoint identity 必须显式指定；
- 不按时间戳选择“最新”文件。

该 start-state checkpoint 用于生成新 MD_INPUT，与 same-TPR execution continuation checkpoint 不得混淆。

## 8. 依赖规则

- `depends_on` 只引用同一有效 protocol/plan 中稳定 run unit IDs；
- 依赖图不得有环；
- 下游 input preparation 前，blocking dependencies 必须有 VALIDATED run-level MD_OUTPUT；
- 上游进程退出或 submission terminal 不等于依赖满足；
- 独立重复、统计重复或参数对照优先建立不同 Workstreams；
- 其他 Workstream 的后台任务不阻塞当前 Focus，除非显式依赖其 artifact。

## 9. Run unit 生命周期

```text
protocol defined
→ plan projected and validated
→ MDP materialized/validated when required
→ MD_INPUT prepared and validated
→ execution attempt specified and validated
→ one or more attempts executed/submitted
→ attempts terminal and independently evidenced
→ run output validation across accepted attempt chain
→ VALIDATED run-level MD_OUTPUT
```

具体 task、submission 和 artifact 状态继续使用共享 contracts。本 reference 不创建重复的共享状态枚举。

## 10. MDP 与 MD_INPUT

MDP source 可以是：

```text
FINAL_FILE
TEMPLATE_WITH_TYPED_OVERRIDES
```

- FINAL_FILE：使用带 hash 的最终 MDP；
- TEMPLATE_WITH_TYPED_OVERRIDES：根据带 hash 的模板与显式 typed overrides 生成业务 MDP；
- 不允许自由文本替换或隐式科学默认值。

`md_run_input_preparation` 负责在一个上下文连续 task 中：

- 物化/复制受控 MDP；
- 唯一解析 SYSTEM 或上游 run output；
- 运行一次 `grompp`；
- 生成 TPR、manifest 和证据；
- 不执行 `mdrun`。

`md_run_input_validator` 独立核验渲染后的 MDP、TPR、输入来源、grompp 命令和 warnings。

## 11. Execution attempt

每个 attempt 必须有稳定且在 run unit 内唯一的 `attempt_id`，例如：

```text
attempt.001
attempt.002
attempt.003
```

attempt 语义、目录、restart 和 mutation policy 见：

```text
execution_attempt_model.md
```

同一 `.tpr` 的 continuation 是新 attempt，不是新 role。

## 12. 目录模型

```text
04_md_simulation/<run_unit_id>/
├── input/
│   ├── run.mdp
│   ├── run.tpr
│   ├── md_run_input_manifest.yaml
│   └── md_run_input_validation_report.yaml
├── attempts/
│   ├── attempt.001/
│   ├── attempt.002/
│   └── ...
├── md_run_output_validation_report.yaml
└── md_run_output_manifest.yaml
```

每个 attempt 目录独立保存 execution spec、command、submission、status 和 engine outputs。不得将 retry/continuation 输出直接混入另一个 attempt 目录。

## 13. Continuation 与新 run unit

### 13.1 同一 run unit 的新 attempt

同时满足以下条件时，可以创建 continuation attempt：

- 使用相同且仍有效的 TPR；
- 使用明确且属于上一 accepted attempt chain 的 checkpoint；
- 目标是继续未完成的同一参数化片段；
- restart policy 已写入新的 execution-attempt spec；
- 不改变科学 protocol 或 completion target。

v1 默认只允许：

```text
CONTINUE_NOAPPEND
```

每次 continuation 写入新的 attempt directory，保留旧文件和 hashes。

### 13.2 必须产生新 run unit/MD_INPUT

以下情况不是 same-TPR continuation：

- 修改 `nsteps` 并生成新 TPR；
- 修改 MDP 参数；
- 改变温度、压力、约束、耦合或科学方案；
- 改变初始 SYSTEM/上游 MD_OUTPUT；
- 从不同 checkpoint 建立对照；
- 需要保留旧方案并比较新方案。

此时修订 protocol/plan，生成新的 run unit identity 和 MD_INPUT。

只有 SYSTEM 的结构、拓扑、盒子、溶剂或离子变化时才返回 `md_preparation_workflow`。

## 14. Run-level MD_OUTPUT

一个 run unit 的 validated output 是当前 accepted attempt chain 的集合，不等同于最后一个 attempt 的单一文件。

可能包括：

- 各 attempt 的 `.log`、`.edr`、`.trr/.xtc`；
- 最终结构和 checkpoint；
- execution-attempt specs、command/submission provenance；
- run output validation report；
- `md_run_output_manifest.yaml`。

run output Validator 必须核验 attempt chain、checkpoint continuity、step/time continuity 和 superseding/rejected attempts。

## 15. Stage-level MD_OUTPUT

Workflow exit 需要唯一 stage-level MD_OUTPUT collection。它引用当前范围内所有 required run-level MD_OUTPUT artifact sets，而不是只引用最后一个 production segment。

阶段 collection 至少记录：

- validated protocol/plan identity；
- included run units；
- included run-level artifact IDs；
- final structure/checkpoint selection；
- trajectory/energy segment ordering；
- excluded/superseded attempts；
- completion validation evidence。

## 16. 技术完成边界

输入、attempt 和 output Validators 可以核验：

- MDP/TPR 和 source provenance；
- attempt 是否按声明命令运行；
- 是否达到显式 step/time target；
- required outputs 是否可解析；
- attempt chain 和 checkpoint continuity；
- 注册的 role-specific checks。

它们不自动证明 equilibration 充分、production sampling 收敛或分析结论成立。