---
name: structure_completeness_check
description: 结构准备 1.5。对每个当前 target 独立执行结构完整性检查：在 1.2 已有诊断基础上限定到 1.3 selection，并对 1.4 实际处理过的残基在当前结构上重新诊断，生成可追溯的 structure_completeness_report.yaml；本步骤不修改结构。
---

# Purpose

完成结构准备 `1.5 Completeness check`。

本 Skill 对当前 target 的当前结构执行完整性检查，并形成该 target 独立的正式 `structure_completeness_report.yaml`。

1.5 本身就是检查环节。它不再建立一套新的 completeness taxonomy，也不修改结构。

每个 target 独立检查、独立生成报告。

# Scope and boundaries

本 Skill 负责：

- 将 1.2 已有 completeness / heavy-atom diagnosis 限定到 1.3 当前 target 的 selection；
- 从 1.2 已确认的 missing-residue 信息中提取当前 target 的缺失范围；
- 根据 1.4 正式报告定位实际经过 alternate-conformation 处理的 residue；
- 对这些 residue 在当前结构上重新执行与 1.2 相同语义的 atom-level completeness diagnosis；
- 记录当前 target 的完整性问题及其判据来源；
- 生成并登记当前 target 的正式 completeness report。

本 Skill 不负责：

- 重新执行 1.2 的 component / residue classification；
- 重新决定 1.3 selection；
- 重新决定 1.4 altLoc / alternate-conformation 选择；
- 修改、补全、删除、改名或优化结构中的 atom / residue；
- 定义后续步骤内部如何处理本报告。

# Inputs / evidence

对每个 target，至少需要：

- 当前实际接受检查的 PDB；
- 1.2 正式 `classification_result.yaml`；
- 与该 1.2 结果对应的正式 `reference_manifest.yaml`；
- 1.3 当前 target 的 `target_xxx.yaml`；
- 如果该 target 实际执行过 1.4：1.4 正式 `altloc_resolution_report.yaml`；
- 当前检查实际需要的 force-field residue definition 或 CCD component file。

当前 PDB 通常为 1.4 输出结构；如果当前 target 没有执行 1.4，则使用当前最新的 1.3 target PDB。

`reference_manifest.yaml` 用于定位和核对 1.2 实际使用过的 force-field / CCD reference 及其文件 identity；1.5 不在本 Skill 中重新定义 1.2 的 manifest 结构。

1.5 不设置 reuse 环节。进入本步骤后，对当前 target 完成本次检查并生成当前报告。

# Reference basis

1.5 的 atom-level completeness diagnosis 沿用 1.2 已定义的诊断语义，不在本 Skill 中重新建立问题类型或比较规则。

如果用户在 1.2 已经明确指定过 atom-level completeness 的检查依据，1.5 沿用该依据，并通过 1.2 `classification_result.yaml` 与对应 `reference_manifest.yaml` 定位实际 reference。

如果用户在 1.2 没有明确指定检查依据，则在需要执行 1.5 新诊断前向用户确认。推荐：

- standard residue：基于目标 force field 的 residue definition；
- nonstandard residue：基于 CCD component definition。

如果 standard residue 需要基于 force field 检查但目标 force field 尚未明确，先向用户确认具体 force field。

如果 nonstandard residue 缺少可用的 CCD definition，或现有参考不足以形成可靠判断，不自行猜测；向用户说明当前对象和缺失的判据，由用户确认或提供参考后继续。

如果 1.2 结果表明使用过某类 reference，但当前 `reference_manifest.yaml` 无法定位到实际文件，不能把仅有的 reference name 当作足以完成 1.5 新诊断的依据；先解决 reference 定位问题。

# Execution guidance

## 1. 确定当前 target 与编号映射

以 1.3 当前 `target_xxx.yaml` 为 selection 与 identity mapping 的正式入口。

1.5 报告中的 residue 定位使用当前 target PDB 的：

```text
chain_id + resid
```

同时，存在坐标的 residue issue 保留 1.2 已物化的 `residue_id`，用于与 1.2 正式结果关联。

不得把 1.2 source residue number 直接当作当前 target 的 `resid`。当前 `chain_id + resid` 必须通过 1.3 已保存的 mapping 确定。

## 2. Missing residues

从 1.2 已确认的 missing-residue 诊断中，只提取属于当前 1.3 target selection 的内容。

使用 1.3 target mapping 将 selected missing residues 定位到当前 target 的 `chain_id + resid`。

同一 chain 中连续的 missing residues 合并为连续范围记录；单个 missing residue 使用 `start_resid == end_resid` 表示。

这里的“连续”必须同时满足：这些 missing residues 在 1.2 authoritative `residue_records[]` 顺序中彼此连续，并且该连续区间没有跨过未被当前 target 选择的 residue。不能仅因为 1.3 重新分配后的 `resid` 数值相邻，就把原本被未选择区域分开的缺失区段合并。

1.5 不根据 PDB residue-number gap、chain break 或坐标缺口重新猜测 missing residue。

## 3. Residue-level atom completeness

先将 1.2 已有 atom-level diagnosis 限定到当前 1.3 target selection。

如果当前 target 没有执行 1.4，则当前 selected residues 的 atom-level diagnosis 直接来自 1.2 已有结果。

如果当前 target 执行过 1.4：

1. 读取当前 target 对应的 `altloc_resolution_report.yaml`；
2. 识别 1.4 实际处理过的 residue；
3. 对这些 residue 基于当前 PDB 重新执行与 1.2 相同语义的 atom-level completeness diagnosis；
4. 这些 residue 使用 1.5 当前诊断结果，不再沿用其 1.2 atom-level diagnosis；
5. 未被 1.4 实际处理的 selected residues 不重复诊断，使用 1.2 已有结果。

如果 1.4 的一个 resolved group 实际涉及多个 residues，则对该 group 中实际受 1.4 处理影响的 residues 分别完成当前诊断。

只有存在 completeness issue 的 residue 写入 `residue_issues`；没有问题的 residue 不需要逐项复制进正式报告。

具体 issue type 沿用 1.2 已定义的诊断语义。1.5 不新增、重命名或重新分类这些问题类型。

## 4. 判据不足

如果某个应检查 residue 的参考依据不足，无法形成可靠判断：

- 不将其静默判为正常；
- 不自行构造预期 atom set；
- 不写入猜测性问题；
- 向用户说明 residue、当前可用依据和缺失信息。

关键检查依据未解决时，当前 target 的 1.5 尚未完成，不生成可误认作最终完成结果的正式报告。

# Official result

每个 target 独立生成：

```text
<project_root>/01_structure_preparation/05_completeness_check/<task_id>/<target_id>/structure_completeness_report.yaml
```

例如：

```text
01_structure_preparation/05_completeness_check/T0001/target_001/structure_completeness_report.yaml
01_structure_preparation/05_completeness_check/T0001/target_002/structure_completeness_report.yaml
```

1.5 不生成新的 PDB。报告中的 `structure` 直接指向本次实际检查的当前 PDB。

## Report organization

每份报告只描述一个 target，不建立多-target 汇总层。

报告至少包含：

```yaml
target_id: target_001
structure: /absolute/path/to/current/target_001.pdb

source_reports:
  classification_result: /absolute/path/to/classification_result.yaml
  reference_manifest: /absolute/path/to/reference_manifest.yaml
  selection_target: /absolute/path/to/target_001.yaml
  altloc_resolution_report: /absolute/path/to/altloc_resolution_report.yaml

missing_residues:
  - chain_id: A
    start_resid: 12
    end_resid: 18
    source_report: classification_result

residue_issues:
  - residue_id: <residue_id>
    chain_id: A
    resid: 25
    residue_name: LEU
    issues:
      - type: <1.2-defined issue type>
        atoms:
          - <atom_name>
        source_report: classification_result

      - type: <1.2-defined issue type>
        atoms:
          - <atom_name>
        reference_file: /absolute/path/to/forcefield/aminoacids.rtp
        reference_entry: LEU
```

这里的 YAML 只说明最低组织要求，不建立额外 rigid schema。

如果当前 target 没有执行 1.4，则不写空的 `altloc_resolution_report` 字段。

### Source-path rules

`structure` 与 `source_reports` 中的文件必须记录完整绝对路径。

上游报告路径放在 target 一级的 `source_reports` 中，具体判据项只引用对应 key，例如：

```yaml
source_report: classification_result
```

`reference_manifest` 作为 1.2 实际 reference provenance 的正式入口放在同一级，不要求每个 issue 重复写 manifest 路径。

如果某个 issue 是 1.5 在当前结构上新完成的判断，则不写 `source_report: classification_result` 伪装成上游判断，而是直接记录本次实际使用的 reference file 完整绝对路径。

对 force-field reference，可以在需要时同时记录实际 residue entry；对 CCD reference，记录实际使用的 CCD component file 完整绝对路径。

### Missing-residue organization

`missing_residues` 以当前 target 的 `chain_id + resid range` 记录。

同一 chain 中只有在 1.2 authoritative residue order 上真正连续、且没有跨过未 selected residue 的 missing residues 才合并为一条 range。不同 chain、不同连续区间，或中间存在未 selected residue 的情况分别记录。

### Residue-issue organization

`residue_issues` 以 residue 为组织单位。

同一个 residue 存在多个问题时，只建立一个 residue record，并在其 `issues` 下列出全部问题；不要为每个问题重复一份 residue identity。

每个 issue 至少应能够表达：

- 1.2 已定义的 issue type；
- 涉及的 atom name（适用时）；
- 判据来自哪个上游报告，或 1.5 新判断实际使用的 reference file。

# Completion requirements

1.5 不再对 completeness science 做第二轮重复检查。正式报告生成前只确认本次检查结果已经完整、可定位、可追溯：

- 当前 target 与实际检查 PDB 已唯一确定；
- 报告中的 `chain_id + resid` 与 1.3 target mapping 一致；
- 1.2 `classification_result.yaml` 与对应 `reference_manifest.yaml` 能够定位本次需要沿用的 reference basis；
- 当前 selection 中的 missing residues 已按真实连续区间记录，没有因 1.3 resid 重新编号而跨未 selected residue 错误合并；
- 1.4 实际处理过的 selected residues 已基于当前 PDB 完成 atom-level diagnosis；
- 未被 1.4 处理的 selected residues 使用 1.2 已有 diagnosis，没有因 1.5 再次重复检查；
- 每个 residue issue 都能定位到明确 residue，涉及 atom 时能够定位到明确 atom name；
- 来自上游的判断能够通过 `source_report` 定位到 target 一级登记的完整报告路径；
- 1.5 新判断记录了实际使用的 force-field / CCD reference file 完整绝对路径；
- 没有尚未解决的关键检查依据；
- 1.5 没有修改当前结构。

这些要求只确认 1.5 的结果是否完整可用，不重新重复执行一次 completeness diagnosis。

# Project result registration

每个 target 的 `structure_completeness_report.yaml` 都是独立正式结果。

生成正式报告后，将该报告的完整绝对路径登记到：

```text
<project_root>/00_project_records/project_result_index.md
```

登记时至少提供：

- `structure_completeness_report.yaml` 的完整绝对路径；
- 简短说明：该文件是 Stage 1.5 当前 target 的正式结构完整性检查结果，记录 missing-residue ranges、residue-level completeness issues 及对应判据来源。

`project_result_index.md` 只负责正式结果检索；本 Skill 不复制或重新定义其内部组织格式。
