---
name: md_run_output_validator
description: 核验一个已经结束的 GROMACS run unit 是否与 validated simulation plan、VALIDATED MDINPUT、execution spec、command 和 submission provenance 一致，检查 required outputs、正常终止、目标步数/时间、checkpoint 和显式 acceptance checks，并生成 MDOUTPUT artifact candidate。该 Validator 不修改输出、不补跑模拟，也不把技术完成夸大为科学收敛。
---

# 目标

验证一个 FINISHED_UNVERIFIED 或同步结束的 run unit：

- plan、MDINPUT、命令和 execution provenance 可追溯；
- required outputs 完整且可解析；
- GROMACS 运行达到显式完成标准；
- continuation 链与 checkpoint identity 一致；
- explicit blocking acceptance checks 通过；
- 输出可以成为当前 run unit 的 MDOUTPUT candidate。

# 职责边界

负责：

- 读取 validated plan、MDINPUT/input manifest、execution spec、command、submission evidence 和 engine outputs；
- 独立核验 plan/run unit/input hashes 和 work directory；
- 解析必要的 log、energy、trajectory、structure 和 checkpoint metadata；
- 核验 termination、target steps/time 和 required outputs；
- 执行 spec 中显式 role-specific checks；
- 核验 continuation/append provenance；
- 写详细 report；
- 返回 Validation result 和 MDOUTPUT candidate。

不负责：

- 修改、截断、拼接、修复或重命名 outputs；
- 继续或重跑模拟；
- 重新生成 `.tpr`；
- 自行定义 EM force、温度、压力、密度等阈值；
- 在 spec 未要求时将波动/漂移/采样设为 hard gate；
- 执行完整科学分析；
- 修改 submission/artifact records；
- 选择下一 run unit；
- 写管理目录；
- 创建子 Agent 或直接向用户提问。

# 输入

必须接收共享 VALIDATOR task unit，并提供：

- validated simulation plan 和 plan validation evidence；
- target run unit；
- `md_run_execution_spec.yaml`；
- 对应 VALIDATED MDINPUT artifact records；
- `md_run_input_manifest.yaml` 和 input validation report；
- execution Operation report；
- command record；
- submission evidence/latest submission record，如异步；
- 当前 run unit engine outputs；
- allowed read/write、forbidden paths 和 report目标。

异步运行必须已有：

```text
submission status: FINISHED_UNVERIFIED
```

同步运行必须有可信 process terminal evidence。

# Preflight

确认：

1. task/Workstream/plan/run unit IDs 一致；
2. plan 有效且 target run unit 未被 superseded；
3. execution spec 与 Operation 使用版本一致；
4. MDINPUT 为 VALIDATED；
5. input manifest、`.tpr`、checkpoint 和其他 input hashes 未改变；
6. execution spec 与 plan/MDINPUT 一致；
7. command record 可由 execution spec 重建；
8. 异步 submission terminal 且不再写 output；
9. 不存在同一 run unit 活动进程；
10. engine outputs 位于授权目录且非未授权 symlink；
11. Validator output path 受授权；
12. 管理目录位于 forbidden paths。

活动进程仍存在时 BLOCKED，不验证动态文件并宣布完成。

# 核验规则

## 1. Provenance

核验完整链：

```text
validated plan
→ validated MDINPUT/input manifest/TPR
→ execution spec
→ command/submission
→ engine outputs
```

至少检查：

- plan/run unit identity；
- execution spec hash；
- MDINPUT artifact ID；
- input manifest 和 `.tpr` identities；
- checkpoint identity；
- command argv；
- executable/version；
- work directory/deffnm；
- PID/session/job identity；
- restart/append policy。

无法解释的输入或命令变化阻止通过。

## 2. Required outputs

以 execution spec `expected_outputs` 为唯一 required/optional 来源。

required files 必须：

- 存在且为常规文件；
- 非空，除非格式明确允许；
- 可由适用 parser/engine tool 读取；
- 属于当前 execution attempt；
- hash、size 和必要 metadata 已记录。

不得只按扩展名或修改时间判断归属。

## 3. GROMACS termination

当 `require_normal_termination: true`：

- 核验正常终止 evidence；
- 同时检查 fatal error、segfault、scheduler kill、resource termination、nonzero exit 和 log truncation；
- normal marker 与 failure evidence 冲突时不得通过。

## 4. Step/time

若提供 target_nsteps/target_time_ps：

- 从实际 output metadata 独立读取 final step/time；
- 使用格式精度允许的明确 tolerance；
- 不用 file name、MDP 或 command expectation 代替实际结果；
- blocking target 未达到时不通过。

未提供目标时不得猜测时长。

## 5. Checkpoint

当 require_checkpoint：

- checkpoint 存在且可解析；
- step/time 与 log/其他 outputs 一致；
- input/output checkpoint lineage 可追溯；
- append/noappend output set 符合 spec。

checkpoint 存在不单独证明运行完成。

## 6. Cross-file consistency

在可行范围内核验：

- log/energy/trajectory/final structure/checkpoint step-time区间一致；
- atom count/system identity 与 `.tpr` 一致；
- trajectory 无明显截断或不可解析 frame；
- energy file 属于当前 run；
- noappend part files 未被误当单一连续文件；
- append continuation 未混入不同 `.tpr`/checkpoint chain。

## 7. Role-specific checks

只执行 execution spec 显式列出的 checks，例如 maximum force、potential energy、指定窗口温度/压力/密度统计等。

- 不新增 threshold；
- 不把未声明 metric 设为 failure；
- blocking check 无法可靠计算：不通过或请求人工决定；
- nonblocking check 无法计算：warning；
- 不伪造数值。

# 技术通过范围

通过表示当前 run unit 按声明输入/命令完成，required outputs 和 explicit blocking checks 满足，可作为下游 run unit 或 analysis 的技术输入。

不表示 equilibration 充分、production sampling 收敛、轨迹科学代表性或分析结论成立。

# Outcome codes

- `MD_RUN_OUTPUT_VALIDATED`；
- `MD_RUN_OUTPUT_VALIDATED_WITH_WARNINGS`；
- `OUTPUT_VALIDATION_INPUT_INCOMPLETE`；
- `SIMULATION_PLAN_OR_RUN_UNIT_MISMATCH`；
- `MD_INPUT_NOT_VALIDATED_OR_MISMATCHED`；
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

只有前两个 outcome 可以建议 Manager 接受 MDOUTPUT candidate。

对象不通过但 Validator 成功执行时可 `status: DONE` + 具体不通过 outcome，不返回 artifact candidate。

# Artifact candidate

通过时返回 MDOUTPUT candidate，至少包含：

- spec 声明 required engine outputs；
- output validation report；
-必要 command/submission provenance files；
- `derived_from_artifact_set_ids` 指向当前 MDINPUT 和前置 MDOUTPUT。

候选在 Manager 接受前保持 present_unvalidated；完成 runtime validation 和 records commit 后登记为 VALIDATED。

# 输出

```text
04_md_simulation/<run_unit_id>/
├── md_run_output_validation_report.yaml
└── md_run_output_validation.log
```

report 至少记录：

- task/workstream/plan/run unit IDs；
- MDINPUT/source artifact IDs 和 hashes；
- input manifest/TPR identity；
- execution spec/command/submission identity；
- output inventory/parser findings；
- actual final step/time；
- termination/failure evidence；
- checkpoint/continuation findings；
- role-specific results；
- warnings/outcome/gate recommendation。

# 返回

返回共享 `subagent_result` 的独立 validation_result，不修改 Operation result、submission record、outputs 或管理记录。

# 失败与恢复建议

- input/records conflict：BLOCKED，要求恢复；
- run active：BLOCKED；
- output technical gate 不通过：DONE + 不通过 outcome；
- Validator implementation error：FAILED；
- 相同 `.tpr` continuation：建议 Workflow 解析明确 checkpoint/append 和新 execution spec；
- 需要新 `.tpr`/MDP/科学参数：建议 route revision 到本 Workflow 的 plan revision 或 run input preparation；
- 只有 SYSTEM 结构/拓扑/盒子/溶剂/离子变化时建议返回 `md_preparation_workflow`；
- 不自动修复、续跑或重提。

# 自检

- [ ] plan/run unit/MDINPUT/execution provenance 已独立核验；
- [ ] 活动进程未被验证为完成；
- [ ] required outputs 来自 spec；
- [ ] 文件可读性/cross-file consistency 已检查；
- [ ] target step/time 来自实际 output；
- [ ] checkpoint 未作为单独完成证据；
- [ ] role-specific thresholds 均来自 spec；
- [ ] 技术通过未描述为科学收敛；
- [ ] 不通过未混同 Validator execution failure；
- [ ] 未修改 output；
- [ ] 通过时才返回 MDOUTPUT candidate；
- [ ] 新 TPR 问题未错误归回 md_preparation；
- [ ] 未写管理目录。