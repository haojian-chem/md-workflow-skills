---
name: structure_preparation_validation
description: Stage 1.9 Structure preparation validation。对 1.8 形成的 Stage 1 final heavy-atom structure / map 做只读最终验证，确认 Stage 1 前序结果闭合并检查目标 force-field compatibility；只有 blocking checks 全部通过时才允许进入 Stage 2。
---

# 1.9 Structure preparation validation

## Purpose

对当前 target 的 Stage 1 最终结果执行只读验证，确认其可以安全进入 Stage 2 topology / parameterization。

本 Skill 只拥有 Stage 1 final validation：

```text
stage1_final.pdb
+ stage1_final_map.yaml
+ 必要的上游正式结果
+ 当前实际采用的相关 force-field residue definitions
↓
Stage 1 structural closure
+ final force-field compatibility
↓
PASS / FAIL
```

1.9 不修改 `stage1_final.pdb`、`stage1_final_map.yaml` 或任何上游正式结果。发现 blocking failure 时定位真正拥有该问题的上游步骤，由对应步骤修复后再重新进入 1.9。

## Inputs / evidence

对每个 target，至少需要：

- 1.8 正式 `stage1_final.pdb`；
- 1.8 正式 `stage1_final_map.yaml`；
- 当前 target 对应的 1.2 正式 classification / identity information；
- 当前实际用于 standard residue compatibility 判断的 force-field residue definition file(s)。

随后只按当前核验需要读取相关上游正式结果，例如：

- 1.4 `altloc_resolution_report.yaml`；
- 1.5 `structure_completeness_report.yaml`；
- 1.6 `completion_report.yaml` / `completion_validation.md`；
- 1.7 `protonation_assignment_report.yaml` / `protonation_validation.md`；
- 1.8 当前正式结果及其 completion status。

不要求为了形式完整而预读 1.4–1.8 的全部历史材料。只有当 final state、blocking item 或判据来源需要追溯时才读取对应正式结果。

如果当前 target 的 relevant force-field definitions 尚未明确，或现有文件不足以判断 standard residue compatibility，先使用项目已有正式信息定位；仍不能确定时向用户确认，不自行假设默认 force field。

## Reuse

开始 1.9 时可以在 `project_result_index.md` 中检索既有正式 `structure_preparation_validation.md`。

已有 `PASS` 结果只有在以下内容均明确等价时才可自动复用：

- `stage1_final.pdb` 内容相同；
- `stage1_final_map.yaml` 内容相同；
- 影响 Stage 1 closure 的上游正式结果没有发生相关变化；
- 实际用于 compatibility 判断的 force-field definitions 等价；
- 用户没有明确要求重新验证或建立对照。

判断结构、map 和 reference 是否相同时优先比较内容 / hash，不只比较路径或文件名。

明确不等价时重新执行；证明等价所需信息不足时向用户确认。复用时直接引用既有正式结果，不复制报告，也不创建当前任务空目录。

## Validation

### 1. Final PDB / map consistency

确认：

- `stage1_final_map.yaml` 指向当前实际验证的 `stage1_final.pdb`；
- final PDB 中每个实际 heavy atom 在 map 中恰有一个对应 record；
- map 中没有指向 final PDB 不存在 atom 的 record；
- `serial / chain_id / resid / residue_name / atom_name` 与 final PDB 实际 identity 一致；
- map 中保存的 `component_id + residue_id` 能定位到当前正式 1.2 / 1.3 identity information；
- final PDB 可正常解析，没有重复 atom identity 或明显结构记录异常。

这里检查的是 1.8 正式结果当前是否一致，不重新执行 1.8 的 reorder / chain-assignment 算法。

### 2. Stage 1 structural closure

基于 final structure 与必要的上游正式结果确认：

- 不存在未解决的 alternate-conformation / altLoc 问题；
- 1.5 中需要后续处理的 repair items 已在当前最终状态中闭合；
- 如果实际执行过 1.6，其正式 validation 已通过且没有 unresolved repair item；
- 如果当前 target 需要 1.7，protonation assignment 已落实为当前 final residue naming，且 1.7 validation 已通过；
- 1.8 自身 completion requirements 已满足；
- 没有仍然阻塞 Stage 2 的上游 unresolved item。

1.9 不重新执行 1.4、1.5、1.6、1.7 或 1.8 的内部判断 / repair 逻辑。前序正式结果已经足以确认某项闭合时，直接使用该结果；只有实际 final state 与正式结果不一致、或存在需要核实的 blocking evidence 时才进一步检查当前结构。

### 3. Final force-field compatibility

对当前 final structure 中分类为 `STANDARD_RESIDUE` 的对象，使用当前实际采用的 force-field residue definitions 检查：

- final residue name 能被相应 force field / residue definition 识别；
- heavy-atom names 与该 residue definition 兼容；
- 当前 final heavy-atom composition 与 Stage 2 正常处理所需 residue representation 兼容；
- 1.7 形成的 protonation-state residue name 在当前实际使用的 naming convention / force-field definitions 中存在；
- 1.6 / 1.7 / 1.8 的修改没有重新产生新的 blocking residue-name、atom-name 或 heavy-atom incompatibility。

`TOPOLOGY_LINKED_NONSTANDARD`、`INDEPENDENT_NONSTANDARD`、solvent / ion 等对象不使用 standard-residue template 判定其 atom set 是否正确；它们只需保持与 1.2 正式 classification / identity 一致，并能够按已确定的 Stage 2 路线继续处理。

如果某种 terminal representation 差异属于当前目标 force field / Stage 2 工具正常的 termini processing 可以处理的情况：

- 不在 1.9 修改；
- 不判为 Stage 1 blocking failure；
- 记录为 Stage 2 handoff item。

只有真正无法由 Stage 2 正常处理、并会阻止 topology / parameterization 的 compatibility 问题才判为 blocking failure。

如果现有 evidence 不足以可靠判断某个差异是否属于正常 Stage 2 handling，不猜测 PASS / FAIL；先核实对应 force-field / tool definition，仍不能确定时向用户确认。

## Failure ownership

1.9 发现 blocking failure 后只记录问题与责任来源，不自行 repair。

根据实际问题定位到真正 owner，例如：

```text
alternate-conformation 仍未闭合
→ 1.4

既定 completeness repair 未落实 / 最终结构仍存在对应 repair failure
→ 1.6

protonation assignment / final protonation residue naming 不正确
→ 1.7

final chain / resid / atom organization 或 map 不一致
→ 1.8

classification / stable identity / topology class 本身错误
→ 更早的实际 owner（通常 1.2 / 1.3）
```

上述例子只用于定位常见 owner；实际 failure 应回到真正产生该问题的步骤，而不是强行套固定分类。

上游修复后，使用新的 current final result 重新执行 1.9；不能只修改 validation report 把旧 FAIL 改成 PASS。

## Validation conclusion

每个 target 分别形成两项结论：

```text
Stage 1 structural validation: PASS | FAIL
Force-field compatibility: PASS | FAIL
```

只有两项都为 `PASS`，且没有 blocking failure 时，当前 target 的 1.9 overall conclusion 才是：

```text
PASS
```

否则 overall conclusion 为：

```text
FAIL
```

Warning 与 Stage 2 handoff item 不建立第三种 conclusion；只要它们不构成 blocking failure，可以在 overall `PASS` 下保留记录。

## Official result

每个 target 独立生成：

```text
<project_root>/01_structure_preparation/09_validation/<task_id>/<target_id>/structure_preparation_validation.md
```

报告至少记录：

- `target_id`；
- 实际验证的 `stage1_final.pdb` 完整绝对路径；
- `stage1_final_map.yaml` 完整绝对路径；
- 实际用于 force-field compatibility 判断的 reference / definition file 完整绝对路径；
- `Stage 1 structural validation: PASS | FAIL`；
- `Force-field compatibility: PASS | FAIL`；
- `Overall: PASS | FAIL`；
- blocking failures（存在时）；
- Stage 2 handoff items（存在时）；
- blocking failure 对应的建议返回步骤。

通过项保持摘要即可，不要求逐 residue / atom 罗列全部 PASS evidence。

只有出现 compatibility issue、blocking failure 或需要 Stage 2 明确处理的 handoff item 时，才展开到足以定位问题的：

```text
chain_id + resid + residue_name
必要时 atom_name
问题说明
判据 / reference
owner / handoff destination
```

本结果使用 Markdown，不另建 rigid schema。

## Project result registration

生成正式 `structure_preparation_validation.md` 后，将其完整绝对路径及简短说明登记到：

```text
<project_root>/00_project_records/project_result_index.md
```

登记只用于后续快速定位“该 target 是否已有 Stage 1 final validation result”。详细 blocking / handoff evidence 留在报告本身，不复制到项目级索引。

`project_result_index.md` 的内部组织格式由项目级 record owner 管理，本 Skill 不重新定义。

## Stage 1 completion / Stage 2 handoff

只有当前 target 的 1.9 overall conclusion 为 `PASS` 时，Stage 1 对该 target 才完成，可将以下 Stage 1 final results 交给 Stage 2：

```text
stage1_final.pdb
stage1_final_map.yaml
structure_preparation_validation.md
```

1.9 只确认 Stage 1 final heavy-atom structure / map 可以进入 Stage 2。

Stage 2 的标准残基补氢、force-field-specific all-atom ordering、topology generation 和 nonstandard parameterization 由 Stage 2 自己处理；正常可由 Stage 2 termini processing 解决的 terminal representation 差异保留在 handoff item 中，不在 1.9 提前转换。
