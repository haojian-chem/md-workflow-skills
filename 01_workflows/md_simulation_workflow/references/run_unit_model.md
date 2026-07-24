# MD Simulation Run Unit Model

## 1. 定义

`run unit` 是 `md_simulation_workflow` 中最小的可准备输入、可执行、可提交、可追踪和可独立验证模拟对象。

一个 run unit 可以表示：

- 一次 energy minimization；
- 一个 NVT、NPT 或其他 equilibration segment；
- 一个 production segment；
- 使用明确 checkpoint 的 continuation；
- 用户定义的其他 GROMACS `mdrun` 片段。

run unit 是阶段内对象，不是 Workstream。一个 Workstream 可以按依赖顺序包含多个 run units。

## 2. Plan、route 与 run unit

```text
simulation protocol spec
→ immutable md_simulation_plan
→ Manager projects current Workstream route
→ run unit task lifecycle
```

- plan 由 `md_simulation_workflow` 局部拥有，描述科学运行方案；
- route 由 Manager 持久化，描述本轮预计 task 路径；
- run unit 是 plan 中的执行对象；
- plan 不是硬编码队列，变化时生成新版本并触发 route revision；
- plan 不直接授权执行。

详细归属见：

```text
simulation_plan_ownership.md
```

## 3. 稳定身份

每个 run unit 必须有稳定且在当前 Workstream/plan 内唯一的 `run_unit_id`。

推荐命名：

```text
em.1
nvt.1
npt.1
md.1
md.2
```

命名只用于身份和目录定位，不推导 ensemble、MDP 参数、时长、资源、continuation 策略或完成阈值。

## 4. 最小描述

每个 run unit 至少描述：

```yaml
run_unit_id:
role: ENERGY_MINIMIZATION | EQUILIBRATION | PRODUCTION | CONTINUATION | CUSTOM
sequence:
depends_on: []
work_directory:
mdp:
start_state:
grompp:
execution_policy:
expected_outputs: []
completion_criteria:
input_preparation_status: NOT_PREPARED | CANDIDATE_AVAILABLE | VALIDATED
```

权威局部结构见：

```text
../schemas/md_simulation_protocol_spec.schema.yaml
../schemas/md_simulation_plan.schema.yaml
```

## 5. 起始状态

### SYSTEM

第一个或独立 run unit 可以从 VALIDATED SYSTEM 开始。SYSTEM 来自 `md_preparation_workflow`，提供完整体系的结构、拓扑、盒子、溶剂和离子等内容。

### PRIOR_RUN_OUTPUT

下游 run unit 可以从明确的上游 VALIDATED MDOUTPUT 开始。必须：

- `source_run_unit_id` 存在；
- source run unit 位于依赖闭包；
- 所需坐标/checkpoint 有稳定 identity；
- 不按时间戳自动选择“最新”文件。

## 6. 依赖规则

- `depends_on` 只引用同一 plan 中稳定 run unit IDs；
- 依赖图不得有环；
- 当前 run unit 的 blocking dependencies 必须通过输出验证后才允许 input preparation/execution；
- 仅有上游进程退出或 submission 结束不能满足依赖；
- 独立重复或参数对照优先建立不同 Workstream；
- 其他 Workstream 的后台 submission 不阻塞当前 Focus，除非显式依赖其 artifact。

## 7. 每个 run unit 的局部生命周期

```text
planned
→ input_preparation
→ input_validation
→ VALIDATED MD_INPUT
→ execute_or_submit
→ submitted_or_process_finished
→ running_or_finished_unverified
→ output_validation
→ VALIDATED MD_OUTPUT | failed | cancelled | unresolved
```

具体 task、submission 和 artifact 状态使用共享 contracts。本 reference 不创建新的共享状态枚举。

## 8. 五类阶段任务

### 8.1 Plan materialization/validation

在 run unit 任务前，`md_simulation_plan_materialization` 与 `md_simulation_plan_validator` 建立并验证当前 plan。

### 8.2 Input preparation

`md_run_input_preparation` 负责：

- 读取 validated plan 和目标 run unit；
- 从 VALIDATED SYSTEM 或上游 VALIDATED MDOUTPUT 唯一解析输入；
- 使用明确 MDP 运行 `grompp`；
- 生成 `.tpr`、manifest 和 command evidence；
- 不修改科学参数，不执行 `mdrun`。

### 8.3 Input validation

`md_run_input_validator` 负责：

- 解析 `.tpr`；
- 核验 MDP、coordinates、topology、checkpoint 和 plan provenance；
- 核验 grompp argv/version/maxwarn/warnings；
- 建议是否接受 MDINPUT candidate；
- 不修改输入或重跑 grompp。

### 8.4 Execution

`md_run_execution` 负责：

- 核验 immutable execution spec；
- 只使用 VALIDATED MDINPUT；
- 同步执行或异步提交；
- 记录命令和提交证据；
- 不判断输出是否通过。

### 8.5 Status/output validation

`md_run_status_validator` 按需查询 backend，不高频轮询；`md_run_output_validator` 核验运行输出并生成 MDOUTPUT candidate。

## 9. 同步与异步运行

### 同步

适用于明确允许在前台完成的短任务。进程结束后仍必须执行 output validation。

### 异步

适用于 tmux、LSF、SLURM、PBS 或其他长任务 backend。

```text
submission accepted
→ Manager records submission
→ Workflow PAUSE
→ on-demand status check
→ FINISHED_UNVERIFIED
→ output validation
```

异步 submission 可以在其他 Workstream 获得 Focus 时继续运行。

## 10. Continuation 与新输入

以下情况可以视为同一 run unit 的新 execution attempt：

- 使用相同且仍有效的 `.tpr`；
- 使用明确且经过身份核验的 checkpoint；
- continuation command 和 append policy 已写入新的 execution spec；
- 目标是继续未完成的同一参数化运行。

以下情况必须修订 plan 或重新生成 MDINPUT：

- 修改 `nsteps` 需要新 `.tpr`；
- 修改 `.mdp` 参数；
- 改变温度、压力、约束、耦合或科学方案；
- 改变 start-state artifact/checkpoint；
- 从不同 checkpoint 建立对照；
- 需要保留旧结果并比较新方案。

只有 SYSTEM 的结构、拓扑、盒子、溶剂或离子变化时才返回 `md_preparation_workflow`。

## 11. MDINPUT 范围

validated MDINPUT 至少包含：

- `.tpr`；
- MDP identity/受控副本；
- coordinates/topology/include/checkpoint provenance；
- grompp command/version/warning evidence；
- run input manifest；
- input validation report。

文件存在本身不是验证证据。

## 12. MDOUTPUT 范围

一个 run unit 的 validated MDOUTPUT 至少包含 execution spec 声明为 required 的文件及 output validation report。

可能包括 `.log`、`.edr`、`.trr/.xtc`、`.gro`、`.cpt` 和其他显式 engine 输出。

## 13. 技术完成与科学结论

input/output Validator 可以核验：

- `.tpr` 和输入 provenance；
- 进程是否正常结束；
- 是否达到显式 step/time 目标；
- required outputs 是否存在并可解析；
- checkpoint、轨迹和能量文件是否与当前 run unit 一致；
- plan/execution spec 明确的 role-specific checks。

它们不自动证明：

- MDP 科学设置最佳；
- equilibration 充分；
- production sampling 收敛；
- 分析结论成立。

这些结论需要明确 gate、专门分析或后续 `analysis_workflow`。