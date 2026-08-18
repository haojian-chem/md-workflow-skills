# Workflow 1 / Stage 1.6 Structure completion architecture freeze

Status: **FROZEN ARCHITECTURE RECORD — ACTIVE SKILL GENERATED**

## 0. 文档定位

本文件保存 `1.6 Structure completion` 在正式 Skill generation 前已经冻结、且仍具有架构意义的设计事实。

当前 runtime authority 已转为：

```text
01_structure_preparation/1.6_structure_completion/SKILL.md
```

具体可变执行细节、reference 方法和 helper interface 由 current `SKILL.md` / `references/` / `scripts/README.md` 拥有；本 freeze 不再维护第二套平行 mutable specification。

Source preservation:

- former active pseudo-Skill: `01_structure_preparation/1.6_missing_region_completion/SKILL.md`, blob `5108970ba61c2c913e57039a54238e6b8bf150a8`
- historical operation source: `02_operations/missing_region_completion/SKILL.md`, blob `4dbafe0f7501ebd5e36e4d45486b52809f3a248e`
- historical validation source: `02_validators/missing_region_completion_validator/SKILL.md`, blob `73c7982650c3e9862213c67981bc59c684376b7b`

## 1. Purpose and boundary

1.6 将 1.5 正式 `structure_completeness_report.yaml` 中已经明确的 Stage 1 repair items 落实到当前 retained target structure，得到完成这些修复后的重原子结构。

1.6 不重新决定什么是 missing / extra / mismatch，也不通过 coordinate reference 扩大既定 repair scope。

## 2. Required object / evidence

架构要求至少消费：

- 当前 target 的现行 PDB；
- 1.5 正式 `structure_completeness_report.yaml`；
- 实际需要补全 missing heavy atom / missing residue 时的 coordinate reference / template；
- 已经确认的 residue / atom identity 与 rename correspondence。

Reference / template 只在对应 repair item 实际需要时提供，不是所有 1.6 execution 的无条件前置输入。

## 3. Frozen repair sequence

处理顺序固定为：

```text
confirmed extra atom deletion
→ confirmed atom-name correction
→ missing-heavy-atom processing
   ├─ atom-level anchors sufficient
   │  → complete listed missing heavy atoms
   └─ atom-level anchors insufficient
      → treat that repair item as whole-residue completion
      → merge with adjacent missing-residue region when applicable
→ missing-residue completion
   (original missing residues + items adjusted from missing-heavy-atom handling)
→ final atom-serial renumbering
```

先处理 missing-heavy-atom items 的原因是：其中部分 residue 可能因 shared-heavy-atom anchors 不足而需要改按完整 residue completion 处理；如果这类 residue 与原有 missing residues 连续，应在 residue-level completion 前合并为同一连续区域。

Whole-residue treatment 只是同一 repair item 的处理方式调整，不是新增 repair scope。

## 4. Missing-heavy-atom architecture

- coordinate reference 可以来自明确对应的 AF3 residue、CCD component coordinate template 或其它可靠 reference；
- 不建立固定 `AF3 > CCD` 来源优先级，实际选择以可确认 correspondence 与局部几何适配为准；
- 使用当前 residue 中已有 shared heavy atoms 做局部 rigid-body alignment；
- 至少需要 3 个 uniquely mapped、non-collinear shared heavy atoms；
- 满足 atom-level anchor 要求时，只 transplant repair scope 中明确缺失的 heavy atoms，不替换已有 valid heavy-atom coordinates；
- 不满足 atom-level anchor 要求时，该 repair item 改按完整 residue completion 方法处理，并纳入后续 residue-level completion set；
- 不添加 final H。

详细规则由 current：

`01_structure_preparation/1.6_structure_completion/references/missing_heavy_atom_completion.md`

拥有。

## 5. Missing-residue architecture

Residue-level completion set 包括：

- 1.5 report 原本列出的 missing residues；
- 因 missing-heavy-atom anchor 不足而改按完整 residue completion 处理的 residue。

连续的 residue-level items 在 completion 前应合并为实际连续 region。

方法要求：

- 主要使用与当前 target 对应的完整 AF3 structure 或其它明确对应的完整 coordinate reference；
- 使用 AF3 前，先对含 missing region 的整个 target polymer chain 建立完整 residue-level correspondence；
- full polymer-chain correspondence 用于 identity mapping，不等于对整条 chain 做全局结构 alignment；
- internal missing region 使用 local bilateral anchors，并由两侧共同确定一个 rigid transform；
- anchor 从缺失区附近开始逐步扩展，不固定 N residues；
- terminal missing region 使用 one-sided local anchor，不人为构造 bilateral constraint；
- 只 transplant 当前 residue-level completion set 中需要补全的 residues；
- reference numbering / chain identity 不替代 target identity；
- 如果当前 reference 不能形成稳定、合理的 required local alignment，不强行插入。

详细规则由 current：

`01_structure_preparation/1.6_structure_completion/references/missing_residue_completion.md`

拥有。

## 6. Reuse architecture

已有 1.6 结果只有在以下影响结果的内容均明确等价时才可自动复用：

- 输入结构；
- 1.5 repair report；
- 实际使用并影响结果的 coordinate references / templates；
- 影响结果的用户决定；
- 既有 validation 与正式结果完整性。

用户明确要求重做或重新比较 reference 时不自动复用。

## 7. Validation architecture

Validation 属于 1.6 结果 owner，不恢复独立 Validator layer。

至少确认：

- 1.5 required repair items 全部闭合；
- missing-heavy-atom item 已通过 atom-level completion 补入，或已经按完整 residue completion 正确处理；
- `completion_report.yaml` 与最终 PDB 的实际修改一致；
- 新增 heavy atom / residue 满足对应 correspondence、alignment 和局部 geometry requirements；
- 没有未记录的额外 structure edits；
- duplicate identity、PDB parse、atom serial、final-H boundary 均满足要求；
- `unresolved_items` 为空。

任一 required repair 未解决时，1.6 不能完成。Validation 不重新执行 1.5 completeness diagnosis。

## 8. Frozen formal-result direction

当前正式 Skill 已实现每个 target 的结果：

```text
<project_root>/01_structure_preparation/06_structure_completion/<task_id>/<target_id>/
├── completed_structure.pdb
├── completion_report.yaml
└── completion_validation.md
```

项目级 result registration 白名单由 current 1.6 Skill 定义。

## 9. Generation outcome

正式生成后采用：

```text
01_structure_preparation/1.6_structure_completion/
├── SKILL.md
├── references/
│   ├── missing_residue_completion.md
│   └── missing_heavy_atom_completion.md
└── scripts/
    ├── README.md
    ├── transplant_coordinates.py
    └── apply_structure_edits.py
```

没有恢复旧 `Operation + Validator` 双层包装，也没有建立额外 runtime dispatcher/state layer。

Stage-level 相邻 Step handoff 继续由 `01_structure_preparation/SKILL.md` 拥有，不在本 freeze 或 1.6 main Skill 中定义下游 Step 的内部执行规则。
