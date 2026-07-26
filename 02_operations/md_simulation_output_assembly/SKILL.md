---
name: md_simulation_output_assembly
description: 根据 validated simulation protocol/plan、明确 route scope 和范围内 VALIDATED run-level MD_OUTPUT artifacts，生成唯一 stage-level MD_OUTPUT collection manifest。该 Operation 只组装引用，不复制、拼接或修改轨迹和能量文件，也不自行宣布阶段完成。
---

# 目标

为 Workflow exit 或明确阶段输出请求生成唯一集合对象：

```text
validated run-level MD_OUTPUT artifacts
+ validated protocol/plan
+ resolved route scope
→ md_simulation_output_manifest.yaml candidate
→ md_simulation_output_validator
→ stage-level MD_OUTPUT artifact candidate
```

# 职责边界

负责：

- 读取 validated protocol/plan 和当前 route scope；
- 确定范围内 required run units；
- 引用各 run unit 的 VALIDATED MD_OUTPUT artifact 和 run output manifest；
- 保存 run/segment ordering；
- 物化 final structure/checkpoint selection；
- 记录 excluded/out-of-scope/superseded outputs；
- 写 stage output manifest 和 assembly report。

不得：

- 复制、拼接、转换、截断或重命名 engine outputs；
- 自动把目录中的额外 run unit 纳入范围；
- 使用未验证或失效 run output；
- 在多个 final-state 候选间猜测；
- 判断采样充分或科学收敛；
- 修改 artifact、route、plan 或管理记录；
- 自行宣布 output collection 通过。

# 输入

必须作为：

```text
OPERATION_WITH_VALIDATOR
operation: md_simulation_output_assembly
validator: md_simulation_output_validator
```

运行。

任务必须提供：

- validated protocol/plan；
- active route ID 和明确 MD simulation scope；
- required/skipped/out-of-scope run unit IDs；
- 每个 required run unit 的 VALIDATED MD_OUTPUT artifact 和 run output manifest；
- resolved final-state selection，如存在多个合法候选；
- allowed read/write 与 forbidden paths；
- manifest/report/log 输出路径。

# Preflight

确认：

1. task/workstream/route/plan IDs 一致；
2. route scope 已解析；
3. required run-unit set 与 plan/route 一致；
4. 每个 required run unit 具有唯一 VALIDATED run-level MD_OUTPUT；
5. run output manifests 可读且 hashes 一致；
6. 无 active/UNKNOWN/FINISHED_UNVERIFIED attempt 属于 required scope；
7. superseded/invalidated outputs 未作为输入；
8. final structure/checkpoint selection 唯一或有 resolved decision；
9. 输出路径位于 `04_md_simulation/99_validation/` 授权范围；
10. 不覆盖旧 stage manifest。

# 组装规则

manifest 必须保存：

- protocol/plan/route/scope identities；
- included run units 及顺序；
- included run-level artifact IDs；
- 每个 run output manifest identity；
- trajectory/energy segment reference ordering；
- final structure/checkpoint reference；
- excluded/superseded artifacts；
- derived-from artifact IDs；
- assembly decisions 和 warnings。

Operation 不展开复制全部 engine file records；底层文件仍由 run-level artifacts 拥有。

# 输出

```text
04_md_simulation/99_validation/
├── md_simulation_output_manifest.yaml
├── md_simulation_output_assembly_report.yaml
└── md_simulation_output_assembly.log
```

本地 schema：

```text
schemas/md_simulation_output_manifest.schema.yaml
```

# Outcome codes

- `SIMULATION_OUTPUT_ASSEMBLED`；
- `SIMULATION_OUTPUT_ASSEMBLED_WITH_WARNINGS`；
- `SIMULATION_OUTPUT_SCOPE_UNRESOLVED`；
- `SIMULATION_OUTPUT_RUN_SET_MISMATCH`；
- `SIMULATION_OUTPUT_RUN_ARTIFACT_MISSING_OR_INVALID`；
- `SIMULATION_OUTPUT_FINAL_STATE_UNRESOLVED`；
- `SIMULATION_OUTPUT_LINEAGE_INVALID`；
- `SIMULATION_OUTPUT_PATH_CONFLICT`；
- `SIMULATION_OUTPUT_ASSEMBLY_INTERNAL_FAILURE`。

# 返回

成功时生成未验证 manifest candidate，artifact candidates 为空；专属 Validator 决定是否返回 stage-level MD_OUTPUT artifact candidate。

# 自检

- [ ] included run set 来自 route scope；
- [ ] 所有 included run outputs 已 VALIDATED；
- [ ] 未扫描目录自动加入 outputs；
- [ ] final state 唯一或有 resolved decision；
- [ ] 没有复制/拼接/修改 engine outputs；
- [ ] manifest 只引用底层 artifacts；
- [ ] 未自行宣布阶段 output 通过；
- [ ] 未写管理目录。