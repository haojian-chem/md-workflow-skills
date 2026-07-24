---
name: md_run_output_validator
description: 核验一个已经结束的 GROMACS run unit 是否与其 execution spec、MD_INPUT、command 和 submission provenance 一致，检查声明的 required outputs、正常终止、目标步数/时间、checkpoint 和显式 role-specific acceptance checks，并生成 MD_OUTPUT artifact candidate。该 Validator 不修改输出、不补跑模拟，也不把技术完成夸大为科学收敛。
---

# 目标

验证一个 `FINISHED_UNVERIFIED` 或同步结束的 run unit：

- 输入和命令 provenance 可追溯；
- required outputs 完整且可解析；
- GROMACS 运行达到显式完成标准；
- continuation 链与 checkpoint 身份一致；
- execution spec 中明确的 blocking acceptance checks 通过；
- 输出可以作为当前 run unit 的 MD_OUTPUT artifact candidate。

# 职责边界

负责：

- 读取 execution spec、MD_INPUT、command record、submission evidence 和 engine outputs；
- 独立核验输入 hashes 和工作目录；
- 解析 GROMACS log、energy、trajectory、structure 和 checkpoint 的必要元数据；
- 核验正常终止、target steps/time 和 required outputs；
- 执行 spec 中明确的 role-specific checks；
- 核验 continuation/append provenance；
- 写详细 output validation report；
- 返回 Validation component result 和 MD_OUTPUT artifact candidate。

不负责：

- 修改、截断、拼接、修复或重命名 engine outputs；
- 继续或重跑模拟；
- 重新生成 `.tpr`；
- 自行定义 EM force、温度、压力、密度或其他科学阈值；
- 在 spec 未要求时将波动、漂移或采样充分性设为 hard gate；
- 执行完整科学分析；
- 修改 submission record 或 artifact records；
- 选择下一 run unit；
- 写管理目录；
- 创建子 Agent 或直接向用户提问。

# 输入

必须接收 `subagent_task.schema.yaml` v2 的 `VALIDATOR` task unit：

```text
operation: null
validator: md_run_output_validator
```

任务必须提供：

- 一个 `md_run_execution_spec.yaml`；
- 对应 VALIDATED MD_INPUT file records；
- execution Operation report；
- command record；
- submission evidence 和最新 submission record，如为异步运行；
- 当前 run unit 的 engine outputs；
- allowed read/write 和 forbidden paths；
- output validation report/result data 路径。

异步运行必须已有：

```text
submission status: FINISHED_UNVERIFIED
```

同步运行必须有可信 process terminal evidence。

# Preflight

确认：

1. task、Workstream 和 run unit IDs 一致；
2. Validator 引用的 execution spec 与 Operation 使用版本一致；
3. `.tpr`、checkpoint 和其他 MD_INPUT hashes 未改变；
4. command record 与 execution spec 可一致重建；
5. 异步 submission 已 terminal 且不再写输出；
6. 不存在同一 run unit 的活动进程；
7. engine outputs 位于授权 run unit 目录；
8. 所有目标文件不是 symlink 到未授权路径；
9. Validator 输出路径位于 allowed write paths；
10. 管理目录位于 forbidden paths。

活动进程仍存在时返回 BLOCKED，不读取可能持续变化的输出并宣布通过。

# 核验规则

## 1. Provenance

核验：

- execution spec hash；
- `.tpr` identity；
- checkpoint identity，如适用；
- command argv；
- GROMACS executable/version；
- work directory 和 `deffnm`；
- submission/PID/session/job identity；
- restart 和 append policy。

任何无法解释的输入或命令变化都阻止通过。

## 2. Required outputs

以 execution spec `expected_outputs` 为唯一 required/optional 来源。

对 required outputs 核验：

- 文件存在且为常规文件；
- 非空，除非格式允许空文件且 spec 明确；
- 可由适用 parser/engine 工具读取；
- 属于当前 run unit，而非旧 task 遗留；
- hash、size 和必要元数据已记录。

不得仅根据扩展名或修改时间判断归属。

## 3. GROMACS termination

当 `require_normal_termination: true` 时，必须核验正常终止证据。

同时检查：

- fatal error；
- segmentation fault；
- scheduler kill/resource termination；
- nonzero process exit；
- log 截断或不一致。

正常终止 marker 与明确 failure evidence 冲突时，不得通过。

## 4. Step 和 time

若 spec 提供 `target_nsteps` 或 `target_time_ps`：

- 从实际输出元数据独立读取最终 step/time；
- 使用格式精度允许的明确容差；
- 不用文件名或 command 中的期望值代替实际结果；
- 未达到 blocking 目标时返回不通过。

未提供目标值时，不得猜测预期时长。

## 5. Checkpoint

当 `require_checkpoint: true` 时：

- checkpoint 必须存在且可解析；
- step/time 与 log 和其他输出一致；
- continuation 来源 checkpoint 与输出链可追溯；
- append/noappend 产生的输出集合符合 spec。

checkpoint 存在只证明可读取，不单独证明运行完成。

## 6. 文件一致性

在可行范围内核验：

- log、energy、trajectory、final structure 和 checkpoint 的 step/time 区间一致；
- atom count 和 system identity 与 `.tpr` 一致；
- trajectory 没有明显截断或不可解析帧；
- energy 文件与本次 run unit 对应；
- noappend continuation 的 part files 没有被误当成单一连续文件；
- append continuation 没有混入不同 `.tpr` 或 checkpoint 链。

## 7. Role-specific checks

只执行 execution spec 中显式列出的 checks。

例如可包括：

- energy minimization 最大力阈值；
- 最终 potential energy 条件；
- 指定时间窗口的温度/压力/密度统计；
- 其他可确定性计算的 blocking 或 warning 指标。

Validator 不新增阈值，也不把未声明指标自动设为失败条件。

若某个显式 check 无法可靠计算：

- blocking check：不通过或请求人工决定；
- nonblocking check：warning；
- 不伪造数值。

# 技术通过范围

通过表示：

- 当前 run unit 按声明输入和命令完成；
- required outputs 与完成标准满足；
- 显式 blocking checks 通过；
- 输出可以作为后续 run unit 或 analysis 的技术输入。

通过不表示：

- equilibration 一定充分；
- production sampling 已收敛；
- 轨迹具有科学代表性；
- 所有体系异常已排除；
- 分析结论成立。

# Outcome codes

- `MD_RUN_OUTPUT_VALIDATED`；
- `MD_RUN_OUTPUT_VALIDATED_WITH_WARNINGS`；
- `OUTPUT_VALIDATION_INPUT_INCOMPLETE`；
- `INPUT_OR_COMMAND_PROVENANCE_MISMATCH`；
- `RUN_STILL_ACTIVE`；
- `REQUIRED_OUTPUT_MISSING`；
- `OUTPUT_UNREADABLE_OR_TRUNCATED`；
- `NORMAL_TERMINATION_NOT_CONFIRMED`；
- `FATAL_OR_NONZERO_EXIT_DETECTED`；
- `TARGET_STEP_OR_TIME_NOT_REACHED`；
- `CHECKPOINT_INVALID_OR_INCONSISTENT`；
- `OUTPUT_CROSS_FILE_INCONSISTENCY`；
- `ROLE_SPECIFIC_CHECK_FAILED`；
- `ROLE_SPECIFIC_CHECK_UNRESOLVED`；
- `OUTPUT_VALIDATOR_INTERNAL_FAILURE`。

# 通过条件

只有：

```text
MD_RUN_OUTPUT_VALIDATED
MD_RUN_OUTPUT_VALIDATED_WITH_WARNINGS
```

可以建议 Manager 接受当前 run unit 的 MD_OUTPUT artifact candidate。

若 Validator 成功执行但对象不通过：

- Validation component 可以 `status: DONE`；
- 使用具体不通过 outcome code；
- `artifact_candidates: []`；
- 返回修复、续跑、重规划或人工决定建议。

# Artifact candidate

通过时返回一个 `MD_OUTPUT` artifact candidate，至少包含：

- spec 声明为 required 的 engine outputs；
- output validation report；
- command/submission provenance 的必要业务文件；
- `derived_from_artifact_set_ids` 指向 MD_INPUT 和前置 MD_OUTPUT。

候选文件在 Manager 接受前保持 `present_unvalidated`；Manager 完成 runtime validation 和记录提交后，才登记为 VALIDATED artifact set。

# 输出

默认：

```text
04_md_simulation/<run_unit_id>/
├── md_run_output_validation_report.yaml
└── md_run_output_validation.log
```

报告至少记录：

- task/workstream/run unit IDs；
- source artifact IDs 和 hashes；
- execution spec/command/submission identity；
- output file inventory；
- parser/readability findings；
- actual final step/time；
- termination/failure evidence；
- checkpoint and continuation findings；
- role-specific check results；
- warnings；
- outcome code 和 gate recommendation。

# 返回

返回符合：

```text
03_contracts/subagent_result.schema.yaml
```

的独立 `validation_result`。

不得修改 Operation result、submission record、engine outputs 或管理记录。

# 失败与恢复建议

- 输入/记录冲突：BLOCKED，要求恢复；
- run still active：BLOCKED，不验证动态文件；
- 输出技术不通过：Validator DONE + 不通过 outcome；
- Validator 实现异常：FAILED；
- 需要同一 `.tpr` continuation 时，建议回到 Workflow 解析明确 checkpoint/append policy；
- 需要新 `.tpr` 或参数变化时，建议 route revision 到 `md_preparation_workflow`；
- 不自动修复、续跑或重提。

# 自检

- [ ] execution spec 和输入 hashes 已独立核验；
- [ ] 活动进程没有被验证为完成；
- [ ] required outputs 来自 spec，不是默认列表；
- [ ] 文件可读性和跨文件一致性已检查；
- [ ] target step/time 来自实际输出；
- [ ] checkpoint 没有被当作单独完成证据；
- [ ] role-specific 阈值均来自 spec；
- [ ] 技术通过没有被描述为科学收敛；
- [ ] 不通过没有被混同为 Validator 执行失败；
- [ ] 没有修改任何 engine output；
- [ ] 通过时才返回 MD_OUTPUT artifact candidate；
- [ ] 没有写管理目录。