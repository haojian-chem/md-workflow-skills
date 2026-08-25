# Workflow 1 / Stage 1.7 Protein protonation assignment architecture freeze

Status: **FROZEN ARCHITECTURE RECORD — ACTIVE SKILL GENERATED**

Current runtime authority:

`01_structure_preparation/1.7_protein_protonation_assignment/SKILL.md`

Current scientific-rule authority:

`01_structure_preparation/1.7_protein_protonation_assignment/references/protonation_assignment_rules.md`

Stage 1 atom-mapping authority:

```text
references/atom_mapping_rules.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_ATOM_MAPPING_MAINTENANCE_FREEZE.md
```

## 0. 文档定位

本文件保留 `1.7 Protein protonation assignment` 的架构事实、责任边界和 generation history。

1.7 已于 2026-08-18 获得用户明确批准并正式生成 active Skill。自正式生成后，可变的执行细节、scientific judgment 细则、report format、validation 和正式结果生命周期由 current `SKILL.md` / reference 拥有；本 freeze 不再维护一份平行可变规范。

Source preservation:

- former active pseudo-Skill: `01_structure_preparation/1.7_protein_protonation_assignment/SKILL.md`, blob `8e57488383663411fa996df1cd985c356fdb7d6c`
- historical operation source: `02_operations/protein_protonation_assignment/SKILL.md`, blob `632e03e6507a598dd9adab3ec6a4690c40afedda`
- historical validation source: `02_validators/protein_protonation_validator/SKILL.md`, blob `a7e2d4f24367837492953264f3472a4e0a934a64`

## 1. Frozen responsibility boundary

1.7 的责任是：

```text
protein protonation assignment
→ target-force-field / naming-convention residue name
```

当前 scientific scope 为：

```text
Asp
Glu
His
```

1.7 将 protonation assignment 落实为 residue-name modification。其结构写入边界保持为：只允许修改 residue name，不加入 final H，不改变 heavy-atom set、atom names、coordinates 或 residue / atom order。

是否在某个 Stage 1 task route 中执行 1.7，以及当前结构由哪个上游 Step 提供，不属于 1.7 自身的 applicability / route-planning ownership。1.7 只要求接收到当前任务认可、足以支持 protonation assignment 的有效 heavy-atom structure，以及与该输入结构对应的最近正式 Stage 1 atom map。

## 2. Frozen required conditions

执行 1.7 时必须明确：

- 当前有效 heavy-atom structure；
- 与该输入结构对应的正式 atom map；
- `target_pH`；
- 当前 protein force field 或明确的 protonation-state residue naming convention；
- 可执行 PROPKA；
- 当前 protonation 判断实际需要的已确认 chemical relation / structural evidence。

如果 pH 或 naming information 未能由当前正式项目信息明确，则由当前用户可见 Agent 向用户确认；不自行假设默认 pH 或默认 force field。

## 3. Frozen scientific architecture

PROPKA 在 1.7 中提供 predicted pKa evidence，不直接承担最终 residue naming decision。

最终 protonation assignment 由两类平级 evidence 共同支持：

```text
Henderson–Hasselbalch assessment
+
local chemical environment assessment
```

Asp / Glu 判断一个 carboxyl protonation state。

His 分别判断 `ND1` 与 `NE2` 两个位点，再由两个 site assignments 得到最终 His state。

如果两类 evidence 不能形成可靠闭合结论，或存在无法可靠解释的冲突，则向用户确认，不静默选择。

具体 `Δ = pKa - pH` 默认阈值、environment evidence、His site semantics 与 evidence-combination rules 由 current `references/protonation_assignment_rules.md` 拥有。

## 4. Frozen execution policy

1.7 不设置结果 reuse 环节。

原因是当前任务中 PROPKA 与 assignment 重跑成本低，而证明既有结果与当前 structure / pH / force field / chemical evidence 完全等价的核验成本更高。每次实际进入 1.7 都重新运行 PROPKA 并重新完成 assignment。

## 5. Frozen atom-mapping behavior

1.7 是 Stage 1 chained atom-map producer。它复制与输入 heavy-atom structure 对应的正式 map，并按共享规则更新：

- atom set、atom name、coordinates、atom order 均保持不变；
- `original_atom_serial`、`component_id + residue_id` 和既有 `operations` history 保持不变；
- `current_atom_serial` 与输出结构保持一致；
- 只有 residue name 实际发生变化的 residue，其全部 atom records 追加 `1.7RENAME`；
- residue name 未变化时不追加 1.7 operation。

详细 map 字段、copy-and-update 规则与 operation code 由 `references/atom_mapping_rules.md` 拥有，并冻结于 `WORKFLOW1_STAGE1_ATOM_MAPPING_MAINTENANCE_FREEZE.md`。

## 6. Frozen result direction

当前正式结果方向保持为：

```text
protonation_assigned_structure.pdb
atom_mapping.yaml
protonation_assignment_report.yaml
protonation_validation.md
```

每个 target 独立组织在：

```text
01_structure_preparation/07_protein_protonation_assignment/<task_id>/<target_id>/
```

项目级结果索引登记：

```text
protonation_assigned_structure.pdb
protonation_assignment_report.yaml
```

`atom_mapping.yaml` 是正式结果，但不要求单独登记 project result index；由 `protonation_assignment_report.yaml.output_atom_mapping` 定位。

固定 report format、validation checks 与正式结果完成条件由 current `SKILL.md` 拥有。

## 7. Generation outcome

正式 package：

```text
01_structure_preparation/1.7_protein_protonation_assignment/
├── SKILL.md
└── references/
    └── protonation_assignment_rules.md
```

当前没有为 1.7 建立 `schemas/`、`scripts/` 或 supporting Skill；现有职责不需要 parser/workflow wrapper 或额外 deterministic helper。

Stage 1 main 的 1.7 applicability / route wording 与 current-entry 更新由其 owner window 处理；相关 cross-Skill finding 已记录于：

`00_authoring/coordination/window_work_orders/STAGE1_MAIN_FOLLOWUP_FROM_1.7.md`