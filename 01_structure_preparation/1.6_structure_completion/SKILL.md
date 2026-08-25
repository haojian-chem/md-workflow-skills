---
name: structure_completion
description: 结构准备 1.6。根据每个 target 的正式 structure_completeness_report.yaml 落实已确认的结构修复，完成 confirmed extra atom 删除、confirmed atom-name correction、缺失重原子与缺失残基补全，并验证形成新的重原子结构与 completion report。
---

# Purpose

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

涉及 atom 删除、atom-name correction、重原子/残基新增和 serial 重编号时同时读取：

`../../references/atom_mapping_rules.md`

本 Skill 仅补充 1.6-specific 的对象、reuse / execution assessment、执行、validation 与 results 规则。

完成结构准备 `1.6 Structure completion`。

本 Skill 将 `structure_completeness_report.yaml` 中已明确的 structure repair items 落实到当前 retained target structure，得到完成这些修复后的重原子结构。

每个 target 独立处理、独立验证、独立形成正式结果。

# Inputs / evidence

对每个 target，至少需要：

- 1.5 正式 `structure_completeness_report.yaml`；
- `structure_completeness_report.yaml` 中 `structure` 字段记录的当前 target PDB；
- 对 confirmed atom-name mismatch，1.5 报告所引用的上游正式证据中已经确认的 atom-name correspondence；
- 对实际存在的 missing-heavy-atom / missing-residue repair item，可用于提供补全坐标的 reference structure / coordinate template。

需要追溯上游 identity / mapping evidence 时，优先使用 `structure_completeness_report.yaml` 中 `source_reports` 字段记录的正式结果路径，不为 1.6 重新建立上游结果接口。

当前 repair items 只有 deletion / rename 时，不要求额外提供 AF3 / CCD coordinate reference。

# Repair scope

当前 repair set 只来自 `structure_completeness_report.yaml`。Coordinate reference / template 只用于获得补全坐标，不改变报告已经确定的 repair scope。

如果某个 atom-name mismatch 无法从已有正式 evidence 中定位到已确认的 observed → reference atom-name correspondence，不自行猜测 rename；该 item 保持 unresolved，直到现有 evidence 或用户确认足以确定对应关系。

# Reuse / execution assessment

进入当前 target 后，先判断是否需要本地执行。

如果 `structure_completeness_report.yaml` 中没有需要 1.6 处理的 repair item：

- 不创建 1.6 task-specific execution directory；
- 不生成空的 completion results；
- 向当前任务执行上下文返回 `已终止`，并说明原因是 1.5 未发现需要 1.6 处理的 repair item。

已有 1.6 正式结果只有在以下内容均明确等价时才自动复用：

- 输入 PDB 内容相同；
- 1.5 `structure_completeness_report.yaml` 内容相同；
- 实际影响结果的 completion reference / coordinate template 相同；
- 影响结果的用户决定相同；
- 既有 `completion_validation.md` 为 `PASS`；
- 既有正式结果仍存在且内容未被改变。

判断文件是否相同时，优先比较内容 / hash，而不是只比较路径或文件名。只比较实际影响既有结果的 reference；新增一个从未参与旧结果的候选 reference，本身不自动使 reuse 失效。

用户明确要求重做、重新比较 reference 或建立对照时，不自动复用。

复用时直接引用既有正式结果，不复制结果，也不创建空目录；向当前任务执行上下文返回 `已终止`、复用原因以及实际复用的正式结果路径。

# Execution guidance

## 1. 建立当前 repair set

从 1.5 report 中提取当前 target 需要落实的 repair items，并确保每个 item 都能定位到当前 PDB 中明确的 residue / atom identity。

总体处理顺序：

```text
confirmed extra atom deletion
→ confirmed atom-name correction
→ missing-heavy-atom processing
   ├─ atom-level anchors sufficient
   │  → complete the listed missing heavy atoms
   └─ atom-level anchors insufficient
      → treat that repair item as whole-residue completion
      → merge with adjacent missing-residue region when applicable
→ missing-residue completion
   (original missing residues + items adjusted from missing-heavy-atom handling)
→ final atom-serial renumbering
```

这里的 whole-residue treatment 只是同一 repair item 的处理方式调整，不是新增 repair scope。

如果某个 unexpected atom 已经属于 confirmed atom-name correspondence，不再把它同时作为 extra atom 删除。

## 2. Confirmed extra atoms

只删除当前 repair scope 中已经确认属于 extra atom 的原子。删除前核对当前 PDB 中的 residue / atom identity 与 repair item 一致。

## 3. Confirmed atom-name corrections

只执行已经确认的 observed atom name → reference atom name 对应关系。Rename 只修改 atom name，保留原坐标和 residue identity。

## 4. Missing heavy atoms

当前 repair set 含 missing heavy atom 时，读取：

`references/missing_heavy_atom_completion.md`

先按该 reference 判断当前 residue 是否满足 atom-level completion 所需的 shared-heavy-atom correspondence 与 alignment 条件。

- 满足要求：按 atom-level 方法补入 report 已列出的 missing heavy atoms；
- 不满足要求：不强行 transplant atom，将该 repair item 改按完整 residue completion 处理，并纳入下一步的 residue-level completion set。

如果这种处理方式调整后的 residue 与原有 missing residues 在 target polymer 的实际 residue order 上连续，应作为同一个连续 completion region 处理，而不是先后独立补全。不能仅因为重新编号后的 `resid` 数值相邻就判定为连续。

## 5. Missing residues

只要 residue-level completion set 非空，就读取：

`references/missing_residue_completion.md`

该集合包括：

- `structure_completeness_report.yaml` 原本列出的 missing residues；
- 因 missing-heavy-atom anchor 不足而改按完整 residue completion 处理的 residue。

对 residue-level completion items，先按照 target polymer 的实际 residue order 合并真正连续的 completion region，再按 reference 中的 residue correspondence、local alignment、internal / terminal handling、multiple-reference comparison、coordinate transplant 和局部 geometry judgment 规则处理。

## 6. Final write

所有已经确定的 edits / transplanted coordinates 都作用于当前 target 的工作副本，不覆盖 1.5 实际检查的输入 PDB。

最终结构沿用 target 自身的 chain / residue identity。Reference structure 中的 chain ID、residue number 和 atom serial 只用于定位 reference coordinates，不直接写入最终 target identity。

完成所有修复后，按最终写入顺序将 atom serial 连续、唯一地重新编号，并生成 `completed_structure.pdb`。

执行期间保留足以支持结构写入、`completion_report.yaml` 和 validation 的 correspondence、实际使用的 reference、alignment / anchor、transplanted identity、geometry evidence 以及必要 warning。普通中间过程不要求生成固定命名文件。

# Deterministic helpers

本 Skill 提供两个可选 deterministic helper：

```text
scripts/transplant_coordinates.py
→ 根据 Agent 已确定的 correspondence / alignment atoms 执行 rigid-body alignment
→ 输出 transformed heavy-atom coordinates 与机械 fit evidence

scripts/apply_structure_edits.py
→ 应用 Agent 已确定的 remove / rename / add / replace operations
→ 写出最终 PDB 并连续重编号 atom serial
```

需要使用 helper 时先读：

`scripts/README.md`

该文件定义两个脚本的 CLI、输入/输出数据格式和衔接方式。当前不为这些 task-local working data 另建 rigid schema。

Helper 只执行确定性操作，不替代科学判断。Reference 选择、residue correspondence、anchor 选择、reference comparison、repair-type adjustment 和最终 validation 仍由 Agent 按本 Skill 与对应 reference 判断。

# Completion report

每个 target 的 `completion_report.yaml` 记录 1.6 实际完成的修改，不复制 1.5 的诊断过程。

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

added_heavy_atoms:
  - chain_id: A
    resid: 125
    residue_name: ARG
    atom_names: [<atom_name>, ...]
    coordinate_reference: /absolute/path/to/reference_or_component_file

added_residues:
  - chain_id: A
    residues:
      - resid: 101
        residue_name: GLY
      - resid: 102
        residue_name: SER
    coordinate_reference: /absolute/path/to/reference_structure
    repair_adjustment: <only when applicable>

unresolved_items: []
```

这里的 YAML 定义正式结果的最低组织要求，不要求建立额外 rigid schema。

规则：

- `input_structure`、`source_completeness_report`、`output_structure` 和实际使用的 `coordinate_reference` 均记录完整绝对路径；
- 连续 missing residues 可以在一个 `added_residues` record 中成组记录，但每个实际新增 residue 的 `resid + residue_name` 必须明确；
- deletion / rename 不重复复制 1.5 的 reference provenance；
- completion operation 记录实际提供最终坐标的 reference / template；比较过但未用于最终坐标的候选 reference 不写入正式 completion report；
- 如果原 missing-heavy-atom item 因 shared-heavy-atom anchors 不足而改按 missing-residue 方法处理，在对应 `added_residues` record 中记录：

```yaml
repair_adjustment: insufficient shared-heavy-atom anchors; treated as missing residue
```

- 如果 whole-residue completion 实际删除了原 partial residue 中已有的 atoms，这些实际删除也要逐项记录在 `removed_atoms` 中；
- `unresolved_items` 只记录当前 repair scope 内未能完成的 item 及原因；用户明确改变当前 repair scope 时，不把已排除的 repair 伪装成 unresolved item。

# Validation

Validation 属于 1.6 结果 owner。对当前 target 完成以下核验，并写入 `completion_validation.md`：

- 1.5 中每个 required repair item 都已闭合：missing heavy atom 已通过 atom-level completion 补入，或已按完整 residue completion 正确处理；missing residue 已位于正确的 target chain / residue identity；confirmed extra atom 已删除；confirmed atom-name mismatch 已按确认关系修改；
- `completion_report.yaml` 与 `completed_structure.pdb` 中的实际修改一致；
- 除 repair scope 以及 method reference 明确要求的整 residue replacement 外，没有未记录的额外删除、rename 或 coordinate replacement；
- 新增 heavy atom / residue 满足对应 method reference 的 correspondence、alignment 和局部 geometry requirements；
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

Warning 独立记录；warning 本身不建立第三种 conclusion。

以下情况属于 blocking failure：required repair 未解决、target identity 错误、必要 reference correspondence 不可靠、missing-residue completion 不能满足 required alignment / junction conditions、出现明显不合理的局部连接或 severe steric clash、存在 duplicate identity、PDB 无法解析、atom serial 不连续/不唯一、错误加入 final H，或 `unresolved_items` 非空。

Validation 不重新执行 1.5 completeness diagnosis。

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

登记时提供简短说明，使后续执行能够明确这两个文件分别是 Stage 1.6 对当前 target 完成既定 structure repair items 后的正式结构和修改报告。

`project_result_index.md` 的内部组织格式由项目级 record owner 管理，本 Skill 不重新定义。

# References / supporting capabilities

按实际 repair item 读取：

```text
references/missing_heavy_atom_completion.md
→ missing-heavy-atom completion and atom-level eligibility assessment

references/missing_residue_completion.md
→ residue-level coordinate completion

scripts/README.md
→ deterministic helper CLI 与 task-local data formats
```

# User confirmation

如果 repair scope 已明确，但当前 evidence 仍不足以唯一建立 required reference correspondence、缺少可用 coordinate reference，或多个可行方案之间存在会影响结构正确性的实质科学歧义，向用户说明当前对象、现有 evidence 和具体歧义后确认。

确认前不发布可误认作完成状态的正式结果。
