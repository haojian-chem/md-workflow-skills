---
name: md_run_input_preparation
description: 根据已验证 md_simulation_plan 中的一个 run unit、VALIDATED SYSTEM 或上游 VALIDATED MD_OUTPUT、明确 MDP 和起始状态，运行 GROMACS grompp 生成该 run unit 的 MD_INPUT candidate、manifest 和命令证据。该 Operation 不选择科学参数、不执行 mdrun，也不自行宣布输入通过。
---

# 目标

为一个 run unit 生成可供 `md_run_execution` 使用的候选 MD_INPUT：

```text
validated md_simulation_plan
+ selected run unit
+ VALIDATED SYSTEM or upstream VALIDATED MD_OUTPUT
+ explicit MDP
→ grompp
→ run.tpr + manifest + evidence
→ md_run_input_validator
```

# 职责边界

负责：

- 读取 task、validated plan 和目标 run unit；
- 解析明确的坐标、拓扑、index、reference coordinates 和 checkpoint 来源；
- 核验 MDP identity、GROMACS executable/version 和 `maxwarn`；
- 以 argv 方式执行一次 `grompp`；
- 保存实际使用的 MDP identity或受控副本；
- 记录 command、stdout/stderr、warnings 和输入 hashes；
- 生成 `.tpr`、run input manifest、Operation report；
- 重新读取输出并进行最小 parse/hash 检查；
- 返回 MD_INPUT artifact candidate，随后交给专属 Validator。

不负责：

- 根据 run unit 名称或常规流程修改 MDP；
- 选择温度、压力、耦合、约束、步数或随机种子；
- 自动提高 `maxwarn`；
- 自动选择多个可能的坐标、checkpoint 或 topology；
- 修改 SYSTEM、MD_OUTPUT、plan、MDP 或 topology source；
- 运行 `mdrun`；
- 判断输入科学合理性或模拟已完成；
- 写管理目录；
- 覆盖已有 MD_INPUT。

# 输入

必须作为：

```text
OPERATION_WITH_VALIDATOR
operation: md_run_input_preparation
validator: md_run_input_validator
```

运行。

任务必须提供：

- 已通过 `md_simulation_plan_validator` 的 plan；
- 唯一目标 `run_unit_id`；
- run unit 所需的 VALIDATED SYSTEM 或上游 VALIDATED MD_OUTPUT artifact records；
- MDP file identity；
- 明确的坐标、topology、可选 index/reference/checkpoint file identities；
- grompp executable、version、`maxwarn` 和 extra argv；
- 一个新的 MD_INPUT 输出路径集合；
- allowed read/write 与 forbidden paths；
- command、manifest、report、log 和 Validator detail paths。

# Preflight

必须确认：

- task/workstream/run unit IDs 一致；
- plan 已验证且未被 superseded/invalidated；
- run unit 存在并允许进入 input preparation；
- 所有依赖 run units 的输出 gate 满足，或该 run unit 从 SYSTEM 起步；
- MDP path/hash 与 plan 一致；
- 坐标、topology、include 文件和可选输入可读且 hash 可追溯；
- 输入 artifact 为 VALIDATED；
- `INPUT_PREPARATION` 类 blocking unresolved items 为空；
- grompp executable 可定位且版本策略满足；
- `maxwarn` 与 plan 完全一致；
- 输出路径不存在，或同一 task 幂等复用时全部 hashes 一致；
- 不存在 source/target 同路径；
- 管理目录位于 forbidden paths。

不满足时返回 BLOCKED，不写部分 `.tpr`。

# 输入选择规则

## 起始状态

### SYSTEM

必须从 plan 和 SYSTEM artifact 明确解析：

- coordinate file；
- topology root；
- topology include closure；
- 可选 index/reference coordinates。

存在多个候选且 plan/task 未唯一指定时返回 `RUN_INPUT_SOURCE_AMBIGUOUS`。

### PRIOR_RUN_OUTPUT

必须引用计划中明确的 source run unit，并使用其 VALIDATED MD_OUTPUT：

- 必需坐标/结构；
- 如计划要求，明确 checkpoint；
- 其他声明的 continuation 输入。

不得仅按最新时间戳选择 checkpoint。

## MDP

- 不修改源 MDP；
- 若需要业务目录副本，必须记录 source hash 和 copied hash；
- 不通过文本替换偷偷改变参数；
- 需要参数变化时先修订 protocol spec/plan。

## `maxwarn`

`maxwarn` 是显式科学/技术风险决定：

- 默认不自动增加；
- plan 未指定时 BLOCKED；
- `grompp` warning 数超过显式允许值时 Operation 不得自行重试；
- 所有 warning 必须进入 manifest/report。

# 默认输出

```text
04_md_simulation/<run_unit_id>/input/
├── run.mdp                         # 受控副本或明确引用
├── run.tpr
├── md_run_input_manifest.yaml
├── grompp_command_record.yaml
├── grompp_stdout.log
├── grompp_stderr.log
└── md_run_input_preparation_report.yaml
```

可选输入文件不必复制，但必须记录 identity 和 provenance。

# Manifest 最小内容

`md_run_input_manifest.yaml` 至少记录：

- task/workstream/plan/run unit IDs；
- plan path/hash；
- source artifact set IDs；
- MDP source/copy identities；
- coordinate/topology/include/index/reference/checkpoint identities；
- GROMACS executable/version；
- 完整 argv；
- `maxwarn`；
- grompp return code；
- warning/error summaries；
- generated `.tpr` identity；
- output paths；
- resolved decision IDs。

本地 schema：

```text
schemas/md_run_input_manifest.schema.yaml
```

# 执行流程

1. 解析 task、权限、plan 和 run unit；
2. 核验 plan validation evidence；
3. 唯一解析起始 artifact 和具体文件；
4. 核验 MDP、topology include closure 和 hashes；
5. 检查 output conflict；
6. 在临时目录构造固定 argv；
7. 执行一次 `grompp`；
8. 捕获 return code、stdout/stderr 和 warnings；
9. 仅在 return code 成功且 `.tpr` 可读取时生成 manifest/report；
10. schema-validate manifest；
11. 原子提交候选输出；
12. 返回 Operation result，随后由专属 Validator 独立核验。

# 完成验证

Operation 只确认：

- `grompp` 实际执行；
- 声明输出已生成；
- `.tpr` 可进行最小读取；
- manifest 可解析；
- source files 未改变。

不替代 Validator 对 `.tpr` provenance、参数和 cross-file consistency 的判断。

# Outcome codes

- `MD_RUN_INPUT_PREPARED`；
- `MD_RUN_INPUT_PREPARED_WITH_WARNINGS`；
- `SIMULATION_PLAN_INVALID_OR_STALE`；
- `RUN_UNIT_NOT_FOUND_OR_NOT_READY`；
- `RUN_INPUT_SOURCE_AMBIGUOUS`；
- `RUN_INPUT_SOURCE_INVALID`；
- `MDP_IDENTITY_MISMATCH`；
- `TOPOLOGY_INCLUDE_INCOMPLETE`；
- `GROMPP_CAPABILITY_UNAVAILABLE`；
- `GROMPP_WARNING_LIMIT_EXCEEDED`；
- `GROMPP_FAILED`；
- `RUN_INPUT_OUTPUT_CONFLICT`；
- `RUN_INPUT_PREPARATION_INTERNAL_FAILURE`。

# Artifact candidate

成功时返回一个 `MD_INPUT` artifact candidate，至少包含：

- `.tpr`；
- MDP identity/副本；
- run input manifest；
- command record；
- Operation report。

状态保持 `present_unvalidated`。只有 `md_run_input_validator` 通过后，Manager 才可登记为 VALIDATED MD_INPUT。

# 失败与清理

- BLOCKED：不运行 grompp 或不提交候选；
- grompp FAILED：清理临时 `.tpr`，保留日志和结构化 failure；
- 不覆盖旧 input；
- 不修改源文件；
- 同一 task 的幂等复用必须比较全部输出 hashes。

# 自检

- [ ] plan 和 run unit 已验证且唯一；
- [ ] 起始 artifact 与具体文件唯一；
- [ ] MDP 未被隐式修改；
- [ ] `maxwarn` 未自动提高；
- [ ] topology include closure 已核验；
- [ ] grompp 只执行一次；
- [ ] command/warnings/hashes 已记录；
- [ ] 候选 MD_INPUT 仍为 UNVALIDATED；
- [ ] 未运行 mdrun；
- [ ] 未写管理目录；
- [ ] 未自行宣布输入通过。