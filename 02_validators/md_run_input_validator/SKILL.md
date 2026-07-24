---
name: md_run_input_validator
description: 独立核验 md_run_input_preparation 生成的 .tpr、MDP identity、输入来源、grompp command/warnings 和 run input manifest，确认该候选准确对应 validated simulation plan 中的目标 run unit。该 Validator 不修改输入、不重新运行 grompp，也不执行模拟。
---

# 目标

验证一个 run unit 的 MD_INPUT candidate 是否可安全交给 `md_run_execution`。

通过表示：

- `.tpr` 可解析；
- `.tpr`、MDP、坐标、拓扑和 checkpoint provenance 与 plan 一致；
- grompp command、版本、warning 和 `maxwarn` 可追踪；
- 输入文件没有被 Operation 非预期修改；
- 候选可以登记为 VALIDATED MD_INPUT。

不表示：

- 模拟一定稳定；
- 科学参数一定适合研究目标；
- run unit 已执行或完成。

# 职责边界

负责：

- 读取 validated plan、目标 run unit、source artifacts；
- 读取 Operation result、`.tpr`、manifest、command record 和 logs；
- 独立解析 `.tpr` 和实际 MDP；
- 核验输入 identities、topology/include closure 和 start-state provenance；
- 核验 grompp warning policy 和关键参数一致性；
- 输出 Validation result、详细 report 和 artifact gate 建议。

不负责：

- 修改 `.tpr`、MDP、topology、coordinates 或 checkpoint；
- 重新运行 grompp；
- 自动提高 `maxwarn`；
- 根据常规经验改参数；
- 执行 `mdrun`；
- 写管理目录；
- 自动重试 Operation。

# 输入

作为 `OPERATION_WITH_VALIDATOR` task unit 的 validator 部分，必须接收：

- 同一 task 的 Operation result；
- validated simulation plan 和 plan validation evidence；
- 目标 run unit；
- source SYSTEM/MD_OUTPUT artifact records；
- candidate `.tpr`；
- MDP source/used file；
- run input manifest；
- grompp command record、stdout/stderr 和 Operation report；
- topology root/include files、coordinates 和可选 index/reference/checkpoint；
- allowed read/write 与 forbidden paths；
- Validator report/result data 路径。

# Preflight

确认：

- task/workstream/run unit IDs 一致；
- Operation status 为 DONE；
- plan 仍有效且目标 run unit 存在；
- candidate files 存在、可读、非 symlink；
- manifest 可通过本地 schema；
- source artifact 为 VALIDATED；
- Validator 不以被验证文件为写入目标；
- 管理目录位于 forbidden paths。

# 独立核验

## 1. Plan 与 manifest

从 plan 独立提取 expected：

- run unit ID 和 role；
- MDP identity；
- start-state source；
- grompp executable/version、`maxwarn` 和 extra argv；
- expected SYSTEM 或 prior-run artifact lineage。

不得信任 manifest 自报 expected 值。

## 2. 文件身份

核验：

- plan、MDP、coordinates、topology root、includes、index/reference/checkpoint hashes；
- source MDP 与 used MDP 内容相同，除非 plan 明确允许经过可追踪转换；v1 默认要求相同；
- source artifacts 在 Operation 前后 hash 不变；
- `.tpr` identity 与 manifest 一致；
- manifest 中不存在未实际使用的输入文件。

## 3. Topology closure

- topology root 可解析；
-所有 required include 文件可定位；
- include identities 与 manifest 一致；
- 不存在执行期间临时替换后未记录的 include；
- topology 与 coordinate atom count/ordering 满足 grompp 输出事实。

## 4. `.tpr` 解析

使用可重复的 GROMACS inspection 路径读取至少：

- run input 可解析性；
- step/time integration settings；
- integrator；
- temperature/pressure coupling presence；
- constraints；
- continuation/checkpoint相关设置；
- system atom count；
- output control settings。

这些字段与实际 MDP、plan 和 role-specific explicit requirements 比较。Validator 不因 role 名称自行创造额外科学标准。

## 5. Command 与 warnings

- argv 与 manifest/command record 一致；
- `maxwarn` 与 plan 一致；
- return code 为成功；
- warnings 数量不超过显式允许值；
- 所有 warning 均被记录；
- 出现未被允许的 blocking warning 时不通过；
- executable/version 与计划策略一致。

## 6. Start-state provenance

### SYSTEM

候选必须追溯到 plan 声明的 VALIDATED SYSTEM。

### PRIOR_RUN_OUTPUT

候选必须追溯到明确的上游 VALIDATED MD_OUTPUT；若使用 checkpoint，identity 必须与 plan 和 manifest 一致。不得使用未验证或“最新”的 checkpoint 替代。

# Gate outcomes

- `MD_RUN_INPUT_VALIDATED`；
- `MD_RUN_INPUT_VALIDATED_WITH_NONBLOCKING_WARNINGS`；
- `RUN_INPUT_PLAN_MISMATCH`；
- `RUN_INPUT_SOURCE_PROVENANCE_MISMATCH`；
- `RUN_INPUT_FILE_HASH_MISMATCH`；
- `RUN_INPUT_TOPOLOGY_CLOSURE_INVALID`；
- `RUN_INPUT_TPR_UNREADABLE`；
- `RUN_INPUT_TPR_PARAMETER_MISMATCH`；
- `RUN_INPUT_GROMPP_COMMAND_MISMATCH`；
- `RUN_INPUT_WARNING_POLICY_VIOLATION`；
- `RUN_INPUT_MANIFEST_MISMATCH`；
- `RUN_INPUT_VALIDATOR_INPUT_INCOMPLETE`；
- `RUN_INPUT_VALIDATOR_INTERNAL_FAILURE`。

只有前两个 outcome 可以建议 Manager 接受 MD_INPUT candidate。

# 输出

默认：

```text
04_md_simulation/<run_unit_id>/input/
├── md_run_input_validation_report.yaml
└── md_run_input_validation_result.yaml
```

通过时：

- `validated_files` 包含 `.tpr`、MDP、manifest 和必要 command evidence；
- top-level artifact candidate 保持 Operation 创建的 MD_INPUT 文件集合；
- Manager 可将其登记为 VALIDATED MD_INPUT；
- 不修改 Operation result。

# 失败处理

- 输入缺失：BLOCKED；
- 对象可检查但不符合 gate：Validator 执行 DONE，outcome 不通过；
- 解析器或 inspection 失败：FAILED；
- 不修改候选，不自动重跑；
- 保留详细差异 report。

# 自检

- [ ] expected inputs 从 plan 独立提取；
- [ ] 未信任 manifest 自报；
- [ ] `.tpr` 已实际解析；
- [ ] MDP、topology、coordinates 和 checkpoint provenance 一致；
- [ ] topology include closure 已核验；
- [ ] grompp argv/version/maxwarn/warnings 已核验；
- [ ] role 名称未被用于隐式增加科学标准；
- [ ] source files 未改变；
- [ ] 未修改候选或重跑 grompp；
- [ ] 未执行 mdrun；
- [ ] 未写管理目录。