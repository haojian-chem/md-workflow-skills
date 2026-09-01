---
name: protein_protonation_assignment
description: Structure preparation 1.7。针对当前蛋白重原子结构，在明确 target pH 与目标 protein force field / protonation naming convention 后，使用 PROPKA predicted pKa 与局部化学环境两类平级证据完成 Asp、Glu、His protonation assignment；每个 1.7 local target 独立记录 target lineage，并允许明确的 alternative protonation strategy 形成独立分支。
---

# Purpose

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

涉及 residue-name modification 对原子定位信息的更新时同时读取：

`../../references/atom_mapping_rules.md`

本 Skill 仅补充 1.7-specific 的对象、执行、validation 与 results 规则；本步骤明确每次重新执行，不做既有 1.7 结果的 reuse assessment。

完成 Structure preparation `1.7 Protein protonation assignment`。

本 Skill 对当前需要处理的蛋白质 heavy-atom structure：

- 运行 PROPKA 获得 predicted pKa；
- 独立完成 Henderson–Hasselbalch assessment；
- 独立完成 local chemical environment assessment；
- 综合两类平级证据，对 Asp / Glu / His 完成 protonation assignment；
- 将最终 assignment 映射为目标 protein force field / protonation naming convention 对应的 residue name；
- 生成 protonation-assigned heavy-atom structure、assignment report、与输出结构对应的 atom map 和 validation result；
- 为每个 actual 1.7 local target 建立独立 target record。

# Target object and lineage

每个 actual 1.7 execution object 都是当前 1.7 自己的 local target，并按 shared target-lineage 规则建立：

```text
targets/target_xxx.yaml
```

`source_target_records` 指向实际形成当前 1.7 target 的上游 target record。正常路径通常来自 1.6；如果 1.6 因无 repair 等原因未形成 execution target，则使用实际提供当前 heavy-atom structure / object state 的上游 target record，例如对应 1.5 / 1.4 target。

当前 1.7 `target_id` 不继承上游编号。

如果同一个 source target 在当前科学问题中需要保留多个 alternative protonation assignments 作为后续独立比较对象，则为每个 alternative 建立独立 1.7 target record；多个 current targets 可以共同引用同一个 source target record，从而形成 branch。

不因为某 residue 有多个理论 protonation state 就自动展开所有组合。只有当前 Task Sheet / 用户明确要求保留 alternatives，或当前科学设计本身要求并行比较时才建立多分支。

# Inputs / evidence

对每个 actual 1.7 target，至少需要：

- 当前 1.7 工作项实际采用的有效 heavy-atom structure；
- 与该输入结构对应的最近正式 atom map；
- 当前 1.7 target record；
- 明确的 `target_pH`；
- 当前使用的 protein force field，或明确的 protonation-state residue naming convention；
- 可执行 PROPKA；
- 当前科研任务中与 protonation 判断有关、已经确认且可追溯的 chemical relation / structural evidence。

当前结构只需要是当前科研任务已经认可、足以支持 protonation assignment 的 heavy-atom structure；本 Skill 不要求它必须来自某一个固定的上游 Step，也不要求对应结构处理必须出现在当前 Task Sheet，但 atom map 必须与该输入结构实际对应，target record 必须能沿 `source_target_records` 追溯实际 source target(s)。

如果 `target_pH` 或 protein force field / protonation naming convention 尚未明确：

- 当前 Agent 先从当前 Task Sheet、同一科研任务明确引用的前序 Task Sheet、已有正式项目记录 / 日志、当前对话上下文和用户既有决定中确认；
- 已有信息能够唯一确定时直接使用，不重复询问；
- 仍不能确定时向用户确认；
- 不自行假设默认 pH 或默认 protein force field。

需要 coordination、bonding 或其他 relation evidence 时，消费当前科研任务已经确认的正式信息，不在 1.7 重新建立外部分类或 relation 规则。

# Processing scope

当前 protonation-assignment scientific scope：

- Asp；
- Glu；
- His。

Asp / Glu 对一个 carboxyl protonation state 做判断。

His 分别判断 `ND1` 与 `NE2` 两个位点的 protonation state，再由两个 site assignments 得到最终 His protonation state。

# Execution guidance

进入当前 actual 1.7 target 后，直接基于当前输入重新执行 1.7；每次重新运行 PROPKA 并重新完成 protonation assignment，不进行既有 1.7 结果的 reuse assessment。

## 1. Run PROPKA

对完整的当前适用蛋白质结构运行 PROPKA，不为了 1.7 的 Asp / Glu / His assignment scope 而先裁掉其余蛋白环境。

PROPKA 在本 Skill 中提供 predicted pKa evidence；其输出不直接等同于最终 residue naming decision。

保留本次 PROPKA 输出及必要运行信息作为 task execution material。正式 `protonation_assignment_report.yaml` 只记录支持最终判定所需的 predicted pKa，不复制 PROPKA 原始输出结构。

## 2. Evaluate every residue in scope

对当前结构中属于 Asp / Glu / His scientific scope 的每一个 residue 都形成独立 assignment record，无论最终 residue name 是否发生变化。

具体科学判据读取：

`references/protonation_assignment_rules.md`

每个 residue 至少完成：

```text
predicted pKa evidence
+ Henderson–Hasselbalch assessment
+ local chemical environment assessment
→ final protonation assignment
→ target-force-field residue-name mapping
```

如果 PROPKA 对某个 residue 没有给出可用 predicted pKa：

- 该 residue 的 Henderson–Hasselbalch assessment 记为 `UNAVAILABLE`；
- 不用默认溶液 pKa 补值；
- local chemical environment assessment 仍独立进行。

## 3. Resolve scientific ambiguity / branch when explicitly required

如果两类证据都不足以形成可靠结论，或两类明确 evidence 相互冲突且 Agent 复核实际 evidence 后仍不能可靠解决，则向用户确认。

确认时说明当前 residue identity、predicted pKa / target pH、两类 assessment 及具体冲突或不确定性。

默认目标仍是为当前 1.7 target 形成一个明确 assignment；assignment 未闭合时不发布该 target 的完成结果。

如果用户决定将多个可行 assignment 作为不同后续研究策略保留，而不是只选一个，则：

- 当前 source target 派生多个 1.7 local targets；
- 各 target record 的 `source_target_records` 指向同一 source target record；
- 每个 target 分别生成独立 structure / map / assignment report / validation；
- 不在一个 target report 中把 mutually exclusive final assignments 同时当成完成结果。

## 4. Map assignment to residue naming

根据当前 protein force field / protonation naming convention，将最终 protonation assignment 映射成合法 residue name。

如果当前 naming convention 不能明确表示已经确定的 protonation state，不自行发明 residue name；向用户确认 representation 后再继续。

## 5. Write structure

将最终 residue-name assignment 写入当前 heavy-atom structure 的工作副本，并生成：

`protonation_assigned_structure.pdb`

本步骤允许的结构修改仅为 residue-name modification。

写出前保持：

- heavy-atom set 不变；
- atom names 不变；
- coordinates 不变；
- residue / atom order 不变；
- 不加入 final H。

## 6. 维护 atom map

以输入 heavy-atom structure 对应的正式 atom map 为基础，按 `../../references/atom_mapping_rules.md` copy-and-update，生成：

`atom_mapping.yaml`

文件级：

- `target_record` 指向当前 1.7 target record；
- `input_map` 指向实际使用的上游 map。

逐原子：

- 所有 atom records 保留；
- `original_atom_serial`、`component_id + residue_id` 和既有 `operations` 不改写；
- `current_atom_serial` 与输出 PDB 实际 serial 保持一致；
- 对 residue name 实际发生变化的 residue，其全部 atom records 追加 `1.7RENAME`；
- residue name 未发生变化的 residue 不追加 operation。

# Protonation assignment report

每个 actual 1.7 target 生成固定格式的：

`protonation_assignment_report.yaml`

报告覆盖当前处理范围内的全部 Asp / Glu / His。正式结构如下：

```yaml
target_id: target_001

references:
  target_record: /absolute/path/to/07_protein_protonation_assignment/T005/targets/target_001.yaml

input_structure: /absolute/path/to/input.pdb
input_atom_mapping: /absolute/path/to/input_atom_mapping.yaml
output_structure: /absolute/path/to/protonation_assigned_structure.pdb
output_atom_mapping: /absolute/path/to/atom_mapping.yaml

target_pH: 7.0
protein_force_field: <force-field-name>
protonation_naming_convention: <naming-convention-or-reference>
hh_delta_threshold: 1.0

residues:
  - chain_id: A
    resid: 83
    original_residue_name: ASP
    residue_type: ASP

    propka_pka: 4.1

    henderson_hasselbalch_assessment:
      delta_pka_ph: -2.9
      judgment: DEPROTONATED

    local_environment_assessment:
      sites:
        carboxyl:
          judgment: DEPROTONATED
          evidence:
            - type: SALT_BRIDGE_OR_CHARGE_COMPENSATION
              description: <concise evidence description>

    final_assignment:
      sites:
        carboxyl: DEPROTONATED
      protonation_state: DEPROTONATED
      final_residue_name: ASP

  - chain_id: A
    resid: 57
    original_residue_name: HIS
    residue_type: HIS

    propka_pka: 6.8

    henderson_hasselbalch_assessment:
      delta_pka_ph: -0.2
      judgment: BORDERLINE

    local_environment_assessment:
      sites:
        ND1:
          judgment: PROTONATED
          evidence:
            - type: HYDROGEN_BOND
              description: <concise evidence description>
        NE2:
          judgment: DEPROTONATED
          evidence:
            - type: METAL_COORDINATION
              description: <concise evidence description>

    final_assignment:
      sites:
        ND1: PROTONATED
        NE2: DEPROTONATED
      protonation_state: NEUTRAL_ND1_PROTONATED
      final_residue_name: <force-field-specific-name>
```

固定字段语义：

- `target_id` 只在当前 1.7 工作项内定位 local target；
- `references.target_record` 记录当前 1.7 target record 完整绝对路径；上游分支沿其 `source_target_records` 追溯；
- `input_structure`、`input_atom_mapping`、`output_structure`、`output_atom_mapping` 均记录完整绝对路径；
- `protein_force_field` 记录当前实际使用的 protein force field；如果当前科研任务只明确提供独立 protonation naming convention、并未确定具体 protein force field，则写 `null`；
- `protonation_naming_convention` 记录最终 residue-name mapping 的实际依据；如果直接使用已命名 protein force field 的默认命名规则，则写 `force_field_default`，否则记录实际 convention / reference；
- `residue_type` 使用 `ASP | GLU | HIS` 表示当前 scientific object class；
- `propka_pka` 为 PROPKA predicted pKa；没有可用值时写 `null`；
- `hh_delta_threshold` 记录本次实际采用的 `|pKa - pH|` 默认/指定阈值；默认值为 `1.0`；
- `henderson_hasselbalch_assessment.judgment` 使用 `PROTONATED | DEPROTONATED | BORDERLINE | UNAVAILABLE`；`UNAVAILABLE` 时 `delta_pka_ph: null`；
- Asp / Glu 的 `local_environment_assessment.sites` 与 `final_assignment.sites` 使用 `carboxyl`；
- His 使用 `ND1` 与 `NE2`；
- local-environment site `judgment` 使用 `PROTONATED | DEPROTONATED | INCONCLUSIVE`；
- `evidence` 为列表；没有支持当前 site judgment 的具体 evidence 时使用空列表；
- evidence `type` 使用以下值之一：

```text
METAL_COORDINATION
COVALENT_OR_SPECIAL_STATE
PROJECT_SPECIFIC_EVIDENCE
SALT_BRIDGE_OR_CHARGE_COMPENSATION
BURIAL_OR_DESOLVATION
HYDROGEN_BOND
SOLVENT_EXPOSURE
OTHER
```

- Asp / Glu 的 `final_assignment.protonation_state` 使用 `PROTONATED | DEPROTONATED`；
- His 的 `final_assignment.protonation_state` 使用：

```text
NEUTRAL_ND1_PROTONATED
NEUTRAL_NE2_PROTONATED
POSITIVELY_CHARGED
```

正式 report 不增加可由现有字段直接推导的 `rename_required`、`changed` 或 confidence-score 字段。

# Validation

Validation 属于 1.7 result owner，并在 assignment 已经闭合、结构、map 与 report 已写出后执行。

只检查以下五类结果属性：

1. **Target lineage**
   - current target record 存在且 `target_id` 与当前 1.7 local target 一致；
   - `source_target_records` 与实际 source target(s) 一致；
   - report `references.target_record` 与 output map `target_record` 指向同一 current target record。

2. **结果完整性**
   - 当前处理范围内的全部 Asp / Glu / His 都有 assignment record；
   - report 中的 residue identity 与输出结构可逐 residue 对应。

3. **改名正确性**
   - `final_residue_name` 与 final protonation assignment 一致；
   - `final_residue_name` 符合当前 protein force field / protonation naming convention；
   - `protonation_assigned_structure.pdb` 中的实际 residue name 与 report 一致。

4. **结构未被意外修改**
   - 除 residue-name modification 外，输入与输出的 heavy-atom set、atom names、coordinates、residue / atom order 均一致；
   - 未加入 final H。

5. **atom map 正确维护**
   - 输出 PDB 每个 `ATOM / HETATM` 恰有一条 map record，map 无额外 atom record；
   - `original_atom_serial`、`component_id + residue_id` 和既有 operation history 与 input map 一致；
   - 只有 residue name 实际变化的 residue atoms 新增 `1.7RENAME`；
   - 输出 map 的 `current_atom_serial` 与输出 PDB 一致。

Validation conclusion 使用：

```text
PASS
FAIL
```

结果写入：

`protonation_validation.md`

Validation 不修改结构、atom map、target record 或 assignment report。

# Official results

当前 Task Sheet 的 1.7 工作目录使用：

```text
<project_root>/01_structure_preparation/07_protein_protonation_assignment/<task_id>/
├── targets/
│   ├── target_001.yaml
│   ├── target_002.yaml
│   └── ...
├── target_001/
│   ├── protonation_assigned_structure.pdb
│   ├── atom_mapping.yaml
│   ├── protonation_assignment_report.yaml
│   └── protonation_validation.md
└── ...
```

这里的 `<task_id>` 是当前 Task Sheet 的 `Txxxx` 标识。

只有 validation 为 `PASS` 时，当前 1.7 local target 的正式结果才完成。

# Project result registration

当前 target 通过 validation 后，将以下两个正式结果的完整绝对路径登记到：

`<project_root>/00_project_records/project_result_index.md`

登记白名单：

```text
protonation_assigned_structure.pdb
protonation_assignment_report.yaml
```

`atom_mapping.yaml` 不单独登记，由 `protonation_assignment_report.yaml.output_atom_mapping` 定位；`protonation_validation.md` 保留为当前 target 的正式结果，但不单独登记为 project-level result entry；target record 不因为创建而单独登记。

`protonation_assignment_report.yaml.references.target_record` 提供当前 1.7 local target 的正式跨 Skill引用，后续需要 ancestry 时沿 target record 的 `source_target_records` 追溯。

`project_result_index.md` 的内部组织格式由项目级 record owner 管理，本 Skill 不重新定义。

# Reference

需要执行具体 protonation 判断时读取：

`references/protonation_assignment_rules.md`

该 reference 拥有：

- Asp / Glu / His site semantics；
- Henderson–Hasselbalch default threshold；
- local chemical environment evidence；
- 两类平级 evidence 的综合判定规则。
