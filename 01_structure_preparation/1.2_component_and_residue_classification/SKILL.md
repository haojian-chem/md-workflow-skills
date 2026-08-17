---
name: component_and_residue_classification
description: Stage 1.2 Component and residue classification。对当前已确定 structure model 建立稳定的 component / residue / relation 分类、参考证据和下游 identity，并输出供 1.3 直接消费的 classification_result.yaml。
---

# 1.2 Component and residue classification

## Purpose

对当前 target 的一个已确定 structure model 完成：

- chain / component / residue classification；
- standard / nonstandard / solvent / ion 等 topology class 判断；
- possible connection / coordination relation 检查；
- 必要的人工关系确认；
- stable component / residue / endpoint / relation identity 物化；
- 下游 `classification_result.yaml` 构建与 validation。

1.2 不修改结构坐标，也不决定 1.3 要保留哪些研究对象。

科学分类语义由：

`references/classification_rules.md`

拥有。字段和机器校验约束位于 `schemas/`。确定性 helper 的 CLI / module boundary 见 `scripts/README.md`。

## Object requirements

当前对象至少需要：

- 一个现有 PDB、PDBx/mmCIF 或 AlphaFold 3 CIF；
- 当前 source format；
- 如果结构含多个 model：明确 `selected_model_id`；
- 当前 classification mode；
- 实际适用的项目 residue definitions、force-field references、CCD references、sequence references 和 relation definition files。

如果存在多个 model 且用户尚未选择，先识别 model scope 并向用户确认。在 model 唯一确定前不得进入完整分类。

## Reuse conditions

开始 1.2 时，在 `project_result_index.md` 中检索已有正式 `classification_result.yaml`。

只有以下条件都明确等价且旧结果有效时才自动复用：

1. 旧结果 `result_status: COMPLETE`；
2. source structure SHA-256 相同；
3. `selected_model_id` 相同；
4. `classification_mode` 相同；
5. 影响分类的 reference set 等价；
6. reference 等价性可由旧 `reference_manifest.yaml` 与当前实际参考核验；
7. 影响 relation classification 的人工决定与当前任务要求一致；
8. 用户没有明确要求重新分类、重新检查、换参考或生成对照结果。

明确不等价时直接重新执行；缺少证明等价所需的信息时向用户确认。

确认复用时直接引用来源任务结果，不复制结果，也不创建当前任务空目录。

## Work directory

基础目录：

```text
<project_root>/01_structure_preparation/02_component_and_residue_classification/
```

需要本地执行时创建：

```text
<project_root>/01_structure_preparation/02_component_and_residue_classification/<task_id>/
```

不同 Task ID 不共享可变 observations、relation decisions 或 final result。

## Preflight

确认需要执行新的 1.2 后，先检查：

- structure 是可读的普通文件，SHA-256 可计算；
- source format 可识别；
- selected model 与结构实际 model 一致；
- 当前 work directory 属于本 Task；
- 需要的 references / definitions 可读；
- `FORCE_FIELD_ANALYSIS` 模式下目标 force-field root 有效；
- Python 依赖满足 `scripts/requirements.txt`；
- 输出不会覆盖其他 Task 的正式结果。

技术 preflight 失败时当前 1.2 保持 `未完成`，不得留下可误认作 COMPLETE 的正式结果。

## Execution guidance

### 1. Model scope

确定当前 structure 实际包含哪些 model。当前 deterministic helper：

```bash
python scripts/inspect_model_scope.py \
  --structure <structure> \
  --structure-sha256 <sha256> \
  --source-format <PDB|MMCIF|AF3_CIF> \
  --output <task_work_directory>/model_scope.yaml
```

单 model 可以直接绑定；多 model 未选择时停止并向用户确认。

### 2. Baseline classification

依据 `references/classification_rules.md` 及当前 references 建立 baseline observations。

当前确定性实现：

```bash
python scripts/classify_structure.py --config <classification_config.yaml>
```

主要工作结果包括：

```text
classification_observations.yaml
reference_manifest.yaml
```

`reference_manifest.yaml` 必须忠实记录实际使用的参考来源及可复核 identity / hash；不要把未实际使用的 reference 填入 manifest。

Agent 可以直接读取结构与参考资料进行开放式科学判断；deterministic scripts 用于需要稳定 parsing、ID、schema 和文件写入的部分，不作为理解输入的许可层。

### 3. Relation checks

按实际适用定义检查 possible connections 和 possible coordination。

当前确定性实现：

```bash
python scripts/check_possible_connections.py --config <possible_connections_check_config.yaml>
python scripts/check_possible_coordination.py --config <possible_coordination_check_config.yaml>
```

每类 check 应产生独立 result，并同步更新当前 `classification_observations.yaml`。未提供某类关系定义时可以形成明确 `NOT_PERFORMED`，不能伪造 COMPLETED。

### 4. User decisions

如果 relation check 产生多个合理解释或需要科学确认的关系，当前用户可见 Agent 向用户确认。

确认结果写入当前 Task 的 `relation_decisions.yaml`，并重新运行受影响的 relation check，使 observations 与决定一致。

当前稳定 writer：

```bash
python scripts/record_relation_decisions.py --config <relation_decision_record_config.yaml>
```

不得只记录用户决定而不把它同步回当前 observations / final result。

### 5. Final result

所有必要 relation stages 闭合后构建最终下游结果：

```bash
python scripts/build_classification_result.py --config <classification_result_build_config.yaml>
```

最终构建使用当前 observations，不在 final build 阶段重新猜 relation 或 topology effect。

1.3 直接消费最终 `classification_result.yaml` 中已经物化的 opaque component / residue / endpoint / relation IDs；不得在 1.3 重新复刻 ID 算法。

## Validation requirements

1.2 只有同时满足以下条件才可标记为 `已完成`：

- selected model 已唯一确定；
- 输入 structure 执行前后 SHA-256 不变；
- baseline observations 与实际 structure / references 一致；
- 所有适用 relation checks 已明确 `COMPLETED` 或 `NOT_PERFORMED`；
- blocking user decisions 已解决并同步到 observations；
- `reference_manifest.yaml` 与实际 references 一致；
- `classification_result.yaml` 通过当前 schema，且 `result_status: COMPLETE`；
- `classification_report.md` 与最终 result 一致；
- 输出全部位于当前 Task 专属目录；
- 没有生成或依赖 Legacy subagent / route / event / Workstream records。

如果仍需 model / classification / relation 确认，Task Sheet 中 1.2 保持 `未完成`。

## Official results

实际执行新的 1.2 时，正式结果至少包括：

```text
classification_result.yaml
reference_manifest.yaml
classification_report.md
```

如果实际使用人工 relation decisions，再额外形成正式结果：

`relation_decisions.yaml`

项目级正式结果索引：

```text
<project_root>/00_project_records/project_result_index.md
```

只登记以下两个 1.2 结果的完整绝对路径及简明说明：

```text
classification_result.yaml
reference_manifest.yaml
```

`classification_report.md` 与 `relation_decisions.yaml` 保持为当前 Task 的正式结果，但不单独登记为 project-level result entry。

以下属于当前 Task 的内部执行 / 诊断材料，不默认作为 project-level official result 单独登记：

```text
model_scope.yaml
classification_observations.yaml
relation_checks/**
confirmation_requests.yaml
logs/**
```

## Current local files

```text
SKILL.md
references/
  classification_rules.md
  residue registries / CCD references
schemas/
scripts/
  README.md
  requirements.txt
  deterministic helpers
```

不在本 Skill 目录保留 Legacy `subagent_result` builder、runtime dependency projection 或 role-taxonomy compatibility files。
