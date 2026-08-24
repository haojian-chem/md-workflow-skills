---
name: structure_completeness_check
description: 结构准备 1.5。对每个当前 target 独立执行结构完整性检查：在 1.2 已有诊断基础上限定到 1.3 selection，并对 1.4 实际处理过的残基在当前结构上重新检查重原子组成与命名，生成可追溯的 structure_completeness_report.yaml；本步骤不修改结构。
---

# Purpose

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 仅补充 1.5-specific 的对象、执行、validation 与 results 规则；本步骤明确不设置 reuse。

完成结构准备 `1.5 Completeness check`。

本 Skill 对当前 target 的当前结构执行完整性检查，并形成该 target 独立的正式 `structure_completeness_report.yaml`。

1.5 本身就是检查环节。它不重新建立 1.2 已定义的问题类型，也不修改结构。

每个 target 独立检查、独立生成报告。

# Scope and boundaries

本 Skill 负责：

- 将 1.2 已有残基缺失与重原子组成/命名检查结果限定到 1.3 当前 target 的 selection；
- 从 1.2 `missing_residue_check.status: ISSUE` 的 residue 中提取当前 target 的缺失范围；
- 根据 1.4 正式报告定位实际经过 alternate-conformation 处理的 residue；
- 对这些 residue 在当前结构上重新执行与 1.2 相同语义的重原子组成与命名检查；
- 记录当前 target 的结构完整性问题及其判据来源；
- 生成并登记当前 target 的正式 completeness report。

本 Skill 不重新执行 1.2 classification、不重新决定 1.3 selection、不重新决定 1.4 构象选择，也不修改当前结构。

# Inputs / evidence

对每个 target，至少需要：

- 当前实际接受检查的 PDB；
- 当前 model 的 1.2 正式 `classification_result.yaml`；
- 1.3 当前 target 的 `target_xxx.yaml`；
- 如果该 target 实际执行过 1.4：1.4 正式 `altloc_resolution_report.yaml`；
- 当前重新检查实际需要的 force-field residue definition 或 CCD component file。

当前 PDB 通常为 1.4 输出结构；如果当前 target 没有执行 1.4，则使用当前最新的 1.3 target PDB。

1.2 本次实际使用的 RTP / CCD reference 由 `classification_result.yaml` 文件级 `references` 及各 residue 检查项的 `evidence` 直接定位；1.5 不读取或要求 `reference_manifest.yaml`。

1.5 不设置 reuse 环节。进入本步骤后，对当前 target 完成本次检查并生成当前报告。

# Reference basis

1.5 的重原子组成与命名检查沿用 1.2 已定义的诊断语义，不在本 Skill 中重新建立问题类型或比较规则。

如果 1.2 已为当前 residue 的 `heavy_atom_check.evidence` 指定 `RTP_n` 或 `{CCD_PATH_n}/XXX.cif`，1.5 在需要重新检查该 residue 时解析同一 `classification_result.yaml.references`，沿用该实际 reference。

如果 1.2 的正式结果没有提供足以完成当前 1.5 新诊断的 reference，不能自行猜测。向用户说明 residue 与缺失的判据，由用户确认或提供实际 reference 后继续。

# Execution guidance

## 1. 确定当前 target 与编号映射

以 1.3 当前 `target_xxx.yaml` 为 selection 与 identity mapping 的正式入口。

1.5 报告中的当前 residue 定位使用 target PDB 的：

```text
chain_id + resid
```

同时保存 1.2 的：

```text
component_id + residue_id
```

用于与 1.2 正式结果关联。

不得把 1.2 的 `source_resid` 直接当作当前 target 的 `resid`。当前 target 定位必须通过 1.3 mapping 确定。

## 2. Missing residues

从 1.2 `components[].residues[]` 中，只提取当前 1.3 target selection 内 `missing_residue_check.status: ISSUE` 的 residue。

使用 1.3 target mapping 将 selected missing residues 定位到当前 target 的 `chain_id + resid`。

同一 chain 中连续的 missing residues 可以合并为连续范围；这里的连续性依据 1.2 所属 component 内 `residues` 的正式数组顺序，并且不能跨过未被当前 target 选择的 residue。不能仅因为 1.3 重新分配后的 `resid` 数值相邻就合并。

1.5 不根据 PDB residue-number gap、chain break 或坐标缺口重新猜测 missing residue。

## 3. Residue-level heavy-atom composition and naming

先将 1.2 已有 `heavy_atom_check` 结果限定到当前 1.3 target selection。

如果当前 target 没有执行 1.4：

- `heavy_atom_check.status: ISSUE` 的 selected residue 直接作为当前 completeness issue；
- `PASS` / `NOT_APPLICABLE` 不产生 residue issue；
- 因 1.2 多构象问题而 `SKIPPED` 的 residue 不在这里伪造重原子结论，应由实际 1.4 处理结果决定是否需要重新检查。

如果当前 target 执行过 1.4：

1. 读取当前 target 对应的 `altloc_resolution_report.yaml`；
2. 识别 1.4 实际处理过的 residue；
3. 对这些 residue 基于当前 PDB 重新执行与 1.2 相同语义的重原子组成与命名检查；
4. 这些 residue 使用 1.5 当前检查结果，不沿用其 1.2 `SKIPPED` 或旧重原子结果；
5. 未被 1.4 实际处理的 selected residue 不重复检查，使用 1.2 已有结果。

只有存在重原子组成或命名问题的 residue 写入 `residue_issues`；没有问题的 residue 不逐项复制进正式报告。

具体 issue type 与问题字段沿用 1.2 `heavy_atom_check`：

```text
missing_heavy_atoms
extra_heavy_atoms
duplicate_atom_names
atom_name_mismatches
element_mismatches
```

## 4. 判据不足

如果某个应检查 residue 的 reference 不足，无法形成可靠判断：

- 不静默判为正常；
- 不自行构造预期 atom set；
- 不写入猜测性问题；
- 向用户说明 residue、当前可用依据和缺失信息。

关键检查依据未解决时，当前 target 的 1.5 尚未完成，不生成可误认作最终完成结果的正式报告。

# Official result

每个 target 独立生成：

```text
<project_root>/01_structure_preparation/05_completeness_check/<task_id>/<target_id>/structure_completeness_report.yaml
```

1.5 不生成新的 PDB。报告中的 `structure` 直接指向本次实际检查的当前 PDB。

## Report organization

每份报告只描述一个 target，不建立多-target 汇总层。

最低组织要求：

```yaml
target_id: target_001
structure: /absolute/path/to/current/target_001.pdb

source_reports:
  classification_result: /absolute/path/to/classification_result.yaml
  selection_target: /absolute/path/to/target_001.yaml
  altloc_resolution_report: /absolute/path/to/altloc_resolution_report.yaml

missing_residues:
  - chain_id: A
    start_resid: 12
    end_resid: 18
    source_report: classification_result

residue_issues:
  - component_id: component_001
    residue_id: residue_025
    chain_id: A
    resid: 25
    residue_name: LEU
    issues:
      - type: missing_heavy_atoms
        atoms: [CD1]
        source_report: classification_result

      - type: atom_name_mismatches
        atoms: [O1]
        evidence: RTP_1
```

如果当前 target 没有执行 1.4，则不写空的 `altloc_resolution_report` 字段。

`source_reports` 中的文件使用完整绝对路径。来自 1.2 的既有判断通过 `source_report: classification_result` 定位；1.5 新执行的重原子判断记录本次实际采用的 evidence。若 evidence 使用 `RTP_n` 或 `{CCD_PATH_n}/XXX.cif`，其变量定义继续由 `source_reports.classification_result` 指向的 1.2 文件解析。

# Completion requirements

正式报告生成前确认：

- 当前 target 与实际检查 PDB 已唯一确定；
- 报告中的 `chain_id + resid` 与 1.3 target mapping 一致；
- 报告中的 `component_id + residue_id` 能定位到当前 model 的 1.2 正式结果；
- 当前 selection 中的 missing residues 来自 1.2 `missing_residue_check.status: ISSUE`，并按真实 residue 顺序组织；
- 1.4 实际处理过的 selected residues 已基于当前 PDB 完成重原子组成与命名检查；
- 未被 1.4 处理的 selected residues 使用 1.2 已有结果，没有因 1.5 再次重复检查；
- 1.5 新判断使用的 `RTP_n` / `CCD_PATH_n` 能在 1.2 `classification_result.yaml.references` 中解析；
- 没有尚未解决的关键检查依据；
- 1.5 没有修改当前结构。

# Project result registration

每个 target 的 `structure_completeness_report.yaml` 都是独立正式结果。

生成正式报告后，将该报告完整绝对路径登记到：

```text
<project_root>/00_project_records/project_result_index.md
```

登记说明该文件是 Stage 1.5 当前 target 的正式结构完整性检查结果，记录 missing-residue ranges、residue-level heavy-atom composition/naming issues 及对应判据来源。
