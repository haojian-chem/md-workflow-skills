---
name: md_simulation_plan_validator
description: 独立核验 MD simulation plan candidate 是否是 validated scientific protocol 的准确静态 task projection，检查 run-unit DAG、目录、start-state logical source、unresolved gate 投影和 revision lineage，并确认 plan 未复制拥有科学参数或嵌入运行状态。该 Validator 不修改 plan，也不生成 MD_INPUT。
---

# 目标

确认 plan 可供 Workflow 生成 route fragments：

- protocol 已通过专属 Validator；
- run-unit projection 精确覆盖 protocol run units；
- DAG、start-state、paths 和 gates 正确；
- protocol 仍是科学字段唯一 owner；
- plan 是 immutable static projection。

# 职责边界

负责：

- 读取 validated protocol、protocol validation、SYSTEM、old plan 和 plan candidate；
- 独立重算 expected run-unit projection；
- 检查 projection set、DAG、paths、gate refs 和 revision chain；
- 检查 plan 未复制 MDP/completion/runtime/status 字段；
- 写 validation report 和 gate 建议。

不得：

- 修改 plan/protocol；
- 补充 run units 或科学参数；
- 生成 MDP/TPR/attempt；
- 把 runtime state 写入 plan；
- 写管理目录；
- 自动重跑 Operation。

# 输入

作为 plan materialization 的专属 Validator，接收：

- Operation result/report；
- plan candidate；
- validated protocol spec 和 validation evidence；
- VALIDATED SYSTEM records；
- old plan，如为 revision；
- allowed read/write 与 forbidden paths；
- report/result data路径。

# Preflight

确认：

1. Operation status 为 DONE；
2. protocol schema v2 和 plan schema v2 有效；
3. protocol Validator outcome 可接受；
4. task/workstream/protocol/plan/SYSTEM IDs 一致；
5. files 可读且 hashes 一致；
6. Validator 不写 plan/protocol/SYSTEM；
7. 管理目录禁止写入。

# 独立检查

## Projection set

从 protocol 独立计算每个 run unit：

- ID、role、dependencies；
- protocol field path；
- start-state source type/source run；
- run/input/attempts directories；
- input/attempt gate status；
- blocking item IDs。

plan projection 必须精确匹配，不得漏项或增加默认 run unit。

## DAG/start-state

- IDs 唯一；
- dependencies 全部存在、无 self/cycle；
- PRIOR_RUN_OUTPUT source 位于 dependency closure；
- SYSTEM source 的 source run 为 null；
- topological route projection 可生成。

## Paths

- run directories 在当前 `04_md_simulation/`；
- input/attempts directories 是各 run directory 的唯一子路径；
- 不与 `00_plan/`、`99_validation/`、其他 run 或管理目录冲突；
- paths 采用项目约定的规范化形式。

## Gate projection

- INPUT_PREPARATION items 只阻塞受影响 run input gate；
- ATTEMPT_SPECIFICATION items 只阻塞受影响 attempt gate；
- blocking item IDs 全部引用 protocol unresolved items；
- 没有 PROTOCOL_VALIDATION unresolved item；
- scientific field 未误分类绕过 protocol gate。

## Owner separation

plan 不得包含或拥有：

- MDP source/typed overrides；
- preprocessing values；
- expected output details；
- completion targets/checks；
- GROMACS executable/backend/resources；
- attempt/submission identities；
- NOT_PREPARED/RUNNING/VALIDATED 等 runtime status。

这些字段仍从 validated protocol 或 runtime records 读取。

## Revision

- 首版 supersedes/reason 可以 null；
- revision 指向提供的 old plan 且 reason 非空；
- old plan hash 不变；
- 新路径/identity 唯一；
- 不覆盖下游 artifacts。

# Outcome codes

- `SIMULATION_PLAN_VALIDATED`；
- `SIMULATION_PLAN_VALIDATED_WITH_DEFERRED_GATES`；
- `PLAN_VALIDATOR_INPUT_INCOMPLETE`；
- `PLAN_PROTOCOL_OR_SYSTEM_MISMATCH`；
- `PLAN_PROJECTION_SET_MISMATCH`；
- `PLAN_DAG_OR_START_STATE_INVALID`；
- `PLAN_GATE_PROJECTION_INVALID`；
- `PLAN_PATH_CONFLICT`；
- `PLAN_OWNER_SEPARATION_VIOLATION`；
- `PLAN_RUNTIME_STATUS_EMBEDDED`；
- `PLAN_REVISION_CHAIN_INVALID`；
- `PLAN_VALIDATOR_INTERNAL_FAILURE`。

只有前两个 outcome 可用于 route projection。

# 输出

```text
04_md_simulation/00_plan/
├── md_simulation_plan_validation_report*.yaml
└── md_simulation_plan_validation*.log
```

不创建 MD artifact candidate。

# 自检

- [ ] expected projection 从 protocol 独立重算；
- [ ] run set/DAG/start-state 精确匹配；
- [ ] paths 唯一且受控；
- [ ] unresolved gates 投影正确；
- [ ] plan 未复制拥有科学字段；
- [ ] plan 未嵌入 runtime status；
- [ ] revision 未覆盖旧 plan；
- [ ] 未生成 MDINPUT/attempt；
- [ ] 未修改对象或管理目录。