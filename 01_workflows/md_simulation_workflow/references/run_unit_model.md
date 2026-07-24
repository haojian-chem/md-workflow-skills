# MD Simulation Run Unit Model

## 1. 定义

`run unit` 是 `md_simulation_workflow` 中最小的可执行、可提交、可追踪和可独立验证模拟对象。

一个 run unit 可以表示：

- 一次 energy minimization；
- 一个 NVT、NPT 或其他 equilibration segment；
- 一个 production segment；
- 使用明确 checkpoint 的 continuation；
- 用户定义的其他 GROMACS `mdrun` 片段。

run unit 是阶段内执行对象，不是 Workstream。一个 Workstream 可以按依赖顺序包含多个 run units。

## 2. 稳定身份

每个 run unit 必须有稳定且在当前 Workstream 内唯一的 `run_unit_id`。

推荐命名：

```text
em.1
nvt.1
npt.1
md.1
md.2
```

命名只用于身份和目录定位，不推导：

- ensemble；
- `.mdp` 参数；
- 时长；
- 资源；
- continuation 策略；
- 完成阈值。

## 3. 最小描述

每个 run unit 至少描述：

```yaml
run_unit_id:
role: ENERGY_MINIMIZATION | EQUILIBRATION | PRODUCTION | CONTINUATION | CUSTOM
sequence:
depends_on: []
work_directory:
md_input_artifact_set_ids: []
execution_spec_path:
expected_outputs: []
completion_criteria: []
```

该结构是领域语义示意，不替代共享 runtime contracts 或 Operation 本地 schema。

## 4. 依赖规则

- `depends_on` 只引用同一 Workstream 中稳定 run unit IDs；
- 依赖图不得有环；
- 默认只有当前 run unit 的全部 blocking dependencies 通过输出验证后，才允许执行下游 run unit；
- 仅有上游进程退出或 submission 结束不能满足依赖；
- 独立重复或参数对照优先建立不同 Workstream；
- 其他 Workstream 的后台 submission 不阻塞当前 Focus，除非当前 run unit 显式依赖其 artifact。

## 5. 每个 run unit 的局部生命周期

```text
planned
→ execute_or_submit
→ submitted_or_process_finished
→ running_or_finished_unverified
→ output_validation
→ validated_output | failed | cancelled | unresolved
```

具体 task、submission 和 artifact 状态分别使用：

- `03_contracts/subagent_task.schema.yaml`；
- `03_contracts/subagent_result.schema.yaml`；
- `03_contracts/submission_record.schema.yaml`；
- `03_contracts/artifact_set.schema.yaml`。

本 reference 不创建新的共享状态枚举。

## 6. 三类任务

### 6.1 Execution

`md_run_execution` 负责：

- 核验 immutable execution spec；
- 同步执行或异步提交；
- 记录命令和提交证据；
- 不判断 MD 输出是否通过。

### 6.2 Status check

`md_run_status_validator` 负责：

- 按需查询 backend；
- 识别任务仍在运行、已结束、失败、取消或状态未知；
- 不高频轮询；
- 不把任务结束直接判定为输出通过。

### 6.3 Output validation

`md_run_output_validator` 负责：

- 核验输入 provenance；
- 核验声明的输出、终止状态和完成标准；
- 生成 MD_OUTPUT artifact candidate；
- 不修改输出或输入。

## 7. 同步与异步运行

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

## 8. Continuation

以下情况可以视为同一 run unit 的 continuation：

- 使用相同且仍有效的 `.tpr`；
- 使用明确且经过身份核验的 checkpoint；
- continuation command 和 append policy 已写入 execution spec；
- 目标是继续未完成的同一参数化运行，而不是改变模拟方案。

以下情况必须创建新 MD_INPUT 和新 run unit：

- 修改 `nsteps` 需要新 `.tpr`；
- 修改 `.mdp` 参数；
- 改变温度、压力、约束、耦合或科学方案；
- 从不同 checkpoint 建立对照；
- 需要保留旧结果并比较新方案。

## 9. 输出范围

一个 run unit 的 validated MD_OUTPUT 至少包含 execution spec 声明为 required 的文件及 output validation report。

可能包括：

- `.log`；
- `.edr`；
- `.trr` 或 `.xtc`；
- `.gro`；
- `.cpt`；
- 其他显式要求的 engine 输出。

文件扩展名或存在性本身不是验证通过证据。

## 10. 技术完成与科学结论

run unit output validation 可以核验：

- 进程是否正常结束；
- 是否达到显式 step/time 目标；
- required outputs 是否存在并可解析；
- checkpoint、轨迹和能量文件是否与本 run unit 一致；
- execution spec 中明确的 role-specific acceptance checks。

它不自动证明：

- equilibration 已充分；
- production sampling 已收敛；
- 体系具有科学合理性；
- 分析结论成立。

这些结论需要明确的阶段 gate、专门分析或后续 `analysis_workflow`。