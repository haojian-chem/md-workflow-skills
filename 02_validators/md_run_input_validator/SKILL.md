---
name: md_run_input_validator
description: 独立核验 md_run_input_preparation 生成的 rendered/copied MDP、TPR、SYSTEM或上游 run-output来源、topology include closure、grompp command/warnings 和 input manifest，确认候选准确实现 validated scientific protocol 中的目标 run unit。该 Validator 不修改输入、不重跑 grompp，也不执行模拟。
---

# 目标

验证一个 run unit 的 MD_INPUT candidate：

- protocol/plan/run-unit identities 一致；
- MDP final file 或 template+typed overrides 被准确物化；
- TPR 可解析且与 rendered MDP/input files 一致；
- grompp runtime evidence、maxwarn 和 warnings 可追踪；
- candidate 可登记为 VALIDATED MD_INPUT。

通过不表示 MDP 科学方案最佳或模拟一定稳定。

# 职责边界

负责：

- 读取 validated protocol/plan、Operation result、input manifest、rendered MDP、TPR 和 source files；
- 独立核验 MDP source/rendering/override provenance；
- 解析 MDP 与 TPR 必要 metadata；
- 核验 coordinates/topology/include/index/reference/input checkpoint；
- 核验 grompp command/version/maxwarn/warnings；
- 检查 source files 未改变；
- 写 validation report并返回 MD_INPUT gate。

不得：

- 修改 MDP/TPR/topology/coordinates/checkpoint；
- 修复或重跑 grompp；
- 添加/调整参数或 maxwarn；
- 执行 mdrun；
- 判断采样或科学收敛；
- 写管理目录。

# 输入

作为 input preparation 的专属 Validator，接收：

- Operation result/report；
- validated protocol/plan 和目标 run projection；
- input manifest；
- MDP source/template、rendered MDP 和 typed override provenance；
- TPR；
- source SYSTEM/upstream run-output records；
- coordinates/topology/includes/index/reference/input checkpoint；
- grompp command/stdout/stderr；
- allowed read/write 与 forbidden paths；
- report/result data路径。

# Preflight

确认：

1. Operation status 为 DONE；
2. protocol/plan schema v2 有效且已验证；
3. task/workstream/protocol/plan/run-unit IDs 一致；
4. manifest schema v2 有效；
5. TPR/rendered MDP/source files 可读且 hashes 一致；
6. source artifact 已 VALIDATED；
7. Validator 不写被验证对象；
8. 管理目录禁止写入。

# 独立检查

## MDP materialization

### FINAL_FILE

- source kind 与 protocol 一致；
- overrides 为空；
- rendered/copy content 与 source 语义和 hash 一致；
- rendering policy 为 USE_FILE_UNCHANGED。

### TEMPLATE_WITH_TYPED_OVERRIDES

- template hash 与 protocol 一致；
- override parameter set/value type/value/unit 与 protocol 一致；
- 每个 parameter 在 template 语义中唯一；
- rendered MDP 只改变声明参数；
- 未声明参数保持模板值；
- rendering policy 为 EXACT_PARAMETER_REPLACEMENT；
- 不存在自由文本注入或额外参数改变。

## Source files

- coordinates/topology/include closure 与 source artifact 一致；
- required index/reference files 存在；
- SYSTEM start-state 的 input checkpoint 为 null；
- PRIOR_RUN_OUTPUT source artifact/run unit 与 dependency closure 一致；
- input checkpoint 如存在，属于声明上游 output；
- 所有 source hashes 在 Operation 前后不变。

## grompp

- command 可由 manifest 重建；
- executable实际版本有记录，且满足 task/profile constraint；
- `maxwarn` 等于 protocol preprocessing policy；
- return code 符合成功条件；
- warnings 数量/内容与 stdout/stderr 一致；
- warning 超过允许值不得通过；
- 不因 executable路径变化要求 scientific protocol revision。

## TPR

核验可用 inspector 读取的：

- atom count/system identity；
- run input source identity；
- integrator/ensemble/step/time等与 rendered MDP一致的可验证字段；
- topology/coordinates/checkpoint linkage；
- TPR 未截断、非旧 task 遗留。

无法可靠解析 blocking metadata 时不伪造通过。

# Outcome codes

- `MD_RUN_INPUT_VALIDATED`；
- `MD_RUN_INPUT_VALIDATED_WITH_WARNINGS`；
- `RUN_INPUT_VALIDATOR_INPUT_INCOMPLETE`；
- `RUN_INPUT_PROTOCOL_OR_PLAN_MISMATCH`；
- `RUN_INPUT_MANIFEST_OR_SOURCE_MISMATCH`；
- `RUN_INPUT_MDP_RENDERING_MISMATCH`；
- `RUN_INPUT_UNDECLARED_MDP_CHANGE`；
- `RUN_INPUT_TOPOLOGY_OR_SOURCE_INVALID`；
- `RUN_INPUT_GROMPP_COMMAND_OR_WARNING_INVALID`；
- `RUN_INPUT_TPR_UNREADABLE_OR_INCONSISTENT`；
- `RUN_INPUT_SOURCE_FILE_MUTATION_DETECTED`；
- `RUN_INPUT_VALIDATOR_INTERNAL_FAILURE`。

只有前两个 outcome 可返回 MD_INPUT artifact candidate。

# Artifact candidate

通过时引用 Operation 已生成的 MD_INPUT candidate files，并确保包含：

- rendered/copied run.mdp；
- run.tpr；
- input manifest；
- grompp command/report；
- input validation report。

`derived_from_artifact_set_ids` 指向 SYSTEM 或上游 run-level MDOUTPUT。

# 自检

- [ ] protocol 是科学字段 owner；
- [ ] FINAL_FILE/template rendering 已独立核验；
- [ ] 未声明 MDP 参数没有变化；
- [ ] source/topology/include/checkpoint provenance 连续；
- [ ] runtime executable 仅作为 evidence；
- [ ] maxwarn 与 protocol 一致；
- [ ] TPR metadata 与 rendered MDP/input一致；
- [ ] source files 未改变；
- [ ] 未修改对象、重跑 grompp或执行模拟；
- [ ] 未写管理目录。