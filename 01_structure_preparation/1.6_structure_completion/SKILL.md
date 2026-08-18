---
name: structure_completion
description: 结构准备 1.6。按每个 target 的正式 structure_completeness_report.yaml 落实已确认的结构修复，完成缺失残基/重原子补全、confirmed extra atom 删除和 confirmed atom-name correction，并验证形成新的重原子结构与 completion report。
---

# Purpose

完成结构准备 `1.6 Structure completion`。

本 Skill 将 `structure_completeness_report.yaml` 中已明确的 structure repair items 落实到当前 retained target structure，得到完成这些修复后的重原子结构。

每个 target 独立处理、独立验证、独立形成正式结果。

# Inputs / evidence

对每个 target，至少需要：

- 1.5 正式 `structure_completeness_report.yaml`；
- 该报告 `structure` 指向的当前 target PDB；
- 对 confirmed atom-name mismatch，1.5 报告所引用的上游正式证据中已经确认的 atom-name correspondence；
- 对实际存在的 missing-residue / missing-heavy-atom repair item，可用于提供补全坐标的 reference structure / coordinate template。

优先从 `structure_completeness_report.yaml` 已登记的 `source_reports` 定位需要追溯的上游 identity / mapping evidence，不为 1.6 重新建立一套上游结果接口。

如果当前 repair items 只包含 confirmed extra-atom deletion 或 confirmed atom-name correction，不要求为了形式完整额外提供 AF3 / CCD coordinate reference。

# Repair scope

当前 repair set 只来自 `structure_completeness_report.yaml`。Coordinate reference / template 用于获得补全坐标，不改变 report 已经确定的 repair scope。

1.6 不重新执行 completeness diagnosis，也不根据 AF3、CCD 或其它模板自行增加新的 missing / extra / mismatch item。

如果报告中的某个 atom-name mismatch 不能定位到已经确认的 observed → reference atom-name correspondence，不自行猜测 rename；该 item 保持 unresolved，直到现有证据能够确认或用户作出确认。

# Reuse

进入当前 target 后，先检查是否需要本地执行。

如果 `structure_completeness_report.yaml` 没有任何属于 1.6 的 repair item，则不创建 1.6 task-specific execution directory，也不生成空的 completion results；由当前 Task Execution Agent 按 Stage 1 dynamic-plan 规则处理该任务项。

已有 1.6 正式结果只有在以下内容均明确等价时才自动复用：

- 输入 PDB 内容相同；
- 1.5 `structure_completeness_report.yaml` 内容相同；
- 实际影响结果的 completion reference / coordinate template 相同；
- 影响结果的用户决定相同；
- 既有 `completion_validation.md` 为 `PASS`；
- 既有正式结果仍存在且未被改变。

文件内容 / hash 比仅比较路径或文件名更可靠。只比较实际影响既有结果的 reference；新增一个从未参与旧结果的候选 reference 本身不自动使 reuse 失效。

用户明确要求重做、重新比较 reference 或建立对照时，不自动复用。

复用时直接引用既有正式结果，不为了当前任务复制一份结果或创建空目录。

# Execution guidance

## 1. 建立当前 repair set

从 1.5 report 中提取当前 target 需要落实的 repair items，并能够定位到当前 PDB 的明确 residue / atom identity。

按以下固定顺序处理：

```text
confirmed extra atom deletion
→ confirmed atom-name correction
→ missing-residue completion
→ missing-heavy-atom completion
→ final atom-serial renumbering
```

如果一个 unexpected atom 已经属于 confirmed atom-name correspondence，不把它同时当作 extra atom 删除。

## 2. Confirmed extra atoms

只删除 1.5 repair scope 中已经确认属于 extra atom 的原子。

删除前核对当前 PDB 中的 chain / residue / atom identity 与 repair item 一致。不要因为模板中不存在某个原子就自行把它追加到 deletion scope。

## 3. Confirmed atom-name corrections

只执行已经确认的 observed atom name → reference atom name 对应关系。

Rename 保留原坐标及原 residue identity，只修改已确认需要修改的 atom name。

## 4. Missing residues

只要当前 repair set 含 missing residue，按需读取：

`references/missing_residue_completion.md`

该 reference 拥有 AF3 residue correspondence、local alignment、internal / terminal missing-region handling、multiple-reference comparison、coordinate transplant 和局部几何判断的详细规则。

## 5. Missing heavy atoms

只要当前 repair set 含 missing heavy atom，按需读取：

`references/missing_heavy_atom_completion.md`

该 reference 拥有 coordinate-template correspondence、shared-heavy-atom alignment、coordinate transplant、必要时按 missing-residue 方法处理整个 residue，以及局部几何判断的详细规则。

## 6. Final write

所有已经确定的 edits / transplanted coordinates 应作用于当前 target 的工作副本；不得覆盖 1.5 实际检查的输入 PDB。

最终结构保持 target 自己的 chain / residue identity。Reference structure 的 chain ID、residue number 或 atom serial 不得直接替代 target identity。

完成所有修复后，按最终写入顺序将 atom serial 连续、唯一地重新编号，并生成 `completed_structure.pdb`。

执行中保留足以支持结构写入、`completion_report.yaml` 和 validation 的 correspondence、actual reference、alignment / anchor、transplanted identity、geometry evidence 与必要 warning。除两个 method reference 明确要求的信息外，不要求为普通中间过程建立固定命名文件。

# Completion report

每个 target 的 `completion_report.yaml` 记录 1.6 实际落实的修改，不复制 1.5 的诊断过程。

最低组织要求：

```yaml
target_id: target_001
input_structure: /absolute/path/to/input.pdb
source_completeness_report: /absolute/path/to/structure_completeness_report.yaml
output_structure: /absolute/path/to/completed_structure.pdb

removed_atoms:
  - chain_id: A
    resid: 25
    residue_name: LEU
    atom_name: <atom_name>

renamed_atoms:
  - chain_id: A
    resid: 30
    residue_name: <residue_name>
    observed_atom_name: <old_name>
    reference_atom_name: <new_name>

added_residues:
  - chain_id: A
    residues:
      - resid: 101
        residue_name: GLY
      - resid: 102
        residue_name: SER
    coordinate_reference: /absolute/path/to/reference_structure
    repair_adjustment: <only when applicable>

added_heavy_atoms:
  - chain_id: A
    resid: 125
    residue_name: ARG
    atom_names: [<atom_name>, ...]
    coordinate_reference: /absolute/path/to/reference_or_component_file

unresolved_items: []
```

这里的 YAML 定义正式结果的最低组织要求，不要求建立额外 rigid schema。

规则：

- `input_structure`、`source_completeness_report`、`output_structure` 和实际使用的 `coordinate_reference` 使用完整绝对路径；
- 连续 missing residues 可以在一个 `added_residues` record 中成组记录，但每个实际新增 residue 的 `resid + residue_name` 必须明确；
- deletion / rename 不重复复制 1.5 的 reference provenance；
- completion operation 记录实际提供坐标的 reference / template；比较过但未用于最终坐标的候选 reference 不需要写入正式 completion report；
- 如果原 missing-heavy-atom item 因局部共同重原子不足而改按 missing-residue 方法处理，在对应 `added_residues` record 中记录：

```yaml
repair_adjustment: insufficient shared-heavy-atom anchors; treated as missing residue
```

- `unresolved_items` 只记录当前 repair scope 内未能完成的 item 及原因；用户明确改变当前 repair scope 不伪装成 unresolved item。

# Validation

Validation 属于 1.6 结果 owner。对当前 target 完成以下核验，并写入 `completion_validation.md`：

- 1.5 每个 required repair item 都已闭合：missing residue 已位于正确 target chain / residue identity，missing heavy atom 已存在，confirmed extra atom 已删除，confirmed atom-name mismatch 已按确认关系修改；
- `completion_report.yaml` 与 `completed_structure.pdb` 的实际修改一致；
- 除 report repair scope 以及 method reference 明确要求的整 residue replacement 外，没有未记录的额外删除、rename 或 coordinate replacement；
- 新增 residue / heavy atom 满足对应 method reference 的 correspondence、alignment 和局部 geometry requirements；
- 不存在重复 residue / atom identity；
- atom serial 连续且唯一；
- PDB 可正常解析；
- 没有加入本阶段后续才应处理的 final H；
- `unresolved_items` 为空。

Validation conclusion 只使用：

```text
PASS
FAIL
```

warning 独立记录；warning 本身不自动把 `PASS` 改成第三种状态。

以下情况属于 blocking failure：required repair 未解决、target identity 错误、必要 reference correspondence 不可靠、missing-residue completion 不能满足其 required alignment / junction conditions、明显不合理的局部连接或 severe steric clash、duplicate identity、PDB 无法解析、atom serial 不连续/不唯一、错误加入 final H，或 `unresolved_items` 非空。

Validation 不重新做一次 1.5 completeness diagnosis。

# Official results

只有 validation 为 `PASS` 且 `unresolved_items` 为空时，当前 target 的 1.6 才完成。

每个 target 的正式结果位于：

```text
<project_root>/01_structure_preparation/06_structure_completion/<task_id>/<target_id>/
├── completed_structure.pdb
├── completion_report.yaml
└── completion_validation.md
```

执行失败时可以保留必要工作材料用于排查，但不得把未通过 validation 的结构登记成 1.6 正式结果。

# Project result registration

当前 target 通过 validation 后，将以下两个正式结果的完整绝对路径登记到：

```text
<project_root>/00_project_records/project_result_index.md
```

登记白名单：

```text
completed_structure.pdb
completion_report.yaml
```

登记时提供简短说明，使后续执行能够知道这是 Stage 1.6 对当前 target 完成既定 structure repair items 后的正式结构与修改报告。

`project_result_index.md` 的内部组织格式由项目级 record owner 管理，本 Skill 不重新定义。

# References

按实际 repair item 读取：

```text
references/missing_residue_completion.md
→ missing-residue coordinate completion

references/missing_heavy_atom_completion.md
→ missing-heavy-atom coordinate completion
```

不要在当前 target 不涉及对应 repair type 时预读或执行相应方法。

# User confirmation

如果 repair scope 已经明确，但当前可用 evidence 仍不足以唯一建立 required reference correspondence、缺少可用 coordinate reference，或多个可行方案之间存在会影响结构正确性的实质科学歧义，向用户说明当前对象、现有证据和具体歧义后确认。

确认前不通过猜测扩大 repair scope，也不发布可误认作完成状态的正式结果。
