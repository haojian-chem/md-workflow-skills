---
name: structure_preparation_validation
description: 结构准备 1.9。对每个 target 的 Stage 1 final PDB 进行只读终检，逐项检查 PDB 表示、标准残基在目标力场中的定义与重原子、非标准残基与 CCD 的对应关系，以及 final map 的逐原子对应与 provenance 连续性，并生成独立验证报告。
---

# 1.9 Structure preparation validation

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

Stage 1 原子映射维护规则读取：

`../../references/atom_mapping_rules.md`

1.9 的 final PDB / final map 逐原子验证必须按该共享规则解释。

本 Skill 只定义 1.9 的最终检查对象、判据、报告和结果边界。

## Purpose

对当前 target 的 Stage 1 最终结构独立执行一次只读检查，形成供后续处理审阅的 `structure_preparation_validation.md`。

1.9 检查当前最终结果本身，不重新执行 1.4–1.8 的内部处理逻辑，也不在检查过程中修改、补全、删除或改名任何原子或残基。

报告逐项记录实际检查结果和发现的问题。1.9 不为整个 target 生成 `PASS / FAIL`，也不根据问题数量自行决定是否进入后续阶段；是否返回上游处理或继续后续任务，由当前 Task Execution Agent 与用户根据报告中的实际结果决定。

每个 target 独立检查、独立生成报告。

## Object requirements

每个 target 至少需要：

- 1.8 正式 `stage1_final.pdb`；
- 1.8 正式 `stage1_final_map.yaml`；
- `stage1_final_map.yaml.original_structure` 指向的原始结构；
- 与当前 target 对应 model 的 1.2 正式 `classification_result.yaml`；
- 当前 target 的 1.5 正式 `structure_completeness_report.yaml`；
- 当前指定目标力场中用于标准残基检查的实际 `*.rtp` 文件；
- 当前非标准残基检查实际采用的 CCD 文件。

`classification_result.yaml` 用于按 `component_id + residue_id` 读取对应 residue 的正式 `topology_class.value`、文件级 `references` 和 `topology_linked_checks[]`。不得根据残基名、`ATOM / HETATM` record 或当前空间位置重新分类。

`stage1_final_map.yaml` 用于把 final PDB 中每个实际重原子对应到原始结构中的 atom serial（若存在），并保持 1.2 已物化的 `component_id + residue_id` 与 Stage 1 operation history。1.9 只验证该 final PDB / map 结果，不修改 map。

如果目标力场尚未唯一确定，或当前非标准 residue 的 CCD reference 无法从 1.2 / 1.5 正式结果中可靠定位，不自行选择新的参考文件。先向用户说明缺失的判据，待检查依据明确后再完成对应检查。

## No reuse

1.9 **不设置 reuse**。

每次实际进入 1.9，都针对当前 `stage1_final.pdb`、当前 `stage1_final_map.yaml` 和当前指定的参考文件重新执行本次检查；不通过 `project_result_index.md` 查找或复用既有 1.9 报告。

## Work directory and multiple targets

真实项目基础目录：

```text
<project_root>/01_structure_preparation/09_validation/
```

当前 Task 的每个 target 独立生成：

```text
<project_root>/01_structure_preparation/09_validation/<task_id>/<target_id>/
└── structure_preparation_validation.md
```

不建立 task 级多-target 汇总报告。

## Reference basis

### STANDARD_RESIDUE

对 `STANDARD_RESIDUE` 使用当前指定目标力场中的标准残基定义。

标准残基定义的定位沿用 1.2 已确定的精确 `*.rtp` 同名匹配语义：按 final PDB 中的 `residue_name` 查找精确同名的 residue block，不通过大小写归一化、模糊匹配、字符串增删或端基 patch 构造替代条目。

### TOPOLOGY_LINKED_NONSTANDARD / INDEPENDENT_NONSTANDARD

对 `TOPOLOGY_LINKED_NONSTANDARD` 和 `INDEPENDENT_NONSTANDARD`，沿用 1.2 / 1.5 已确定的 CCD reference。

- 对未被 1.4 改动、直接沿用 1.2 重原子检查依据的 residue：从 1.2 对应 residue 的 `heavy_atom_check.evidence` 读取 `{CCD_PATH_n}/XXX.cif`，并通过同一 `classification_result.yaml.references` 解析实际路径；
- 对 1.4 处理后由 1.5 重新执行重原子检查的 residue：使用 1.5 `structure_completeness_report.yaml` 中记录的实际 evidence，并按需要通过 1.2 `classification_result.yaml.references` 解析变量。

1.9 不为非标准残基重新选择 CCD，也不使用 alternate atom name 自动替代 final PDB 中实际原子名。

### SOLVENT_COMPONENT / ION_COMPONENT

`SOLVENT_COMPONENT` 和 `ION_COMPONENT` 在当前阶段没有确定对应力场，因此不执行本 Skill 中的力场 / CCD 重原子比较。它们仍属于 final PDB 的 PDB 表示检查和 final map 逐原子检查范围。

## Checks

按以下项目独立检查并逐项写入报告。

### 1. PDB 可读取性

确认 `stage1_final.pdb` 能够被可靠解析为当前结构对象。

如果 PDB 无法可靠读取，记录实际解析问题。依赖可靠结构解析的后续检查不得伪造结果。

### 2. PDB serial

按 `stage1_final.pdb` 中的实际写出顺序检查：

- `ATOM / HETATM / TER` serial 从 1 连续编号；
- serial 不重复。

该检查只核对 1.8 已定义的 final PDB serial 规则，不增加其它 serial 约束。

### 3. Alternate conformation

独立检查当前 `stage1_final.pdb` 是否只保留唯一构象。

对于 PDB 表示，已保留原子不应再存在未解决的 `altLoc`。如果仍发现 alternate conformation / `altLoc` 记录，按当前 final PDB 中的 `chain_id + resid + residue_name` 定位并如实记录；1.9 不重新决定应选择哪个构象。

### 4. STANDARD_RESIDUE 残基定义

对 final PDB 中所有 `STANDARD_RESIDUE`：

1. 通过 `stage1_final_map.yaml` 的 `current_atom_serial` 找到当前 atom record，再读取其 `component_id + residue_id` 定位 1.2 正式分类；
2. 读取 final PDB 的 `residue_name`；
3. 在当前指定目标力场的 `*.rtp` 中查找精确同名的 residue block；
4. 记录找不到对应定义的残基。

本项只检查残基名是否存在对应力场定义，不在此处比较重原子。

1.7 已落实到 final PDB 的质子化状态残基名也在本项按相同规则检查，不另设独立质子化检查项目。

### 5. STANDARD_RESIDUE 重原子

对能够在目标力场中找到精确同名定义的 `STANDARD_RESIDUE`，独立比较：

```text
final PDB 中该残基的重原子名称及出现次数
↔
目标力场同名 residue block 中定义的重原子名称及出现次数
```

逐残基检查并如实记录：

- 目标力场定义中存在、final PDB 中缺失的重原子；
- final PDB 中存在、目标力场定义中没有的额外重原子；
- 同一重原子名称出现次数不符合定义的情况。

如果某个 `STANDARD_RESIDUE` 与 `TOPOLOGY_LINKED_NONSTANDARD` 存在于 1.2 `topology_linked_checks[]` 中，且对应记录为 `judgment: CONFIRMED`、`topology_effect_applied: true`，在该标准残基的本项检查记录中标明这一已确认 topology-linked 关系。该关系不自动改变或豁免标准残基的比较结果；相对于目标力场定义多出的或缺少的重原子均按实际结果记录。

### 6. TOPOLOGY_LINKED_NONSTANDARD

对每个 `TOPOLOGY_LINKED_NONSTANDARD`，使用当前正式结果能够定位到的 CCD 文件独立检查：

- final PDB 的 `residue_name` 与 CCD component ID 精确一致；
- final PDB 中该残基的重原子名称及出现次数与 CCD 定义的重原子名称及出现次数严格一致。

逐残基记录缺失、额外或重复的重原子名称。已确认 topology-linked 关系不作为修改 CCD 比较结果的自动例外。

### 7. INDEPENDENT_NONSTANDARD

对每个 `INDEPENDENT_NONSTANDARD`，使用当前正式结果能够定位到的 CCD 文件，按与上一项相同的规则检查：

- final PDB 的 `residue_name` 与 CCD component ID 精确一致；
- final PDB 中该残基的重原子名称及出现次数与 CCD 定义严格一致；
- 缺失、额外或重复的重原子名称均如实记录。

### 8. `stage1_final_map.yaml` 逐原子与 provenance 检查

按 `../../references/atom_mapping_rules.md` 独立验证 final map。

首先确认 final PDB 与 final map 一一对应：

- final PDB 中每个 `ATOM / HETATM` serial 恰好对应一条 `current_atom_serial` 相同的 map record；
- map 不存在 final PDB 中没有的额外 atom record；
- `current_atom_serial` 在 map 内唯一；
- map 的 `current_structure` 指向当前 `stage1_final.pdb`。

然后逐条检查：

```text
current_atom_serial
original_atom_serial
component_id
residue_id
operations
```

要求：

- `component_id + residue_id` 能定位到当前 model 的 1.2 `components[].residues[]`；
- `original_atom_serial != null` 时，该 serial 能定位到 `original_structure` 中唯一 atom；
- `original_atom_serial` 对应原始 atom 与当前 record 的 `component_id + residue_id` 不得冲突；
- `original_atom_serial == null` 时，`operations` 中必须存在使该 atom 在后续 Stage 1 中进入当前结构的 `ADD` operation；
- 由 1.3 直接纳入 target 的原始 atoms 应保留 `1.3ADD`，且其 `original_atom_serial` 非空；
- `operations` 只能使用共享规则已定义的 Step-specific operation code，并保持实际发生顺序；
- operation history 与能够定位到的 1.3 / 1.4 / 1.6 / 1.7 / 1.8 正式结构处理结果不得矛盾。

本项不要求 final map 保留已经从当前结构删除的 atom record；删除历史通过相邻正式 map 与对应 Step 报告追溯。

## Report organization

每份 `structure_preparation_validation.md` 只描述一个 target，采用固定检查顺序，但不建立额外 schema。

报告顶部至少记录本次实际使用的完整路径：

```text
target_id
stage1_final.pdb
stage1_final_map.yaml
original_structure
classification_result.yaml
structure_completeness_report.yaml
目标力场参考文件
本次实际使用的 CCD 文件
```

正文按以下章节组织：

```markdown
# Structure preparation validation

## 1. PDB 可读取性
## 2. PDB serial
## 3. Alternate conformation
## 4. STANDARD_RESIDUE 残基定义
## 5. STANDARD_RESIDUE 重原子
## 6. TOPOLOGY_LINKED_NONSTANDARD
## 7. INDEPENDENT_NONSTANDARD
## 8. stage1_final_map.yaml 逐原子与 provenance 检查
```

每个检查项先给出简短的实际结果摘要；发现问题时再列具体对象。没有问题的普通残基不逐个展开。

问题定位默认使用 final PDB 的：

```text
chain_id + resid + residue_name
```

涉及重原子差异时，在同一残基下分别列出实际缺失、额外或重复的原子名，并记录对应力场文件或 CCD 文件。

第 5 项中，与 `TOPOLOGY_LINKED_NONSTANDARD` 存在已确认 topology-linked 关系的 `STANDARD_RESIDUE` 应单独标明关系背景及其实际重原子比较结果；不把这一信息拆成新的检查项目。

第 8 项发现 atom-map 不一致时，优先使用 `current_atom_serial` 定位 final PDB atom，同时记录 map 中的 `original_atom_serial`、`component_id + residue_id` 与 `operations` 实际值。

报告只写检查事实，例如“未发现……”或“发现 N 个残基存在……”。不设置 section-level 或 overall `PASS / FAIL`，不建立新的状态枚举，也不生成自动后续决策。

## Completion requirements

1.9 的完成条件是本次规定检查已经完整执行并形成可追溯报告，而不是得到某个自动通过状态。

正式结束当前 target 的 1.9 前确认：

- 当前 `stage1_final.pdb`、`stage1_final_map.yaml`、`original_structure` 和 `classification_result.yaml` 已唯一确定；
- `STANDARD_RESIDUE` 检查所需的目标力场参考文件已明确；
- 需要检查的 `TOPOLOGY_LINKED_NONSTANDARD` / `INDEPENDENT_NONSTANDARD` 均能通过当前 1.2 / 1.5 正式结果定位到实际 CCD；
- 八项检查均已按当前对象实际执行并写入报告；
- final PDB 与 final map 的每个实际重原子已经完成一一对应及 provenance 核对；
- 发现的问题能够定位到具体残基，涉及重原子或 mapping 时能够定位到具体原子；
- 报告记录了本次实际使用的参考文件；
- 1.9 没有修改 `stage1_final.pdb`、`stage1_final_map.yaml` 或任何上游正式结果；
- 报告没有生成整体 `PASS / FAIL` 或自动后续决策。

满足这些结果完整性要求后，当前 1.9 可在 Task Sheet 中标记为 `已完成`。如果报告中的问题需要修正，按实际问题返回真正拥有该结构问题的上游步骤处理；修正后的 final result 再次进入 1.9 时重新执行检查。

## Official result

每个 target 的 1.9 结果只有：

```text
structure_preparation_validation.md
```

1.9 **不把该报告登记到**：

```text
<project_root>/00_project_records/project_result_index.md
```

报告保留在当前 Task / target 的 1.9 工作目录中，供当前任务审阅和后续处理使用。
